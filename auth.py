from flask import flash, redirect, render_template, request, url_for
from flask_login import current_user, login_user, logout_user
from werkzeug.security import check_password_hash

from app import app
from extensions import login_manager
from models import User


@login_manager.user_loader
def load_user(user_id):
    return db_session_get_user(user_id)


def db_session_get_user(user_id):
    try:
        return User.query.get(int(user_id))
    except (TypeError, ValueError):
        return None


@app.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("index"))

    if request.method == "POST":
        login_value = request.form.get("login", "").strip()
        password = request.form.get("password", "")
        remember = request.form.get("remember") == "on"

        user = User.query.filter_by(login=login_value).first()

        if user and check_password_hash(user.password_hash, password):
            login_user(user, remember=remember)
            next_page = request.args.get("next")
            return redirect(next_page or url_for("index"))

        flash("Невозможно аутентифицироваться с указанными логином и паролем")

    return render_template("login.html")


@app.route("/logout")
def logout():
    logout_user()
    return redirect(request.referrer or url_for("index"))
