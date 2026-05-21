# Manual de despliegue en Render

> Despliega OpenDesk en https://render.com con el plan free, usando el
> archivo `render.yaml` del repositorio (Blueprint).

## 1. Requisitos previos

- Cuenta gratuita en [Render](https://render.com).
- El repositorio `opendesk` debe ser accesible para Render (público o conectado
  a la cuenta de GitHub de quien despliega).

## 2. Despliegue con Blueprint (recomendado)

El archivo [`render.yaml`](../render.yaml) en la raíz del repo declara:

- Un servicio web `opendesk` (Python + gunicorn).
- Una base PostgreSQL gratuita `opendesk-db`.
- `SECRET_KEY` generada automáticamente y `DATABASE_URL` enlazada a la base.

Pasos:

1. Iniciar sesión en Render.
2. Click en **New +** → **Blueprint**.
3. Conectar la cuenta de GitHub si es la primera vez y seleccionar el repo
   `DarthMayan/opendesk`.
4. Render detecta `render.yaml` y muestra los recursos a crear.
5. Confirmar (botón **Apply**). Render construye la imagen, provisiona la base
   y arranca el servicio.

El primer build toma 3–5 minutos. Al terminar, Render entrega una URL del tipo:

```
https://opendesk.onrender.com
```

## 3. Verificación post-despliegue

Comprobar en el navegador o con `curl`:

- `GET /health` → `{"status": "ok", "service": "opendesk"}`
- `/register` permite crear una cuenta
- `/login` y `/logout` funcionan
- `/tickets/` y `/dashboard` requieren sesión

## 4. Notas

- El plan free de Render hiberna el servicio tras ~15 min sin tráfico; el
  primer request tras la hibernación tarda ~30 segundos.
- La base PostgreSQL free expira a los 90 días; renovar o migrar antes.
- `SECRET_KEY` queda configurada automáticamente por Render; no se versiona.
- Los logs de la app están en el panel de Render → servicio `opendesk` → Logs.

## 5. Despliegue manual (sin Blueprint)

Si se prefiere configurar sin `render.yaml`:

1. New + → **Web Service** → conectar el repo.
2. **Runtime**: Python 3.
3. **Build Command**: `pip install -r requirements.txt`.
4. **Start Command**: `gunicorn run:app --bind 0.0.0.0:$PORT`.
5. New + → **PostgreSQL** → plan free → anotar la `Internal Connection String`.
6. En el servicio web, agregar variables de entorno:
   - `SECRET_KEY` (valor aleatorio largo).
   - `DATABASE_URL` (la connection string del paso 5).
7. Deploy.
