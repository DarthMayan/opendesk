from flask import Blueprint, abort, jsonify, render_template
from flask_login import current_user, login_required

from ..models import Comment, Ticket, User
from ..sla import _as_aware_utc, is_sla_overdue, sla_summaries

main_bp = Blueprint("main", __name__)

STATUS_LABELS = {
    "abierto": "Abiertos",
    "en_proceso": "En proceso",
    "resuelto": "Resueltos",
    "cerrado": "Cerrados",
}

PRIORITY_LABELS = {
    "baja": "Baja",
    "media": "Media",
    "alta": "Alta",
}


def _percent(value, total):
    if total == 0:
        return 0
    return round((value / total) * 100)


def _average_resolution_hours(tickets):
    resolved_tickets = [
        ticket
        for ticket in tickets
        if ticket.status in ("resuelto", "cerrado")
    ]
    if not resolved_tickets:
        return None

    total_hours = 0
    for ticket in resolved_tickets:
        created_at = _as_aware_utc(ticket.created_at)
        updated_at = _as_aware_utc(ticket.updated_at)
        total_hours += max((updated_at - created_at).total_seconds() / 3600, 0)

    return round(total_hours / len(resolved_tickets), 1)


def _dashboard_metrics():
    tickets = Ticket.query.order_by(Ticket.updated_at.desc(), Ticket.created_at.desc()).all()
    users = User.query.order_by(User.name.asc()).all()
    comments_total = Comment.query.count()
    total = len(tickets)

    status_counts = {
        status: sum(ticket.status == status for ticket in tickets)
        for status in STATUS_LABELS
    }
    priority_counts = {
        priority: sum(ticket.priority == priority for ticket in tickets)
        for priority in PRIORITY_LABELS
    }
    resolved_total = status_counts["resuelto"] + status_counts["cerrado"]
    open_total = status_counts["abierto"] + status_counts["en_proceso"]
    unassigned_total = sum(ticket.assignee_id is None for ticket in tickets)
    overdue_tickets = [ticket for ticket in tickets if is_sla_overdue(ticket)]
    avg_resolution_hours = _average_resolution_hours(tickets)

    technicians = [user for user in users if user.role in ("tecnico", "admin")]
    workload = []
    for user in technicians:
        assigned = [ticket for ticket in tickets if ticket.assignee_id == user.id]
        active = [
            ticket
            for ticket in assigned
            if ticket.status in ("abierto", "en_proceso")
        ]
        workload.append(
            {
                "name": user.name,
                "role": user.role,
                "assigned": len(assigned),
                "active": len(active),
                "high_priority": sum(ticket.priority == "alta" for ticket in assigned),
            }
        )

    workload.sort(key=lambda item: (item["active"], item["assigned"]), reverse=True)

    return {
        "totals": {
            "tickets": total,
            "users": len(users),
            "comments": comments_total,
            "unassigned": unassigned_total,
            "resolved": resolved_total,
            "active": open_total,
            "open_total": open_total,
            "closed_total": resolved_total,
            "high_priority": priority_counts["alta"],
            "overdue": len(overdue_tickets),
            "avg_resolution_hours": avg_resolution_hours,
        },
        "open_closed_rows": [
            {
                "label": "Abiertos",
                "count": open_total,
                "percent": _percent(open_total, total),
            },
            {
                "label": "Resueltos o cerrados",
                "count": resolved_total,
                "percent": _percent(resolved_total, total),
            },
        ],
        "status_rows": [
            {
                "key": status,
                "label": label,
                "count": status_counts[status],
                "percent": _percent(status_counts[status], total),
            }
            for status, label in STATUS_LABELS.items()
        ],
        "priority_rows": [
            {
                "key": priority,
                "label": label,
                "count": priority_counts[priority],
                "percent": _percent(priority_counts[priority], total),
            }
            for priority, label in PRIORITY_LABELS.items()
        ],
        "workload": workload,
        "recent_tickets": tickets[:5],
        "overdue_tickets": overdue_tickets[:5],
        "sla_by_ticket": sla_summaries(tickets),
    }


@main_bp.route("/")
def index():
    return render_template("index.html")


@main_bp.route("/dashboard")
@login_required
def dashboard():
    if current_user.role != "admin":
        abort(403)

    return render_template("dashboard.html", metrics=_dashboard_metrics())


@main_bp.route("/health")
def health():
    return jsonify(status="ok", service="opendesk")
