# OpenDesk

Sistema de helpdesk y gestion de tickets de TI construido con tecnologias de
codigo abierto.

> Proyecto final - Sistemas y Lenguajes de Codigo Abierto - Universidad
> Panamericana.

## Descripcion

OpenDesk centraliza solicitudes de soporte en una aplicacion web Flask. La base
actual permite registrar usuarios, iniciar sesion y consultar tickets con su
estado, prioridad, responsable e historial de comentarios.

La meta del proyecto es ofrecer una mesa de ayuda simple para equipos de TI:
menos solicitudes perdidas, mejor trazabilidad y una vista clara del trabajo
pendiente.

## Alcance actual

En esta rama el sistema incluye:

1. Autenticacion de usuarios: registro, login, logout y sesiones con
   Flask-Login.
2. Modelo de usuarios con roles preparados para `usuario`, `tecnico` y `admin`.
3. Modelo de tickets con estado, prioridad, creador y tecnico asignado.
4. Modelo de comentarios para conservar historial por ticket.
5. Vistas UI para inicio, autenticacion, listado de tickets y detalle de ticket.
6. Endpoint de salud en `/health`.
7. Pruebas automatizadas con pytest para rutas principales, autenticacion y
   render de tickets.

Funcionalidades planeadas para completar el flujo operativo:

- Creacion y edicion de tickets desde la interfaz.
- Cambios de estado y asignacion por rol.
- Reglas de SLA y escalamiento automatico.
- Dashboard administrativo con metricas de operacion.

## Stack tecnologico

| Capa | Tecnologia | Uso |
| --- | --- | --- |
| Lenguaje | Python 3 | Backend de la aplicacion |
| Framework | Flask | Rutas, vistas y ciclo web |
| ORM | Flask-SQLAlchemy | Persistencia de usuarios, tickets y comentarios |
| Autenticacion | Flask-Login | Manejo de sesiones |
| Base de datos | SQLite local / PostgreSQL en contenedor o nube | Desarrollo y despliegue |
| Templates | Jinja2 + Bootstrap 5 | Interfaz renderizada del lado del servidor |
| Pruebas | pytest | Validacion automatizada |
| Contenedores | Docker + Docker Compose | Entorno reproducible |

## Estructura del proyecto

```text
opendesk/
+-- app/
|   +-- auth/          # Rutas de autenticacion
|   +-- main/          # Inicio y health check
|   +-- tickets/       # Rutas de listado y detalle de tickets
|   +-- templates/     # Vistas Jinja2
|   +-- config.py      # Configuracion por variables de entorno
|   +-- extensions.py  # Instancias compartidas de Flask extensions
|   +-- models.py      # Modelos SQLAlchemy
+-- tests/             # Suite pytest
+-- Dockerfile
+-- docker-compose.yml
+-- requirements.txt
+-- run.py
```

## Instalacion local

Requisitos:

- Python 3.10 o superior
- pip

Pasos:

```bash
git clone https://github.com/DarthMayan/opendesk.git
cd opendesk
python -m venv .venv
```

Activar el entorno virtual:

```bash
# Windows PowerShell
.\.venv\Scripts\Activate.ps1

# macOS/Linux
source .venv/bin/activate
```

Instalar dependencias y preparar variables:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
cp .env.example .env
```

En Windows PowerShell, si `cp` no esta disponible:

```powershell
Copy-Item .env.example .env
```

Ejecutar la aplicacion:

```bash
python run.py
```

La aplicacion local queda disponible en:

```text
http://localhost:5000
```

## Variables de entorno

El archivo `.env.example` incluye los valores base:

```env
SECRET_KEY=cambia-esta-clave-en-produccion
DATABASE_URL=sqlite:///opendesk.db
```

Si `DATABASE_URL` no se define, la app usa SQLite local en
`sqlite:///opendesk.db`. Para despliegues o Docker se puede usar PostgreSQL con
una URL de la forma:

```env
DATABASE_URL=postgresql://usuario:password@host:5432/opendesk
```

## Ejecucion con Docker

```bash
docker-compose up --build
```

Docker Compose levanta:

- `web`: aplicacion Flask servida con Gunicorn.
- `db`: PostgreSQL 16 Alpine.

La aplicacion en Docker queda disponible en:

```text
http://localhost:8000
```

Para detener los servicios:

```bash
docker-compose down
```

## Pruebas

Ejecutar la suite:

```bash
python -m pytest
```

Las pruebas usan una configuracion temporal definida en `tests/conftest.py`, por
lo que no dependen de la base de datos local de desarrollo.

## Flujo de trabajo

- La rama `main` se mantiene protegida.
- Los cambios entran por ramas `feature/*`, `fix/*` o `docs/*`.
- Todo cambio debe pasar por Pull Request y revision de otro integrante.
- Los commits siguen el formato descrito en [CONTRIBUTING.md](CONTRIBUTING.md).

## Equipo

| Integrante | Rol principal |
| --- | --- |
| Diego Morales Gomez | QA / DevOps / gestion |
| Diego Salvador Padilla Victoria | Backend lead |
| Joseph Emiliano Arias Limas | Frontend / documentacion |

## Licencia

Distribuido bajo licencia [MIT](LICENSE).
