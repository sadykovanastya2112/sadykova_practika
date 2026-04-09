from functools import wraps
from flask import request, jsonify, current_app
import jwt
from jwt import PyJWKClient
import requests_cache

requests_cache.install_cache('jwks_cache', expire_after=86400)


def jwt_required(f):
    @wraps(f)
    def decorated(*args, **kwargs):
        auth_header = request.headers.get('Authorization', '')
        if not auth_header.startswith('Bearer '):
            return jsonify({'error': 'Missing or invalid Authorization header'}), 401
        token = auth_header[7:]

        try:
            jwks_url = f"{current_app.config['AUTHGEAR_ISSUER']}/oauth2/jwks"
            jwks_client = PyJWKClient(jwks_url)
            signing_key = jwks_client.get_signing_key_from_jwt(token)
            payload = jwt.decode(
                token,
                signing_key.key,
                algorithms=['RS256'],
                audience=current_app.config['AUTHGEAR_CLIENT_ID'],
                options={'verify_exp': True}
            )
            request.jwt_payload = payload
            request.authgear_user_id = payload['sub']
            request.authgear_roles = payload.get('https://authgear.com/claims/roles', [])
        except jwt.ExpiredSignatureError:
            return jsonify({'error': 'Token expired'}), 401
        except jwt.InvalidTokenError as e:
            return jsonify({'error': f'Invalid token: {str(e)}'}), 401
        except Exception as e:
            return jsonify({'error': 'Authentication error'}), 401

        return f(*args, **kwargs)
    return decorated