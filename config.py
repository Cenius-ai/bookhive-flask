import os
import secrets

basedir = os.path.abspath(os.path.dirname(__file__))


class Config:
    SECRET_KEY = os.environ.get("SECRET_KEY") or secrets.token_hex(32)
    SQLALCHEMY_DATABASE_URI = os.environ.get(
        "DATABASE_URL", "sqlite:///" + os.path.join(basedir, "bookhive.db")
    )
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    BOOKS_PER_PAGE = 8
    FEED_ITEMS_PER_PAGE = 15
    WTF_CSRF_ENABLED = True
