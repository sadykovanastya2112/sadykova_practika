from datetime import datetime

from flask import Blueprint, g, jsonify, request

from app.extension import db
from app.jwt_auth import jwt_required
from app.models import Appointment, AppointmentStatus, Client, Slot

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
    """
    Получение свободных слотов выбранного специалиста.

    ---
    tags:
      - Clients
    summary: Получить свободные слоты специалиста
    description: Возвращает список свободных слотов (без бронирований) для указанного специалиста, дата начала которых позже текущего момента.
    parameters:
      - name: specialist_id
        in: query
        type: integer
        required: true
        description: ID специалиста
    security:
      - BearerAuth: []
    responses:
      200:
        description: Успешный ответ
        schema:
          type: array
          items:
            type: object
            properties:
              id:
                type: integer
              start_at:
                type: string
                format: date-time
              end_at:
                type: string
                format: date-time
      404:
        description: Специалист не найден
      401:
        description: Неавторизован
    """
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
        return jsonify({"message":"specialist dont have slots"}),200

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

    ---
    tags:
      - Clients
    summary: Забронировать слот
    description: Создаёт бронирование (appointment) для текущего клиента на указанный слот. Слот должен быть свободен, цена фиксируется.
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - slot_id
            - specialist_id
          properties:
            slot_id:
              type: integer
              description: ID слота
            specialist_id:
              type: integer
              description: ID специалиста
    security:
      - BearerAuth: []
    responses:
      201:
        description: Бронирование успешно создано
        schema:
          type: object
          properties:
            appointment_id:
              type: integer
            slot_id:
              type: integer
            client_id:
              type: integer
            status_id:
              type: integer
            price:
              type: integer
      400:
        description: Неверные данные (слот уже занят, отсутствуют поля и т.д.)
      403:
        description: Пользователь не является клиентом
      401:
        description: Неавторизован
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

    # я пока неуверен может ли пользователь одновременно сделать несколько бронирований, но пока что сделаю только по одному


    price_appoinment = slot.price
    status = AppointmentStatus.query.filter_by(code="pending_payment").first()

    appointment = Appointment(
        slot_id=data_slot["slot_id"],
        client_id=client.id,
        status_id=status.id,
        created_at=datetime.now(),
        price = price_appoinment
    )

    db.session.add(appointment)
    db.session.commit()

    return jsonify(
        {
            "appointment_id": appointment.id,
            "slot_id": slot.id,
            "client_id": client.id,
            "status_id": status.id,  # позже исправить
            "price": price_appoinment
        }
    ), 201
