from flask import Blueprint, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user

from ..extensions import db
from ..models import User

auth_bp = Blueprint("auth", __name__)

ROLE_OPTIONS = [
    ("usuario", "Usuario", "Reporta incidencias y consulta el avance de sus solicitudes."),
    ("tecnico", "Tecnico", "Atiende tickets y actualiza el seguimiento operativo."),
    ("admin", "Admin", "Supervisa tickets, prioridades y cambios de estado."),
]

VALID_ROLES = {role for role, _, _ in ROLE_OPTIONS}


def _register_context(form_data=None):
    return {
        "form_data": form_data or {
            "name": "",
            "email": "",
            "role": "usuario",
        },
        "role_options": ROLE_OPTIONS,
    }


@auth_bp.route("/login", methods=["GET", "POST"])
def login():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    if request.method == "POST":
        email = request.form.get("email", "").strip().lower()
        password = request.form.get("password", "")

        user = User.query.filter_by(email=email).first()
        if user is None or not user.check_password(password):
            flash("Correo o contrasena incorrectos.", "danger")
            return render_template("auth/login.html"), 401

        login_user(user)
        flash("Sesion iniciada correctamente.", "success")
        next_page = request.args.get("next")
        return redirect(next_page or url_for("main.index"))

    return render_template("auth/login.html")


@auth_bp.route("/register", methods=["GET", "POST"])
def register():
    if current_user.is_authenticated:
        return redirect(url_for("main.index"))

    if request.method == "POST":
        name = request.form.get("name", "").strip()
        email = request.form.get("email", "").strip().lower()
        role = request.form.get("role", "usuario").strip()
        password = request.form.get("password", "")
        confirm_password = request.form.get("confirm_password", "")
        form_data = {
            "name": name,
            "email": email,
            "role": role if role in VALID_ROLES else "usuario",
        }

        if not name or not email or not password:
            flash("Completa todos los campos obligatorios.", "danger")
            return render_template("auth/register.html", **_register_context(form_data)), 400

        if password != confirm_password:
            flash("Las contrasenas no coinciden.", "danger")
            return render_template("auth/register.html", **_register_context(form_data)), 400

        if role not in VALID_ROLES:
            flash("Selecciona un rol valido.", "danger")
            return render_template("auth/register.html", **_register_context(form_data)), 400

        existing_user = User.query.filter_by(email=email).first()
        if existing_user is not None:
            flash("Ya existe una cuenta con ese correo.", "warning")
            return render_template("auth/register.html", **_register_context(form_data)), 400

        user = User(name=name, email=email, role=role)
        user.set_password(password)
        db.session.add(user)
        db.session.commit()

        login_user(user)
        flash("Cuenta creada correctamente.", "success")
        return redirect(url_for("main.index"))

    return render_template("auth/register.html", **_register_context())


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Sesion cerrada.", "info")
    return redirect(url_for("main.index"))
