from datetime import datetime, timedelta

from flask import Blueprint, app, g, jsonify, request

from sqlalchemy import func

from app.extension import db
from app.jwt_auth import jwt_required, require_role
from app.models import (
    Appointment,
    Client,
    Member,
    MemberRole,
    Payment,
    Role,
    Specialist,
)

admin_bp = Blueprint("admin", __name__, url_prefix="/admin")

# ------------------------ Управление пользователями ------------------------


@admin_bp.route("/users", methods=["GET"])
@jwt_required
@require_role("admin")
def list_users():
    """
    Получить список пользователей с фильтрацией.
    ---
    tags:
      - Admin
    parameters:
      - name: page
        in: query
        type: integer
        default: 1
        description: Номер страницы
      - name: per_page
        in: query
        type: integer
        default: 20
        description: Количество на странице (макс 100)
      - name: role
        in: query
        type: string
        description: Фильтр по роли (client, specialist, admin)
      - name: is_active
        in: query
        type: boolean
        description: true/false
      - name: date_from
        in: query
        type: string
        format: date
        description: Начальная дата регистрации (YYYY-MM-DD)
      - name: date_to
        in: query
        type: string
        format: date
        description: Конечная дата регистрации
    security:
      - BearerAuth: []
    responses:
      200:
        description: Список пользователей с пагинацией
        schema:
          type: object
          properties:
            items:
              type: array
              items:
                type: object
                properties:
                  id: {type: integer}
                  auth_id: {type: string}
                  email: {type: string}
                  is_active: {type: boolean}
                  created_at: {type: string, format: date-time}
                  last_login_at: {type: string, format: date-time, nullable: true}
                  roles: {type: array, items: {type: string}}
            total: {type: integer}
            page: {type: integer}
            per_page: {type: integer}
            pages: {type: integer}
      400: {description: Неверный параметр роли}
      401: {description: Неавторизован}
      403: {description: Доступ запрещён (требуется admin)}
    """
        
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    if per_page > 100:
        per_page = 100

    role_filter = request.args.get("role")  # client, specialist, admin и т.д.
    is_active = request.args.get("is_active")  # true/false
    date_from = request.args.get("date_from")  # YYYY-MM-DD
    date_to = request.args.get("date_to")

    query = Member.query

    if role_filter:
        # Ищем пользователей с определённой ролью через member_role
        role = Role.query.filter_by(code=role_filter).first()
        if role:
            subquery = db.session.query(MemberRole.member_id).filter_by(role_id=role.id)
            query = query.filter(Member.id.in_(subquery))
        else:
            return jsonify({"error": "Invalid role"}), 400

    if is_active is not None:
        is_active_bool = is_active.lower() == "true"
        query = query.filter(Member.is_active == is_active_bool)

    if date_from:
        query = query.filter(Member.created_at >= datetime.fromisoformat(date_from))
    if date_to:
        query = query.filter(Member.created_at <= datetime.fromisoformat(date_to))

    paginated = query.order_by(Member.created_at.desc()).paginate(
        page=page, per_page=per_page, error_out=False
    )

    result = []
    for m in paginated.items:
        roles = [r.code for r in m.roles]
        result.append(
            {
                "id": m.id,
                "auth_id": m.auth_id,
                "email": m.email,
                "is_active": m.is_active,
                "created_at": m.created_at.isoformat(),
                "last_login_at": m.last_login_at.isoformat()
                if m.last_login_at
                else None,
                "roles": roles,
            }
        )
    return jsonify(
        {
            "items": result,
            "total": paginated.total,
            "page": page,
            "per_page": per_page,
            "pages": paginated.pages,
        }
    ), 200


@admin_bp.route("/users/<int:user_id>", methods=["GET"])
@jwt_required
@require_role("admin")
def get_user_detail(user_id):
    """
    Получить детальную информацию о пользователе.
    ---
    tags:
      - Admin
    parameters:
      - name: user_id
        in: path
        type: integer
        required: true
        description: ID пользователя
    security:
      - BearerAuth: []
    responses:
      200:
        description: Данные пользователя (включая профили client/specialist)
        schema:
          type: object
          properties:
            id: {type: integer}
            auth_id: {type: string}
            email: {type: string}
            is_active: {type: boolean}
            created_at: {type: string, format: date-time}
            last_login_at: {type: string, format: date-time, nullable: true}
            roles: {type: array, items: {type: string}}
            client_profile: {type: object, nullable: true}
            specialist_profile: {type: object, nullable: true}
      404: {description: Пользователь не найден}
      401: {description: Неавторизован}
      403: {description: Доступ запрещён}
    """
    member = Member.query.get(user_id)
    if not member:
        return jsonify({"error": "User not found"}), 404

    roles = [r.code for r in member.roles]

    client_profile = None
    specialist_profile = None
    if "client" in roles:
        client = Client.query.filter_by(member_id=member.id).first()
        if client:
            client_profile = {
                "id": client.id,
                "display_name": client.display_name,
                "bio": client.bio,
                "avatar_url": client.avatar_url,
                "is_anonymous": client.is_anonymous,
                "created_at": client.created_at.isoformat(),
            }
    if "specialist" in roles:
        spec = Specialist.query.filter_by(member_id=member.id).first()
        if spec:
            specialist_profile = {
                "id": spec.id,
                "first_name": spec.first_name,
                "last_name": spec.last_name,
                "specialization": spec.specialization,
                "education": spec.education,
                "bio": spec.bio,
                "experience_years": spec.experience_years,
                "base_price": spec.base_price,
                "photo_url": spec.photo_url,
                "verification_status": spec.verification_status,
                "is_approved": spec.is_approved,
                "created_at": spec.created_at.isoformat(),
            }

    return jsonify(
        {
            "id": member.id,
            "auth_id": member.auth_id,
            "email": member.email,
            "is_active": member.is_active,
            "created_at": member.created_at.isoformat(),
            "last_login_at": member.last_login_at.isoformat()
            if member.last_login_at
            else None,
            "roles": roles,
            "client_profile": client_profile,
            "specialist_profile": specialist_profile,
        }
    ), 200


@admin_bp.route("/users/<int:user_id>/toggle-block", methods=["POST"])
@jwt_required
@require_role("admin")
def toggle_block_user(user_id):
    """
    Блокировка/разблокировка пользователя.
    ---
    tags:
      - Admin
    parameters:
      - name: user_id
        in: path
        type: integer
        required: true
        description: ID пользователя
    security:
      - BearerAuth: []
    responses:
      200:
        description: Статус изменён
        schema:
          type: object
          properties:
            message: {type: string}
            is_active: {type: boolean}
      404: {description: Пользователь не найден}
      401: {description: Неавторизован}
      403: {description: Доступ запрещён}
    """
    member = Member.query.get(user_id)
    if not member:
        return jsonify({"error": "User not found"}), 404
    member.is_active = not member.is_active
    db.session.commit()
    return jsonify(
        {
            "message": f"User {user_id} {'blocked' if not member.is_active else 'unblocked'}",
            "is_active": member.is_active,
        }
    ), 200


@admin_bp.route("/users/<int:user_id>/roles", methods=["PUT"])
@jwt_required
@require_role("admin")
def update_user_roles(user_id):
    """
    Заменить список ролей пользователя.
    ---
    tags:
      - Admin
    parameters:
      - name: user_id
        in: path
        type: integer
        required: true
        description: ID пользователя
    requestBody:
      required: true
      content:
        application/json:
          schema:
            type: object
            properties:
              roles:
                type: array
                items:
                  type: string
                example: ["client", "specialist"]
    security:
      - BearerAuth: []
    responses:
      200:
        description: Роли обновлены
        schema:
          type: object
          properties:
            message: {type: string}
            roles: {type: array, items: {type: string}}
      400: {description: Неверный формат или роль не найдена}
      404: {description: Пользователь не найден}
      401: {description: Неавторизован}
      403: {description: Доступ запрещён}
    """
    data = request.get_json()
    if not data or "roles" not in data:
        return jsonify({"error": "roles list required"}), 400
    new_role_codes = data["roles"]
    # Найти все роли по кодам
    roles = Role.query.filter(Role.code.in_(new_role_codes)).all()
    if len(roles) != len(new_role_codes):
        return jsonify({"error": "Some roles not found"}), 400

    member = Member.query.get(user_id)
    if not member:
        return jsonify({"error": "User not found"}), 404

    # Удаляем текущие членства
    MemberRole.query.filter_by(member_id=member.id).delete()
    # Добавляем новые
    for role in roles:
        mr = MemberRole(
            member_id=member.id,
            role_id=role.id,
            is_active=True,
            assigned_at=datetime.utcnow(),
        )
        db.session.add(mr)
    db.session.commit()
    return jsonify(
        {"message": f"Roles for user {user_id} updated", "roles": new_role_codes}
    ), 200


# ------------------------ Статистика ------------------------









@admin_bp.route("/stats", methods=["GET"])
@jwt_required
@require_role("admin")
def platform_stats():
    """
    Ключевые метрики платформы.
    ---
    tags:
      - Admin
    security:
      - BearerAuth: []
    responses:
      200:
        description: Статистика
        schema:
          type: object
          properties:
            total_users: {type: integer}
            active_specialists: {type: integer}
            total_revenue_rub: {type: integer}
            platform_profit_rub: {type: integer}
            completed_sessions: {type: integer}
            new_users:
              type: object
              properties:
                today: {type: integer}
                week: {type: integer}
                month: {type: integer}
      401: {description: Неавторизован}
      403: {description: Доступ запрещён}
    """
    # Общее количество пользователей
    total_users = Member.query.count()
    # Активные специалисты (is_approved=True, is_active=True)
    active_specialists = Specialist.query.filter_by(
        is_approved=True, is_active=True
    ).count()
    # Количество сессий (завершённых)
    completed_appointments = Appointment.query.filter_by(
        status_id=...
    ).count()  # нужно получить id статуса "completed"
    # Оборот (сумма успешных платежей)
    total_revenue = (
        db.session.query(func.sum(Payment.amount))
        .filter_by(status="succeeded")
        .scalar()
        or 0
    )
    # Прибыль платформы (комиссия) – можно вычислить как процент от оборота, но хранится отдельно
    # Для простоты: сумма комиссии (если есть поле commission_amount)
    # Пока заглушка:
    platform_profit = int(total_revenue * 0.1)  # условно 10%

    # Статистика новых пользователей за сегодня/неделю/месяц
    today = datetime.utcnow().date()
    week_ago = today - timedelta(days=7)
    month_ago = today - timedelta(days=30)

    new_today = Member.query.filter(Member.created_at >= today).count()
    new_week = Member.query.filter(Member.created_at >= week_ago).count()
    new_month = Member.query.filter(Member.created_at >= month_ago).count()

    return jsonify(
        {
            "total_users": total_users,
            "active_specialists": active_specialists,
            "total_revenue_rub": total_revenue,
            "platform_profit_rub": platform_profit,
            "completed_sessions": completed_appointments,
            "new_users": {"today": new_today, "week": new_week, "month": new_month},
        }
    ), 200


# ------------------------ Управление комиссией ------------------------
commission_history = []  # временное хранилище


@admin_bp.route("/commission", methods=["GET"])
@jwt_required
@require_role("admin")
def get_commission():
    """Получить текущий процент комиссии и историю изменений."""
    # Предположим, комиссия хранится в настройках (можно в отдельной таблице или просто в БД)
    # Для простоты используем временный объект
    current_commission = 5  # процент
    return jsonify(
        {"current_percent": current_commission, "history": commission_history}
    ), 200


@admin_bp.route("/commission", methods=["POST"])
@jwt_required
@require_role("admin")
def set_commission():
    """Установить новый процент комиссии (применяется к новым сессиям)."""
    data = request.get_json()
    if not data or "percent" not in data:
        return jsonify({"error": "percent required"}), 400
    percent = data["percent"]
    if not isinstance(percent, (int, float)) or percent < 0:
        return jsonify({"error": "percent must be a non-negative number"}), 400

    # Сохраняем в историю
    commission_history.append(
        {
            "percent": percent,
            "changed_at": datetime.utcnow().isoformat(),
            "changed_by": g.member_id,
        }
    )
    # Здесь можно сохранить в БД: например, в таблицу settings
    return jsonify(
        {"message": f"Commission set to {percent}%", "current": percent}
    ), 200
