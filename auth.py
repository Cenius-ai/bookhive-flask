from flask import Blueprint, render_template, redirect, url_for, flash, request
from flask_login import login_user, logout_user, login_required, current_user
from werkzeug.security import generate_password_hash, check_password_hash

from models import db, User

auth_bp = Blueprint("auth", __name__)


def _safe_next_or_default(default_endpoint="home.index"):
    """Validate the ``next`` query parameter and return a safe redirect
    target. Only relative paths (starting with ``/``) are permitted —
    absolute URLs and protocol-relative URLs are rejected to prevent
    open-redirect attacks. Falls back to ``default_endpoint`` when the
    parameter is missing or unsafe."""
    next_page = request.args.get("next")
    if next_page and next_page.startswith("/") and not next_page.startswith("//"):
        return next_page
    return url_for(default_endpoint)


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("home.index"))

    if request.method == "POST":
        username = (request.form.get("username") or "").strip()
        email = (request.form.get("email") or "").strip()
        password = request.form.get("password") or ""
        confirm = request.form.get("confirm_password") or ""

        errors = {}
        if not username or len(username) < 2:
            errors["username"] = "Username must be at least 2 characters."
        elif User.query.filter_by(username=username).first():
            errors["username"] = "That username is already taken."

        if not email or "@" not in email:
            errors["email"] = "Please enter a valid email address."
        elif User.query.filter_by(email=email).first():
            errors["email"] = "An account with that email already exists."

        if not password or len(password) < 6:
            errors["password"] = "Password must be at least 6 characters."
        elif password != confirm:
            errors["confirm_password"] = "Passwords do not match."

        if errors:
            return render_template(
                "register.html",
                errors=errors,
                username=username,
                email=email,
            )

        user = User(
            username=username,
            email=email,
            password_hash=generate_password_hash(password),
        )
        db.session.add(user)
        db.session.commit()

        flash("Account created! Please log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("register.html", errors={}, username="", email="")


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("home.index"))

    if request.method == "POST":
        email = (request.form.get("email") or "").strip()
        password = request.form.get("password") or ""

        user = User.query.filter_by(email=email).first()
        if user and check_password_hash(user.password_hash, password):
            login_user(user, remember=True)
            flash(f"Welcome back, {user.username}!", "success")
            return redirect(_safe_next_or_default())

        flash("Invalid email or password.", "error")
        return render_template("login.html", email=email)

    return render_template("login.html", email="")


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("You have been logged out.", "info")
    return redirect(url_for("auth.login"))
