from datetime import datetime, timezone

from flask import Blueprint, redirect, url_for, flash
from flask_login import login_required, current_user

from models import db, Follow, User

follows_bp = Blueprint("follows", __name__)


@follows_bp.route("/follow/<int:user_id>", methods=["POST"])
@login_required
def toggle_follow(user_id):
    user_to_follow = db.session.get(User, user_id)
    if user_to_follow is None:
        flash("User not found.", "error")
        return redirect(url_for("home.index"))

    if user_to_follow.id == current_user.id:
        flash("You cannot follow yourself.", "error")
        return redirect(url_for("shelves.profile", user_id=user_id))

    existing = Follow.query.filter_by(
        follower_id=current_user.id, followed_id=user_id
    ).first()

    if existing:
        db.session.delete(existing)
        db.session.commit()
        flash(f"You unfollowed {user_to_follow.username}.", "info")
    else:
        follow = Follow(
            follower_id=current_user.id,
            followed_id=user_id,
            created_at=datetime.now(timezone.utc),
        )
        db.session.add(follow)
        db.session.commit()
        flash(f"You are now following {user_to_follow.username}!", "success")

    return redirect(url_for("shelves.profile", user_id=user_id))
