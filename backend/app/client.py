from datetime import datetime

from flask import Blueprint, g, jsonify, request


from sqlalchemy import and_
from app.extension import db
from app.jwt_auth import jwt_required
from app.models import Slot, Specialist, Client, Appointment, AppointmentStatus

clients_bp = Blueprint('clients', __name__)

def get_current_client(member_id):
    client = Client.query.filter_by(member_id=member_id).first()
    if not client:
        return None, jsonify({"message": "User is not client"}), 403
    return client, None, None


#Просмотр свободных слотов выбранного специалиста
@clients_bp.route('/get-slots', methods=['GET'])
@jwt_required
def check_specialist_slots():



    # получаем айди специалиста
    specialist_id = request.args.get('specialist_id')

    if not specialist_id:
        return jsonify({"error": "specialist not found"}),404
    
    # запрос на показ слотов позже даты пользователя и проверка на бронирование слота
    slots = Slot.query.filter(Slot.specialist_id == specialist_id, 
                              Slot.start_at > datetime.now(),
                                ~Slot.appointments.any()
                                ).order_by(Slot.start_at).all()
    
    # отдаём данные
    return jsonify([{
        "id": s.id,
        "start_at": s.start_at.isoformat(),
        "end_at": s.end_at.isoformat(),
    }for s in slots])
    




@clients_bp.route('/make-appointment', methods=['POST'])
@jwt_required
def create_appointment():
    # Тело запроса, например: {"slot_id": 123, "specialist_id": 1}
    data_slot = request.get_json()
    if not data_slot:
        return jsonify({"error": "slot id not in request"}),400

    # получаем клиента
    member_id = g.member_id
    client, error_response, status = get_current_client(member_id)
    if error_response:
        return error_response, status
    
    # проверяем есть ли такой слот
    slot = Slot.query.filter(Slot.id == data_slot['slot_id'],
                            Slot.specialist_id == data_slot['specialist_id'],
                            Slot.start_at > datetime.now(),
                            ~Slot.appointments.any()
                            ).order_by(Slot.start_at).first()

    if not slot:
        return jsonify({"error": "slot in appointment"}),400
    
    # if client.member_id == slot.specialist.member_id:
    #     return jsonify({"error":"психолог не может сам у себя забронировать слот"}),400

    # я пока неуверен может ли пользователь одновременно сделать несколько бронирований, но пока что сделаю только по одному

    status = AppointmentStatus.query.filter_by(code='pending_payment').first()

    appointment = Appointment(
        slot_id = data_slot['slot_id'],
        client_id = client.id,
        status_id = status.id,
        created_at = datetime.now()
    )

    db.session.add(appointment)
    db.session.commit()

    return jsonify({
        "appointment_id": appointment.id,
        "slot_id": slot.id,
        "client_id": client.id,
        "status_id" : status.id #позже исправить 
    }),201

