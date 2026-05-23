from app.extensions import db
from app.models import Comment, Ticket, User


def _register_and_login(client, name="Emiliano", email="emiliano@example.com", role="usuario"):
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
    assert b"usuario" in response.data
    assert b"Cerrar sesion" in response.data


def test_register_can_create_admin_user(client, app):
    response = _register_and_login(client, name="Admin", email="admin-register@example.com", role="admin")

    assert response.status_code == 200
    assert b"Cuenta creada correctamente." in response.data
    assert b"Admin" in response.data
    assert b"admin" in response.data

    with app.app_context():
        user = User.query.filter_by(email="admin-register@example.com").first()

        assert user is not None
        assert user.role == "admin"


def test_tickets_requires_login(client):
    response = client.get("/tickets/", follow_redirects=False)

    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_create_ticket_requires_login(client):
    response = client.get("/tickets/new", follow_redirects=False)

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


def test_authenticated_user_can_create_ticket(client, app):
    _register_and_login(client)

    form_response = client.get("/tickets/new")

    assert form_response.status_code == 200
    assert b"Datos del ticket" in form_response.data
    assert b"Crear ticket" in form_response.data

    response = client.post(
        "/tickets/new",
        data={
            "title": "Monitor no enciende",
            "description": "El monitor principal no muestra imagen desde esta manana.",
            "priority": "alta",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Ticket creado correctamente." in response.data
    assert b"Monitor no enciende" in response.data
    assert b"El monitor principal no muestra imagen" in response.data
    assert b"Alta" in response.data

    with app.app_context():
        ticket = Ticket.query.filter_by(title="Monitor no enciende").first()

        assert ticket is not None
        assert ticket.description == "El monitor principal no muestra imagen desde esta manana."
        assert ticket.priority == "alta"
        assert ticket.status == "abierto"
        assert ticket.creator.email == "emiliano@example.com"
        assert ticket.assignee is None


def test_edit_ticket_requires_login(client):
    response = client.get("/tickets/1/edit", follow_redirects=False)

    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_update_ticket_status_requires_login(client):
    response = client.post("/tickets/1/status", data={"status": "en_proceso"}, follow_redirects=False)

    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_authenticated_user_can_edit_ticket(client, app):
    _register_and_login(client)

    with app.app_context():
        creator = User.query.filter_by(email="emiliano@example.com").first()
        ticket = Ticket(
            title="Teclado no responde",
            description="El teclado USB no funciona en el equipo principal.",
            status="abierto",
            priority="media",
            creator=creator,
        )
        db.session.add(ticket)
        db.session.commit()
        ticket_id = ticket.id

    form_response = client.get(f"/tickets/{ticket_id}/edit")

    assert form_response.status_code == 200
    assert b"Editar ticket" in form_response.data
    assert b"Teclado no responde" in form_response.data
    assert b"Guardar cambios" in form_response.data

    response = client.post(
        f"/tickets/{ticket_id}/edit",
        data={
            "title": "Teclado y mouse no responden",
            "description": "El teclado y el mouse USB dejaron de responder en el equipo principal.",
            "priority": "alta",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Ticket actualizado correctamente." in response.data
    assert b"Teclado y mouse no responden" in response.data
    assert b"El teclado y el mouse USB dejaron de responder" in response.data
    assert b"Alta" in response.data

    with app.app_context():
        updated_ticket = db.session.get(Ticket, ticket_id)

        assert updated_ticket.title == "Teclado y mouse no responden"
        assert updated_ticket.description == "El teclado y el mouse USB dejaron de responder en el equipo principal."
        assert updated_ticket.priority == "alta"
        assert updated_ticket.status == "abierto"


def test_technician_can_mark_ticket_in_progress_and_resolved(client, app):
    _register_and_login(client)

    with app.app_context():
        creator = User.query.filter_by(email="emiliano@example.com").first()
        technician = User(name="Tecnico", email="tecnico@example.com", role="tecnico")
        technician.set_password("secret123")
        db.session.add(technician)
        db.session.flush()

        ticket = Ticket(
            title="VPN intermitente",
            description="La conexion VPN se desconecta cada pocos minutos.",
            status="abierto",
            priority="alta",
            creator=creator,
            assignee=technician,
        )
        db.session.add(ticket)
        db.session.commit()
        ticket_id = ticket.id

    client.get("/logout")
    _login(client, "tecnico@example.com")

    detail_response = client.get(f"/tickets/{ticket_id}")

    assert detail_response.status_code == 200
    assert b"Cambiar estado" in detail_response.data
    assert b"Marcar en proceso" in detail_response.data
    assert b"Marcar resuelto" in detail_response.data

    progress_response = client.post(
        f"/tickets/{ticket_id}/status",
        data={"status": "en_proceso"},
        follow_redirects=True,
    )

    assert progress_response.status_code == 200
    assert b"Ticket marcado como en proceso." in progress_response.data
    assert b"En proceso" in progress_response.data

    resolved_response = client.post(
        f"/tickets/{ticket_id}/status",
        data={"status": "resuelto"},
        follow_redirects=True,
    )

    assert resolved_response.status_code == 200
    assert b"Ticket marcado como resuelto." in resolved_response.data
    assert b"Resuelto" in resolved_response.data

    with app.app_context():
        updated_ticket = db.session.get(Ticket, ticket_id)

        assert updated_ticket.status == "resuelto"


def test_creator_can_close_resolved_ticket(client, app):
    _register_and_login(client)

    with app.app_context():
        creator = User.query.filter_by(email="emiliano@example.com").first()
        ticket = Ticket(
            title="Solicitud de acceso atendida",
            description="El acceso al sistema interno ya fue habilitado.",
            status="resuelto",
            priority="media",
            creator=creator,
        )
        db.session.add(ticket)
        db.session.commit()
        ticket_id = ticket.id

    detail_response = client.get(f"/tickets/{ticket_id}")

    assert detail_response.status_code == 200
    assert b"Cerrar ticket" in detail_response.data

    response = client.post(
        f"/tickets/{ticket_id}/status",
        data={"status": "cerrado"},
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Ticket marcado como cerrado." in response.data
    assert b"Cerrado" in response.data

    with app.app_context():
        updated_ticket = db.session.get(Ticket, ticket_id)

        assert updated_ticket.status == "cerrado"


def test_admin_can_change_ticket_to_any_status(client, app):
    _register_and_login(client)

    with app.app_context():
        creator = User.query.filter_by(email="emiliano@example.com").first()
        admin = User(name="Admin", email="admin@example.com", role="admin")
        admin.set_password("secret123")
        db.session.add(admin)
        db.session.flush()

        ticket = Ticket(
            title="Equipo cerrado por error",
            description="El ticket necesita volver a seguimiento.",
            status="cerrado",
            priority="baja",
            creator=creator,
        )
        db.session.add(ticket)
        db.session.commit()
        ticket_id = ticket.id

    client.get("/logout")
    _login(client, "admin@example.com")

    detail_response = client.get(f"/tickets/{ticket_id}")

    assert detail_response.status_code == 200
    assert b"Reabrir ticket" in detail_response.data
    assert b"Marcar en proceso" in detail_response.data
    assert b"Marcar resuelto" in detail_response.data

    response = client.post(
        f"/tickets/{ticket_id}/status",
        data={"status": "abierto"},
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Ticket marcado como abierto." in response.data

    with app.app_context():
        updated_ticket = db.session.get(Ticket, ticket_id)

        assert updated_ticket.status == "abierto"


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
