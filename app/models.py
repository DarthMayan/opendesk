from datetime import datetime, timezone

from flask_login import UserMixin
from werkzeug.security import check_password_hash, generate_password_hash

from .extensions import db, login_manager


def _utcnow():
    """Devuelve la fecha y hora actual con zona horaria UTC."""
    return datetime.now(timezone.utc)


class User(UserMixin, db.Model):
    """Representa una cuenta de usuario autenticable en OpenDesk.

    El modelo almacena credenciales, rol de acceso y datos basicos de perfil.
    Hereda de ``UserMixin`` para integrarse con Flask-Login.
    """

    __tablename__ = "users"

    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(120), unique=True, nullable=False)
    name = db.Column(db.String(120), nullable=False)
    password_hash = db.Column(db.String(255), nullable=False)
    # Roles: 'usuario' | 'tecnico' | 'admin'
    role = db.Column(db.String(20), nullable=False, default="usuario")
    avatar_filename = db.Column(db.String(255), nullable=True)
    created_at = db.Column(db.DateTime, default=_utcnow)

    def set_password(self, password):
        """Genera y guarda el hash seguro de una contrasena."""
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        """Valida una contrasena en texto plano contra el hash guardado."""
        return check_password_hash(self.password_hash, password)


class Ticket(db.Model):
    """Representa una solicitud de soporte registrada en el sistema.

    Un ticket tiene solicitante, responsable opcional, estado, prioridad y
    fechas para seguimiento operativo y calculo de SLA.
    """

    __tablename__ = "tickets"

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(200), nullable=False)
    description = db.Column(db.Text, nullable=False)
    # Estados: 'abierto' | 'en_proceso' | 'resuelto' | 'cerrado'
    status = db.Column(db.String(20), nullable=False, default="abierto")
    # Prioridad: 'baja' | 'media' | 'alta'
    priority = db.Column(db.String(20), nullable=False, default="media")
    created_at = db.Column(db.DateTime, default=_utcnow)
    updated_at = db.Column(db.DateTime, default=_utcnow, onupdate=_utcnow)

    creator_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    assignee_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)

    creator = db.relationship("User", foreign_keys=[creator_id])
    assignee = db.relationship("User", foreign_keys=[assignee_id])


class Comment(db.Model):
    """Guarda comentarios e historial asociados a un ticket.

    El mismo modelo se usa para comentarios escritos por usuarios y para eventos
    internos como cambios de estado o asignacion de responsables.
    """

    __tablename__ = "comments"

    id = db.Column(db.Integer, primary_key=True)
    body = db.Column(db.Text, nullable=False)
    created_at = db.Column(db.DateTime, default=_utcnow)

    ticket_id = db.Column(db.Integer, db.ForeignKey("tickets.id"), nullable=False)
    author_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)

    ticket = db.relationship("Ticket", backref=db.backref("comments", lazy=True))
    author = db.relationship("User")


class Notification(db.Model):
    """Representa una notificacion interna relacionada con un ticket.

    Las notificaciones avisan a usuarios sobre eventos como asignaciones,
    comentarios o cambios de estado. ``read_at`` indica si ya fueron leidas.
    """

    __tablename__ = "notifications"

    id = db.Column(db.Integer, primary_key=True)
    type = db.Column(db.String(40), nullable=False)
    title = db.Column(db.String(160), nullable=False)
    body = db.Column(db.Text, nullable=False)
    read_at = db.Column(db.DateTime, nullable=True)
    created_at = db.Column(db.DateTime, default=_utcnow)

    user_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=False)
    ticket_id = db.Column(db.Integer, db.ForeignKey("tickets.id"), nullable=False)
    actor_id = db.Column(db.Integer, db.ForeignKey("users.id"), nullable=True)

    user = db.relationship("User", foreign_keys=[user_id])
    ticket = db.relationship("Ticket")
    actor = db.relationship("User", foreign_keys=[actor_id])

    @property
    def is_read(self):
        """Indica si la notificacion ya fue marcada como leida."""
        return self.read_at is not None


@login_manager.user_loader
def load_user(user_id):
    """Carga un usuario por ID para restaurar la sesion de Flask-Login."""
    return db.session.get(User, int(user_id))
