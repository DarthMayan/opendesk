# Manual de instalacion de OpenDesk

> Borrador inicial para el Modulo 4. Este documento describe una instalacion
> local reproducible y una alternativa con Docker para desarrollo y pruebas.

## 1. Requisitos previos

- Git
- Python 3.11 o superior
- pip
- Docker y Docker Compose, solo si se usara el entorno con contenedores

## 2. Obtener el codigo fuente

```bash
git clone https://github.com/DarthMayan/opendesk.git
cd opendesk
```

Si se trabaja desde una rama de desarrollo:

```bash
git fetch --all --prune
git switch feature/ui-dashboard
```

## 3. Instalacion local con Python

Crear y activar un entorno virtual:

```bash
python -m venv venv
```

En Windows PowerShell:

```powershell
.\venv\Scripts\Activate.ps1
```

En Linux o macOS:

```bash
source venv/bin/activate
```

Instalar dependencias:

```bash
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## 4. Configuracion

OpenDesk puede ejecutarse sin variables adicionales en desarrollo. Por defecto
usa:

- `SECRET_KEY=dev-secret-key`
- `DATABASE_URL=sqlite:///opendesk.db`

Para usar valores propios, copiar el archivo de ejemplo y ajustar sus valores:

En Windows PowerShell:

```powershell
Copy-Item .env.example .env
```

En Linux o macOS:

```bash
cp .env.example .env
```

Tambien se pueden definir variables de entorno antes de ejecutar la aplicacion.

En Windows PowerShell:

```powershell
$env:SECRET_KEY="cambiar-en-produccion"
$env:DATABASE_URL="sqlite:///opendesk.db"
```

En Linux o macOS:

```bash
export SECRET_KEY="cambiar-en-produccion"
export DATABASE_URL="sqlite:///opendesk.db"
```

## 5. Ejecutar la aplicacion

```bash
python run.py
```

La aplicacion queda disponible en:

```text
http://localhost:5000
```

## 6. Instalacion con Docker

Construir y levantar los servicios:

```bash
docker-compose up --build
```

Para detenerlos:

```bash
docker-compose down
```

## 7. Verificacion

Ejecutar pruebas automatizadas:

```bash
python -m pytest
```

Comprobar manualmente:

- `GET /health` responde con `status: ok`
- `/register` permite crear una cuenta
- `/login` permite iniciar sesion
- `/tickets/` muestra la vista de tickets para usuarios autenticados
- `/dashboard` muestra metricas de soporte para usuarios autenticados

## 8. Problemas comunes

### El entorno virtual no activa en PowerShell

Ejecutar PowerShell como usuario normal y permitir scripts para la sesion:

```powershell
Set-ExecutionPolicy -Scope Process -ExecutionPolicy Bypass
```

Despues activar de nuevo:

```powershell
.\venv\Scripts\Activate.ps1
```

### El puerto 5000 ya esta ocupado

Detener el proceso que usa el puerto o configurar Flask para usar otro puerto
durante desarrollo.

### La base de datos local quedo con datos de prueba

Detener la aplicacion, eliminar el archivo `opendesk.db` y volver a ejecutar
`python run.py`. Flask-SQLAlchemy recreara las tablas al iniciar la app.

## 9. Notas para despliegue

- Cambiar `SECRET_KEY` por un valor privado y seguro.
- Usar PostgreSQL para un entorno compartido o productivo.
- No versionar archivos `.env` con secretos.
- Ejecutar `python -m pytest` antes de abrir un Pull Request.
