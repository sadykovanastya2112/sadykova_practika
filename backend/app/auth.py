# bluprint для регистрации
import secrets
from datetime import datetime

from authlib.integrations.flask_client import OAuthError
from flask import Blueprint, current_app, g, jsonify, redirect, request, session
from flask_jwt_extended import create_access_token

from app.extension import db
from app.jwt_auth import jwt_required
from app.logto import oauth
from app.models import Client, Member, MemberRole, Role, Specialist
from app.client import get_current_client

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
    print("Login: session before set:", dict(session))
    session["oauth_state"] = state
    print("Login: session after set:", dict(session))

    return oauth.logto.authorize_redirect(redirect_uri, state=state, nonce=nonce)


@auth_bp.route("/callback")
def callback():
    """Обрабатывает возврат от Logto, сохраняет JWT в сессию и перенаправляет на фронтенд."""

    if request.args.get("state") != session.get("oauth_state"):
        return jsonify({"error": "invalid state parametrs"}), 400

    try:
        # код авторизации на код досутпа
        token = oauth.logto.authorize_access_token()
    except OAuthError as e:
        return jsonify({"error": f"authorizstion failed: {e.error}"}), 400

    id_token = token.get("id_token")  # JWT
    if id_token:
        session["id_token"] = id_token
        print("\n" + "=" * 70)
        print("  JWT токен:")
        print(id_token)
        print("=" * 70 + "\n")
    else:
        print("id_token не найден")
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

    roles = [r.code for r in member.roles]
    if not roles:
        return jsonify({"error": "WTF n0 roles"}),500
    if len(roles) == 1:
        session['active_role'] = roles[0]
    else:
        last_role = member.last_active_role
        if last_role and last_role in roles:
            session['active_role'] = last_role
        else:
            session['active_role'] = 'client'


    print("Access token:", token.get("access_token"))
    # 5. Сохраняем member.id в сессию для быстрого доступа
    session["member_id"] = member.id

    id_token = token.get("id_token")
    if id_token:
        session["jwt_token"] = id_token
    else:
        return jsonify({"warning": "id_token not found in Logto response"}), 100

    print("Callback: session state:", session.get("oauth_state"))

    return redirect(f"{current_app.config['BASE_URL']}/catalog")



@auth_bp.route("/switch-role")
@jwt_required
def sitch_role():
    """
    Переключает роль у пользователя
    принимает json{
    role : client
    }
    """

    data = request.get_json()
    switch_role = data.get('role')
    if not switch_role:
        return jsonify({"error": "Missing role in json data"}),400
    
    member_id = g.member_id
    member = Member.query.get(member_id)

    if switch_role == 'specialist':
        existing_specialist = Specialist.query.filter_by(member_id=member.id).first()
    if not existing_specialist:
        specialist = Specialist(
            member_id=member.id,
            first_name=member.email.split('@')[0] if member.email else '',
            last_name='',
            specialization='',
            base_price=0,
            is_approved=False,
            verification_status='pending'
        )
        db.session.add(specialist)
        db.session.commit()


    roles = [r.role.code for r in member.roles]
    if switch_role not in roles:
        return jsonify({"error": "Role is not asigned to member"}),400
    
    session['active_role'] = switch_role
    db.session.commit()

    return jsonify({"message": f"Acttive role switched to {switch_role}", "active_role": switch_role}),200



@auth_bp.route("/get-token")
def get_token():
    """
    Возвращает JWT-токен текущего аутентифицированного пользователя.
    Требует наличия активной сессии (пользователь должен войти через /auth/login).
    Дополнительно защищено проверкой Referer (опционально).
    """
    referer = request.headers.get("Referer")

    allowed_referers = ["http://localhost:5000", "https://npm.safe-contact.duckdns.org"]
    if referer and not any(referer.startswith(host) for host in allowed_referers):
        return jsonify({"error": "Invalid request source"}), 403

    member_id = session.get("member_id")
    if not member_id:
        return jsonify({"error": "Not authenticated"}), 401

    jwt_token = session.get("jwt_token")
    if not jwt_token:
        return jsonify({"error": "Token not found"}), 404

    return jsonify({"access_token": jwt_token}), 200


@auth_bp.route("/whoami")
@jwt_required
def whoami():

    try:
        member_id = g.member_id
    except OAuthError as e:
        return jsonify({"error": f"{e}"}),500
    return jsonify({"member_id": member_id})


@auth_bp.route("/change-role", methods=["POST"])
@jwt_required
def change_role():

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
                first_name=email.split("@")[0],
                last_name="",
                specialization="",
                base_price=1500,
                is_approved=False,
                verification_status="pending",
            )
            db.session.add(specialist)

    db.session.commit()
    return jsonify(
        {"message": f"Role {role_code} assigned", "id": f"member_id {member_id}"}
    ), 200


@auth_bp.route("/me", methods=["GET"])
@jwt_required
def get_me():
    member_id = g.member_id
    member = Member.query.get(member_id)

    if not member:
        return jsonify({"error": "Member not found"}), 404

    # Ищем активную роль
    active_role = (
        db.session.query(Role.code)
        .join(MemberRole)
        .filter(MemberRole.member_id == member_id, MemberRole.is_active)
        .first()
    )

    # Если роли почему-то нет (аварийный случай)
    if not active_role:
        client_role = Role.query.filter_by(code="client").first()
        # Назначаем роль 'client' по умолчанию
        new_mr = MemberRole(
            member_id=member_id,
            role_id=client_role.id,
            is_active=True,
            assigned_at=datetime.utcnow(),
        )
        db.session.add(new_mr)

        # Проверяем наличие профиля клиента
        if not Client.query.filter_by(member_id=member_id).first():
            new_client = Client(member_id=member_id, display_name=f"User{member_id}")
            db.session.add(new_client)

        db.session.commit()
        role_code = "client"
    else:
        role_code = active_role[0]


    roles = [r.code for r in member.roles]
    active_role = session.get('active_role')
    return jsonify({"id": member.id,
                    "email": member.email,
                    "all_roles": roles,
                    "active_role": active_role
                    }), 200


@auth_bp.route("/logout", methods=["POST"])
def logout():
    """
    Выход из системы.
    """
    session.clear()
    if request.args.get("test") == "1":
        return jsonify({"message": "Logged out"}), 200
    logout_url = f"{current_app.config['LOGTO_ISSUER']}/logout?post_logout_redirect_uri={current_app.config['BASE_URL']}"
    return redirect(logout_url)


@auth_bp.route("/test-token", methods=["POST"])
def test_token():
    """
    ТЕСТОВЫЙ эндпоинт: возвращает JWT для заданного email.
    Использовать только для Postman-тестов!
    """
    data = request.get_json()
    email = data.get("email")
    # В реальности вы должны проверить пароль, но для тестов можно упростить
    member = Member.query.filter_by(email=email).first()
    if not member:
        # Создаём тестового пользователя, если нет
        member = Member(email=email, auth_id=f"test_{email.split('@')[0]}")
        db.session.add(member)
        db.session.commit()
        # Назначаем роль client
        client_role = Role.query.filter_by(code="client").first()
        if client_role:
            mr = MemberRole(member_id=member.id, role_id=client_role.id, is_active=True)
            db.session.add(mr)
            if not Client.query.filter_by(member_id=member.id).first():
                client = Client(member_id=member.id, display_name=f"User{member.id}")
                db.session.add(client)
            db.session.commit()
    # Генерируем JWT (используйте ваш метод генерации)
    access_token = create_access_token(identity=member.auth_id)
    return jsonify({"access_token": access_token, "id": member.id}), 200
