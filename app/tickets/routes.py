from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from ..extensions import db
from ..models import Comment, Notification, Ticket, User
from ..sla import is_sla_overdue, sla_summaries

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
        "overdue": sum(is_sla_overdue(ticket) for ticket in tickets),
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


def _can_view_ticket(ticket, user):
    if user.role == "admin":
        return True
    if ticket.creator_id == user.id:
        return True
    if user.role == "tecnico":
        return ticket.assignee_id in (None, user.id)
    return False


def _can_edit_ticket(ticket, user):
    return user.role == "admin" or ticket.creator_id == user.id


def _can_comment_ticket(ticket, user):
    return _can_view_ticket(ticket, user)


def _visible_tickets_for(user):
    tickets = Ticket.query.order_by(Ticket.updated_at.desc(), Ticket.created_at.desc()).all()
    return [ticket for ticket in tickets if _can_view_ticket(ticket, user)]


def _list_filter_options(tickets):
    creators = sorted(
        {
            ticket.creator
            for ticket in tickets
            if ticket.creator is not None
        },
        key=lambda user: user.name.lower(),
    )
    assignees = sorted(
        {
            ticket.assignee
            for ticket in tickets
            if ticket.assignee is not None
        },
        key=lambda user: user.name.lower(),
    )
    return {
        "creators": creators,
        "assignees": assignees,
    }


def _list_filters_from_request():
    return {
        "q": request.args.get("q", "").strip(),
        "status": request.args.get("status", "").strip(),
        "priority": request.args.get("priority", "").strip(),
        "creator_id": request.args.get("creator_id", "").strip(),
        "assignee_id": request.args.get("assignee_id", "").strip(),
        "unassigned": request.args.get("unassigned", "").strip(),
    }


def _matches_int_filter(raw_value, value):
    if not raw_value:
        return True
    try:
        return int(raw_value) == value
    except ValueError:
        return False


def _filter_tickets(tickets, filters):
    filtered = tickets

    if filters["q"]:
        query = filters["q"].lower()
        filtered = [
            ticket
            for ticket in filtered
            if query in ticket.title.lower()
            or query in ticket.description.lower()
        ]

    if filters["status"] in STATUS_META:
        filtered = [ticket for ticket in filtered if ticket.status == filters["status"]]

    if filters["priority"] in PRIORITY_META:
        filtered = [ticket for ticket in filtered if ticket.priority == filters["priority"]]

    if filters["creator_id"]:
        filtered = [
            ticket
            for ticket in filtered
            if _matches_int_filter(filters["creator_id"], ticket.creator_id)
        ]

    if filters["assignee_id"]:
        filtered = [
            ticket
            for ticket in filtered
            if ticket.assignee_id is not None
            and _matches_int_filter(filters["assignee_id"], ticket.assignee_id)
        ]

    if filters["unassigned"] == "1":
        filtered = [ticket for ticket in filtered if ticket.assignee_id is None]

    return filtered


def _get_visible_ticket_or_404(ticket_id):
    ticket = db.session.get(Ticket, ticket_id)
    if ticket is None:
        abort(404)
    if not _can_view_ticket(ticket, current_user):
        abort(403)
    return ticket


def _add_ticket_history(ticket, body, author=None):
    db.session.add(
        Comment(
            body=body,
            ticket=ticket,
            author=author or current_user,
        )
    )


def _notification_recipients(ticket, *extra_users):
    recipients = []
    for user in (ticket.creator, ticket.assignee, *extra_users):
        if user is None or user.id == current_user.id:
            continue
        if user.id not in {recipient.id for recipient in recipients}:
            recipients.append(user)
    return recipients


def _notify_ticket_users(ticket, notification_type, title, body, users=None):
    recipients = users if users is not None else _notification_recipients(ticket)
    for user in recipients:
        db.session.add(
            Notification(
                type=notification_type,
                title=title,
                body=body,
                ticket=ticket,
                user=user,
                actor=current_user,
            )
        )


@tickets_bp.route("/")
@login_required
def list_tickets():
    visible_tickets = _visible_tickets_for(current_user)
    filters = _list_filters_from_request()
    tickets = _filter_tickets(visible_tickets, filters)
    return render_template(
        "tickets/list.html",
        tickets=tickets,
        stats=_ticket_stats(tickets),
        filters=filters,
        filter_options=_list_filter_options(visible_tickets),
        sla_by_ticket=sla_summaries(tickets),
        status_meta=STATUS_META,
        priority_meta=PRIORITY_META,
    )


@tickets_bp.route("/<int:ticket_id>/status", methods=["POST"])
@login_required
def update_ticket_status(ticket_id):
    ticket = _get_visible_ticket_or_404(ticket_id)

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
    _notify_ticket_users(
        ticket,
        "status",
        f"Ticket #{ticket.id} cambio de estado",
        f"{current_user.name} cambio el estado de {previous_status} a {next_status}.",
    )
    db.session.commit()

    flash(f"Ticket marcado como {STATUS_META[status]['label'].lower()}.", "success")
    return redirect(url_for("tickets.ticket_detail", ticket_id=ticket.id))


@tickets_bp.route("/<int:ticket_id>/assign", methods=["POST"])
@login_required
def assign_ticket(ticket_id):
    ticket = _get_visible_ticket_or_404(ticket_id)

    if current_user.role != "admin":
        flash("Solo un administrador puede asignar responsables.", "danger")
        return redirect(url_for("tickets.ticket_detail", ticket_id=ticket.id))

    assignee_id = request.form.get("assignee_id", "").strip()
    previous_assignee = ticket.assignee.name if ticket.assignee else "Sin asignar"
    previous_assignee_user = ticket.assignee
    if not assignee_id:
        ticket.assignee = None
        _add_ticket_history(
            ticket,
            f"Responsable actualizado: {previous_assignee} -> Sin asignar.",
        )
        _notify_ticket_users(
            ticket,
            "assignment",
            f"Ticket #{ticket.id} quedo sin responsable",
            f"{current_user.name} dejo el ticket sin tecnico asignado.",
            users=_notification_recipients(ticket, previous_assignee_user),
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
    _notify_ticket_users(
        ticket,
        "assignment",
        f"Ticket #{ticket.id} asignado a {assignee.name}",
        f"{current_user.name} asigno el ticket a {assignee.name}.",
        users=_notification_recipients(ticket, previous_assignee_user, assignee),
    )
    db.session.commit()

    flash(f"Ticket asignado a {assignee.name}.", "success")
    return redirect(url_for("tickets.ticket_detail", ticket_id=ticket.id))


@tickets_bp.route("/<int:ticket_id>/comments", methods=["POST"])
@login_required
def add_comment(ticket_id):
    ticket = _get_visible_ticket_or_404(ticket_id)

    body = request.form.get("body", "").strip()
    if not body:
        flash("Escribe un comentario antes de guardarlo.", "danger")
        return redirect(url_for("tickets.ticket_detail", ticket_id=ticket.id))

    comment = Comment(body=body, ticket=ticket, author=current_user)
    db.session.add(comment)
    _notify_ticket_users(
        ticket,
        "comment",
        f"Nuevo comentario en ticket #{ticket.id}",
        f"{current_user.name} agrego un comentario: {body[:120]}",
    )
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
    ticket = _get_visible_ticket_or_404(ticket_id)
    if not _can_edit_ticket(ticket, current_user):
        abort(403)

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
    ticket = _get_visible_ticket_or_404(ticket_id)

    comments = sorted(ticket.comments, key=lambda comment: comment.created_at)
    return render_template(
        "tickets/detail.html",
        ticket=ticket,
        comments=comments,
        status_meta=STATUS_META,
        status_actions=_status_actions(ticket, current_user),
        technicians=_available_technicians() if current_user.role == "admin" else [],
        can_edit_ticket=_can_edit_ticket(ticket, current_user),
        sla=sla_summaries([ticket])[ticket.id],
        priority_meta=PRIORITY_META,
    )
