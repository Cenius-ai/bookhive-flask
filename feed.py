from flask import Blueprint, current_app
from sqlalchemy import union_all, select, literal_column, desc

from models import db, Review, UserBookShelf, Follow

feed_bp = Blueprint("feed", __name__)


def get_activity_feed(user_id, limit=None):
    """Return recent reviews and shelf changes from users that `user_id` follows.

    Returns a list of dicts with keys: type ('review' or 'shelf'), user, book,
    timestamp, and type-specific data (rating, text, shelf).
    """
    if limit is None:
        limit = current_app.config["FEED_ITEMS_PER_PAGE"]

    # IDs of users that `user_id` follows
    followed_ids_sub = (
        select(Follow.followed_id)
        .where(Follow.follower_id == user_id)
        .subquery()
    )

    reviews_q = (
        select(
            Review.created_at.label("timestamp"),
            literal_column("'review'").label("event_type"),
            Review.user_id,
            Review.book_id,
            Review.rating,
            Review.text,
            literal_column("NULL").label("shelf"),
            Review.id.label("event_id"),
        )
        .where(Review.user_id.in_(select(followed_ids_sub)))
    )

    shelves_q = (
        select(
            UserBookShelf.created_at.label("timestamp"),
            literal_column("'shelf'").label("event_type"),
            UserBookShelf.user_id,
            UserBookShelf.book_id,
            literal_column("NULL").label("rating"),
            literal_column("NULL").label("text"),
            UserBookShelf.shelf,
            UserBookShelf.id.label("event_id"),
        )
        .where(UserBookShelf.user_id.in_(select(followed_ids_sub)))
    )

    union_q = (
        union_all(reviews_q, shelves_q)
        .order_by(desc("timestamp"))
        .limit(limit)
    )

    rows = db.session.execute(union_q).all()

    from models import User, Book

    feed_items = []
    for row in rows:
        event = {
            "type": row.event_type,
            "user": db.session.get(User, row.user_id),
            "book": db.session.get(Book, row.book_id),
            "timestamp": row.timestamp,
        }
        if row.event_type == "review":
            event["rating"] = row.rating
            event["text"] = row.text
        else:
            event["shelf"] = row.shelf
        feed_items.append(event)

    return feed_items
