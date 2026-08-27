"""Seed the database with demo content.

Creates an admin user, 12 books across genres, several demo users, reviews,
shelf entries, and follows. Safe to run multiple times (idempotent check via
admin email).

Access is gated: requires either the BOOKHIVE_ALLOW_SEED environment variable
set to "true", or an authenticated admin user. On first run (no users at all)
the env-var gate is the only way in — set BOOKHIVE_ALLOW_SEED=true, visit
/seed, then unset it.

The ``run_seed()`` function is also importable for use in install.sh scripts.
"""

import os
from werkzeug.security import generate_password_hash
from datetime import datetime, timezone, timedelta

from flask import Blueprint, abort
from flask_login import current_user
from models import db, User, Book, Review, UserBookShelf, Follow

seed_bp = Blueprint("seed", __name__, url_prefix="/seed")

DEMO_BOOKS = [
    {
        "title": "The Midnight Library",
        "author": "Matt Haig",
        "cover_url": "https://covers.openlibrary.org/b/id/10547292-L.jpg",
        "genre": "Fiction",
        "publication_year": 2020,
        "description": (
            "Between life and death there is a library, and within that library, "
            "the shelves go on forever. Every book provides a chance to try another "
            "life you could have lived. Nora Seed finds herself in the Midnight Library, "
            "where she must search within herself to decide what is truly fulfilling."
        ),
    },
    {
        "title": "Project Hail Mary",
        "author": "Andy Weir",
        "cover_url": "https://covers.openlibrary.org/b/id/11891581-L.jpg",
        "genre": "Science Fiction",
        "publication_year": 2021,
        "description": (
            "Ryland Grace is the sole survivor on a desperate, last-chance mission — "
            "and if he fails, humanity and the Earth itself will perish. Except he "
            "doesn't know that. He can't even remember his own name, let alone the "
            "nature of his assignment."
        ),
    },
    {
        "title": "Klara and the Sun",
        "author": "Kazuo Ishiguro",
        "cover_url": "https://covers.openlibrary.org/b/id/11542675-L.jpg",
        "genre": "Fiction",
        "publication_year": 2021,
        "description": (
            "Klara is an Artificial Friend with outstanding observational qualities, "
            "who from her place in the store watches the behavior of those who come in "
            "to browse. She remains hopeful that a customer will soon choose her."
        ),
    },
    {
        "title": "Dune",
        "author": "Frank Herbert",
        "cover_url": "https://covers.openlibrary.org/b/id/11153217-L.jpg",
        "genre": "Science Fiction",
        "publication_year": 1965,
        "description": (
            "Set on the desert planet Arrakis, Dune is the story of the boy Paul "
            "Atreides, heir to a noble family tasked with ruling an inhospitable world "
            "where the only thing of value is the spice melange — a substance that "
            "extends life and expands consciousness."
        ),
    },
    {
        "title": "The Song of Achilles",
        "author": "Madeline Miller",
        "cover_url": "https://covers.openlibrary.org/b/id/8573788-L.jpg",
        "genre": "Historical Fiction",
        "publication_year": 2012,
        "description": (
            "A tale of gods, kings, immortal fame, and the human heart. Greece in the "
            "age of heroes: Patroclus, an awkward young prince, is exiled to the court "
            "of King Peleus and his perfect son Achilles. Despite their differences, "
            "the boys become steadfast companions."
        ),
    },
    {
        "title": "Atomic Habits",
        "author": "James Clear",
        "cover_url": "https://covers.openlibrary.org/b/id/10561280-L.jpg",
        "genre": "Non-Fiction",
        "publication_year": 2018,
        "description": (
            "No matter your goals, Atomic Habits offers a proven framework for "
            "improving — every day. James Clear reveals practical strategies that "
            "teach you exactly how to form good habits, break bad ones, and master "
            "the tiny behaviors that lead to remarkable results."
        ),
    },
    {
        "title": "Circe",
        "author": "Madeline Miller",
        "cover_url": "https://covers.openlibrary.org/b/id/10559974-L.jpg",
        "genre": "Historical Fiction",
        "publication_year": 2018,
        "description": (
            "In the house of Helios, god of the sun and mightiest of the Titans, a "
            "daughter is born. But Circe is a strange child — not powerful like her "
            "father, nor viciously alluring like her mother. Turning to the world of "
            "mortals for companionship, she discovers she does possess power."
        ),
    },
    {
        "title": "The Thursday Murder Club",
        "author": "Richard Osman",
        "cover_url": "https://covers.openlibrary.org/b/id/10698257-L.jpg",
        "genre": "Mystery",
        "publication_year": 2020,
        "description": (
            "In a peaceful retirement village, four unlikely friends meet weekly to "
            "discuss unsolved crimes. When a local developer is found dead, the "
            "Thursday Murder Club finds themselves in the middle of their first "
            "live case."
        ),
    },
    {
        "title": "Educated",
        "author": "Tara Westover",
        "cover_url": "https://covers.openlibrary.org/b/id/8758895-L.jpg",
        "genre": "Non-Fiction",
        "publication_year": 2018,
        "description": (
            "Born to survivalists in the mountains of Idaho, Tara Westover was "
            "seventeen the first time she set foot in a classroom. Her family was so "
            "isolated from mainstream society that there was no one to ensure the "
            "children received an education."
        ),
    },
    {
        "title": "The Name of the Wind",
        "author": "Patrick Rothfuss",
        "cover_url": "https://covers.openlibrary.org/b/id/8260346-L.jpg",
        "genre": "Fantasy",
        "publication_year": 2007,
        "description": (
            "Told in Kvothe's own voice, this is the tale of the magically gifted "
            "young man who grows to be the most notorious wizard his world has ever "
            "seen — from his childhood in a troupe of traveling players, to years "
            "spent as a near-feral orphan, to his daringly brazen yet successful "
            "bid to enter a legendary school of magic."
        ),
    },
    {
        "title": "Piranesi",
        "author": "Susanna Clarke",
        "cover_url": "https://covers.openlibrary.org/b/id/10482965-L.jpg",
        "genre": "Fantasy",
        "publication_year": 2020,
        "description": (
            "Piranesi's house is no ordinary building: its rooms are infinite, its "
            "corridors endless, its walls are lined with thousands upon thousands of "
            "statues. Within the labyrinth of halls an ocean is imprisoned; waves "
            "thunder up staircases, rooms are flooded in an instant."
        ),
    },
    {
        "title": "Gone Girl",
        "author": "Gillian Flynn",
        "cover_url": "https://covers.openlibrary.org/b/id/8225672-L.jpg",
        "genre": "Mystery",
        "publication_year": 2012,
        "description": (
            "On a warm summer morning in North Carthage, Missouri, it is Nick and "
            "Amy Dunne's fifth wedding anniversary. When Amy suddenly vanishes, the "
            "police suspect Nick. Under mounting pressure from the police and the "
            "media, Nick's portrait of a blissful union begins to crumble."
        ),
    },
]

DEMO_REVIEWS = [
    # (book_index, username, rating, text)
    (0, "literarylara", 5, "Beautifully written. Made me think about every choice I've ever made."),
    (0, "scifi_sam", 4, "An inventive concept with genuine emotional depth."),
    (1, "scifi_sam", 5, "Andy Weir does it again. Pure joy from start to finish."),
    (1, "admin", 5, "One of the best sci-fi novels of the decade."),
    (2, "literarylara", 4, "Quiet, thoughtful, and devastatingly relevant."),
    (3, "scifi_sam", 5, "The greatest sci-fi novel ever written. Fight me."),
    (3, "bookworm_ben", 5, "A masterpiece of world-building and political intrigue."),
    (4, "literarylara", 5, "I cried. Multiple times. Miller's prose is breathtaking."),
    (5, "bookworm_ben", 4, "Practical and actionable. I've already changed several habits."),
    (6, "literarylara", 5, "Every bit as good as The Song of Achilles."),
    (7, "bookworm_ben", 4, "Charming, clever, and genuinely funny."),
    (8, "admin", 5, "A staggering memoir. Essential reading."),
    (9, "scifi_sam", 5, "Rothfuss writes like a dream. When is book three?"),
    (10, "literarylara", 4, "Strange, beautiful, and utterly original."),
    (11, "bookworm_ben", 3, "Gripping but deeply unpleasant. Flynn knows how to twist the knife."),
]

DEMO_SHELVES = [
    # (username, book_index, shelf)
    ("literarylara", 0, "read"),
    ("literarylara", 4, "read"),
    ("literarylara", 6, "reading"),
    ("literarylara", 2, "want_to_read"),
    ("scifi_sam", 1, "read"),
    ("scifi_sam", 3, "read"),
    ("scifi_sam", 9, "reading"),
    ("scifi_sam", 10, "want_to_read"),
    ("bookworm_ben", 5, "read"),
    ("bookworm_ben", 8, "reading"),
    ("bookworm_ben", 7, "want_to_read"),
]

DEMO_FOLLOWS = [
    # (follower_username, followed_username)
    ("admin", "literarylara"),
    ("admin", "scifi_sam"),
    ("admin", "bookworm_ben"),
    ("literarylara", "scifi_sam"),
    ("literarylara", "bookworm_ben"),
    ("scifi_sam", "literarylara"),
    ("bookworm_ben", "admin"),
]


def _seed_allowed():
    """Return True if the current request is authorised to run the seed."""
    if os.environ.get("BOOKHIVE_ALLOW_SEED", "") == "true":
        return True
    if current_user.is_authenticated and getattr(current_user, "is_admin", False):
        return True
    return False


def run_seed():
    """Seed the database with demo content. Idempotent — safe to call
    multiple times. Must be called within a Flask application context."""
    admin = User.query.filter_by(email="admin@bookhive.com").first()
    if admin is not None:
        return False  # already seeded

    # -- Create users --
    admin_pw = generate_password_hash("admin123")
    admin_user = User(
        username="admin",
        email="admin@bookhive.com",
        password_hash=admin_pw,
        is_admin=True,
    )
    db.session.add(admin_user)

    demo_users_data = {
        "literarylara": User(
            username="literarylara",
            email="lara@bookhive.com",
            password_hash=generate_password_hash("password1"),
        ),
        "scifi_sam": User(
            username="scifi_sam",
            email="sam@bookhive.com",
            password_hash=generate_password_hash("password1"),
        ),
        "bookworm_ben": User(
            username="bookworm_ben",
            email="ben@bookhive.com",
            password_hash=generate_password_hash("password1"),
        ),
    }
    for u in demo_users_data.values():
        db.session.add(u)

    db.session.flush()  # get IDs

    # Build a unified lookup for all users (including admin)
    all_users = {"admin": admin_user}
    all_users.update(demo_users_data)

    # -- Create books --
    books = []
    for data in DEMO_BOOKS:
        book = Book(**data)
        db.session.add(book)
        books.append(book)

    db.session.flush()

    # -- Create reviews with staggered timestamps --
    base_time = datetime.now(timezone.utc)
    for i, (book_idx, username, rating, text) in enumerate(DEMO_REVIEWS):
        review = Review(
            user_id=all_users[username].id,
            book_id=books[book_idx].id,
            rating=rating,
            text=text,
            created_at=base_time - timedelta(days=30 - i),
        )
        db.session.add(review)

    # -- Create shelf entries --
    for username, book_idx, shelf in DEMO_SHELVES:
        entry = UserBookShelf(
            user_id=all_users[username].id,
            book_id=books[book_idx].id,
            shelf=shelf,
            created_at=base_time - timedelta(days=25),
        )
        db.session.add(entry)

    # -- Create follows --
    for follower_uname, followed_uname in DEMO_FOLLOWS:
        follow = Follow(
            follower_id=all_users[follower_uname].id,
            followed_id=all_users[followed_uname].id,
        )
        db.session.add(follow)

    db.session.commit()
    return True


@seed_bp.route("")
def seed():
    if not _seed_allowed():
        abort(403)

    if not run_seed():
        return "<p>Database already seeded. <a href='/'>Go home</a>.</p>"

    return "<p>Database seeded! <a href='/'>Go to BookHive</a>.</p>"
