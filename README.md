# OpenDesk

Sistema de **helpdesk y gestión de tickets de TI** construido íntegramente con
tecnologías de código abierto.

Proyecto final · Sistemas y Lenguajes de Código Abierto · Universidad Panamericana.

## Problema que resuelve

Los equipos de TI reciben solicitudes por correo, chat o voz sin trazabilidad,
priorización ni control de tiempos de respuesta. OpenDesk centraliza las
incidencias en tickets con estados, asignación, prioridad y reglas de SLA.

## Módulos

1. **Autenticación y control de acceso** — roles: usuario, técnico, admin.
2. **Gestión de tickets** — creación, asignación, estados, prioridad, comentarios.
3. **SLA y escalado automático** — tiempos límite por prioridad, escalado de vencidos.
4. **Dashboard de métricas** — tickets abiertos, vencidos, por técnico.

## Stack tecnológico (100% OSS)

| Capa | Tecnología |
|---|---|
| Lenguaje | Python 3 |
| Framework | Flask |
| ORM | Flask-SQLAlchemy |
| Auth | Flask-Login |
| Base de datos | SQLite (local) / PostgreSQL (nube) |
| UI | Jinja2 + Bootstrap 5 |
| Pruebas | pytest |
| Contenedores | Docker + docker-compose |

## Instalación rápida

```bash
git clone https://github.com/DarthMayan/opendesk.git
cd opendesk
python -m venv venv
source venv/bin/activate        # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env            # Windows: copy .env.example .env
python run.py
```

La aplicación queda disponible en http://localhost:5000

### Con Docker

```bash
docker-compose up --build
```

## Pruebas

```bash
pytest
```

## Equipo

- Diego Morales Gómez
- Diego Salvador Padilla Victoria
- Joseph Emiliano Arias Limas

## Licencia

[MIT](LICENSE)
