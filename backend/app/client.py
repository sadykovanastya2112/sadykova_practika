import os
from datetime import datetime

import filetype
from flask import Blueprint, current_app, g, jsonify, request
from werkzeug.utils import secure_filename

from app.extension import db
from app.jwt_auth import jwt_required
from app.models import Appointment, AppointmentStatus, Client, Member, Slot

clients_bp = Blueprint("clients", __name__)


def validate_and_save_image(file, member_id, max_size_mb=5):
    """
    Проверяет и сохраняет изображение (аватарку).
    Принимает файл и member_id.
    Возвращает (new_filename, error_message) – при ошибке new_filename = None.
    """
    allowed_extensions = {"jpg", "jpeg", "png", "gif", "webp"}

    if file.filename == "":
        return None, "No selected file"

    # Расширение
    ext = file.filename.rsplit(".", 1)[1].lower() if "." in file.filename else ""
    if ext not in allowed_extensions:
        return None, f"Extension not allowed. Allowed: {', '.join(allowed_extensions)}"

    # MIME-тип по сигнатуре
    file_data = file.read(1024)
    kind = filetype.guess(file_data)
    file.seek(0)
    allowed_mime = ["image/jpeg", "image/png", "image/gif", "image/webp"]
    if kind is None or kind.mime not in allowed_mime:
        return None, "File MIME type not allowed (only images)"

    # Размер
    file.seek(0, os.SEEK_END)
    size = file.tell()
    file.seek(0)
    if size > max_size_mb * 1024 * 1024:
        return None, f"File size exceeds {max_size_mb} MB"

    # Генерация уникального имени и сохранение
    original_filename = secure_filename(file.filename)
    timestamp = datetime.utcnow().timestamp()
    new_filename = f"avatar_{member_id}_{timestamp}.{ext}"
    filepath = os.path.join(current_app.config["UPLOAD_FOLDER"], new_filename)
    file.save(filepath)
    return new_filename, None


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
            "status_id": status.id,
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

    # Обрабатываем текстовые поля из form-data
    display_name = request.form.get("display_name")
    bio = request.form.get("bio")
    if display_name:
        client.display_name = display_name
    if bio:
        client.bio = bio

    # Обрабатываем файл
    file = request.files.get('avatar')
    if file and file.filename != '':
        new_filename, error = validate_and_save_image(file, member_id)
        if error:
            return jsonify({"error": error}), 400
        # удаляем старый файл
        old_avatar_url = client.avatar_url
        if old_avatar_url:
            old_filename = old_avatar_url.split('/')[-1]
            old_path = os.path.join(current_app.config['UPLOAD_FOLDER'], old_filename)
            if os.path.exists(old_path):
                os.remove(old_path)
        client.avatar_url = f"/uploads/{new_filename}"

    db.session.commit()
    return jsonify({"message": "profile info updated", "id": member_id}), 200


@clients_bp.route("/appointments", methods=["GET"])
@jwt_required
def show_appointment():
    """
    список бронирований у клиента.
    """

    # получаем клиента
    member_id = g.member_id
    client, error_response, status = get_current_client(member_id)
    if error_response:
        return error_response, status

    # if client.member_id == slot.specialist.member_id:
    #   return jsonify({"error":"психолог не может сам у себя забронировать слот"}),400

    # получаем все бронирования клиента
    appointments = Appointment.query.filter_by(client_id=client.id).all()
    if not appointments:
        return jsonify([]), 200

    appointments_list = []
    for appoint in appointments:
        appointment_status = AppointmentStatus.query.get(appoint.status_id)

        slot = appoint.slot_id
        specialist = slot.specialist

        (
            appointments_list.append(
                {
                    "appointment_id": appoint.id,
                    "slot_id": appoint.slot_id,
                    "status_label": appointment_status.label,
                    "price": appoint.price,
                    "specialist_id": specialist.id,
                    "specialist_first_name": specialist.first_name,
                    "specialist_last_name": specialist.last_name,
                    "start_at": slot.start_at,
                    "end_at": slot.end_at,
                    "created_at": appoint.created_at.isoformat(),
                }
            ),
            200,
        )
    return jsonify(appointments_list)
