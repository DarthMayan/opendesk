from datetime import datetime, timedelta, timezone
from io import BytesIO
from pathlib import Path

from app.extensions import db
from app.models import Comment, Ticket, User
from app.sla import sla_summary


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


def test_profile_requires_login(client):
    response = client.get("/profile", follow_redirects=False)

    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_profile_renders_user_information(client, app):
    _register_and_login(client)

    with app.app_context():
        user = User.query.filter_by(email="emiliano@example.com").first()
        ticket = Ticket(
            title="Perfil con actividad",
            description="Ticket para validar resumen del perfil.",
            status="abierto",
            priority="media",
            creator=user,
            assignee=user,
        )
        db.session.add(ticket)
        db.session.flush()
        db.session.add(Comment(body="Seguimiento desde perfil.", ticket=ticket, author=user))
        db.session.commit()

    response = client.get("/profile")

    assert response.status_code == 200
    assert b"Informacion del usuario" in response.data
    assert b"Emiliano" in response.data
    assert b"emiliano@example.com" in response.data
    assert b"usuario" in response.data
    assert b"Correo registrado" in response.data
    assert b"Foto de perfil" in response.data
    assert b'name="avatar"' in response.data
    assert b'name="email"' not in response.data
    assert b"Guardar cambios" in response.data


def test_user_can_update_profile_name_without_changing_email(client, app):
    _register_and_login(client)

    response = client.post(
        "/profile",
        data={
            "name": "Emiliano Actualizado",
            "email": "emiliano.actualizado@example.com",
            "current_password": "",
            "new_password": "",
            "confirm_password": "",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Perfil actualizado correctamente." in response.data
    assert b"Emiliano Actualizado" in response.data
    assert b"emiliano@example.com" in response.data
    assert b"emiliano.actualizado@example.com" not in response.data

    with app.app_context():
        user = User.query.filter_by(email="emiliano@example.com").first()

        assert user is not None
        assert user.name == "Emiliano Actualizado"
        assert user.email == "emiliano@example.com"
        assert user.role == "usuario"


def test_profile_ignores_duplicate_email_attempt(client, app):
    _register_and_login(client)

    with app.app_context():
        user = User(name="Otro", email="otro-perfil@example.com")
        user.set_password("secret123")
        db.session.add(user)
        db.session.commit()

    response = client.post(
        "/profile",
        data={
            "name": "Emiliano",
            "email": "otro-perfil@example.com",
            "current_password": "",
            "new_password": "",
            "confirm_password": "",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Perfil actualizado correctamente." in response.data
    assert b"otro-perfil@example.com" not in response.data

    with app.app_context():
        user = User.query.filter_by(email="emiliano@example.com").first()

        assert user is not None
        assert user.email == "emiliano@example.com"


def test_user_can_update_password_from_profile(client):
    _register_and_login(client)

    response = client.post(
        "/profile",
        data={
            "name": "Emiliano",
            "email": "emiliano@example.com",
            "current_password": "secret123",
            "new_password": "nuevo123",
            "confirm_password": "nuevo123",
        },
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Perfil actualizado correctamente." in response.data

    client.get("/logout")
    login_response = _login(client, "emiliano@example.com", password="nuevo123")

    assert login_response.status_code == 200
    assert b"Sesion iniciada correctamente." in login_response.data


def test_user_can_upload_profile_avatar(client, app):
    _register_and_login(client)

    response = client.post(
        "/profile",
        data={
            "name": "Emiliano",
            "avatar": (BytesIO(b"fake image bytes"), "avatar.png"),
            "current_password": "",
            "new_password": "",
            "confirm_password": "",
        },
        content_type="multipart/form-data",
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Perfil actualizado correctamente." in response.data
    assert b"uploads/avatars/user-" in response.data

    with app.app_context():
        user = User.query.filter_by(email="emiliano@example.com").first()
        avatar_path = Path(app.config["PROFILE_AVATAR_UPLOAD_FOLDER"]) / user.avatar_filename

        assert user.avatar_filename.endswith(".png")
        assert avatar_path.exists()


def test_profile_rejects_invalid_avatar_extension(client, app):
    _register_and_login(client)

    response = client.post(
        "/profile",
        data={
            "name": "Emiliano",
            "avatar": (BytesIO(b"not an image"), "avatar.txt"),
            "current_password": "",
            "new_password": "",
            "confirm_password": "",
        },
        content_type="multipart/form-data",
    )

    assert response.status_code == 400
    assert b"Sube una imagen valida" in response.data

    with app.app_context():
        user = User.query.filter_by(email="emiliano@example.com").first()

        assert user.avatar_filename is None


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


def test_dashboard_requires_admin_role(client):
    _register_and_login(client)

    response = client.get("/dashboard")

    assert response.status_code == 403


def test_dashboard_renders_metrics_for_authenticated_user(client, app):
    _register_and_login(client, name="Admin", email="admin-dashboard@example.com", role="admin")

    with app.app_context():
        creator = User.query.filter_by(email="admin-dashboard@example.com").first()
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


def test_user_only_sees_own_tickets(client, app):
    _register_and_login(client)

    with app.app_context():
        creator = User.query.filter_by(email="emiliano@example.com").first()
        other = User(name="Otro usuario", email="otro@example.com")
        other.set_password("secret123")
        db.session.add(other)
        db.session.flush()

        own_ticket = Ticket(
            title="Mi laptop no carga",
            description="La bateria no recibe energia.",
            status="abierto",
            priority="media",
            creator=creator,
        )
        other_ticket = Ticket(
            title="Ticket privado de otro usuario",
            description="Este ticket no debe mostrarse al usuario actual.",
            status="abierto",
            priority="alta",
            creator=other,
        )
        db.session.add_all([own_ticket, other_ticket])
        db.session.commit()
        other_ticket_id = other_ticket.id

    response = client.get("/tickets/")

    assert response.status_code == 200
    assert b"Mi laptop no carga" in response.data
    assert b"Ticket privado de otro usuario" not in response.data

    detail_response = client.get(f"/tickets/{other_ticket_id}")

    assert detail_response.status_code == 403


def test_technician_sees_assigned_and_unassigned_tickets_only(client, app):
    _register_and_login(client)

    with app.app_context():
        creator = User.query.filter_by(email="emiliano@example.com").first()
        technician = User(name="Tecnico A", email="tecnico-a@example.com", role="tecnico")
        technician.set_password("secret123")
        other_technician = User(name="Tecnico B", email="tecnico-b@example.com", role="tecnico")
        other_technician.set_password("secret123")
        db.session.add_all([technician, other_technician])
        db.session.flush()

        assigned_ticket = Ticket(
            title="Asignado al tecnico A",
            description="Debe verlo el tecnico A.",
            status="abierto",
            priority="media",
            creator=creator,
            assignee=technician,
        )
        unassigned_ticket = Ticket(
            title="Pendiente sin responsable",
            description="Debe verlo cualquier tecnico.",
            status="abierto",
            priority="media",
            creator=creator,
        )
        other_assigned_ticket = Ticket(
            title="Asignado al tecnico B",
            description="No debe verlo el tecnico A.",
            status="abierto",
            priority="media",
            creator=creator,
            assignee=other_technician,
        )
        db.session.add_all([assigned_ticket, unassigned_ticket, other_assigned_ticket])
        db.session.commit()
        other_assigned_ticket_id = other_assigned_ticket.id

    client.get("/logout")
    _login(client, "tecnico-a@example.com")

    response = client.get("/tickets/")

    assert response.status_code == 200
    assert b"Asignado al tecnico A" in response.data
    assert b"Pendiente sin responsable" in response.data
    assert b"Asignado al tecnico B" not in response.data
    assert b"Editar" not in response.data

    detail_response = client.get(f"/tickets/{other_assigned_ticket_id}")

    assert detail_response.status_code == 403


def test_ticket_list_filters_by_text_status_priority_creator_assignee_and_unassigned(client, app):
    _register_and_login(client, name="Admin", email="admin-filters@example.com", role="admin")

    with app.app_context():
        admin = User.query.filter_by(email="admin-filters@example.com").first()
        creator = User(name="Solicitante", email="solicitante@example.com")
        creator.set_password("secret123")
        technician = User(name="Filtro Tecnico", email="filtro-tecnico@example.com", role="tecnico")
        technician.set_password("secret123")
        db.session.add_all([creator, technician])
        db.session.flush()

        vpn_ticket = Ticket(
            title="VPN no conecta",
            description="La conexion remota falla al iniciar sesion.",
            status="abierto",
            priority="alta",
            creator=creator,
            assignee=technician,
        )
        printer_ticket = Ticket(
            title="Impresora sin toner",
            description="El equipo de impresion requiere consumible.",
            status="resuelto",
            priority="baja",
            creator=admin,
        )
        db.session.add_all([vpn_ticket, printer_ticket])
        db.session.commit()
        creator_id = creator.id
        technician_id = technician.id

    response = client.get("/tickets/?q=remota")
    assert response.status_code == 200
    assert b"VPN no conecta" in response.data
    assert b"Impresora sin toner" not in response.data

    response = client.get("/tickets/?status=resuelto")
    assert b"Impresora sin toner" in response.data
    assert b"VPN no conecta" not in response.data

    response = client.get("/tickets/?priority=alta")
    assert b"VPN no conecta" in response.data
    assert b"Impresora sin toner" not in response.data

    response = client.get(f"/tickets/?creator_id={creator_id}")
    assert b"VPN no conecta" in response.data
    assert b"Impresora sin toner" not in response.data

    response = client.get(f"/tickets/?assignee_id={technician_id}")
    assert b"VPN no conecta" in response.data
    assert b"Impresora sin toner" not in response.data

    response = client.get("/tickets/?unassigned=1")
    assert b"Impresora sin toner" in response.data
    assert b"VPN no conecta" not in response.data


def test_ticket_list_and_detail_show_overdue_sla(client, app):
    _register_and_login(client)

    with app.app_context():
        creator = User.query.filter_by(email="emiliano@example.com").first()
        ticket = Ticket(
            title="Servidor sin respuesta",
            description="El servidor principal no responde desde ayer.",
            status="abierto",
            priority="alta",
            creator=creator,
            created_at=datetime.now(timezone.utc) - timedelta(hours=6),
        )
        db.session.add(ticket)
        db.session.commit()
        ticket_id = ticket.id

    list_response = client.get("/tickets/")

    assert list_response.status_code == 200
    assert b"Servidor sin respuesta" in list_response.data
    assert b"Vencido" in list_response.data
    assert b"Escalado" in list_response.data
    assert b"Vencidos 1" in list_response.data

    detail_response = client.get(f"/tickets/{ticket_id}")

    assert detail_response.status_code == 200
    assert b"SLA" in detail_response.data
    assert b"4 horas" in detail_response.data
    assert b"Fecha limite" in detail_response.data
    assert b"Vencido y escalado" in detail_response.data
    assert b"Tiempo SLA" in detail_response.data
    assert b"Tiempo vencido" in detail_response.data
    assert b"od-sla-red" in detail_response.data


def test_sla_summary_bar_thresholds(app):
    now = datetime(2026, 5, 23, 12, 0, tzinfo=timezone.utc)

    with app.app_context():
        creator = User(name="SLA", email="sla@example.com")
        creator.set_password("secret123")
        db.session.add(creator)
        db.session.flush()

        green_ticket = Ticket(
            title="Verde",
            description="Menos de la mitad del tiempo.",
            status="abierto",
            priority="alta",
            creator=creator,
            created_at=now - timedelta(hours=1),
        )
        yellow_ticket = Ticket(
            title="Amarillo",
            description="Mas de la mitad del tiempo.",
            status="abierto",
            priority="alta",
            creator=creator,
            created_at=now - timedelta(hours=2),
        )
        orange_ticket = Ticket(
            title="Naranja",
            description="Tres cuartas partes del tiempo.",
            status="abierto",
            priority="alta",
            creator=creator,
            created_at=now - timedelta(hours=3),
        )
        red_ticket = Ticket(
            title="Rojo",
            description="Tiempo vencido.",
            status="abierto",
            priority="alta",
            creator=creator,
            created_at=now - timedelta(hours=5),
        )

        assert sla_summary(green_ticket, now=now)["bar_class"] == "od-sla-green"
        assert sla_summary(yellow_ticket, now=now)["bar_class"] == "od-sla-yellow"
        assert sla_summary(orange_ticket, now=now)["bar_class"] == "od-sla-orange"
        assert sla_summary(red_ticket, now=now)["bar_class"] == "od-sla-red"
        assert sla_summary(red_ticket, now=now)["bar_percent"] == 100


def test_dashboard_counts_overdue_active_tickets_only(client, app):
    _register_and_login(client, name="Admin", email="admin-sla@example.com", role="admin")

    now = datetime.now(timezone.utc)
    with app.app_context():
        admin = User.query.filter_by(email="admin-sla@example.com").first()
        overdue_ticket = Ticket(
            title="Base de datos caida",
            description="La base de datos no responde.",
            status="en_proceso",
            priority="alta",
            creator=admin,
            created_at=now - timedelta(hours=8),
        )
        resolved_old_ticket = Ticket(
            title="Caso resuelto fuera de fecha",
            description="No debe contar como vencido activo.",
            status="resuelto",
            priority="alta",
            creator=admin,
            created_at=now - timedelta(hours=8),
            updated_at=now - timedelta(hours=2),
        )
        db.session.add_all([overdue_ticket, resolved_old_ticket])
        db.session.commit()

    response = client.get("/dashboard")

    assert response.status_code == 200
    assert b"Tickets vencidos" in response.data
    assert b"Base de datos caida" in response.data
    assert b"1 vencidos" in response.data
    assert b"Promedio" in response.data
    assert b"6.0h" in response.data
    assert b"Abiertos vs cerrados" in response.data


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
    assert b"Ticket creado con prioridad Alta." in response.data

    with app.app_context():
        ticket = Ticket.query.filter_by(title="Monitor no enciende").first()

        assert ticket is not None
        assert ticket.description == "El monitor principal no muestra imagen desde esta manana."
        assert ticket.priority == "alta"
        assert ticket.status == "abierto"
        assert ticket.creator.email == "emiliano@example.com"
        assert ticket.assignee is None
        assert ticket.comments[0].body == "Ticket creado con prioridad Alta."


def test_edit_ticket_requires_login(client):
    response = client.get("/tickets/1/edit", follow_redirects=False)

    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_update_ticket_status_requires_login(client):
    response = client.post("/tickets/1/status", data={"status": "en_proceso"}, follow_redirects=False)

    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_assign_ticket_requires_login(client):
    response = client.post("/tickets/1/assign", data={"assignee_id": "1"}, follow_redirects=False)

    assert response.status_code == 302
    assert "/login" in response.headers["Location"]


def test_add_comment_requires_login(client):
    response = client.post("/tickets/1/comments", data={"body": "Seguimiento inicial."}, follow_redirects=False)

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
    assert b"Ticket editado:" in response.data
    assert b"descripcion actualizada" in response.data

    with app.app_context():
        updated_ticket = db.session.get(Ticket, ticket_id)

        assert updated_ticket.title == "Teclado y mouse no responden"
        assert updated_ticket.description == "El teclado y el mouse USB dejaron de responder en el equipo principal."
        assert updated_ticket.priority == "alta"
        assert updated_ticket.status == "abierto"
        assert updated_ticket.comments[0].body == (
            "Ticket editado: titulo: Teclado no responde -> Teclado y mouse no responden; "
            "descripcion actualizada; prioridad: Media -> Alta."
        )


def test_user_cannot_edit_or_comment_other_users_ticket(client, app):
    _register_and_login(client)

    with app.app_context():
        other = User(name="Otro usuario", email="otro-edit@example.com")
        other.set_password("secret123")
        db.session.add(other)
        db.session.flush()

        ticket = Ticket(
            title="Ticket ajeno",
            description="El usuario actual no debe editar ni comentar este ticket.",
            status="abierto",
            priority="media",
            creator=other,
        )
        db.session.add(ticket)
        db.session.commit()
        ticket_id = ticket.id

    edit_response = client.get(f"/tickets/{ticket_id}/edit")
    comment_response = client.post(
        f"/tickets/{ticket_id}/comments",
        data={"body": "Intento de comentario no permitido."},
    )

    assert edit_response.status_code == 403
    assert comment_response.status_code == 403

    with app.app_context():
        assert Comment.query.filter_by(ticket_id=ticket_id).count() == 0


def test_non_admin_cannot_assign_ticket(client, app):
    _register_and_login(client)

    with app.app_context():
        creator = User.query.filter_by(email="emiliano@example.com").first()
        technician = User(name="Tecnico", email="tecnico-no-admin@example.com", role="tecnico")
        technician.set_password("secret123")
        db.session.add(technician)
        db.session.flush()

        ticket = Ticket(
            title="Sin responsable inicial",
            description="El ticket aun no debe poder asignarse por un usuario comun.",
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

        assert ticket.assignee is None


def test_admin_can_assign_ticket_to_technician(client, app):
    _register_and_login(client, name="Admin", email="admin-assign@example.com", role="admin")

    with app.app_context():
        admin = User.query.filter_by(email="admin-assign@example.com").first()
        technician = User(name="Soporte Nivel 1", email="soporte-n1@example.com", role="tecnico")
        technician.set_password("secret123")
        db.session.add(technician)
        db.session.flush()

        ticket = Ticket(
            title="Computadora sin internet",
            description="El equipo de recepcion no tiene conexion a la red.",
            status="abierto",
            priority="alta",
            creator=admin,
        )
        db.session.add(ticket)
        db.session.commit()
        ticket_id = ticket.id
        technician_id = technician.id

    detail_response = client.get(f"/tickets/{ticket_id}")

    assert detail_response.status_code == 200
    assert b"Responsable" in detail_response.data
    assert b"Soporte Nivel 1" in detail_response.data
    assert b"Guardar responsable" in detail_response.data

    response = client.post(
        f"/tickets/{ticket_id}/assign",
        data={"assignee_id": str(technician_id)},
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Ticket asignado a Soporte Nivel 1." in response.data
    assert b"Soporte Nivel 1" in response.data
    assert b"Responsable actualizado: Sin asignar -&gt; Soporte Nivel 1." in response.data

    list_response = client.get("/tickets/")

    assert list_response.status_code == 200
    assert b"Sin asignar 0" in list_response.data

    with app.app_context():
        updated_ticket = db.session.get(Ticket, ticket_id)

        assert updated_ticket.assignee_id == technician_id
        assert updated_ticket.comments[0].body == "Responsable actualizado: Sin asignar -> Soporte Nivel 1."


def test_admin_can_unassign_ticket(client, app):
    _register_and_login(client, name="Admin", email="admin-unassign@example.com", role="admin")

    with app.app_context():
        admin = User.query.filter_by(email="admin-unassign@example.com").first()
        technician = User(name="Soporte Nivel 2", email="soporte-n2@example.com", role="tecnico")
        technician.set_password("secret123")
        db.session.add(technician)
        db.session.flush()

        ticket = Ticket(
            title="Cambio de responsable",
            description="El ticket debe quedar pendiente de reasignacion.",
            status="en_proceso",
            priority="media",
            creator=admin,
            assignee=technician,
        )
        db.session.add(ticket)
        db.session.commit()
        ticket_id = ticket.id

    response = client.post(
        f"/tickets/{ticket_id}/assign",
        data={"assignee_id": ""},
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Ticket marcado como sin asignar." in response.data
    assert b"Sin asignar" in response.data
    assert b"Responsable actualizado: Soporte Nivel 2 -&gt; Sin asignar." in response.data

    with app.app_context():
        updated_ticket = db.session.get(Ticket, ticket_id)

        assert updated_ticket.assignee is None
        assert updated_ticket.comments[0].body == "Responsable actualizado: Soporte Nivel 2 -> Sin asignar."


def test_authenticated_user_can_add_comment_to_ticket(client, app):
    _register_and_login(client)

    with app.app_context():
        creator = User.query.filter_by(email="emiliano@example.com").first()
        ticket = Ticket(
            title="Seguimiento de correo",
            description="El usuario requiere una actualizacion sobre su acceso al correo.",
            status="abierto",
            priority="media",
            creator=creator,
        )
        db.session.add(ticket)
        db.session.commit()
        ticket_id = ticket.id

    form_response = client.get(f"/tickets/{ticket_id}")

    assert form_response.status_code == 200
    assert b"Agregar comentario" in form_response.data

    response = client.post(
        f"/tickets/{ticket_id}/comments",
        data={"body": "Se reviso la cuenta y se escalo al equipo de identidad."},
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Comentario agregado correctamente." in response.data
    assert b"Se reviso la cuenta y se escalo al equipo de identidad." in response.data
    assert b"Emiliano" in response.data

    with app.app_context():
        comment = Comment.query.filter_by(ticket_id=ticket_id).first()

        assert comment is not None
        assert comment.body == "Se reviso la cuenta y se escalo al equipo de identidad."
        assert comment.author.email == "emiliano@example.com"


def test_add_comment_requires_body(client, app):
    _register_and_login(client)

    with app.app_context():
        creator = User.query.filter_by(email="emiliano@example.com").first()
        ticket = Ticket(
            title="Comentario vacio",
            description="El sistema no debe guardar comentarios vacios.",
            status="abierto",
            priority="baja",
            creator=creator,
        )
        db.session.add(ticket)
        db.session.commit()
        ticket_id = ticket.id

    response = client.post(
        f"/tickets/{ticket_id}/comments",
        data={"body": "   "},
        follow_redirects=True,
    )

    assert response.status_code == 200
    assert b"Escribe un comentario antes de guardarlo." in response.data

    with app.app_context():
        assert Comment.query.filter_by(ticket_id=ticket_id).count() == 0


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
    assert b"Estado actualizado: Abierto -&gt; En proceso." in progress_response.data

    resolved_response = client.post(
        f"/tickets/{ticket_id}/status",
        data={"status": "resuelto"},
        follow_redirects=True,
    )

    assert resolved_response.status_code == 200
    assert b"Ticket marcado como resuelto." in resolved_response.data
    assert b"Resuelto" in resolved_response.data
    assert b"Estado actualizado: En proceso -&gt; Resuelto." in resolved_response.data

    with app.app_context():
        updated_ticket = db.session.get(Ticket, ticket_id)

        assert updated_ticket.status == "resuelto"
        assert [comment.body for comment in updated_ticket.comments] == [
            "Estado actualizado: Abierto -> En proceso.",
            "Estado actualizado: En proceso -> Resuelto.",
        ]


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
