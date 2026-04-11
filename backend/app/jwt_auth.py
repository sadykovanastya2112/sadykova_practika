from functools import wraps
from flask import request, jsonify, current_app, g
import jwt
from jwt import PyJWKClient
import requests_cache
from app.models import Member

requests_cache.install_cache('jwks_cache', expire_after=86400)


def jwt_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        DEBUG_BYPASS_JWT = True
        if DEBUG_BYPASS_JWT:
            g.member_id = 1
            return f(*args, **kwargs)
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Missing or invalid Authorization header'}), 401
        token = auth_header[7:]

        try:
            jwks_url = f"{current_app.config['LOGTO_ISSUER']}/oauth2/jwks"
            jwks_client = PyJWKClient(jwks_url)
            signing_key = jwks_client.get_signing_key_from_jwt(token)
            payload = jwt.decode(
                token,
                signing_key.key,
                algorithms=['RS256'],
                audience=current_app.config['LOGTO_CLIENT_ID'],
                options={'verify_exp': True}
            )
            request.jwt_payload = payload
            request.logto_user_id = payload['sub']
            request.logto_roles = payload.get('https://logto.io/claims/roles', [])

            auth_id = payload['sub']
            member = Member.query.filter_by(auth_id=auth_id).first()
            if not member:
                return jsonify({'error': 'User not found'}), 401
            g.member_id = member.id
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token expired'}), 401
        except jwt.InvalidTokenError as e:
            return jsonify({'error': f'Invalid token: {str(e)}'}), 401
        except Exception as e:
            return jsonify({f"error': 'Authentication error\n{str(e)}"}), 401

        return f(*args, **kwargs)
    return decorated