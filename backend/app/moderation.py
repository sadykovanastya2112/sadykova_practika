from datetime import datetime

from flask import Blueprint, g, jsonify, request

from app.extension import db
from app.jwt_auth import jwt_required
from app.models import Member, Specialist, SpecialistDocuments

moderation_bp = Blueprint("moderation", __name__)


# ------------------------- Список документов на модерацию -------------------------
@moderation_bp.route("/documents", methods=["GET"])
@jwt_required
# @require_role('admin')  # или 'moderator' – зависит от вашей роли
def get_documents():

    # Получаем документы на проверке
    docs = (
        SpecialistDocuments.query.filter_by(verification_status="pending")
        .order_by(SpecialistDocuments.uploaded_time.desc())
        .all()
    )

    result = []
    for doc in docs:
        result.append(
            {
                "document_id": doc.id,
                "specialist_id": doc.specialist_id,
                "specialist_name": f"{doc.specialist.first_name} {doc.specialist.last_name}",
                "document_type": doc.document_type,
                "title": doc.title,
                "file_url": doc.file_url,
                "uploaded_at": doc.uploaded_time.isoformat(),
                "status": doc.verification_status,
            }
        )
    return jsonify(result), 200


# ------------------------- Модерация документа (approve/reject) -------------------------
@moderation_bp.route("/documents/<int:doc_id>", methods=["POST"])
@jwt_required
# @require_role('admin')
def moderate_document(doc_id):

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


# ------------------------- Список специалистов, ожидающих верификацию -------------------------
@moderation_bp.route("/specialists/pending", methods=["GET"])
@jwt_required
def get_pending_specialists():
    page = request.args.get("page", 1, type=int)
    per_page = min(request.args.get("per_page", 20, type=int), 100)

    query = (
        db.session.query(Specialist, Member.email)
        .outerjoin(Member, Specialist.member_id == Member.id)
        .filter(
            Specialist.verification_status == "pending", Specialist.is_approved == False
        )
        .order_by(Specialist.created_at.asc())
    )

    paginated = query.paginate(page=page, per_page=per_page, error_out=False)

    return jsonify(
        {
            "items": [
                {
                    "id": s.Specialist.id,
                    "full_name": f"{s.Specialist.first_name} {s.Specialist.last_name}",
                    "email": s.email if s.email else "Email не указан",
                    "specialization": s.Specialist.specialization,
                    "education": s.Specialist.education,
                    "experience_years": s.Specialist.experience_years,
                    "base_price": s.Specialist.base_price,
                    "bio": s.Specialist.bio,
                    "photo_url": s.Specialist.photo_url,
                    "created_at": s.Specialist.created_at.isoformat()
                    if s.Specialist.created_at
                    else None,
                }
                for s in paginated.items
            ],
            "total": paginated.total,
            "page": page,
            "per_page": per_page,
            "pages": paginated.pages,
        }
    ), 200


# ------------------------- Модерация профиля специалиста -------------------------
@moderation_bp.route("/specialists/<int:specialist_id>", methods=["POST"])
@jwt_required
# @require_role('admin')
def moderate_specialist(specialist_id):
    data = request.get_json()
    action = data.get("action")
    reason = data.get("reason")

    if action not in ["approve", "reject"]:
        return jsonify({"error": "Invalid action, must be 'approve' or 'reject'"}), 400

    specialist = Specialist.query.filter_by(
        id=specialist_id, verification_status="pending"
    ).first()
    if not specialist:
        return jsonify({"error": "Specialist not found or already moderated"}), 404

    if action == "approve":
        specialist.verification_status = "approved"
        specialist.is_approved = True
    else:  # reject
        if not reason:
            return jsonify({"error": "Reason required for rejection"}), 400
        specialist.verification_status = "rejected"
        specialist.reject_reason = reason

    specialist.verified_by = g.member_id
    specialist.verified_at = datetime.utcnow()
    db.session.commit()

    return jsonify(
        {"message": f"Specialist {specialist_id} {action}d successfully"}
    ), 200


# ------------------------- Опционально: отдельные эндпоинты approve/reject -------------------------


@moderation_bp.route("/approve/document/<int:doc_id>", methods=["POST"])
@jwt_required
# @require_role('admin')
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
# @require_role('admin')
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
