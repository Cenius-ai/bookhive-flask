from flask import Blueprint, render_template
from flask_login import login_required, current_user
from sqlalchemy import func, select

from models import db, Book, Review, UserBookShelf
from feed import get_activity_feed

home_bp = Blueprint("home", __name__)


@home_bp.route("/")
def index():
    if not current_user.is_authenticated:
        # Show a welcome/public page with top-rated books
        top_books = (
            db.session.query(
                Book, func.coalesce(func.avg(Review.rating), 0).label("avg_rating")
            )
            .outerjoin(Review, Review.book_id == Book.id)
            .group_by(Book.id)
            .order_by(func.avg(Review.rating).desc())
            .limit(6)
            .all()
        )
        return render_template("home.html", top_books=top_books)

    # -- Authenticated home dashboard --

    # Reading shelf
    reading_entries = (
        UserBookShelf.query.filter_by(user_id=current_user.id, shelf="reading")
        .order_by(UserBookShelf.created_at.desc())
        .limit(5)
        .all()
    )
    reading_books = [e.book for e in reading_entries]

    # Recommended: highest-rated books the user hasn't shelved
    shelved_sub = (
        select(UserBookShelf.book_id)
        .where(UserBookShelf.user_id == current_user.id)
        .subquery()
    )
    recommended = (
        db.session.query(
            Book, func.coalesce(func.avg(Review.rating), 0).label("avg_rating")
        )
        .outerjoin(Review, Review.book_id == Book.id)
        .filter(~Book.id.in_(select(shelved_sub)))
        .group_by(Book.id)
        .order_by(func.avg(Review.rating).desc())
        .limit(4)
        .all()
    )

    # Activity feed
    feed_items = get_activity_feed(current_user.id)

    return render_template(
        "home.html",
        reading_books=reading_books,
        recommended=recommended,
        feed_items=feed_items,
    )
