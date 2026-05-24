from flask import Blueprint, abort, jsonify, render_template
from flask_login import current_user, login_required

from ..models import Comment, Ticket, User

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
    unassigned_total = sum(ticket.assignee_id is None for ticket in tickets)

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
            "active": status_counts["abierto"] + status_counts["en_proceso"],
            "high_priority": priority_counts["alta"],
        },
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
