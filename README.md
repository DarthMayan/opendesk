# OpenDesk

Sistema de **helpdesk y gestión de tickets de TI** construido íntegramente con
tecnologías de código abierto.

> Proyecto final · Sistemas y Lenguajes de Código Abierto · Universidad Panamericana.

**Demo en vivo:** https://opendesk-a7uf.onrender.com · **Licencia:** [MIT](LICENSE)

---

## El problema

Muchos equipos de TI reciben solicitudes de soporte por correo, chat o de voz.
Sin una herramienta central, esas solicitudes se pierden, no se priorizan y nadie
mide cuánto se tarda en responder. No hay trazabilidad ni rendición de cuentas.

## La solución que estamos construyendo

OpenDesk centraliza todas las incidencias en **tickets** con un ciclo de vida
claro. Cada solicitud queda registrada, se asigna a un técnico, tiene una
prioridad y un **tiempo límite de atención (SLA)**. Si un ticket se vence, el
sistema lo **escala automáticamente**. Un panel de métricas permite a los
responsables ver el estado del soporte de un vistazo.

En concreto, el sistema entrega:

1. **Autenticación y control de acceso** — registro/login con roles
   diferenciados: `usuario` (crea tickets), `técnico` (los atiende),
   `admin` (gestiona y supervisa).
2. **Gestión de tickets** — crear, asignar, cambiar de estado
   (abierto → en proceso → resuelto → cerrado), prioridad y comentarios/historial.
3. **SLA y escalado automático** — cada prioridad tiene un tiempo límite; los
   tickets vencidos se marcan y escalan sin intervención manual.
4. **Dashboard de métricas** — tickets abiertos, vencidos, carga por técnico y
   tiempos promedio de resolución.

## Stack tecnológico (100% OSS)

| Capa | Tecnología | Por qué |
|---|---|---|
| Lenguaje | Python 3 | Conocido por el equipo, ecosistema amplio |
| Framework | Flask | Ligero, bajo consumo de recursos |
| ORM | Flask-SQLAlchemy | Modelos persistentes simples |
| Autenticación | Flask-Login | Sesiones y control de acceso sin servicios externos |
| Base de datos | SQLite (local) / PostgreSQL (nube) | Cero configuración en local |
| Interfaz | Jinja2 + Bootstrap 5 | Sin build de Node, render del lado del servidor |
| Pruebas | pytest | Suite automatizada |
| Contenedores | Docker + docker-compose | Entorno reproducible |

Todas las piezas son de código abierto y debidamente licenciadas. El proyecto
no usa ningún servicio de pago.

## Documentación

| Documento | Contenido |
|---|---|
| [Arquitectura](docs/arquitectura.md) | Diagrama de capas y responsabilidades |
| [Modelo de datos](docs/modelo-datos.md) | Entidades, relaciones y restricciones |
| [Módulo 1 — Auth y roles](docs/modulos/m1-auth.md) | Registro, login, roles, control de acceso |
| [Módulo 2 — Tickets](docs/modulos/m2-tickets.md) | CRUD, estados, asignación, comentarios |
| [Módulo 3 — SLA](docs/modulos/m3-sla.md) | Tiempos límite, vencidos, escalado |
| [Módulo 4 — Dashboard](docs/modulos/m4-dashboard.md) | Métricas de soporte |
| [Manual de instalación](docs/manual-instalacion.md) | Puesta en marcha local y con Docker |
| [Manual de despliegue (Render)](docs/manual-despliegue-render.md) | Despliegue en la nube |
| [Guía de contribución](CONTRIBUTING.md) | Flujo de trabajo del equipo |

## Equipo y roles

> Todos los integrantes son responsables de **todo el sistema**. El rol indica
> el área principal de cada quien, no un trabajo aislado: todos commitean y
> todos revisan los Pull Requests de los demás.

| Integrante | Rol principal | Responsabilidades |
|---|---|---|
| **Diego Morales Gómez** | QA / DevOps / Gestión | Pruebas pytest, Docker, despliegue, tablero de proyecto, coordinación |
| **Diego Salvador Padilla Victoria** | Backend lead | Modelos, autenticación, lógica de tickets y SLA |
| **Joseph Emiliano Arias Limas** | Frontend / Documentación | Plantillas e interfaz, README y manuales |

## Cómo trabajamos

- La rama `main` está **protegida**: nadie hace push directo.
- Todo cambio entra por una rama (`feature/*`, `fix/*`, `docs/*`) y un
  **Pull Request** que debe ser aprobado por otro integrante (code review).
- Commits pequeños, frecuentes y descriptivos según la convención de
  [CONTRIBUTING.md](CONTRIBUTING.md).
- El avance del equipo se registra en la carpeta [`bitacora/`](bitacora/).

## Instalación rápida

```bash
git clone https://github.com/DarthMayan/opendesk.git
cd opendesk
python -m venv venv
source venv/bin/activate        # Windows (PowerShell): .\venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
cp .env.example .env            # Windows: Copy-Item .env.example .env
python run.py
```

La aplicación queda disponible en http://localhost:5000

Para una guia mas completa, consulta el
[manual de instalacion](docs/manual-instalacion.md).

### Con Docker

```bash
docker-compose up --build
```

## Pruebas

```bash
python -m pytest
```

La suite cubre autenticación, control por rol, tickets y dashboard.

## Despliegue

La aplicación está desplegada en Render (plan gratuito) a partir de
[`render.yaml`](render.yaml). Pasos detallados en el
[manual de despliegue](docs/manual-despliegue-render.md).

Demo: https://opendesk-a7uf.onrender.com

## Licencia

Distribuido bajo licencia [MIT](LICENSE).
