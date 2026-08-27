from flask import (
    Blueprint, render_template, redirect, url_for, flash, request, current_app,
)
from flask_login import login_required, current_user
from sqlalchemy import func, or_

from models import db, Book, Review

books_bp = Blueprint("books", __name__)


def _book_from_form(book=None):
    """Validate and populate a Book from form data. Returns (book_or_None, errors_dict)."""
    title = (request.form.get("title") or "").strip()
    author = (request.form.get("author") or "").strip()
    cover_url = (request.form.get("cover_url") or "").strip()
    genre = (request.form.get("genre") or "").strip()
    year_str = (request.form.get("publication_year") or "").strip()
    description = (request.form.get("description") or "").strip()

    errors = {}
    if not title:
        errors["title"] = "Title is required."
    if not author:
        errors["author"] = "Author is required."
    if not genre:
        errors["genre"] = "Genre is required."

    year = None
    if year_str:
        try:
            year = int(year_str)
            if year < 1000 or year > 2100:
                errors["publication_year"] = "Please enter a reasonable year."
        except ValueError:
            errors["publication_year"] = "Year must be a number."
    else:
        errors["publication_year"] = "Publication year is required."

    if errors:
        return None, errors

    if book is None:
        book = Book()
    book.title = title
    book.author = author
    book.cover_url = cover_url
    book.genre = genre
    book.publication_year = year
    book.description = description
    return book, {}


@books_bp.route("/books")
def list_books():
    page = request.args.get("page", 1, type=int)
    genre_filter = request.args.get("genre", "").strip()
    sort_by = request.args.get("sort", "title")
    search = request.args.get("q", "").strip()

    query = Book.query

    # Full-text search on title, author, description
    if search:
        like = f"%{search}%"
        query = query.filter(
            or_(
                Book.title.ilike(like),
                Book.author.ilike(like),
                Book.description.ilike(like),
            )
        )

    # Genre filter
    if genre_filter:
        query = query.filter(Book.genre == genre_filter)

    # Sorting
    if sort_by == "year":
        query = query.order_by(Book.publication_year.desc(), Book.title)
    elif sort_by == "rating":
        # Subquery for average rating
        avg_sub = (
            db.select(func.coalesce(func.avg(Review.rating), 0))
            .where(Review.book_id == Book.id)
            .correlate(Book)
            .scalar_subquery()
        )
        query = query.order_by(avg_sub.desc(), Book.title)
    else:
        query = query.order_by(Book.title)

    per_page = current_app.config["BOOKS_PER_PAGE"]
    pagination = query.paginate(page=page, per_page=per_page, error_out=False)
    books = pagination.items

    # Compute average ratings for displayed books
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

    # Get all genres for the filter dropdown
    genres = sorted(
        row[0] for row in db.session.query(Book.genre).distinct().all() if row[0]
    )

    return render_template(
        "books.html",
        books=books,
        pagination=pagination,
        genres=genres,
        avg_ratings=avg_ratings,
        current_genre=genre_filter,
        current_sort=sort_by,
        current_search=search,
    )


@books_bp.route("/books/add", methods=["GET", "POST"])
@login_required
def add_book():
    if request.method == "POST":
        book, errors = _book_from_form()
        if errors:
            return render_template("add_book.html", errors=errors, form=request.form)

        db.session.add(book)
        db.session.commit()
        flash(f"Added \"{book.title}\" to BookHive!", "success")
        return redirect(url_for("books.book_detail", id=book.id))

    return render_template("add_book.html", errors={}, form={})


@books_bp.route("/books/<int:id>")
def book_detail(id):
    book = db.session.get(Book, id)
    if book is None:
        flash("Book not found.", "error")
        return redirect(url_for("books.list_books"))

    reviews = (
        Review.query.filter_by(book_id=book.id)
        .order_by(Review.created_at.desc())
        .all()
    )

    # Check if current user already reviewed this book
    user_review = None
    if current_user.is_authenticated:
        user_review = Review.query.filter_by(
            user_id=current_user.id, book_id=book.id
        ).first()

    # Check current user's shelf for this book
    user_shelf = None
    if current_user.is_authenticated:
        from models import UserBookShelf
        shelf_entry = UserBookShelf.query.filter_by(
            user_id=current_user.id, book_id=book.id
        ).first()
        if shelf_entry:
            user_shelf = shelf_entry.shelf

    return render_template(
        "book_detail.html",
        book=book,
        reviews=reviews,
        user_review=user_review,
        user_shelf=user_shelf,
    )


@books_bp.route("/books/<int:id>/edit", methods=["GET", "POST"])
@login_required
def edit_book(id):
    if not current_user.is_admin:
        flash("You do not have permission to edit books.", "error")
        return redirect(url_for("books.book_detail", id=id))

    book = db.session.get(Book, id)
    if book is None:
        flash("Book not found.", "error")
        return redirect(url_for("books.list_books"))

    if request.method == "POST":
        updated, errors = _book_from_form(book=book)
        if errors:
            return render_template(
                "edit_book.html", book=book, errors=errors, form=request.form
            )

        db.session.commit()
        flash(f"Updated \"{book.title}\".", "success")
        return redirect(url_for("books.book_detail", id=book.id))

    return render_template("edit_book.html", book=book, errors={}, form={})


@books_bp.route("/books/<int:id>/delete", methods=["POST"])
@login_required
def delete_book(id):
    if not current_user.is_admin:
        flash("You do not have permission to delete books.", "error")
        return redirect(url_for("books.book_detail", id=id))

    book = db.session.get(Book, id)
    if book is None:
        flash("Book not found.", "error")
        return redirect(url_for("books.list_books"))

    title = book.title
    db.session.delete(book)
    db.session.commit()
    flash(f"Deleted \"{title}\" and all associated data.", "success")
    return redirect(url_for("books.list_books"))
