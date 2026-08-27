from flask import Blueprint, jsonify, request, current_app
from sqlalchemy import func

from models import db, Book, Review

api_bp = Blueprint("api", __name__)


@api_bp.route("/books")
def list_books():
    page = request.args.get("page", 1, type=int)
    per_page = current_app.config["BOOKS_PER_PAGE"]
    genre_filter = request.args.get("genre", "").strip()
    search = request.args.get("q", "").strip()
    sort_by = request.args.get("sort", "title")

    query = Book.query

    if search:
        from sqlalchemy import or_
        like = f"%{search}%"
        query = query.filter(
            or_(
                Book.title.ilike(like),
                Book.author.ilike(like),
                Book.description.ilike(like),
            )
        )

    if genre_filter:
        query = query.filter(Book.genre == genre_filter)

    if sort_by == "year":
        query = query.order_by(Book.publication_year.desc(), Book.title)
    elif sort_by == "rating":
        avg_sub = (
            db.select(func.coalesce(func.avg(Review.rating), 0))
            .where(Review.book_id == Book.id)
            .correlate(Book)
            .scalar_subquery()
        )
        query = query.order_by(avg_sub.desc(), Book.title)
    else:
        query = query.order_by(Book.title)

    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    books = pagination.items

    book_ids = [b.id for b in books]
    if book_ids:
        avg_ratings = dict(
            db.session.query(Review.book_id, func.avg(Review.rating))
            .filter(Review.book_id.in_(book_ids))
            .group_by(Review.book_id)
            .all()
        )
    else:
        avg_ratings = {}

    results = []
    for book in books:
        avg_r = avg_ratings.get(book.id)
        results.append({
            "id": book.id,
            "title": book.title,
            "author": book.author,
            "cover_url": book.cover_url,
            "genre": book.genre,
            "publication_year": book.publication_year,
            "description": book.description,
            "average_rating": round(avg_r, 2) if avg_r else None,
        })

    return jsonify({
        "books": results,
        "page": pagination.page,
        "per_page": pagination.per_page,
        "total": pagination.total,
        "pages": pagination.pages,
    })


@api_bp.route("/books/<int:id>")
def book_detail(id):
    book = db.session.get(Book, id)
    if book is None:
        return jsonify({"error": {"code": "not_found", "message": "Book not found"}}), 404

    avg_r = db.session.query(func.avg(Review.rating)).filter(
        Review.book_id == book.id
    ).scalar()

    return jsonify({
        "id": book.id,
        "title": book.title,
        "author": book.author,
        "cover_url": book.cover_url,
        "genre": book.genre,
        "publication_year": book.publication_year,
        "description": book.description,
        "average_rating": round(avg_r, 2) if avg_r else None,
        "review_count": Review.query.filter_by(book_id=book.id).count(),
    })
