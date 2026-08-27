from datetime import datetime, timezone

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user

from models import db, Book, UserBookShelf, User, Review

shelves_bp = Blueprint("shelves", __name__)

VALID_SHELVES = {"want_to_read", "reading", "read"}
SHELF_LABELS = {
    "want_to_read": "Want to Read",
    "reading": "Reading",
    "read": "Read",
}


@shelves_bp.route("/books/<int:book_id>/shelf", methods=["POST"])
@login_required
def update_shelf(book_id):
    book = db.session.get(Book, book_id)
    if book is None:
        flash("Book not found.", "error")
        return redirect(url_for("books.list_books"))

    shelf = request.form.get("shelf", "").strip()
    if shelf not in VALID_SHELVES:
        flash("Invalid shelf selection.", "error")
        return redirect(url_for("books.book_detail", id=book_id))

    entry = UserBookShelf.query.filter_by(
        user_id=current_user.id, book_id=book_id
    ).first()

    if entry:
        entry.shelf = shelf
        entry.created_at = datetime.now(timezone.utc)
    else:
        entry = UserBookShelf(
            user_id=current_user.id,
            book_id=book_id,
            shelf=shelf,
            created_at=datetime.now(timezone.utc),
        )
        db.session.add(entry)

    db.session.commit()
    flash(f"Added to your {SHELF_LABELS[shelf]} shelf!", "success")
    return redirect(url_for("books.book_detail", id=book_id))


@shelves_bp.route("/users/<int:user_id>")
def profile(user_id):
    user = db.session.get(User, user_id)
    if user is None:
        flash("User not found.", "error")
        return redirect(url_for("home.index"))

    # Get books for each shelf
    want_shelved = (
        UserBookShelf.query.filter_by(user_id=user_id, shelf="want_to_read")
        .order_by(UserBookShelf.created_at.desc())
        .all()
    )
    reading_shelved = (
        UserBookShelf.query.filter_by(user_id=user_id, shelf="reading")
        .order_by(UserBookShelf.created_at.desc())
        .all()
    )
    read_shelved = (
        UserBookShelf.query.filter_by(user_id=user_id, shelf="read")
        .order_by(UserBookShelf.created_at.desc())
        .all()
    )

    # Reviews by this user
    reviews = (
        Review.query.filter_by(user_id=user_id)
        .order_by(Review.created_at.desc())
        .limit(20)
        .all()
    )

    # Follower / following counts
    from models import Follow
    follower_count = Follow.query.filter_by(followed_id=user_id).count()
    following_count = Follow.query.filter_by(follower_id=user_id).count()

    # Check if current user follows this user
    is_following = False
    if current_user.is_authenticated and current_user.id != user_id:
        is_following = Follow.query.filter_by(
            follower_id=current_user.id, followed_id=user_id
        ).first() is not None

    return render_template(
        "profile.html",
        profile_user=user,
        want_shelved=want_shelved,
        reading_shelved=reading_shelved,
        read_shelved=read_shelved,
        reviews=reviews,
        follower_count=follower_count,
        following_count=following_count,
        is_following=is_following,
        shelf_labels=SHELF_LABELS,
    )
