from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from ..extensions import db
from ..models import Comment, Ticket, User

tickets_bp = Blueprint("tickets", __name__, url_prefix="/tickets")

STATUS_META = {
    "abierto": {"label": "Abierto", "class": "text-bg-primary"},
    "en_proceso": {"label": "En proceso", "class": "text-bg-warning"},
    "resuelto": {"label": "Resuelto", "class": "text-bg-success"},
    "cerrado": {"label": "Cerrado", "class": "text-bg-secondary"},
}

STATUS_ACTION_LABELS = {
    "abierto": "Reabrir ticket",
    "en_proceso": "Marcar en proceso",
    "resuelto": "Marcar resuelto",
    "cerrado": "Cerrar ticket",
}

PRIORITY_META = {
    "baja": {"label": "Baja", "class": "text-bg-light"},
    "media": {"label": "Media", "class": "text-bg-info"},
    "alta": {"label": "Alta", "class": "text-bg-danger"},
}

PRIORITY_OPTIONS = [
    ("baja", "Baja", "Solicitud simple o no urgente."),
    ("media", "Media", "Problema que afecta el trabajo normal."),
    ("alta", "Alta", "Incidencia critica que requiere atencion inmediata."),
]


def _ticket_stats(tickets):
    return {
        "total": len(tickets),
        "open": sum(ticket.status == "abierto" for ticket in tickets),
        "in_progress": sum(ticket.status == "en_proceso" for ticket in tickets),
        "high_priority": sum(ticket.priority == "alta" for ticket in tickets),
        "unassigned": sum(ticket.assignee_id is None for ticket in tickets),
    }


def _allowed_statuses(ticket, user):
    if user.role == "admin":
        return [status for status in STATUS_META if status != ticket.status]

    if user.role == "tecnico" and ticket.status != "cerrado":
        return [
            status
            for status in ("en_proceso", "resuelto")
            if status != ticket.status
        ]

    if ticket.creator_id == user.id and ticket.status == "resuelto":
        return ["cerrado"]

    return []


def _status_actions(ticket, user):
    return [
        {
            "key": status,
            "label": STATUS_ACTION_LABELS[status],
            "badge": STATUS_META[status]["label"],
        }
        for status in _allowed_statuses(ticket, user)
    ]


def _available_technicians():
    return User.query.filter_by(role="tecnico").order_by(User.name.asc()).all()


def _add_ticket_history(ticket, body, author=None):
    db.session.add(
        Comment(
            body=body,
            ticket=ticket,
            author=author or current_user,
        )
    )


@tickets_bp.route("/")
@login_required
def list_tickets():
    tickets = Ticket.query.order_by(Ticket.updated_at.desc(), Ticket.created_at.desc()).all()
    return render_template(
        "tickets/list.html",
        tickets=tickets,
        stats=_ticket_stats(tickets),
        status_meta=STATUS_META,
        priority_meta=PRIORITY_META,
    )


@tickets_bp.route("/<int:ticket_id>/status", methods=["POST"])
@login_required
def update_ticket_status(ticket_id):
    ticket = db.session.get(Ticket, ticket_id)
    if ticket is None:
        abort(404)

    status = request.form.get("status", "").strip()
    if status not in STATUS_META:
        flash("Selecciona un estado valido.", "danger")
        return redirect(url_for("tickets.ticket_detail", ticket_id=ticket.id))

    if status not in _allowed_statuses(ticket, current_user):
        flash("No tienes permisos para realizar ese cambio de estado.", "danger")
        return redirect(url_for("tickets.ticket_detail", ticket_id=ticket.id))

    previous_status = STATUS_META[ticket.status]["label"]
    next_status = STATUS_META[status]["label"]
    ticket.status = status
    _add_ticket_history(
        ticket,
        f"Estado actualizado: {previous_status} -> {next_status}.",
    )
    db.session.commit()

    flash(f"Ticket marcado como {STATUS_META[status]['label'].lower()}.", "success")
    return redirect(url_for("tickets.ticket_detail", ticket_id=ticket.id))


@tickets_bp.route("/<int:ticket_id>/assign", methods=["POST"])
@login_required
def assign_ticket(ticket_id):
    ticket = db.session.get(Ticket, ticket_id)
    if ticket is None:
        abort(404)

    if current_user.role != "admin":
        flash("Solo un administrador puede asignar responsables.", "danger")
        return redirect(url_for("tickets.ticket_detail", ticket_id=ticket.id))

    assignee_id = request.form.get("assignee_id", "").strip()
    previous_assignee = ticket.assignee.name if ticket.assignee else "Sin asignar"
    if not assignee_id:
        ticket.assignee = None
        _add_ticket_history(
            ticket,
            f"Responsable actualizado: {previous_assignee} -> Sin asignar.",
        )
        db.session.commit()
        flash("Ticket marcado como sin asignar.", "success")
        return redirect(url_for("tickets.ticket_detail", ticket_id=ticket.id))

    try:
        assignee_id = int(assignee_id)
    except ValueError:
        flash("Selecciona un tecnico valido.", "danger")
        return redirect(url_for("tickets.ticket_detail", ticket_id=ticket.id))

    assignee = db.session.get(User, assignee_id)
    if assignee is None or assignee.role != "tecnico":
        flash("Selecciona un tecnico valido.", "danger")
        return redirect(url_for("tickets.ticket_detail", ticket_id=ticket.id))

    ticket.assignee = assignee
    _add_ticket_history(
        ticket,
        f"Responsable actualizado: {previous_assignee} -> {assignee.name}.",
    )
    db.session.commit()

    flash(f"Ticket asignado a {assignee.name}.", "success")
    return redirect(url_for("tickets.ticket_detail", ticket_id=ticket.id))


@tickets_bp.route("/<int:ticket_id>/comments", methods=["POST"])
@login_required
def add_comment(ticket_id):
    ticket = db.session.get(Ticket, ticket_id)
    if ticket is None:
        abort(404)

    body = request.form.get("body", "").strip()
    if not body:
        flash("Escribe un comentario antes de guardarlo.", "danger")
        return redirect(url_for("tickets.ticket_detail", ticket_id=ticket.id))

    comment = Comment(body=body, ticket=ticket, author=current_user)
    db.session.add(comment)
    db.session.commit()

    flash("Comentario agregado correctamente.", "success")
    return redirect(url_for("tickets.ticket_detail", ticket_id=ticket.id))


@tickets_bp.route("/new", methods=["GET", "POST"])
@login_required
def create_ticket():
    form_data = {
        "title": "",
        "description": "",
        "priority": "media",
    }

    if request.method == "POST":
        form_data = {
            "title": request.form.get("title", "").strip(),
            "description": request.form.get("description", "").strip(),
            "priority": request.form.get("priority", "media").strip(),
        }

        if not form_data["title"] or not form_data["description"]:
            flash("Completa el titulo y la descripcion del ticket.", "danger")
            return render_template(
                "tickets/new.html",
                form_data=form_data,
                priority_options=PRIORITY_OPTIONS,
            ), 400

        if form_data["priority"] not in PRIORITY_META:
            flash("Selecciona una prioridad valida.", "danger")
            return render_template(
                "tickets/new.html",
                form_data=form_data,
                priority_options=PRIORITY_OPTIONS,
            ), 400

        ticket = Ticket(
            title=form_data["title"],
            description=form_data["description"],
            priority=form_data["priority"],
            creator=current_user,
        )
        db.session.add(ticket)
        _add_ticket_history(
            ticket,
            f"Ticket creado con prioridad {PRIORITY_META[ticket.priority]['label']}.",
        )
        db.session.commit()

        flash("Ticket creado correctamente.", "success")
        return redirect(url_for("tickets.ticket_detail", ticket_id=ticket.id))

    return render_template(
        "tickets/new.html",
        form_data=form_data,
        priority_options=PRIORITY_OPTIONS,
    )


@tickets_bp.route("/<int:ticket_id>/edit", methods=["GET", "POST"])
@login_required
def edit_ticket(ticket_id):
    ticket = db.session.get(Ticket, ticket_id)
    if ticket is None:
        abort(404)

    form_data = {
        "title": ticket.title,
        "description": ticket.description,
        "priority": ticket.priority,
    }

    if request.method == "POST":
        form_data = {
            "title": request.form.get("title", "").strip(),
            "description": request.form.get("description", "").strip(),
            "priority": request.form.get("priority", "media").strip(),
        }

        if not form_data["title"] or not form_data["description"]:
            flash("Completa el titulo y la descripcion del ticket.", "danger")
            return render_template(
                "tickets/edit.html",
                ticket=ticket,
                form_data=form_data,
                priority_options=PRIORITY_OPTIONS,
            ), 400

        if form_data["priority"] not in PRIORITY_META:
            flash("Selecciona una prioridad valida.", "danger")
            return render_template(
                "tickets/edit.html",
                ticket=ticket,
                form_data=form_data,
                priority_options=PRIORITY_OPTIONS,
            ), 400

        changes = []
        if ticket.title != form_data["title"]:
            changes.append(f"titulo: {ticket.title} -> {form_data['title']}")
        if ticket.description != form_data["description"]:
            changes.append("descripcion actualizada")
        if ticket.priority != form_data["priority"]:
            changes.append(
                f"prioridad: {PRIORITY_META[ticket.priority]['label']} -> {PRIORITY_META[form_data['priority']]['label']}"
            )

        ticket.title = form_data["title"]
        ticket.description = form_data["description"]
        ticket.priority = form_data["priority"]
        if changes:
            _add_ticket_history(ticket, f"Ticket editado: {'; '.join(changes)}.")
        db.session.commit()

        flash("Ticket actualizado correctamente.", "success")
        return redirect(url_for("tickets.ticket_detail", ticket_id=ticket.id))

    return render_template(
        "tickets/edit.html",
        ticket=ticket,
        form_data=form_data,
        priority_options=PRIORITY_OPTIONS,
    )


@tickets_bp.route("/<int:ticket_id>")
@login_required
def ticket_detail(ticket_id):
    ticket = db.session.get(Ticket, ticket_id)
    if ticket is None:
        abort(404)

    comments = sorted(ticket.comments, key=lambda comment: comment.created_at)
    return render_template(
        "tickets/detail.html",
        ticket=ticket,
        comments=comments,
        status_meta=STATUS_META,
        status_actions=_status_actions(ticket, current_user),
        technicians=_available_technicians() if current_user.role == "admin" else [],
        priority_meta=PRIORITY_META,
    )
