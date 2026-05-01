import base64
import hashlib
import hmac
import uuid
from datetime import datetime

from flask import Blueprint, current_app, g, jsonify, request
from sqlalchemy.exc import SQLAlchemyError
from yookassa import Configuration
from yookassa import Payment as YooPayment

from app.extension import db
from app.jwt_auth import jwt_required
from app.models import Appointment, AppointmentStatus, Client, Payment

payments_bp = Blueprint("payments", __name__)


# ------------------------- Настройка ЮKassa -------------------------
def init_yookassa():
    Configuration.configure(
        account_id=current_app.config["YOOKASSA_SHOP_ID"],
        secret_key=current_app.config["YOOKASSA_SECRET_KEY"],
    )


def verify_yookassa_webhook_signature(
    secret_key: str, request_body: bytes, signature_header: str
) -> bool:
    """
    Проверяет подпись вебхука ЮKassa (HMAC-SHA256).
    secret_key – ваш секретный ключ из личного кабинета.
    request_body – тело запроса в байтах.
    signature_header – значение заголовка 'X-Yookassa-Signature'.
    """
    try:
        expected_signature = base64.b64encode(
            hmac.new(secret_key.encode("utf-8"), request_body, hashlib.sha256).digest()
        ).decode("utf-8")
        return hmac.compare_digest(expected_signature, signature_header)
    except Exception:
        return False


# ------------------------- Endpoint создания платежа -------------------------
@payments_bp.route("/create-payment", methods=["POST"])
@jwt_required
def create_payment():
    """
    Создание платежа в ЮKassa для указанного бронирования.
    """
    data = request.get_json()
    if not data or "appointment_id" not in data:
        return jsonify({"error": "appointment_id is required"}), 400

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

    price = appointment.price

    try:
        init_yookassa()
    except Exception:
        return jsonify({"error": "Payment service init failed"}), 500

    idempotence_key = str(uuid.uuid4())

    try:
        yoo_payment = YooPayment.create(
            {
                "amount": {"value": f"{price:.2f}", "currency": "RUB"},
                "confirmation": {
                    "type": "redirect",
                    "return_url": f"{current_app.config['API_URL']}/payment-success?appointment_id={appointment_id}",
                },
                "capture": True,
                "description": f"Оплата сессии #{appointment_id}",
            },
            idempotence_key,
        )
    except Exception as e:
        return jsonify({"error": f"YooKassa error: {str(e)}"}), 500

    payment = Payment(
        appointment_id=appointment.id,
        provider="yookassa",
        provider_payment_id=yoo_payment.id,
        amount=price,
        currency="RUB",
        status="pending",
        created_at=datetime.utcnow(),
    )
    db.session.add(payment)
    db.session.commit()

    print(f"бля короче вот пайсмент {yoo_payment.id}")

    return jsonify(
        {
            "confirmation_url": yoo_payment.confirmation.confirmation_url,
            "payment_id": yoo_payment.id,
            "appointment_id": appointment.id,
        }
    ), 200


# ------------------------- Endpoint успешной оплаты (редирект) -------------------------
@payments_bp.route("/payment-success")
def payment_success():
    return jsonify({"message": "Тестовый платёж прошёл успешно"})


# ------------------------- Endpoint опроса статуса (polling) -------------------------
@payments_bp.route("/check/<string:payment_id>", methods=["GET"])
@jwt_required
def check_payment(payment_id):
    # Находим локальный платёж
    payment = Payment.query.filter_by(provider_payment_id=payment_id).first()
    if not payment:
        return jsonify({"error": "Payment not found"}), 404

    # Проверяем права: только клиент, создавший бронирование, или администратор (можно расширить)
    member_id = g.member_id
    client = Client.query.filter_by(member_id=member_id).first()
    appointment = Appointment.query.get(payment.appointment_id)
    if not client or appointment.client_id != client.id:
        return jsonify({"error": "Access denied"}), 403

    # Запрашиваем статус у ЮKassa
    try:
        init_yookassa()
        yoo_payment = YooPayment.find_one(payment_id)
        if not yoo_payment:
            return jsonify({"error": "Payment not found in YooKassa"}), 404
        new_status = (
            yoo_payment.status
        )  # 'pending', 'waiting_for_capture', 'succeeded', 'canceled'
    except Exception as e:
        return jsonify({"error": f"Failed to query YooKassa: {str(e)}"}), 500

    # Обновляем локальный статус, если изменился
    if payment.status != new_status:
        payment.status = new_status
        if new_status == "succeeded":
            payment.paid_at = datetime.utcnow()
            if appointment:
                paid_status = AppointmentStatus.query.filter_by(code="paid").first()
                if paid_status:
                    appointment.status_id = paid_status.id
        elif new_status == "canceled":
            # Можно вернуть слот в доступное состояние? Не требуется.
            pass
        db.session.commit()

    return jsonify(
        {
            "payment_id": payment.provider_payment_id,
            "status": payment.status,
            "amount": payment.amount,
            "currency": payment.currency,
            "paid_at": payment.paid_at.isoformat() if payment.paid_at else None,
        }
    ), 200


# ------------------------- Обработчик вебхуков ЮKassa -------------------------
@payments_bp.route("/webhook/yookassa", methods=["POST"])
def yookassa_webhook():
    """
    Обработчик вебхуков от ЮKassa.

    ---
    tags:
      - Payments
    summary: Приём уведомлений ЮKassa
    description: Принимает уведомления об изменении статуса платежа, проверяет подпись и обновляет локальные статусы платежа и бронирования.
    parameters:
      - name: X-Yookassa-Signature
        in: header
        type: string
        required: true
        description: Подпись вебхука для верификации
    security: []
    responses:
      200:
        description: Уведомление обработано
        schema:
          type: object
          properties:
            status:
              type: string
            event:
              type: string
      401:
        description: Неверная подпись
      400:
        description: Неверный JSON
    """
    # Получаем тело запроса в сыром виде для проверки подписи
    raw_body = request.get_data()
    signature_header = request.headers.get("X-Yookassa-Signature", "")

    secret_key = current_app.config.get("YOOKASSA_SECRET_KEY")
    if not verify_yookassa_webhook_signature(secret_key, raw_body, signature_header):
        # Вместо логгера просто печатаем в консоль (или можно игнорировать)
        print("Invalid webhook signature")
        return jsonify({"error": "Invalid signature"}), 401

    try:
        event_json = request.get_json()
    except Exception:
        return jsonify({"error": "Invalid JSON"}), 400

    event = event_json.get("event")
    obj = event_json.get("object", {})

    if event == "payment.succeeded":
        process_successful_payment(obj)
        return jsonify({"status": "ok", "event": "payment.succeeded"}), 200
    elif event == "payment.waiting_for_capture":
        return jsonify({"status": "ok", "event": "payment.waiting_for_capture"}), 200
    elif event == "payment.canceled":
        provider_payment_id = obj.get("id")
        if provider_payment_id:
            payment = Payment.query.filter_by(
                provider_payment_id=provider_payment_id
            ).first()
            if payment and payment.status != "canceled":
                payment.status = "canceled"
                db.session.commit()
        return jsonify({"status": "ok", "event": "payment.canceled"}), 200
    elif event == "refund.succeeded":
        return jsonify({"status": "ok", "event": "refund.succeeded"}), 200
    elif event == "payment.refunded":
        return jsonify({"status": "ok", "event": "payment.refunded"}), 200
    else:
        return jsonify({"status": "ignored", "event": event}), 200


# ------------------------- Вспомогательная функция для успешного платежа -------------------------
def process_successful_payment(payment_data: dict):
    """Обновляет статус платежа и бронирования после успешной оплаты."""
    provider_payment_id = payment_data.get("id")
    if not provider_payment_id:
        print("Payment succeeded webhook missing 'id'")
        return

    payment = Payment.query.filter_by(provider_payment_id=provider_payment_id).first()
    if not payment:
        print(f"Payment with provider_id {provider_payment_id} not found in DB")
        return

    if payment.status == "succeeded":
        # уже обработан
        return

    payment.status = "succeeded"
    payment.paid_at = datetime.utcnow()

    paid_amount = payment_data.get("amount", {}).get("value")
    if paid_amount:
        paid_amount_kop = int(float(paid_amount) * 100)
        if paid_amount_kop != payment.amount:
            payment.amount = paid_amount_kop

    paid_currency = payment_data.get("amount", {}).get("currency")
    if paid_currency:
        payment.currency = paid_currency

    appointment = Appointment.query.get(payment.appointment_id)
    if appointment:
        paid_status = AppointmentStatus.query.filter_by(code="paid").first()
        if paid_status:
            appointment.status_id = paid_status.id

    try:
        db.session.commit()
    except SQLAlchemyError:
        db.session.rollback()
        print(f"DB error while processing payment {provider_payment_id}")
