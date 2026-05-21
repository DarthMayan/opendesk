from flask import Blueprint, abort, render_template
from flask_login import login_required

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
