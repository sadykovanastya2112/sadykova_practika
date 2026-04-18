from datetime import datetime

from flask import Blueprint, g, jsonify, request

from app.extension import db
from app.jwt_auth import jwt_required
from app.models import SpecialistDocuments

moderation_bp = Blueprint("moderation", __name__)


def is_moderator(member_id):
    from app.models import MemberRole, Role

    moderator_role = Role.query.filter_by(code="moderator").first()
    if not moderator_role:
        return False
    return (
        MemberRole.query.filter_by(
            member_id=member_id, role_id=moderator_role.id, is_active=True
        ).first()
        is not None
    )


@moderation_bp.route("/documents", methods=["POST"])
@jwt_required
def get_documents():
    """
    получение списка документов на проверку
    """
    if not is_moderator(g.member_id):
        return jsonify({"error": "access denied"}), 400

    # получаем документы на проверке
    docs = SpecialistDocuments.query.filter_by(verification_status="pending").order_by
    (SpecialistDocuments.uploaded_time.desc()).all()

    result = []

    for doc in docs:
        result.append(
            {
                "id": doc.id,
                "specialist_id": doc.specialist_id,
                "specialist_name": f"{doc.specialist.first_name} {doc.specialist.last_name}",
                "document_type": doc.document_type,
                "title": doc.title,
                "file_url": doc.file_url,
                "uploaded_at": doc.uploaded_at.isoformat(),
            }
        )
    return jsonify(result), 200


@moderation_bp.route("/moderation/documents/<int:doc_id>", methods=["POST"])
@jwt_required
def moderating_documents(doc_id):
    """
    логика модерации лоркументов
    тело json {
    action: например, approve
    reason : для отказа
    }
    """
    data = request.get_json()
    action = data.get("action")
    reason = data.get("reason")

    if action not in ["approve", "reject"]:
        return jsonify({"error": "need action"}), 400

    doc = SpecialistDocuments.query.get(doc_id)
    if not doc:
        return jsonify({"error": "document not found"}), 404

    if doc.verification_status != "pending":
        return jsonify({"error": "document already moderated"}), 400

    if action == "approve":
        doc.verification_status = "approve"
    else:
        if not reason:
            return jsonify({"error": "need reason"}), 400
        doc.verification_status = "reject"
        doc.reject_reason = reason

    doc.verified_by = g.member_id
    doc.verified_at = datetime.utcnow()
    db.session.commit()
