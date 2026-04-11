# bluprint для регистрации
import secrets
from datetime import datetime

from authlib.integrations.flask_client import OAuthError
from flask import Blueprint, current_app, jsonify, redirect, request, session

from app.extension import db
from app.logto import oauth
from app.models import Client, Member, MemberRole, Role

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login")
def login():
    # генерим рандомною строку
    state = secrets.token_urlsafe(16)
    nonce = secrets.token_urlsafe(16)
    # сохряет стате в сессии, что бы проверять на возврате
    session["oauth_state"] = state
    session["oauth_nonce"] = nonce
    redirect_uri = current_app.config["LOGTO_REDIRECT_URI"]
    return oauth.logto.authorize_redirect(redirect_uri, state=state, nonce=nonce)


@auth_bp.route("/callback")
def callback():
    """
    Обрабатывает возврат от logto после успешного (или неуспешного) входа.
    Проверяет state, получает токен и информацию о пользователе
    """

    if request.args.get("state") != session.get("oauth_state"):
        return jsonify({"error": "invalid state parametrs"}), 400

    try:
        # код авторизации на код досутпа
        token = oauth.logto.authorize_access_token()
    except OAuthError as e:
        return jsonify({"error": f"authorizstion failed: {e.error}"}), 400

    # извлечение информации user'а из ID-токена (JWT)
    user_info = oauth.logto.parse_id_token(token, nonce=session.get("oauth_nonce"))
    auth_id = user_info["sub"]  # айди пользователя
    email = user_info["email"]  # email user
    member = Member.query.filter_by(auth_id=auth_id).first()

    if not member:
        member = Member(auth_id=auth_id, is_active=True, created_at=datetime.utcnow())
        db.session.add(member)
        db.session.commit()

        # 4a. Назначение роли 'client'
        # Убедимся, что роль 'client' существует
        client_role = Role.query.filter_by(code="client").first()
        if not client_role:
            client_role = Role(code="client", label="Клиент")
            db.session.add(client_role)
            db.session.commit()

        member_role = MemberRole(
            member_id=member.id,
            role_id=client_role.id,
            is_active=True,
            assigned_at=datetime.utcnow(),
        )
        db.session.add(member_role)
        db.session.commit()

        # 4b. Создание записи в Client (если нужна)
        # Предполагаем, что по умолчанию пользователь – клиент
        client = Client(
            member_id=member.id,
            display_name=email.split("@")[0] if email else f"User{member.id}",
            created_at=datetime.utcnow(),
        )
        db.session.add(client)
        db.session.commit()

    else:
        # Пользователь уже существует – обновляем время последнего входа (если есть поле)
        # Если в модели Member есть поле last_login_at, раскомментируйте:
        # member.last_login_at = datetime.utcnow()
        db.session.commit()

    # 5. Сохраняем member.id в сессию для быстрого доступа
    session["member_id"] = member.id

    return redirect("http://127.0.0.1:5000/dashboard")


@auth_bp.route("/logout")
def logout():
    session.clear()
    logout_url = f"{current_app.config['LOGTO_ISSUER']}/logout?post_logout_redirect_uri=http://127.0.0.1:5000"
    return redirect(logout_url)
