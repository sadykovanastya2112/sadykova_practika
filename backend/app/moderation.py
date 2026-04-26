from datetime import datetime

from flask import Blueprint, g, jsonify, request

from app.extension import db
from app.jwt_auth import jwt_required, require_role
from app.models import Specialist, SpecialistDocuments

moderation_bp = Blueprint("moderation", __name__)

# ------------------------- Список документов на модерацию -------------------------
@moderation_bp.route("/documents", methods=["GET"])
@jwt_required
@require_role('admin')  # или 'moderator' – зависит от вашей роли
def get_documents():
    """
    Получение списка документов на проверку.

    ---
    tags:
      - Moderation
    summary: Получить список документов на модерацию
    description: Возвращает список всех документов со статусом `pending`. Доступно только администраторам/модераторам.
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
              document_id:
                type: integer
              specialist_id:
                type: integer
              specialist_name:
                type: string
              document_type:
                type: string
              title:
                type: string
              file_url:
                type: string
              uploaded_at:
                type: string
                format: date-time
              status:
                type: string
      401:
        description: Неавторизован
      403:
        description: Доступ запрещён (недостаточно прав)
    """

    # Получаем документы на проверке
    docs = SpecialistDocuments.query.filter_by(verification_status="pending")\
        .order_by(SpecialistDocuments.uploaded_time.desc()).all()

    result = []
    for doc in docs:
        result.append({
            "document_id": doc.id,
            "specialist_id": doc.specialist_id,
            "specialist_name": f"{doc.specialist.first_name} {doc.specialist.last_name}",
            "document_type": doc.document_type,
            "title": doc.title,
            "file_url": doc.file_url,
            "uploaded_at": doc.uploaded_time.isoformat(),
            "status": doc.verification_status
        })
    return jsonify(result), 200


# ------------------------- Модерация документа (approve/reject) -------------------------
@moderation_bp.route("/documents/<int:doc_id>", methods=["POST"])
@jwt_required
@require_role('admin')
def moderate_document(doc_id):
    """
    Модерация документа (одобрение/отклонение).

    ---
    tags:
      - Moderation
    summary: Принять решение по документу
    description: Одобрить или отклонить документ. При отклонении обязательно указать причину.
    parameters:
      - name: doc_id
        in: path
        type: integer
        required: true
        description: ID документа
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - action
          properties:
            action:
              type: string
              enum: [approve, reject]
            reason:
              type: string
              description: Причина отклонения (обязательна при reject)
    security:
      - BearerAuth: []
    responses:
      200:
        description: Решение принято
        schema:
          type: object
          properties:
            message:
              type: string
      400:
        description: Неверное действие или отсутствует причина при отказе
      401:
        description: Неавторизован
      403:
        description: Доступ запрещён
      404:
        description: Документ не найден
    """
    data = request.get_json()
    action = data.get("action")
    reason = data.get("reason")

    if action not in ["approve", "reject"]:
        return jsonify({"error": "Invalid action, must be 'approve' or 'reject'"}), 400

    doc = SpecialistDocuments.query.get(doc_id)
    if not doc:
        return jsonify({"error": "Document not found"}), 404

    if doc.verification_status != "pending":
        return jsonify({"error": "Document already moderated"}), 400

    if action == "approve":
        doc.verification_status = "approved"
    else:  # reject
        if not reason:
            return jsonify({"error": "Reason required for rejection"}), 400
        doc.verification_status = "rejected"
        doc.rejection_reason = reason

    doc.verified_by = g.member_id
    doc.verified_at = datetime.utcnow()
    db.session.commit()

    return jsonify({"message": f"Document {action}d successfully"}), 200


# ------------------------- Модерация профиля специалиста -------------------------
@moderation_bp.route("/specialists/<int:specialist_id>", methods=["POST"])
@jwt_required
@require_role('admin')
def moderate_specialist(specialist_id):
    """
    Модерация профиля специалиста.

    ---
    tags:
      - Moderation
    summary: Принять решение по верификации специалиста
    description: Одобрить или отклонить профиль специалиста. При отклонении обязательно указать причину.
    parameters:
      - name: specialist_id
        in: path
        type: integer
        required: true
        description: ID специалиста
      - name: body
        in: body
        required: true
        schema:
          type: object
          required:
            - action
          properties:
            action:
              type: string
              enum: [approve, reject]
            reason:
              type: string
              description: Причина отклонения (обязательна при reject)
    security:
      - BearerAuth: []
    responses:
      200:
        description: Решение принято
        schema:
          type: object
          properties:
            message:
              type: string
      400:
        description: Неверное действие или отсутствует причина при отказе
      401:
        description: Неавторизован
      403:
        description: Доступ запрещён
      404:
        description: Специалист не найден или уже промодерирован
    """
    data = request.get_json()
    action = data.get("action")
    reason = data.get("reason")

    if action not in ["approve", "reject"]:
        return jsonify({"error": "Invalid action, must be 'approve' or 'reject'"}), 400

    specialist = Specialist.query.filter_by(id=specialist_id, verification_status='pending').first()
    if not specialist:
        return jsonify({"error": "Specialist not found or already moderated"}), 404

    if action == "approve":
        specialist.verification_status = "approved"
        specialist.is_approved = True
    else:  # reject
        if not reason:
            return jsonify({"error": "Reason required for rejection"}), 400
        specialist.verification_status = "rejected"
        specialist.rejection_reason = reason

    specialist.verified_by = g.member_id
    specialist.verified_at = datetime.utcnow()
    db.session.commit()

    return jsonify({"message": f"Specialist {specialist_id} {action}d successfully"}), 200


# ------------------------- Опционально: отдельные эндпоинты approve/reject -------------------------

@moderation_bp.route("/approve/document/<int:doc_id>", methods=["POST"])
@jwt_required
@require_role('admin')
def approve_document(doc_id):
    doc = SpecialistDocuments.query.get(doc_id)
    if not doc:
        return jsonify({"error": "Document not found"}), 404
    if doc.verification_status != "pending":
        return jsonify({"error": "Document already moderated"}), 400

    doc.verification_status = "approved"
    doc.verified_by = g.member_id
    doc.verified_at = datetime.utcnow()
    db.session.commit()
    return jsonify({"message": "Document approved successfully"}), 200


@moderation_bp.route("/reject/document/<int:doc_id>", methods=["POST"])
@jwt_required
@require_role('admin')
def reject_document(doc_id):
    data = request.get_json()
    if not data or not data.get("reason"):
        return jsonify({"error": "Reason required"}), 400

    doc = SpecialistDocuments.query.get(doc_id)
    if not doc:
        return jsonify({"error": "Document not found"}), 404
    if doc.verification_status != "pending":
        return jsonify({"error": "Document already moderated"}), 400

    doc.verification_status = "rejected"
    doc.reject_reason = data["reason"]  
    doc.verified_by = g.member_id
    doc.verified_at = datetime.utcnow()
    db.session.commit()
    return jsonify({"message": "Document rejected successfully"}), 200