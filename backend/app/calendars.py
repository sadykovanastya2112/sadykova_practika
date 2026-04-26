import hmac
import hashlib
from datetime import datetime

from flask import Blueprint, current_app, g, jsonify, request

from app.calcom import CalComClient
from app.extension import db
from app.jwt_auth import jwt_required
from app.models import Appointment, AppointmentStatus, Client, Member, Specialist

cal_bp = Blueprint("calendars", __name__, url_prefix="/calendars")


def get_current_client(member_id):
    """Вспомогательная функция для получения клиента по member_id."""
    client = Client.query.filter_by(member_id=member_id).first()
    if not client:
        return None, jsonify({"error": "Client not found"}), 403
    return client, None, None


@cal_bp.route("/slots", methods=["GET"])
def get_available_slots():
    """
    Получение свободных слотов из Cal.com.

    ---
    tags:
      - Calendars
    summary: Получить доступные слоты
    description: Возвращает список свободных временных слотов из Cal.com для заданного типа события (eventTypeSlug).
    parameters:
      - name: start
        in: query
        type: string
        format: date
        required: true
        description: Дата начала периода (ISO 8601, например, 2025-05-01)
      - name: end
        in: query
        type: string
        format: date
        required: true
        description: Дата окончания периода (ISO 8601)
    responses:
      200:
        description: Успешный ответ
        schema:
          type: object
          properties:
            slots:
              type: array
              items:
                type: object
                properties:
                  start:
                    type: string
                    format: date-time
      400:
        description: Отсутствуют параметры start или end
      500:
        description: Ошибка при обращении к Cal.com
    """
    start_date = request.args.get("start")
    end_date = request.args.get("end")
    if not start_date or not end_date:
        return jsonify({"error": "start and end parameters are required"}), 400

    try:
        cal_client = CalComClient()
        slots = cal_client.get_available_slots(start_date, end_date)
        return jsonify({"slots": slots}), 200
    except Exception:
        return jsonify({"error": "Could not fetch availability"}), 500


@cal_bp.route("/book", methods=["POST"])
@jwt_required
def create_cal_booking():
    """
    Создание бронирования в Cal.com после подтверждения записи клиентом.

    ---
    tags:
      - Calendars
    summary: Создать бронирование в Cal.com
    description: Принимает идентификатор бронирования (`appointment_id`) и создаёт соответствующее событие в Cal.com, сохраняя полученный external_booking_id.
    parameters:
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - appointment_id
          properties:
            appointment_id:
              type: integer
              description: ID бронирования в локальной системе
    security:
      - BearerAuth: []
    responses:
      200:
        description: Бронирование успешно создано в Cal.com
        schema:
          type: object
          properties:
            message:
              type: string
            cal_booking_uid:
              type: string
            cal_booking_id:
              type: string
      400:
        description: Не передан appointment_id или неверный формат
      403:
        description: Доступ запрещён (не ваш клиент)
      404:
        description: Бронирование или слот не найдены
      409:
        description: Бронирование уже не в статусе ожидания оплаты
      500:
        description: Ошибка при создании бронирования в Cal.com
    """
    data = request.get_json()
    if not data or "appointment_id" not in data:
        return jsonify({"error": "appointment_id is required"}), 400

    appointment_id = data["appointment_id"]

    # Получаем текущего клиента
    member_id = g.member_id
    client, err_response, status = get_current_client(member_id)
    if err_response:
        return err_response, status

    # Находим бронирование
    appointment = Appointment.query.get(appointment_id)
    if not appointment:
        return jsonify({"error": "Appointment not found"}), 404
    if appointment.client_id != client.id:
        return jsonify({"error": "Not your appointment"}), 403

    # Бронирование должно быть в статусе "pending_payment"
    pending_status = AppointmentStatus.query.filter_by(code="pending_payment").first()
    if not pending_status:
        return jsonify({"error": "Status 'pending_payment' not found"}), 500
    if appointment.status_id != pending_status.id:
        return jsonify({"error": "Appointment is not pending payment"}), 409

    # Получаем слот
    slot = appointment.slot
    if not slot:
        return jsonify({"error": "Slot not found"}), 404

    # Получаем специалиста
    specialist = slot.specialist
    if not specialist:
        return jsonify({"error": "Specialist not found for this slot"}), 404

    # Данные участника для Cal.com (клиент)
    client_member = Member.query.get(client.member_id)
    attendee_email = client_member.email if client_member else "client@example.com"
    attendee_name = client_member.username if client_member else "Клиент"

    start_iso = slot.start_at.isoformat()

    try:
        cal_client = CalComClient()
        booking_data = cal_client.book_slot(start_iso, attendee_name, attendee_email)

        # Сохраняем external_booking_id от Cal.com
        appointment.external_booking_id = booking_data.get("uid")
        appointment.booking_provider = "cal.com"
        db.session.commit()

        return jsonify(
            {
                "message": "Booking created in Cal.com",
                "cal_booking_uid": booking_data.get("uid"),
                "cal_booking_id": booking_data.get("id"),
            }
        ), 200
    except Exception:
        return jsonify({"error": "Could not create booking in external calendar"}), 500


@cal_bp.route("/webhook", methods=["POST"])
def cal_webhook():
    """
    Обработчик вебхуков от Cal.com (уведомления о создании, оплате, отмене).

    ---
    tags:
      - Calendars
    summary: Обработка вебхуков Cal.com
    description: Принимает уведомления от Cal.com (например, об успешной оплате или отмене) и обновляет статус соответствующего бронирования в локальной БД.
    parameters:
      - name: X-Cal-Signature-256
        in: header
        type: string
        required: false
        description: Подпись вебхука для верификации
    security: []
    responses:
      200:
        description: Уведомление обработано (или проигнорировано)
        schema:
          type: object
          properties:
            status:
              type: string
              example: ok
      401:
        description: Неверная подпись вебхука
      400:
        description: Неверный JSON или отсутствуют данные
    """
    raw_data = request.get_data()
    signature = request.headers.get("X-Cal-Signature-256")

    # Проверка подписи (если секрет задан)
    secret = current_app.config.get("CALCOM_WEBHOOK_SECRET")
    if secret and signature:
        expected = hmac.new(
            key=secret.encode("utf-8"), msg=raw_data, digestmod=hashlib.sha256
        ).hexdigest()
        if not hmac.compare_digest(expected, signature):
            return jsonify({"error": "Invalid signature"}), 401

    # Парсим тело
    try:
        data = request.get_json()
    except Exception:
        return jsonify({"error": "Invalid JSON"}), 400
    if not data:
        return jsonify({"error": "No data"}), 400

    trigger_event = data.get("triggerEvent")
    payload = data.get("payload", {})
    booking_uid = payload.get("uid")

    if not booking_uid:
        return jsonify({"status": "ignored"}), 200

    # Находим связанное бронирование в нашей системе
    appointment = Appointment.query.filter_by(external_booking_id=booking_uid).first()
    if not appointment:
        return jsonify({"status": "ignored"}), 200

    # Обработка событий
    if trigger_event == "BOOKING_CREATED":
        # Бронирование уже существует, статус не меняем
        pass
    elif trigger_event == "BOOKING_PAID":
        paid_status = AppointmentStatus.query.filter_by(code="paid").first()
        if paid_status and appointment.status_id != paid_status.id:
            appointment.status_id = paid_status.id
            db.session.commit()
    elif trigger_event == "BOOKING_CANCELLED":
        cancelled_status = AppointmentStatus.query.filter_by(code="cancelled").first()
        if cancelled_status:
            appointment.status_id = cancelled_status.id
            db.session.commit()
    else:
        print(f"Unhandled Cal.com event: {trigger_event}")

    return jsonify({"status": "ok"}), 200