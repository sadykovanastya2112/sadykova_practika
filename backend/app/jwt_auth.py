from functools import wraps

import jwt
import requests_cache
from flask import current_app, g, jsonify, request, session
from jwt import PyJWKClient

from app.models import Member

requests_cache.install_cache("jwks_cache", expire_after=86400)


def jwt_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        DEBUG_BYPASS_JWT = False
        if DEBUG_BYPASS_JWT:
            g.member_id = 6
            session['member_id'] = 6  # также сохраняем в сессию для единообразия с require_role
            return f(*args, **kwargs)

        auth_header = request.headers.get("Authorization", "")
        if not auth_header.startswith("Bearer "):
            return jsonify({"error": "Missing or invalid Authorization header"}), 401
        token = auth_header[7:]

        try:
            jwks_url = f"{current_app.config['LOGTO_ISSUER']}/jwks"
            jwks_client = PyJWKClient(jwks_url)
            signing_key = jwks_client.get_signing_key_from_jwt(token)
            payload = jwt.decode(
                token,
                signing_key.key,
                algorithms=["RS256", "ES384"],
                audience=current_app.config["LOGTO_CLIENT_ID"],
                options={"verify_exp": True},
            )
            request.jwt_payload = payload
            request.logto_user_id = payload["sub"]
            request.logto_roles = payload.get("https://logto.io/claims/roles", [])

            auth_id = payload["sub"]
            member = Member.query.filter_by(auth_id=auth_id).first()
            if not member:
                return jsonify({"error": "User not found"}), 401
            g.member_id = member.id
            session['member_id'] = member.id   # синхронизируем с сессией

        except jwt.ExpiredSignatureError:
            return jsonify({"error": "Token expired"}), 401
        except jwt.InvalidTokenError as e:
            return jsonify({"error": f"Invalid token: {str(e)}"}), 401
        except Exception as e:
            return jsonify({"error": f"Authentication error\n{str(e)}"}), 401

        return f(*args, **kwargs)

    return decorated


def require_role(role_name):
    def decorator(f):
        @wraps(f)
        def decorated_function(*args, **kwargs):
            print(">>> Request to protected endpoint")
            print("Authorization header:", request.headers.get("Authorization"))
            # Получаем member_id из g (если установлен) или из сессии
            member_id = getattr(g, 'member_id', None)
            if not member_id:
                member_id = session.get('member_id')
            if not member_id:
                return jsonify({"error": "Unauthorized"}), 401

            member = Member.query.get(member_id)
            if not member:
                return jsonify({"error": "User not found"}), 401

            # Проверяем наличие требуемой роли (роли хранятся в member.roles)
            roles_codes = [r.code for r in member.roles]
            if role_name not in roles_codes:
                return jsonify({"error": "Forbidden"}), 403

            return f(*args, **kwargs)
        return decorated_function
    return decorator