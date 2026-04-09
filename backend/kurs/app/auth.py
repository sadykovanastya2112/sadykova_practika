#bluprint для регистрации
from flask import Blueprint, request, jsonify, current_app, redirect, url_for, session
from authlib.integrations.flask_client import OAuthError
from app.authgear import oauth
from datetime import datetime
from app.extension import bcrypt
from  app.models import users, find_user_by_authID, create_user_by_authID, update_user_role
from app.sсhemas import user_schema
from marshmallow import ValidationError
import secrets

auth_bp = Blueprint('auth', __name__)

@auth_bp.route('/login')
def login():
    #генерим рандомною строку
    state = secrets.token_urlsafe(16)
    nonce = secrets.token_urlsafe(16)
    print(f'Generated state: {state}')
    #сохряет стате в сессии, что бы проверять на возврате
    session['oauth_state'] = state
    session['oauth_nonce'] = nonce
    print("Session saved, session ID:", session.sid if hasattr(session, 'sid') else 'no sid')
    redirect_uri = current_app.config['AUTHGEAR_REDIRECT_URI']
    return oauth.authgear.authorize_redirect(redirect_uri, state=state, nonce=nonce)


@auth_bp.route('/callback')
def callback():
    """
    Обрабатывает возврат от Authgear после успешного (или неуспешного) входа.
    Проверяет state, получает токен и информацию о пользователе
    """

    print(f" Callback received state: {request.args.get('state')}")
    print(f" Session state: {session.get('oauth_state')}")
    print(f" Full session: {dict(session)}")
    if request.args.get('state') != session.get('oauth_state'):
        return jsonify({"error": "invalid state parametrs"}), 400
    
    try:
        #код авторизации на код досутпа
        token = oauth.authgear.authorize_access_token()
    except OAuthError as e:
        return jsonify({"error": f"authorizstion failed: {e.error}"}), 400
    
    print("Session state in callback:", session.get('oauth_state'))
    print("Full session keys:", list(session.keys()))
    print("=== Debug: client_id =", current_app.config['AUTHGEAR_CLIENT_ID'])
    print("=== Debug: secret length =", len(current_app.config['AUTHGEAR_CLIENT_SECRET']))
    #извлечение информации user'а из ID-токена (JWT)
    user_info = oauth.authgear.parse_id_token(token,nonce=session.get('oauth_nonce'))
    
    authgear_id = user_info['sub'] #айди пользователя
    email = user_info['email'] #email user
    name = user_info['name']
    print("Cookies:", request.cookies)
    #ищем пользователя по id
    user = find_user_by_authID(authgear_id)
    if not user:
        #создание нового пользователя
        user = create_user_by_authID(authgear_id, email, name)
        #перенаправление на страницу выбора роли user'а
        return redirect('http://127.0.0.1:5000/choose-role')
    session['user_id'] = user['id'] # сохранение локального айди в сессии
    return redirect('http://127.0.0.1:5000/dashboard') #возвращение на главный экран





@auth_bp.route('/logout')
def logout():
    session.clear()
    logout_url = f"{current_app.config['AUTHGEAR_ISSUER']}/logout?post_logout_redirect_uri=http://127.0.0.1:5000"
    return redirect(logout_url)

