import json
import uuid
from datetime import datetime

from flask import Blueprint, current_app, g, jsonify, request
from yookassa import Configuration, Payment as YooPayment


from app.extension import db
from app.models import Appointment, AppointmentStatus, Client, Payment

payments_bp = Blueprint("payments", __name__)

# Настройка ЮКассы


def init_yookassa():
    Configuration.configure(
        account_id=current_app.config["YOOKASSA_SHOP_ID"],
        secret_key=current_app.config["YOOKASSA_SECRET_KEY"],
    )


@payments_bp.route("/create-payment", methods=["POST"])
def create_payment():
    """
    Ожидает JSON: {"appointment_id": 123}
    Создаёт платёж в ЮKassa, привязанный к бронированию.
    """

    # получаем запрос
    data = request.get_json()
    if not data or "appointment_id" not in data:
        return jsonify({"error": "appointment_id is required"}), 400

    # принмаем номер брони
    appointment_id = data["appointment_id"]
    # получаем клиента
    member_id = g.member_id
    client = Client.query.filter_by(member_id=member_id).first()
    if not client:
        return jsonify({"error": "Client profile not found"}), 403

    # находим бронирование
    appointment = Appointment.query.get(appointment_id)
    if not appointment:
        return jsonify({"error": "Appointment not found"}), 404

    if appointment.client_id != client.id:
        return jsonify({"error": "Not your appointment"}), 403

    # проверяем статус оплаты
    pending_status = AppointmentStatus.query.filter_by(code="pending_payment").first()
    if not pending_status:
        return jsonify({"error": "Status 'pending_payment' not found in DB"}), 500
    if appointment.status_id != pending_status.id:
        return jsonify({"error": "Appointment is not pending payment"}), 409

    amount = 1000.00  # Замени на реальную логику

    # 6. Инициализируем ЮKassa
    try:
        init_yookassa()
    except Exception:
        return jsonify({"error": "Payment service init failed"}), 500

    idempotence_key = str(uuid.uuid4())

    # 7. Создаём платёж в ЮKassa
    try:
        yoo_payment = YooPayment.create(
            {
                "amount": {"value": f"{amount:.2f}", "currency": "RUB"},
                "confirmation": {
                    "type": "redirect",
                    "return_url": f"http://127.0.0.1:5000/payment-success?appointment_id={appointment_id}",
                },
                "capture": True,
                "description": f"Оплата сессии #{appointment_id}",
            },
            idempotence_key,
        )
    except Exception as e:
        return jsonify({"error": f"YooKassa error: {str(e)}"}), 500

    # 8. Сохраняем информацию о платеже в БД
    payment = Payment(
        appointment_id=appointment.id,
        provider="yookassa",
        provider_payment_id=yoo_payment.id,
        amount=amount,
        currency="RUB",
        status="pending",
        created_at=datetime.utcnow(),
    )
    db.session.add(payment)
    db.session.commit()

    # 9. Возвращаем ссылку на оплату
    return jsonify(
        {
            "confirmation_url": yoo_payment.confirmation.confirmation_url,
            "payment_id": yoo_payment.id,
            "appointment_id": appointment.id,
        }
    ), 200


@payments_bp.route("/payment-success")
def payment_success():
    # редирект на страницу с успешной оплатой
    return jsonify({"message": "Тестовый платёж прошёл успешно"})


@payments_bp.route("/webhook/yookassa", methods=["POST"])
def yookassa_webhook():
    """
    Обработчик уведомлений от ЮKassa (меняет статус платежа).
    """
    event_json = request.get_json()
    print("Webhook received:", json.dumps(event_json, indent=2))

    # Здесь можно проверить объект и обновить статус платежа (позже с БД)
    # Сейчас просто логируем
    return "", 200
