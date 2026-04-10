from flask import Blueprint, request, jsonify, redirect, url_for, session, current_app
from yookassa import Configuration, Payment
import uuid
import json
import os

payments_bp = Blueprint('payments', __name__)

#Настройка ЮКассы

def init_yookassa():
    Configuration.configure(
        account_id=current_app.config['YOOKASSA_SHOP_ID'],
        secret_key=current_app.config['YOOKASSA_SECRET_KEY']
    )

@payments_bp.route('/create-payment', methods=['POST'])
def create_payment():
    
    try:
        #Создаёт тестовый платёж и возвращает ссылку на оплату
        init_yookassa()
        #Генерируем уникальный idempotence key
        idempotence_key=str(uuid.uuid4())
        #Создание платежа
        payment = Payment.create({
            "amount": {
                "value": "100.00",
                "currency": "RUB"
            },
            "confirmation": {
                "type": "redirect",
                "return_url": "http://127.0.0.1:5000/payment-success"
            },
            "capture": True,
            "description": "Проверка тестового платежа"
        }, idempotence_key)
        #Сохранение в сессии
        session['last_payment_id'] = payment.id
        #Возвращение ссылки для редиректа

        response_data = {
            'confirmation_url': payment.confirmation.confirmation_url,
            'payment_id': payment.id
        }
        return jsonify(response_data)
    except Exception as e:
        print(f"Ошибка создания платежа: {e}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': str(e)}), 500

@payments_bp.route('/payment-success')
def payment_success():
    #редирект на страницу с успешной оплатой
    return jsonify({"message": "Тестовый платёж прошёл успешно"})

@payments_bp.route('/webhook/yookassa', methods=['POST'])
def yookassa_webhook():
    """
    Обработчик уведомлений от ЮKassa (меняет статус платежа).
    """
    event_json = request.get_json()
    print("Webhook received:", json.dumps(event_json, indent=2))
    
    # Здесь можно проверить объект и обновить статус платежа (позже с БД)
    # Сейчас просто логируем
    return '', 200