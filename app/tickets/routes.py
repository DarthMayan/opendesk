from flask import Blueprint, abort, flash, redirect, render_template, request, url_for
from flask_login import current_user, login_required

from ..extensions import db
from ..models import Ticket

tickets_bp = Blueprint("tickets", __name__, url_prefix="/tickets")

STATUS_META = {
    "abierto": {"label": "Abierto", "class": "text-bg-primary"},
    "en_proceso": {"label": "En proceso", "class": "text-bg-warning"},
    "resuelto": {"label": "Resuelto", "class": "text-bg-success"},
    "cerrado": {"label": "Cerrado", "class": "text-bg-secondary"},
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
    }


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

        ticket.title = form_data["title"]
        ticket.description = form_data["description"]
        ticket.priority = form_data["priority"]
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
        priority_meta=PRIORITY_META,
    )
