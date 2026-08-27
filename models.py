from datetime import datetime, timezone

from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin

db = SQLAlchemy()


class User(UserMixin, db.Model):
    __tablename__ = "user"

    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(80), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    is_admin = db.Column(db.Boolean, default=False, nullable=False)

    reviews = db.relationship("Review", back_populates="user", lazy="dynamic",
                              cascade="all, delete-orphan")
    shelves = db.relationship("UserBookShelf", back_populates="user", lazy="dynamic",
                              cascade="all, delete-orphan")
    # users this user follows
    following_rel = db.relationship(
        "Follow", foreign_keys="Follow.follower_id",
        back_populates="follower", lazy="dynamic",
        cascade="all, delete-orphan"
    )
    # users who follow this user
    followers_rel = db.relationship(
        "Follow", foreign_keys="Follow.followed_id",
        back_populates="followed", lazy="dynamic",
        cascade="all, delete-orphan"
    )

    def __repr__(self):
        return f"<User {self.username}>"


class Book(db.Model):
    __tablename__ = "book"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    author = db.Column(db.String(200), nullable=False)
    cover_url = db.Column(db.String(500), default="")
    genre = db.Column(db.String(100), default="")
    publication_year = db.Column(db.Integer, nullable=True)
    description = db.Column(db.Text, default="")

    reviews = db.relationship("Review", back_populates="book", lazy="dynamic",
                              cascade="all, delete-orphan")
    shelved_by = db.relationship("UserBookShelf", back_populates="book", lazy="dynamic",
                                 cascade="all, delete-orphan")

    def average_rating(self):
        result = db.session.query(
            db.func.avg(Review.rating)
        ).filter(Review.book_id == self.id).scalar()
        return round(result, 2) if result else None

    def rating_count(self):
        return db.session.query(
            db.func.count(Review.id)
        ).filter(Review.book_id == self.id).scalar() or 0

    def __repr__(self):
        return f"<Book {self.title}>"


class Review(db.Model):
    __tablename__ = "review"
    __table_args__ = (
        db.UniqueConstraint("user_id", "book_id", name="uq_user_book_review"),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey("book.id"), nullable=False)
    rating = db.Column(db.Integer, nullable=False)
    text = db.Column(db.Text, default="")
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           nullable=False)
    updated_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           onupdate=lambda: datetime.now(timezone.utc), nullable=True)

    user = db.relationship("User", back_populates="reviews")
    book = db.relationship("Book", back_populates="reviews")

    def __repr__(self):
        return f"<Review user={self.user_id} book={self.book_id} rating={self.rating}>"


class UserBookShelf(db.Model):
    __tablename__ = "user_book_shelf"
    __table_args__ = (
        db.UniqueConstraint("user_id", "book_id", name="uq_user_book_shelf"),
    )

    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey("user.id"), nullable=False)
    book_id = db.Column(db.Integer, db.ForeignKey("book.id"), nullable=False)
    shelf = db.Column(db.String(20), nullable=False)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           nullable=False)

    user = db.relationship("User", back_populates="shelves")
    book = db.relationship("Book", back_populates="shelved_by")

    def __repr__(self):
        return f"<UserBookShelf user={self.user_id} book={self.book_id} shelf={self.shelf}>"


class Follow(db.Model):
    __tablename__ = "follow"

    follower_id = db.Column(db.Integer, db.ForeignKey("user.id"), primary_key=True)
    followed_id = db.Column(db.Integer, db.ForeignKey("user.id"), primary_key=True)
    created_at = db.Column(db.DateTime, default=lambda: datetime.now(timezone.utc),
                           nullable=False)

    follower = db.relationship(
        "User", foreign_keys=[follower_id], back_populates="following_rel"
    )
    followed = db.relationship(
        "User", foreign_keys=[followed_id], back_populates="followers_rel"
    )

    def __repr__(self):
        return f"<Follow {self.follower_id} -> {self.followed_id}>"
