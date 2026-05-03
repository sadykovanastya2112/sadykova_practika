from datetime import datetime

from flask import Blueprint, g, jsonify, request

from app.extension import db
from app.jwt_auth import jwt_required, require_role
from app.models import Slot, Specialist

slots_bp = Blueprint("slots", __name__)


def get_current_specialist(member_id):
    specialist = Specialist.query.filter_by(member_id=member_id, is_active=True).first()
    if not specialist:
        return None, jsonify({"message": "User is not specialist"}), 403
    return specialist, None, None


# получаем слоты специалиста
@slots_bp.route("/get", methods=["GET"])
@jwt_required
def get_specialist_slots():
    """
    Получение списка слотов текущего специалиста.
    """


    # получаем слоты специлиста
    member_id = g.member_id
    specialist, error_responce, status = get_current_specialist(member_id)
    if error_responce:
        return error_responce, status

    # фильтрация
    start_date = request.args.get("start_date")
    end_date = request.args.get("end_date")
    query = Slot.query.filter_by(specialist_id=specialist.id)

    # запросы
    if start_date:
        query = query.filter(Slot.start_at >= datetime.isoformat(start_date))
    if end_date:
        query = query.filter(Slot.end_at >= datetime.isoformat(end_date))

    slots = query.order_by(Slot.start_at).all()
    if not slots:
        return jsonify({"message": "empty"}),200
    
    if isinstance(slots, list):
        slots_list = []
        return jsonify([
            {
                "id": s.id,
                "start_at": s.start_at.isoformat(),
                "end_at": s.end_at.isoformat(),
                "external_id": s.external_id,
                "price": s.price_slot
            }
            for s in slots_list
        ]), 201
    else:
        return jsonify({
                "id": slots.id,
                "start_at": slots.start_at.isoformat(),
                "end_at": slots.end_at.isoformat(),
                "external_id": slots.external_id,
                "price": slots.price_slot
            })



def check_slot_overlap(specialist_id, start, end):
    """Проверяет, пересекается ли слот с существующими"""
    overlapping = Slot.query.filter(
        Slot.specialist_id == specialist_id,
        Slot.start_at < end,
        Slot.end_at > start
    ).first()
    return overlapping is not None

def slots_overlap(s1_start, s1_end, s2_start, s2_end):
    return s1_start < s2_end and s1_end > s2_start


# Создание слота
@slots_bp.route("/create", methods=["POST"])
@jwt_required
def create_slot():
    member_id = g.member_id
    specialist, error_response, status = get_current_specialist(member_id)
    if error_response:
        return error_response, status

    data = request.get_json()
    if not data:
        return jsonify({"error": "data is not in JSON format"}), 400

    # Преобразование входных данных в единый список 
    if isinstance(data, dict):
        items = [data]
    else:
        items = data

    # Валидация и подготовка данных с проверкой цен
    slots_data = []
    for item in items:
        try:
            start_at = datetime.fromisoformat(item.get("start_at"))
            end_at = datetime.fromisoformat(item.get("end_at"))
        except (TypeError, ValueError):
            return jsonify({"error": "Invalid date format, use ISO 8601"}), 400
        if start_at >= end_at:
            return jsonify({"error": "start_at must be before end_at"}), 400

        price = item.get('price')
        if price is None or price <= 0:
            price = specialist.base_price
        elif not isinstance(price, (int, float)):
            return jsonify({"error": "invalid price"}), 400

        slots_data.append({
            "start": start_at,
            "end": end_at,
            "price": price
        })

    # Проверка конфликтов между новыми слотами
    for i in range(len(slots_data)):
        for j in range(i+1, len(slots_data)):
            if slots_overlap(slots_data[i]["start"], slots_data[i]["end"],
                             slots_data[j]["start"], slots_data[j]["end"]):
                return jsonify({"error": "New slots overlap each other"}), 409

    # Проверка конфликтов с существующими слотами
    for new in slots_data:
        if check_slot_overlap(specialist.id, new["start"], new["end"]):
            return jsonify({"error": "Slot overlaps an existing slot"}), 409

    # Создание слотов
    new_slots = []
    for s_data in slots_data:
        slot = Slot(
            specialist_id=specialist.id,
            start_at=s_data["start"],
            end_at=s_data["end"],
            provider="manual",
            price=s_data["price"]
        )
        db.session.add(slot)
        new_slots.append(slot)
    db.session.commit()

    # Формирование ответа
    if isinstance(data, dict):
        # если был одиночный объект, возвращаем один объект, а не список
        return jsonify({
            "id": new_slots[0].id,
            "start_at": new_slots[0].start_at.isoformat(),
            "end_at": new_slots[0].end_at.isoformat(),
            "price": new_slots[0].price
        }), 201
    else:
        return jsonify([
            {
                "id": s.id,
                "start_at": s.start_at.isoformat(),
                "end_at": s.end_at.isoformat(),
                "price": s.price
            }
            for s in new_slots
        ]), 201


@slots_bp.route("/update/<int:slot_id>", methods=["PUT"])
@jwt_required
def update_slot(slot_id):
    """
    Обновление существующего слота.
    """

    # получаем слоты специлиста
    member_id = g.member_id
    specialist, error_responce, status = get_current_specialist(member_id)
    if error_responce:
        return error_responce, status

    # находи у специлиста его слот
    slot = Slot.query.filter_by(id=slot_id, specialist_id=specialist.id).first()
    if not slot:
        return jsonify({"error": "Slot not found"}), 404
    # проверка на бронь
    if slot.appointments:
        return jsonify({"error": "on this slot already has appointment"})

    data_ab_slot = request.get_json()
    # меняем только то что есть в запросе
    if "start_at" in data_ab_slot:
        slot.start_at = datetime.fromisoformat(data_ab_slot["start_at"])
    if "end_at" in data_ab_slot:
        slot.end_at = datetime.fromisoformat(data_ab_slot["end_at"])
    if slot.start_at > slot.end_at:
        return jsonify({"error": "start_at > end_at"})
    if "price" in data_ab_slot:
        slot.price = data_ab_slot.get('price')
    db.session.commit()
    return jsonify(
        {
            "id": slot.id,
            "start_at": slot.start_at.isoformat(),
            "end_at": slot.end_at.isoformat(),
            "price": slot.peice
        }
    ), 201


@slots_bp.route("/delete/<int:slot_id>", methods=["DELETE"])
@jwt_required

def delete_slot(slot_id):
    """
    Удаление слота.
    """
    # получаем слоты специлиста
    member_id = g.member_id
    specialist, error_responce, status = get_current_specialist(member_id)
    if error_responce:
        return error_responce, status

    # находим у специлиста его слот
    slot = Slot.query.filter_by(id=slot_id, specialist_id=specialist.id).first()
    if not slot:
        return jsonify({"error": "Slot not found"}), 404
    # проверка на бронь
    if slot.appointments:
        return jsonify({"error": "on this slot already has appointment"})

    db.session.delete(slot)
    db.session.commit()
    return jsonify({"message": "slot successfull deleted"}), 200
