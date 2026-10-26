from functools import wraps
from flask import session, redirect, url_for, flash
from flask import Blueprint, render_template, request, redirect, url_for, flash, session
from models import Admin
from extensions import db

auth_bp = Blueprint("auth", __name__)


def login_required(view):
    @wraps(view)
    def wrapped_view(*args, **kwargs):
        if "admin_id" not in session:
            flash("Please log in to access this page.", "warning")
            return redirect(url_for("auth.login"))

        return view(*args, **kwargs)

    return wrapped_view




@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    # Allow initial setup only when no administrator exists.
    if Admin.query.first() is not None:
        flash("Registration is disabled. Please log in.", "warning")
        return redirect(url_for("auth.login"))

    if request.method == "POST":
        username = request.form.get("username", "").strip()
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        if not username or not email or not password:
            flash("All fields are required.", "danger")
            return render_template("register.html")

        if len(password) < 12:
            flash("Password must be at least 12 characters.", "danger")
            return render_template("register.html")

        admin = Admin(username=username, email=email)
        admin.set_password(password)

        db.session.add(admin)
        db.session.commit()

        flash("Registration successful. Please log in.", "success")
        return redirect(url_for("auth.login"))

    return render_template("register.html")

@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        admin = Admin.query.filter_by(email=email).first()

        if admin and admin.check_password(password):
            session.clear()
            session["admin_id"] = admin.id
            return redirect(url_for("home"))

        flash("Invalid email or password.", "danger")

    return render_template("login.html")


@auth_bp.route("/logout", methods=["POST"])
def logout():
    session.clear()
    return redirect(url_for("auth.login"))
