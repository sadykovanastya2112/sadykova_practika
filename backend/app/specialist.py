from flask import Blueprint, g, jsonify, request
from sqlalchemy import func

from app.extension import db
from app.jwt_auth import jwt_required
from app.models import Member, Review, Specialist, SpecialistDocuments

specialist_bp = Blueprint("specialist", __name__)


def get_current_specialist(member_id):
    specialist = Specialist.query.filter_by(member_id=member_id).first()
    if not specialist:
        return None, jsonify({"message": "User is not specialist"}), 403
    return specialist, None, None


@specialist_bp.route("/specialists", methods=["GET"])
def all_specialist():

    # Параметры пагинации
    page = request.args.get("page", 1, type=int)
    per_page = request.args.get("per_page", 20, type=int)
    if per_page > 100:
        per_page = 100

    # Базовый запрос: только активные и одобренные специалисты
    query = Specialist.query.filter_by(is_active=True, is_approved=True)

    # Фильтр по специализации (частичное совпадение)
    specialization = request.args.get("specialization")
    if specialization:
        query = query.filter(Specialist.specialization.ilike(f"%{specialization}%"))

    # Фильтр по минимальной цене
    min_price = request.args.get("min_price")
    if min_price is not None:
        try:
            min_price = int(min_price)
            query = query.filter(Specialist.base_price >= min_price)
        except ValueError:
            pass

    # Фильтр по максимальной цене
    max_price = request.args.get("max_price")
    if max_price is not None:
        try:
            max_price = int(max_price)
            query = query.filter(Specialist.base_price <= max_price)
        except ValueError:
            pass

    # Фильтр по минимальному рейтингу (нужен подзапрос)
    min_rating = request.args.get("min_rating")
    if min_rating is not None:
        try:
            min_rating = float(min_rating)
            # Подзапрос для среднего рейтинга
            subq = db.session.query(
                Review.specialist_id,
                func.avg(Review.rating).label("avg_rating")
            ).group_by(Review.specialist_id).subquery()
            query = query.outerjoin(subq, Specialist.id == subq.c.specialist_id)
            query = query.filter(subq.c.avg_rating >= min_rating)
        except ValueError:
            pass

    # Фильтр по минимальному опыту
    min_experience = request.args.get("min_experience")
    if min_experience is not None:
        try:
            min_experience = int(min_experience)
            query = query.filter(Specialist.experience_years >= min_experience)
        except ValueError:
            pass


    # Сортировка
    sort_by = request.args.get("sort_by", "id")
    sort_order = request.args.get("sort_order", "asc")

    # Общий подзапрос для рейтинга (если используется сортировка по рейтингу)
    rating_subq = None
    if sort_by == "rating":
        rating_subq = db.session.query(
            Review.specialist_id,
            func.avg(Review.rating).label("avg_rating")
        ).group_by(Review.specialist_id).subquery()
        query = query.outerjoin(rating_subq, Specialist.id == rating_subq.c.specialist_id)

    if sort_order == "desc":
        if sort_by == "price":
            query = query.order_by(Specialist.base_price.desc())
        elif sort_by == "experience":
            query = query.order_by(Specialist.experience_years.desc())
        elif sort_by == "name":
            query = query.order_by(Specialist.first_name.desc())
        elif sort_by == "rating" and rating_subq:
            query = query.order_by(rating_subq.c.avg_rating.desc())
        else:
            query = query.order_by(Specialist.id.desc())
    else:
        if sort_by == "price":
            query = query.order_by(Specialist.base_price.asc())
        elif sort_by == "experience":
            query = query.order_by(Specialist.experience_years.asc())
        elif sort_by == "name":
            query = query.order_by(Specialist.first_name.asc())
        elif sort_by == "rating" and rating_subq:
            query = query.order_by(rating_subq.c.avg_rating.asc())
        else:
            query = query.order_by(Specialist.id.asc())

    # Пагинация
    paginated = query.paginate(page=page, per_page=per_page, error_out=False)

    specialist_list = []
    for s in paginated.items:
        avg_rating = db.session.query(func.avg(Review.rating)).filter_by(specialist_id=s.id).scalar()
        avg_rating = round(avg_rating, 1) if avg_rating else 0

        specialist_list.append({
            "id": s.id,
            "first_name": s.first_name,
            "last_name": s.last_name,
            "specialization": s.specialization,
            "base_price": s.base_price,
            "experience_years": s.experience_years,
            "photo_url": s.photo_url,
            "rating": avg_rating,
            "is_approved": s.is_approved,
        })

    return jsonify({
        "items": specialist_list,
        "total": paginated.total,
        "page": page,
        "per_page": per_page,
        "pages": paginated.pages,
    }), 200


@specialist_bp.route("/profile/<int:specialist_id>", methods=["GET"])
def specialist_profile(specialist_id):
    
    specialist = Specialist.query.filter_by(id=specialist_id, is_active=True, is_approved=True).first()
    if not specialist:
        return jsonify({"error": "Specialist not found"}), 404

    avg_rating = db.session.query(func.avg(Review.rating)).filter_by(specialist_id=specialist.id).scalar()
    avg_rating = round(avg_rating, 1) if avg_rating else 0

    recent_reviews = Review.query.filter_by(specialist_id=specialist.id).order_by(Review.created_at.desc()).limit(5).all()
    reviews_list = [{
        "rating": r.rating,
        "comment": r.comment,
        "created_at": r.created_at.isoformat(),
        "client_name": r.client.display_name if r.client else "Аноним",
    } for r in recent_reviews]

    reviews_count = Review.query.filter_by(specialist_id=specialist.id).count()

    return jsonify({
        "id": specialist.id,
        "first_name": specialist.first_name,
        "last_name": specialist.last_name,
        "specialization": specialist.specialization,
        "experience_years": specialist.experience_years,
        "base_price": specialist.base_price,
        "bio": specialist.bio,
        "photo_url": specialist.photo_url,
        "education": specialist.education,
        "rating": avg_rating,
        "reviews_count": reviews_count,
        "recent_reviews": reviews_list,
    }), 200


@specialist_bp.route("/me", methods=["GET"])
@jwt_required
def profile():
    
    member_id = g.member_id
    specialist, error_response, status = get_current_specialist(member_id)
    if error_response:
        return error_response, status

    member = Member.query.get(member_id)

    profile_data = {
        "id": specialist.id,
        "first_name": specialist.first_name,
        "last_name": specialist.last_name,
        "specialization": specialist.specialization,
        "education": specialist.education,
        "bio": specialist.bio,
        "experience_years": specialist.experience_years,
        "base_price": specialist.base_price,
        "photo_url": specialist.photo_url,
        "verification_status": specialist.verification_status,
        "is_approved": specialist.is_approved,
        "created_at": specialist.created_at.isoformat() if specialist.created_at else None,
        "email": member.email if member else None,
    }

    return jsonify({"me": profile_data, "id": specialist.id})


@specialist_bp.route("/update", methods=["PUT"])
@jwt_required
def update_profile():
    member_id = g.member_id
    specialist, error_response, status = get_current_specialist(member_id)
    if error_response:
        return error_response, status

    data = request.get_json()
    if not data:
        return jsonify({"error": "no json data"}), 400

    allowed_fields = ["specialization", "bio", "base_price", "photo_url", "experience_years"]
    changed = False

    for item in allowed_fields:
        if item in data:
            if item == 'base_price' and data[item] <= 0:
                return jsonify({"error": f"{item} cannot be 0 or lower"}), 400
            if item == 'experience_years' and data[item] <= 0:
                return jsonify({"error": f"{item} cannot be 0 or lower"}), 400
            setattr(specialist, item, data[item])
            changed = True

    if changed and specialist.is_approved:
        specialist.is_approved = False
        specialist.verification_status = "pending"

    db.session.commit()
    return jsonify({"message": "profile info updated", "id": member_id}), 200


@specialist_bp.route('/me/documents', methods=['GET'])
@jwt_required
def get_my_documents():
    member_id = g.member_id
    specialist, error, status = get_current_specialist(member_id)
    if error:
        return error, status

    docs = SpecialistDocuments.query.filter_by(specialist_id=specialist.id).order_by(SpecialistDocuments.uploaded_at.desc()).all()
    result = []
    for doc in docs:
        result.append({
            'id': doc.id,
            'document_type': doc.document_type,
            'title': doc.title,
            'file_url': doc.file_url,
            'verification_status': doc.verification_status,
            'is_active': doc.is_active,
            'uploaded_at': doc.uploaded_at.isoformat()
        })
    return jsonify(result), 200