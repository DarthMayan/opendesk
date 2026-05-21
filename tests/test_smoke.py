from app.extensions import db
from app.models import Comment, Ticket, User


def _register_and_login(client, name="Emiliano", email="emiliano@example.com"):
    return client.post(
        "/register",
        data={
            "name": name,
            "email": email,
            "password": "secret123",
            "confirm_password": "secret123",
        },
        follow_redirects=True,
    )


def test_health_endpoint(client):
    response = client.get("/health")

    assert response.status_code == 200
    assert response.get_json() == {"status": "ok", "service": "opendesk"}


def test_index_page(client):
    response = client.get("/")

    assert response.status_code == 200
    assert b"OpenDesk" in response.data


def test_auth_pages_render_for_guest(client):
    login_response = client.get("/login")
    register_response = client.get("/register")

    assert login_response.status_code == 200
    assert b"Iniciar sesion" in login_response.data
    assert b"Crear cuenta" in login_response.data
    assert register_response.status_code == 200
    assert b"Crea tu acceso a OpenDesk" in register_response.data


def test_register_logs_user_in_and_updates_navbar(client):
    response = _register_and_login(client)

    assert response.status_code == 200
    assert b"Cuenta creada correctamente." in response.data
    assert b"Emiliano" in response.data
    assert b"Cerrar sesion" in response.data


def test_tickets_requires_login(client):
    response = client.get("/tickets/", follow_redirects=False)

    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_dashboard_requires_login(client):
    response = client.get("/dashboard", follow_redirects=False)

    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_dashboard_renders_metrics_for_authenticated_user(client, app):
    _register_and_login(client)

    with app.app_context():
        creator = User.query.filter_by(email="emiliano@example.com").first()
        technician = User(name="Soporte", email="soporte-dashboard@example.com", role="tecnico")
        technician.set_password("secret123")
        db.session.add(technician)
        db.session.flush()

        ticket = Ticket(
            title="Correo corporativo sin acceso",
            description="El usuario no puede entrar al correo desde la manana.",
            status="en_proceso",
            priority="alta",
            creator=creator,
            assignee=technician,
        )
        db.session.add(ticket)
        db.session.flush()

        db.session.add(
            Comment(
                body="Se valido el estado de la cuenta y se inicio seguimiento.",
                ticket=ticket,
                author=technician,
            )
        )
        db.session.commit()

    response = client.get("/dashboard")

    assert response.status_code == 200
    assert b"Dashboard de metricas" in response.data
    assert b"Correo corporativo sin acceso" in response.data
    assert b"Soporte" in response.data
    assert b"1 comentarios" in response.data


def test_ticket_list_renders_for_authenticated_user(client, app):
    _register_and_login(client)

    with app.app_context():
        creator = User.query.filter_by(email="emiliano@example.com").first()
        ticket = Ticket(
            title="Laptop sin acceso a VPN",
            description="El usuario reporta que no puede conectarse a la VPN corporativa desde casa.",
            status="en_proceso",
            priority="alta",
            creator=creator,
            assignee=creator,
        )
        db.session.add(ticket)
        db.session.commit()

    response = client.get("/tickets/")

    assert response.status_code == 200
    assert b"Seguimiento visual de incidencias" in response.data
    assert b"Laptop sin acceso a VPN" in response.data
    assert b"Alta prioridad" in response.data
    assert b"Ver detalle" in response.data


def test_ticket_detail_renders_comments(client, app):
    _register_and_login(client)

    with app.app_context():
        creator = User.query.filter_by(email="emiliano@example.com").first()
        assignee = User(name="Soporte", email="soporte@example.com")
        assignee.set_password("secret123")
        db.session.add(assignee)
        db.session.flush()

        ticket = Ticket(
            title="Impresora fuera de linea",
            description="La impresora del area administrativa no responde desde la manana.",
            status="abierto",
            priority="media",
            creator=creator,
            assignee=assignee,
        )
        db.session.add(ticket)
        db.session.flush()

        comment = Comment(
            body="Se reviso la red local y se detecto que el cable de conexion estaba suelto.",
            ticket=ticket,
            author=assignee,
        )
        db.session.add(comment)
        db.session.commit()

        ticket_id = ticket.id

    response = client.get(f"/tickets/{ticket_id}")

    assert response.status_code == 200
    assert b"Impresora fuera de linea" in response.data
    assert b"Comentarios del ticket" in response.data
    assert b"Soporte" in response.data
    assert b"cable de conexion estaba suelto" in response.data
