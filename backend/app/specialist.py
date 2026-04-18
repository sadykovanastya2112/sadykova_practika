from flask import Blueprint, request, jsonify, g
from app.extension import db
from app.models import Specialist, Review
from sqlalchemy import func, and_, or_
from app.jwt_auth import jwt_required

specialist_bp = Blueprint("specialist", __name__)

@specialist_bp.route("/specialists", methods=["GET"])
def all_specialist():
    """
    Возвращает список одобренных специалистов с пагинацией и фильтрацией.
    Параметры (все необязательные):
        page: номер страницы
        per_page: количество на странице 
        specialization: фильтр по специализации 
        min_price, max_price: диапазон цены
        min_rating: минимальный рейтинг (1-5)
        min_experience: минимальный опыт в годах
        gender: пол (m/f) 
        sort_by: поле для сортировки (price, rating, experience, name)
        sort_order: asc или desc
    """
    # Параметры пагинации
    page = request.args.get('page', 1, type=int)
    per_page = request.args.get('per_page', 20, type=int)
    if per_page > 100:
        per_page = 100


    # базовый запрос
    query = Specialist.query.filter_by(is_visible=True, is_active=True)
    # фильры
    specialization = request.args.get('specialization')
    if specialization:
        query = query.filter(Specialist.specialization.ilike(f"%{specialization}"))

    min_price = request.args.get('min_price')
    if min_price:
        query = query.filter(Specialist.base_price >= min_price)
    
    max_price = request.args.get('max_price')
    if min_price:
        query = query.filter(Specialist.base_price >= max_price)
    
    # min_rating = request.args.get('min_rating')
    # if min_rating:

    min_experience = request.args.get('min_experience')
    if min_price:
        query = query.filter(Specialist.experience_years >= min_experience)

    min_experience = request.args.get('min_experience')
    if min_price:
        query = query.filter(Specialist.experience_years >= min_experience)


    # Сортировка
    sort_by = request.args.get('sort_by', 'id')
    sort_order = request.args.get('sort_order', 'asc')
    if sort_order == 'desc':
        if sort_by == 'price':
            query = query.order_by(Specialist.base_price.desc())
        elif sort_by == 'experience':
            query = query.order_by(Specialist.experience_years.desc())
        elif sort_by == 'name':
            query = query.order_by(Specialist.first_name.desc())
        elif sort_by == 'rating':
            # Сортировка по рейтингу (нужен тот же подзапрос)
            subq = db.session.query(
                Review.specialist_id,
                func.avg(Review.rating).label('avg_rating')
            ).group_by(Review.specialist_id).subquery()
            query = query.outerjoin(subq, Specialist.id == subq.c.specialist_id)
            query = query.order_by(subq.c.avg_rating.desc())
        else:
            query = query.order_by(Specialist.id.desc())
    else:
        if sort_by == 'price':
            query = query.order_by(Specialist.base_price.asc())
        elif sort_by == 'experience':
            query = query.order_by(Specialist.experience_years.asc())
        elif sort_by == 'name':
            query = query.order_by(Specialist.first_name.asc())
        elif sort_by == 'rating':
            subq = db.session.query(
                Review.specialist_id,
                func.avg(Review.rating).label('avg_rating')
            ).group_by(Review.specialist_id).subquery()
            query = query.outerjoin(subq, Specialist.id == subq.c.specialist_id)
            query = query.order_by(subq.c.avg_rating.asc())
        else:
            query = query.order_by(Specialist.id.asc())

    # Пагинация
    paginated = query.paginate(page=page, per_page=per_page, error_out=False)

    specialist_list = []
    for s in paginated.items:
        avg_rating = db.session.query(func.avg(Review.rating)).filter_by(specialist_id=s.id).scalar()
        avg_rating = round(avg_rating, 1) if avg_rating else 0

        specialist_list.append({
            'id': s.id,
            'first_name': s.first_name,
            'last_name': s.last_name,
            'specialization': s.specialization,
            'base_price': s.base_price,
            'experience_years': s.experience_years,
            'photo_url': s.photo_url,
            'rating': avg_rating,
            'is_approved': s.is_approved
        })

    return jsonify({
        'items': specialist_list,
        'total': paginated.total,
        'page': page,
        'per_page': per_page,
        'pages': paginated.pages
    }), 200


@specialist_bp.route('/specialist/<int:specialist_id>', methods=['GET'])
def specialist_profile():
    """
        Возвращает полную информацию о специалисте.
        Доступно без авторизации (гостю).
    """
    specialist_id = request.args.get('specialist_id')
    if not specialist_id:
        return jsonify({"error":"requared specialist_id"}),400
    specialist = Specialist.query.filter_by(specialist_id=specialist_id).first()

    member = specialist.member

    review_count = Review.query.filter_by(specialist_id = specialist.id).count()

    # Формируем ответ
    # return jsonify({
    #     'id': specialist.id,
    #     'first_name': specialist.first_name,
    #     'last_name': specialist.last_name,
    #     'specialization': specialist.specialization,
    #     'experience_years': specialist.experience_years,
    #     'base_price': specialist.base_price,
    #     'bio': specialist.bio,
    #     'photo_url': specialist.photo_url,
    #     'education': specialist.education,   # если есть
    #     'rating': avg_rating,
    #     'reviews_count': reviews_count,
    #     'recent_reviews': reviews_list,
    # }), 200

    # Рейтинг
    # avg_rating = db.session.query(func.avg(Review.rating)).filter_by(specialist_id=specialist.id).scalar()
    # avg_rating = round(avg_rating, 1) if avg_rating else 0


