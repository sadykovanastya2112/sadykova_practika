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