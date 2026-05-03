from datetime import datetime

from flask import Blueprint, g, jsonify, request

from app.extension import db
from app.jwt_auth import jwt_required
from app.models import Appointment, AppointmentStatus, Client, Member, Slot

clients_bp = Blueprint("clients", __name__)


def get_current_client(member_id):
    client = Client.query.filter_by(member_id=member_id).first()
    if not client:
        return None, jsonify({"message": "User is not client"}), 403
    return client, None, None


# Просмотр свободных слотов выбранного специалиста
@clients_bp.route("/get-slots", methods=["GET"])
@jwt_required
def check_specialist_slots():

    # получаем айди специалиста
    specialist_id = request.args.get("specialist_id")

    if not specialist_id:
        return jsonify({"error": "specialist not found"}), 404

    # запрос на показ слотов позже даты пользователя и проверка на бронирование слота
    slots = (
        Slot.query.filter(
            Slot.specialist_id == specialist_id,
            Slot.start_at > datetime.now(),
            ~Slot.appointments.any(),
        )
        .order_by(Slot.start_at)
        .all()
    )

    if not slots:
        return jsonify({"message": "specialist dont have slots"}), 200

    # отдаём данные
    return jsonify(
        [
            {
                "id": s.id,
                "start_at": s.start_at.isoformat(),
                "end_at": s.end_at.isoformat(),
            }
            for s in slots
        ]
    )


@clients_bp.route("/make-appointment", methods=["POST"])
@jwt_required
def create_appointment():
    """
    Создание бронирования на выбранный слот.
    """
    # Тело запроса, например: {"slot_id": 123, "specialist_id": 1}
    data_slot = request.get_json()
    if not data_slot:
        return jsonify({"error": "slot id not in request"}), 400

    # получаем клиента
    member_id = g.member_id
    client, error_response, status = get_current_client(member_id)
    if error_response:
        return error_response, status

    # проверяем есть ли такой слот
    slot = (
        Slot.query.filter(
            Slot.id == data_slot["slot_id"],
            Slot.specialist_id == data_slot["specialist_id"],
            Slot.start_at > datetime.now(),
            ~Slot.appointments.any(),
        )
        .order_by(Slot.start_at)
        .first()
    )

    if not slot:
        return jsonify({"error": "slot in appointment"}), 400

    # if client.member_id == slot.specialist.member_id:
    #     return jsonify({"error":"психолог не может сам у себя забронировать слот"}),400


    price_appoinment = slot.price
    status = AppointmentStatus.query.filter_by(code="pending_payment").first()

    appointment = Appointment(
        slot_id=data_slot["slot_id"],
        client_id=client.id,
        status_id=status.id,
        created_at=datetime.now(),
        price=price_appoinment,
    )

    db.session.add(appointment)
    db.session.commit()

    return jsonify(
        {
            "appointment_id": appointment.id,
            "slot_id": slot.id,
            "client_id": client.id,
            "status_id": status.id,  # позже исправить
            "price": price_appoinment,
        }
    ), 201


@clients_bp.route("/me", methods=["GET"])
@jwt_required
def client_profile():

    member_id = g.member_id
    client, error_response, status = get_current_client(member_id)
    if error_response:
        return error_response, status

    member = Member.query.get(member_id)

    profile_data = {
        "id": client.id,
        "member_id": member_id,
        "display_name": client.display_name,
        "bio": client.bio,
        "avatar_url": client.avatar_url,
        "created_at": client.created_at.isoformat() if client.created_at else None,
        "email": member.email if member else None,
    }

    return jsonify({"me": profile_data, "clietn_id": client.id, "member_id": member_id})


@clients_bp.route("/me", methods=["PUT"])
@jwt_required
def client_profile_update():

    member_id = g.member_id
    client, error_response, status = get_current_client(member_id)
    if error_response:
        return error_response, status

    data = request.get_json()
    if not data:
        return jsonify({"error": "no json data"}), 400

    allowed_fields = [
        "display_name",
        "bio",
        "avatar_url",
    ]

    for item in allowed_fields:
        if item in data:
            setattr(client, item, data[item])

    db.session.commit()
    return jsonify({"message": "profile info updated", "id": member_id}), 200
