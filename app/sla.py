"""Utilidades para calcular SLA, vencimiento y escalado de tickets.

El modulo no modifica la base de datos. Sus funciones reciben tickets y
devuelven fechas, banderas o resumenes calculados a partir del estado actual,
la prioridad y la fecha de creacion.
"""

from datetime import datetime, timedelta, timezone


SLA_HOURS = {
    "alta": 4,
    "media": 24,
    "baja": 72,
}

ACTIVE_STATUSES = {"abierto", "en_proceso"}


def _as_aware_utc(value):
    """Normaliza una fecha para trabajar con zona horaria UTC.

    Args:
        value: Fecha ``datetime`` que puede ser naive o timezone-aware.

    Returns:
        ``datetime`` equivalente con zona horaria UTC.
    """
    if value.tzinfo is None:
        return value.replace(tzinfo=timezone.utc)
    return value.astimezone(timezone.utc)


def sla_due_at(ticket):
    """Calcula la fecha limite de SLA para un ticket.

    Args:
        ticket: Ticket con atributos ``created_at`` y ``priority``.

    Returns:
        ``datetime`` UTC con la fecha y hora limite de atencion.
    """
    created_at = _as_aware_utc(ticket.created_at)
    hours = SLA_HOURS.get(ticket.priority, SLA_HOURS["media"])
    return created_at + timedelta(hours=hours)


def is_sla_overdue(ticket, now=None):
    """Indica si un ticket activo ya supero su fecha limite de SLA.

    Args:
        ticket: Ticket con atributos ``status``, ``priority`` y ``created_at``.
        now: Fecha actual opcional para pruebas deterministas.

    Returns:
        ``True`` si el ticket esta activo y vencido; de lo contrario ``False``.
    """
    if ticket.status not in ACTIVE_STATUSES:
        return False

    current_time = now or datetime.now(timezone.utc)
    current_time = _as_aware_utc(current_time)
    return current_time > sla_due_at(ticket)


def sla_summary(ticket, now=None):
    """Genera un resumen de SLA listo para vistas y metricas.

    Args:
        ticket: Ticket a evaluar.
        now: Fecha actual opcional para controlar el calculo en pruebas.

    Returns:
        Diccionario con fecha limite, horas de SLA, estado de vencimiento,
        escalado, porcentaje consumido, clase visual y etiqueta de estado.
    """
    current_time = now or datetime.now(timezone.utc)
    current_time = _as_aware_utc(current_time)
    created_at = _as_aware_utc(ticket.created_at)
    due_at = sla_due_at(ticket)
    total_seconds = max((due_at - created_at).total_seconds(), 1)
    elapsed_seconds = max((current_time - created_at).total_seconds(), 0)
    elapsed_percent = round((elapsed_seconds / total_seconds) * 100)
    bar_percent = min(elapsed_percent, 100)
    overdue = is_sla_overdue(ticket, now=now)

    if overdue:
        bar_class = "od-sla-red"
        status_label = "Tiempo vencido"
    elif elapsed_percent >= 75:
        bar_class = "od-sla-orange"
        status_label = "Atencion urgente"
    elif elapsed_percent >= 50:
        bar_class = "od-sla-yellow"
        status_label = "En observacion"
    else:
        bar_class = "od-sla-green"
        status_label = "Dentro de tiempo"

    return {
        "due_at": due_at,
        "hours": SLA_HOURS.get(ticket.priority, SLA_HOURS["media"]),
        "overdue": overdue,
        "escalated": overdue,
        "elapsed_percent": elapsed_percent,
        "bar_percent": bar_percent,
        "bar_class": bar_class,
        "status_label": status_label,
    }


def sla_summaries(tickets, now=None):
    """Genera resumenes de SLA indexados por ID de ticket.

    Args:
        tickets: Iterable de tickets a evaluar.
        now: Fecha actual opcional para reutilizar el mismo punto de corte.

    Returns:
        Diccionario ``{ticket.id: sla_summary(ticket)}``.
    """
    return {ticket.id: sla_summary(ticket, now=now) for ticket in tickets}
