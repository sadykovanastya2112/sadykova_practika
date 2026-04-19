import os
from datetime import datetime

from flask import Blueprint, current_app, g, jsonify, request
from werkzeug.utils import secure_filename

from app.extension import db
from app.jwt_auth import jwt_required
from app.models import SpecialistDocuments
from app.specialist import get_current_specialist

documents_bp = Blueprint("documents", __name__)


def allowed_file(filename):
    return (
        "." in filename
        and filename.rsplit(".", 1)[1].lower()
        in current_app.config["ALLOWED_EXTENSIONS"]
    )


@documents_bp.route("/upload", methods=["POST"])
@jwt_required
def upload_document():
    """
    Загрузка документа специалистом.
    Ожидает multipart/form-data с полями:
        - file_url: сам файл
        - document_type: 'diploma', 'certificate'
        - title: название документа
    """

    # получаем специалиста
    member_id = g.member_id
    specialist, error, status = get_current_specialist(
        member_id
    )  # предполагаем, что функция есть
    if error:
        return error, status

    # проверяем на наличие файла внутри запроса
    if "file" not in request.files:
        return jsonify({"error": "no file_url"}), 400
    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "no selected file"}), 400
    if not allowed_file(file.filename):
        return jsonify({"error": "File type not allowed"}), 400

    # сохраняем файл
    original_filename = secure_filename(file.filename)

    # генерируем уникальное имя файла по типу: {specialist_<specialist_id_<time>.{etc}>}
    etc = secure_filename(original_filename).rsplit(".", 1)[1].lower()
    unix_filename = f"specialist_{specialist.id}_{datetime.utcnow().timestamp()}.{etc}"
    filepath = os.path.join(current_app.config["UPLOAD_FOLDER"], unix_filename)
    file.save(filepath)

    document_type = request.form.get("document_type")
    title = request.form.get("title")
    if not document_type:
        return jsonify({"error": "document_type are required"}), 400

    if not title:
        return jsonify({"error": "title are required"}), 400

    if document_type == "diploma":
        old_diploma = SpecialistDocuments.query.filter_by(
            specialist_id=specialist.id, is_active=True, document_title="diploma"
        ).first()
        if old_diploma:
            old_diploma.is_active = False
            db.session.add(old_diploma)
    elif document_type == "certificate":
        old_cert = SpecialistDocuments.query.filter_by(
            specialist_id=specialist.id, is_active=True, document_title="certificate"
        ).first()
        if old_cert:
            old_cert.is_active = False
            db.session.add(old_cert)

    doc = SpecialistDocuments(
        specialist_id=specialist.id,
        document_title=document_type,
        file_url=f"/uploads/{unix_filename}",
        is_active=True,
        origin_name=original_filename,
        uploaded_time=datetime.utcnow(),
        verification_status="pending",
    )
    db.session.add(doc)
    db.session.commit()

    return jsonify({"id": doc.id, "file_url": doc.file_url, "status": "pending"}), 201
