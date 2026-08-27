from datetime import datetime, timezone

from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_required, current_user

from models import db, Review, Book

reviews_bp = Blueprint("reviews", __name__)


@reviews_bp.route("/books/<int:book_id>/review", methods=["POST"])
@login_required
def create_review(book_id):
    book = db.session.get(Book, book_id)
    if book is None:
        flash("Book not found.", "error")
        return redirect(url_for("books.list_books"))

    # Check for existing review
    existing = Review.query.filter_by(
        user_id=current_user.id, book_id=book_id
    ).first()
    if existing:
        flash("You have already reviewed this book. You can edit your existing review.", "error")
        return redirect(url_for("books.book_detail", id=book_id))

    rating_str = request.form.get("rating", "").strip()
    text = (request.form.get("text") or "").strip()

    errors = {}
    try:
        rating = int(rating_str)
        if rating < 1 or rating > 5:
            errors["rating"] = "Rating must be between 1 and 5."
    except (ValueError, TypeError):
        errors["rating"] = "Please select a rating."

    if errors:
        flash(errors.get("rating", "Invalid rating."), "error")
        return redirect(url_for("books.book_detail", id=book_id))

    review = Review(
        user_id=current_user.id,
        book_id=book_id,
        rating=rating,
        text=text,
    )
    db.session.add(review)
    db.session.commit()
    flash("Your review has been posted!", "success")
    return redirect(url_for("books.book_detail", id=book_id))


@reviews_bp.route("/reviews/<int:review_id>/edit", methods=["GET", "POST"])
@login_required
def edit_review(review_id):
    review = db.session.get(Review, review_id)
    if review is None:
        flash("Review not found.", "error")
        return redirect(url_for("home.index"))

    if review.user_id != current_user.id and not current_user.is_admin:
        flash("You can only edit your own reviews.", "error")
        return redirect(url_for("books.book_detail", id=review.book_id))

    if request.method == "POST":
        rating_str = request.form.get("rating", "").strip()
        text = (request.form.get("text") or "").strip()

        errors = {}
        try:
            rating = int(rating_str)
            if rating < 1 or rating > 5:
                errors["rating"] = "Rating must be between 1 and 5."
        except (ValueError, TypeError):
            errors["rating"] = "Please select a rating."

        if errors:
            return render_template(
                "edit_review.html", review=review, errors=errors
            )

        review.rating = rating
        review.text = text
        review.updated_at = datetime.now(timezone.utc)
        db.session.commit()
        flash("Your review has been updated.", "success")
        return redirect(url_for("books.book_detail", id=review.book_id))

    return render_template("edit_review.html", review=review, errors={})


@reviews_bp.route("/reviews/<int:review_id>/delete", methods=["POST"])
@login_required
def delete_review(review_id):
    review = db.session.get(Review, review_id)
    if review is None:
        flash("Review not found.", "error")
        return redirect(url_for("home.index"))

    if review.user_id != current_user.id and not current_user.is_admin:
        flash("You can only delete your own reviews.", "error")
        return redirect(url_for("books.book_detail", id=review.book_id))

    book_id = review.book_id
    db.session.delete(review)
    db.session.commit()
    flash("Your review has been deleted.", "success")
    return redirect(url_for("books.book_detail", id=book_id))
