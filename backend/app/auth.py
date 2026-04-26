# bluprint для регистрации
import secrets
from datetime import datetime

from authlib.integrations.flask_client import OAuthError
from flask import Blueprint, current_app, jsonify, redirect, request, session, g
from flask_jwt_extended import create_access_token

from app.extension import db
from app.jwt_auth import jwt_required
from app.logto import oauth
from app.models import Client, Member, MemberRole, Role, Specialist

auth_bp = Blueprint("auth", __name__)


@auth_bp.route("/login")
def login():

    """
    Инициирует аутентификацию через Logto.
    ---
    tags:
      - Auth
    summary: Начать вход через Logto
    description: Перенаправляет пользователя на страницу входа Logto. Сохраняет state и nonce в сессии.
    responses:
      302:
        description: Редирект на страницу авторизации Logto.
    """

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
    Обрабатывает callback от Logto после аутентификации.
    ---
    tags:
      - Auth
    summary: Callback после входа
    description: Обменивает код на токен, создаёт/обновляет пользователя в БД, устанавливает сессию.
    parameters:
      - name: code
        in: query
        type: string
        required: true
        description: Код авторизации от Logto.
      - name: state
        in: query
        type: string
        required: true
        description: Параметр state для защиты от CSRF.
    responses:
      302:
        description: Редирект на дашборд.
      400:
        description: Ошибка валидации state или параметров.
      500:
        description: Внутренняя ошибка сервера.
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
        member = Member(
            auth_id=auth_id, is_active=True, created_at=datetime.utcnow(), email=email
        )
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
        db.session.commit()

    # 5. Сохраняем member.id в сессию для быстрого доступа
    session["member_id"] = member.id

    return redirect("http://127.0.0.1:5000/dashboard")


@auth_bp.route("/change-role",methods=['POST'])
@jwt_required
def change_role():
    """
    Изменяет активную роль пользователя.
    ---
    tags:
      - Auth
    summary: Сменить роль
    description: Позволяет авторизованному пользователю сменить роль (client, specialist и т.д.). При смене на specialist создаётся профиль специалиста.
    security:
      - BearerAuth: []
    parameters:
      - in: body
        name: body
        required: true
        schema:
          type: object
          properties:
            role:
              type: string
              enum: ["client", "specialist", "moderator", "admin", "owner"]
    responses:
      200:
        description: Роль успешно изменена.
        schema:
          type: object
          properties:
            message:
              type: string
            id:
              type: string
      400:
        description: Неверная роль.
      401:
        description: Неавторизован.
      500:
        description: Роль не найдена в БД.
    """
    data = request.get_json()
    role_code = data.get("role")

    if role_code not in ["client", "specialist", "moderator", "admin", "owner"]:
        return jsonify({"error": "invalid role"}), 400

    member_id = g.member_id
    role = Role.query.filter_by(code=role_code).first()
    if not role:
        return jsonify({"error": "role not found"}), 500

    MemberRole.query.filter_by(member_id=member_id).delete()

    member = Member.query.get(member_id)
    email = member.email
    

    new_role = MemberRole(
        member_id=member_id,
        role_id=role.id,
        is_active=True,
        assigned_at=datetime.utcnow(),
    )
    db.session.add(new_role)

    if role_code in ["client", "moderator", "admin", "owner"]:
        if not Client.query.filter_by(member_id=member_id).first():
            client = Client(member_id=member_id, display_name=f"User{member_id}")
            db.session.add(client)
    elif role_code == "specialist":
        if not Specialist.query.filter_by(member_id=member_id).first():
            specialist = Specialist(
                member_id=member.id,
                first_name= email.split("@")[0],
                last_name='',
                specialization='',
                base_price=1500,
                is_approved=False,
                verification_status='pending'
            )
            db.session.add(specialist)

    db.session.commit()
    return jsonify(
        {"message": f"Role {role_code} assigned", "id": f"member_id {member_id}"}
    ), 200





@auth_bp.route('/logout',methods=['POST'])
def logout():
    """
    Выход из системы.
    ---
    tags:
      - Auth
    summary: Выйти из системы
    description: Очищает локальную сессию и перенаправляет на logout URL Logto.
    responses:
      200:
        description: Успешный выход (только при тестовом параметре).
      302:
        description: Редирект на Logto logout.
    """
    session.clear()
    if request.args.get('test') == '1':
        return jsonify({"message": "Logged out"}), 200
    logout_url = f"{current_app.config['LOGTO_ISSUER']}/logout?post_logout_redirect_uri=http://127.0.0.1:5000"
    return redirect(logout_url)






@auth_bp.route('/test-token', methods=['POST'])
def test_token():
    """
    ТЕСТОВЫЙ эндпоинт: возвращает JWT для заданного email.
    Использовать только для Postman-тестов!
    """
    data = request.get_json()
    email = data.get('email')
    # В реальности вы должны проверить пароль, но для тестов можно упростить
    member = Member.query.filter_by(email=email).first()
    if not member:
        # Создаём тестового пользователя, если нет
        member = Member(email=email, auth_id=f"test_{email.split('@')[0]}")
        db.session.add(member)
        db.session.commit()
        # Назначаем роль client
        client_role = Role.query.filter_by(code='client').first()
        if client_role:
            mr = MemberRole(member_id=member.id, role_id=client_role.id, is_active=True)
            db.session.add(mr)
            db.session.commit()
    # Генерируем JWT (используйте ваш метод генерации)
    access_token = create_access_token(identity=member.auth_id)
    return jsonify({
    'access_token': access_token,
    'id': member.id
}), 200