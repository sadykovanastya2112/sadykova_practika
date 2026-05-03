import os
from datetime import datetime

import filetype
from flask import Blueprint, current_app, g, jsonify, request
from werkzeug.utils import secure_filename

from app.extension import db
from app.jwt_auth import jwt_required
from app.models import Specialist, SpecialistDocuments

documents_bp = Blueprint("documents", __name__)


def allowed_file(filename):
    ALLOWED_EXTENSIONS = {"pdf", "jpg", "jpeg", "png", "doc", "docx"}
    return "." in filename and filename.rsplit(".", 1)[1].lower() in ALLOWED_EXTENSIONS


def get_current_specialist(member_id):
    specialist = Specialist.query.filter_by(member_id=member_id, is_active=True).first()
    if not specialist:
        return None, jsonify({"error": "Specialist not found"}), 404
    return specialist, None, None


@documents_bp.route("/upload", methods=["POST"])
@jwt_required
def upload_document():
    member_id = g.member_id
    specialist, error, status = get_current_specialist(member_id)
    if error:
        return error, status

    if "file" not in request.files:
        return jsonify({"error": "No file part"}), 400
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No selected file"}), 400

    if not allowed_file(file.filename):
        return jsonify({"error": "File extension not allowed"}), 400

    # Проверка MIME-типа через filetype
    file_data = file.read(1024)
    kind = filetype.guess(file_data)
    file.seek(0)

    allowed_mime_types = [
        "application/pdf",
        "image/jpeg",
        "image/png",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ]
    if kind is None or kind.mime not in allowed_mime_types:
        return jsonify({"error": "File MIME type not allowed"}), 400

    original_filename = secure_filename(file.filename)
    ext = original_filename.rsplit(".", 1)[1].lower()
    timestamp = datetime.utcnow().timestamp()
    new_filename = f"specialist_{specialist.id}_{timestamp}.{ext}"
    filepath = os.path.join(current_app.config["UPLOAD_FOLDER"], new_filename)
    file.save(filepath)

    document_type = request.form.get("document_title")
    title = request.form.get("title")
    if not document_type:
        return jsonify({"error": "document_type is required"}), 400
    if not title:
        return jsonify({"error": "title is required"}), 400

    if document_type in ["diploma", "certificate"]:
        old = SpecialistDocuments.query.filter_by(
            specialist_id=specialist.id, document_type=document_type, is_active=True
        ).first()
        if old:
            old.is_active = False
            db.session.add(old)

    doc = SpecialistDocuments(
        specialist_id=specialist.id,
        document_type=document_type,
        title=title,
        file_url=f"/uploads/{new_filename}",
        original_name=original_filename,
        is_active=True,
        uploaded_at=datetime.utcnow(),
        verification_status="pending",
    )
    db.session.add(doc)
    db.session.commit()

    return jsonify({"id": doc.id, "file_url": doc.file_url, "status": "pending"}), 201
