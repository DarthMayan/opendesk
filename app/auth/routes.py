from pathlib import Path
from uuid import uuid4

from flask import Blueprint, current_app, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required, login_user, logout_user
from werkzeug.utils import secure_filename

from ..extensions import db
from ..models import User

auth_bp = Blueprint("auth", __name__)

ROLE_OPTIONS = [
    ("usuario", "Usuario", "Reporta incidencias y consulta el avance de sus solicitudes."),
    ("tecnico", "Tecnico", "Atiende tickets y actualiza el seguimiento operativo."),
    ("admin", "Admin", "Supervisa tickets, prioridades y cambios de estado."),
]

VALID_ROLES = {role for role, _, _ in ROLE_OPTIONS}
ALLOWED_AVATAR_EXTENSIONS = {"gif", "jpeg", "jpg", "png", "webp"}


def _register_context(form_data=None):
    return {
        "form_data": form_data or {
            "name": "",
            "email": "",
            "role": "usuario",
        },
        "role_options": ROLE_OPTIONS,
    }


def _profile_context(form_data=None):
    return {
        "form_data": form_data or {
            "name": current_user.name,
        },
    }


def _avatar_extension(filename):
    if "." not in filename:
        return ""
    return filename.rsplit(".", 1)[1].lower()


def _save_avatar(file_storage):
    if not file_storage or not file_storage.filename:
        return None

    extension = _avatar_extension(file_storage.filename)
    if extension not in ALLOWED_AVATAR_EXTENSIONS:
        flash("Sube una imagen valida: PNG, JPG, GIF o WEBP.", "danger")
        return False

    if file_storage.mimetype and not file_storage.mimetype.startswith("image/"):
        flash("El archivo seleccionado debe ser una imagen.", "danger")
        return False

    upload_folder = Path(current_app.config["PROFILE_AVATAR_UPLOAD_FOLDER"])
    upload_folder.mkdir(parents=True, exist_ok=True)

    original_name = secure_filename(file_storage.filename)
    suffix = Path(original_name).suffix.lower() or f".{extension}"
    filename = f"user-{current_user.id}-{uuid4().hex}{suffix}"
    file_storage.save(upload_folder / filename)

    if current_user.avatar_filename:
        old_avatar = upload_folder / current_user.avatar_filename
        if old_avatar.exists():
            old_avatar.unlink()

    return filename


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


@auth_bp.route("/profile", methods=["GET", "POST"])
@login_required
def profile():
    if request.method == "POST":
        name = request.form.get("name", "").strip()
        current_password = request.form.get("current_password", "")
        new_password = request.form.get("new_password", "")
        confirm_password = request.form.get("confirm_password", "")
        avatar_file = request.files.get("avatar")
        form_data = {
            "name": name,
        }

        if not name:
            flash("Completa el nombre.", "danger")
            return render_template("auth/profile.html", **_profile_context(form_data)), 400

        password_fields = [current_password, new_password, confirm_password]
        if any(password_fields):
            if not all(password_fields):
                flash("Completa todos los campos para cambiar la contrasena.", "danger")
                return render_template("auth/profile.html", **_profile_context(form_data)), 400

            if not current_user.check_password(current_password):
                flash("La contrasena actual no es correcta.", "danger")
                return render_template("auth/profile.html", **_profile_context(form_data)), 400

            if new_password != confirm_password:
                flash("Las contrasenas no coinciden.", "danger")
                return render_template("auth/profile.html", **_profile_context(form_data)), 400

            current_user.set_password(new_password)

        avatar_filename = _save_avatar(avatar_file)
        if avatar_filename is False:
            return render_template("auth/profile.html", **_profile_context(form_data)), 400
        if avatar_filename:
            current_user.avatar_filename = avatar_filename

        current_user.name = name
        db.session.commit()

        flash("Perfil actualizado correctamente.", "success")
        return redirect(url_for("auth.profile"))

    return render_template("auth/profile.html", **_profile_context())


@auth_bp.route("/logout")
@login_required
def logout():
    logout_user()
    flash("Sesion cerrada.", "info")
    return redirect(url_for("main.index"))
