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
    for s in slots:
        return jsonify(
            {
                "id": s.id,
                "start_at": s.start_at.isoformat(),
                "end_at": s.end_at.isoformat(),
                "external_id": s.external_id,
                "provider": s.provider,
                "price": s.price
            }
        ), 200


# Создание слота
@slots_bp.route("/create", methods=["POST"])
@jwt_required

def create_slot():
    """
    Создание одного или нескольких слотов.
    """
    # получаем слоты специалиста
    member_id = g.member_id
    specialist, error_response, status = get_current_specialist(member_id)
    if error_response:
        return error_response, status

    # Получаем данные в JSON
    data_ab_slot = request.get_json()
    if not data_ab_slot:
        return jsonify({"error": "data is not in JSON format"}), 400
    
    # проверка на то что пришёл список данных
    if isinstance(data_ab_slot, list):
        new_slots = []
        for item in data_ab_slot:
            # преобразуем строку в объект datetime
            try:
                price_slot = item.get('price')
                if not price_slot or price_slot < 0:
                    price_slot = specialist.base_price
            except (TypeError, ValueError):
                return jsonify({"error": "invalid price"}), 400
            try:    
                start_at = datetime.fromisoformat(item.get("start_at"))
                end_at = datetime.fromisoformat(item.get("end_at"))
            except (TypeError, ValueError):
                return jsonify({"error": "Invalid date format, use ISO 8601"}), 400

            # проверка на правильность дат
            if start_at >= end_at:
                return jsonify({"error": "start_at > end_at"}), 400

            slot = Slot(
                specialist_id=specialist.id,
                start_at=start_at,
                end_at=end_at,
                provider="manual",
                price = price_slot
            )
            db.session.add(slot)
            new_slots.append(slot)
        db.session.commit()
        # отдаём слоты
        return jsonify([
            {
                "id": s.id,
                "start_at": s.start_at.isoformat(),
                "end_at": s.end_at.isoformat(),
                "external_id": s.external_id,
                "price": s.price_slot
            }
            for s in new_slots
        ]), 201
    else:
        # аналогично, только теперь если это не список
        try:
            if 'price' in data_ab_slot:
                price_slot = data_ab_slot.get('price')
                if price_slot < 0:
                    price_slot = specialist.base_price
            else:
                price_slot = specialist.base_price
             
            start_at = datetime.fromisoformat(data_ab_slot.get("start_at"))
            end_at = datetime.fromisoformat(data_ab_slot.get("end_at"))
        except (TypeError, ValueError):
            return jsonify({"error": "Invalid date format, use ISO 8601"}), 400

        if start_at >= end_at:
            return jsonify({"error": "start_at > end_at"}), 400

        slot = Slot(
            specialist_id=specialist.id,
            start_at=start_at,
            end_at=end_at,
            provider="manual",
            price = price_slot
        )
        db.session.add(slot)
        db.session.commit()
        return jsonify(
            {
                "id": slot.id,
                "start_at": slot.start_at.isoformat(),
                "end_at": slot.end_at.isoformat(),
                "price": price_slot
            }
        ), 201


@slots_bp.route("/update/<int:slot_id>", methods=["PUT"])
@jwt_required
def update_slot(slot_id):
    """
    Обновление существующего слота.

    ---
    tags:
      - Slots
    summary: Обновить слот
    description: Изменяет время начала и/или окончания слота. Нельзя обновить слот, на который уже есть бронирование.
    parameters:
      - name: slot_id
        in: path
        type: integer
        required: true
        description: ID слота
      - name: body
        in: body
        required: true
        schema:
          type: object
          properties:
            start_at:
              type: string
              format: date-time
            end_at:
              type: string
              format: date-time
    security:
      - BearerAuth: []
    responses:
      200:
        description: Слот обновлён
        schema:
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
      400:
        description: Неверные данные (start_at > end_at)
      403:
        description: Пользователь не является специалистом
      404:
        description: Слот не найден
      409:
        description: На слоте уже есть бронирование
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
    db.session.commit()
    return jsonify(
        {
            "id": slot.id,
            "start_at": slot.start_at.isoformat(),
            "end_at": slot.end_at.isoformat(),
        }
    ), 201


@slots_bp.route("/delete/<int:slot_id>", methods=["DELETE"])
@jwt_required

def delete_slot(slot_id):
    """
    Удаление слота.

    ---
    tags:
      - Slots
    summary: Удалить слот
    description: Удаляет слот, если на него нет бронирований.
    parameters:
      - name: slot_id
        in: path
        type: integer
        required: true
        description: ID слота
    security:
      - BearerAuth: []
    responses:
      200:
        description: Слот удалён
        schema:
          type: object
          properties:
            message:
              type: string
      403:
        description: Пользователь не является специалистом
      404:
        description: Слот не найден
      409:
        description: Невозможно удалить слот с существующим бронированием
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
