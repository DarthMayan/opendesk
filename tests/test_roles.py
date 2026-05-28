from app.extensions import db
from app.models import Ticket, User


def _register_and_login(client, name="Diego", email="diego@example.com", role="usuario"):
    return client.post(
        "/register",
        data={
            "name": name,
            "email": email,
            "role": role,
            "password": "secret123",
            "confirm_password": "secret123",
        },
        follow_redirects=True,
    )


def _login(client, email, password="secret123"):
    return client.post(
        "/login",
        data={
            "email": email,
            "password": password,
        },
        follow_redirects=True,
    )


def _create_user(name, email, role="usuario"):
    user = User(name=name, email=email, role=role)
    user.set_password("secret123")
    db.session.add(user)
    return user


def test_guest_is_redirected_from_admin_dashboard(client):
    response = client.get("/dashboard", follow_redirects=False)

    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_regular_user_cannot_access_admin_dashboard(client):
    _register_and_login(client, role="usuario")

    response = client.get("/dashboard")

    assert response.status_code == 403


def test_admin_can_access_dashboard(client):
    _register_and_login(
        client,
        name="Admin",
        email="admin-roles@example.com",
        role="admin",
    )

    response = client.get("/dashboard")

    assert response.status_code == 200
    assert b"Dashboard de metricas" in response.data


def test_technician_only_sees_assigned_or_unassigned_tickets(client, app):
    with app.app_context():
        creator = _create_user("Solicitante", "solicitante-roles@example.com")
        technician = _create_user("Tecnico Uno", "tecnico-uno@example.com", "tecnico")
        other_technician = _create_user("Tecnico Dos", "tecnico-dos@example.com", "tecnico")
        db.session.flush()

        assigned_ticket = Ticket(
            title="Asignado al tecnico correcto",
            description="Debe verlo el tecnico autenticado.",
            status="abierto",
            priority="media",
            creator=creator,
            assignee=technician,
        )
        unassigned_ticket = Ticket(
            title="Ticket sin responsable",
            description="Debe verlo cualquier tecnico.",
            status="abierto",
            priority="media",
            creator=creator,
        )
        other_ticket = Ticket(
            title="Asignado a otro tecnico",
            description="No debe verlo el tecnico autenticado.",
            status="abierto",
            priority="alta",
            creator=creator,
            assignee=other_technician,
        )
        db.session.add_all([assigned_ticket, unassigned_ticket, other_ticket])
        db.session.commit()
        other_ticket_id = other_ticket.id

    _login(client, "tecnico-uno@example.com")

    response = client.get("/tickets/")

    assert response.status_code == 200
    assert b"Asignado al tecnico correcto" in response.data
    assert b"Ticket sin responsable" in response.data
    assert b"Asignado a otro tecnico" not in response.data

    detail_response = client.get(f"/tickets/{other_ticket_id}")

    assert detail_response.status_code == 403


def test_regular_user_cannot_assign_ticket(client, app):
    _register_and_login(client, role="usuario")

    with app.app_context():
        creator = User.query.filter_by(email="diego@example.com").first()
        technician = _create_user("Tecnico Asignacion", "tecnico-asignacion@example.com", "tecnico")
        db.session.flush()
        ticket = Ticket(
            title="Asignacion protegida",
            description="Solo un admin debe poder asignar este ticket.",
            status="abierto",
            priority="media",
            creator=creator,
        )
        db.session.add(ticket)
        db.session.commit()
        ticket_id = ticket.id
        technician_id = technician.id

    response = client.post(
        f"/tickets/{ticket_id}/assign",
        data={"assignee_id": str(technician_id)},
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Solo un administrador puede asignar responsables." in response.data

    with app.app_context():
        ticket = db.session.get(Ticket, ticket_id)

        assert ticket.assignee_id is None


def test_admin_can_view_and_update_any_ticket_status(client, app):
    with app.app_context():
        creator = _create_user("Solicitante Admin", "solicitante-admin@example.com")
        admin = _create_user("Admin Roles", "admin-update@example.com", "admin")
        db.session.flush()
        ticket = Ticket(
            title="Ticket modificable por admin",
            description="El admin debe poder verlo y actualizar su estado.",
            status="cerrado",
            priority="baja",
            creator=creator,
        )
        db.session.add(ticket)
        db.session.commit()
        ticket_id = ticket.id

    _login(client, "admin-update@example.com")

    detail_response = client.get(f"/tickets/{ticket_id}")

    assert detail_response.status_code == 200
    assert b"Ticket modificable por admin" in detail_response.data

    update_response = client.post(
        f"/tickets/{ticket_id}/status",
        data={"status": "abierto"},
        follow_redirects=True,
    )

    assert update_response.status_code == 200
    assert b"Ticket marcado como abierto." in update_response.data

    with app.app_context():
        ticket = db.session.get(Ticket, ticket_id)

        assert ticket.status == "abierto"
