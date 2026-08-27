import os
from flask import Flask
from config import Config
from models import db
from flask_login import LoginManager
from flask_wtf.csrf import CSRFProtect


def create_app():
    app = Flask(__name__)
    app.config.from_object(Config)

    db.init_app(app)
    csrf = CSRFProtect(app)

    login_manager = LoginManager()
    login_manager.login_view = "auth.login"
    login_manager.login_message_category = "info"
    login_manager.init_app(app)

    from models import User

    @login_manager.user_loader
    def load_user(user_id):
        return db.session.get(User, int(user_id))

    # Register blueprints
    from auth import auth_bp
    app.register_blueprint(auth_bp)

    from books import books_bp
    app.register_blueprint(books_bp)

    from reviews import reviews_bp
    app.register_blueprint(reviews_bp)

    from shelves import shelves_bp
    app.register_blueprint(shelves_bp)

    from follows import follows_bp
    app.register_blueprint(follows_bp)

    from feed import feed_bp
    app.register_blueprint(feed_bp)

    from home import home_bp
    app.register_blueprint(home_bp)

    from api import api_bp
    app.register_blueprint(api_bp, url_prefix="/api")

    from seed import seed_bp
    app.register_blueprint(seed_bp)

    # Create tables on first request if they don't exist
    with app.app_context():
        db.create_all()

    return app


if __name__ == "__main__":
    app = create_app()
    debug_mode = os.environ.get("FLASK_DEBUG", "0") == "1"
    app.run(host="0.0.0.0", port=5000, debug=debug_mode)
