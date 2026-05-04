import os
from datetime import datetime

import filetype
from flask import Blueprint, current_app, g, jsonify, request
from werkzeug.utils import secure_filename

from app.extension import db
from app.jwt_auth import jwt_required
from app.models import Specialist, SpecialistDocuments

documents_bp = Blueprint("documents", __name__)


def validate_and_save_document_file(file, specialist_id, allowed_extensions=None, max_size_mb=10):
    """
    Проверяет файл документа (расширение, MIME, размер) и сохраняет его в папку uploads.
    Возвращает (new_filename, error_message). Если ошибка – new_filename = None.
    """
    if allowed_extensions is None:
        allowed_extensions = {"pdf", "jpg", "jpeg", "png", "doc", "docx"}

    # 1. Проверка имени файла
    if file.filename == '':
        return None, "No selected file"

    # 2. Проверка расширения
    ext = file.filename.rsplit('.', 1)[1].lower() if '.' in file.filename else ''
    if ext not in allowed_extensions:
        return None, f"File extension not allowed. Allowed: {', '.join(allowed_extensions)}"

    # 3. Проверка MIME-типа по сигнатуре
    file_data = file.read(1024)
    kind = filetype.guess(file_data)
    file.seek(0)  # возвращаем указатель в начало
    allowed_mime_types = [
        "application/pdf",
        "image/jpeg",
        "image/png",
        "application/msword",
        "application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    ]
    if kind is None or kind.mime not in allowed_mime_types:
        return None, "File MIME type not allowed (only PDF, JPEG, PNG, DOC, DOCX)"

    # 4. Проверка размера (опционально)
    file.seek(0, os.SEEK_END)
    size = file.tell()
    file.seek(0)
    if size > max_size_mb * 1024 * 1024:
        return None, f"File size exceeds {max_size_mb} MB"

    # 5. Генерация уникального имени и сохранение
    original_filename = secure_filename(file.filename)
    timestamp = datetime.utcnow().timestamp()
    new_filename = f"specialist_{specialist_id}_{timestamp}.{ext}"
    filepath = os.path.join(current_app.config['UPLOAD_FOLDER'], new_filename)
    file.save(filepath)
    return new_filename, None



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
   

    new_filename, err = validate_and_save_document_file(file, specialist.id)
    if err:
        return jsonify({"error": err}), 400


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
        original_name=secure_filename(file.filename),
        is_active=True,
        uploaded_at=datetime.utcnow(),
        verification_status="pending",
    )
    db.session.add(doc)
    db.session.commit()

    return jsonify({"id": doc.id, "file_url": doc.file_url, "status": "pending"}), 201
