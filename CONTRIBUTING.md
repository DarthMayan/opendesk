# Guía de Contribución — OpenDesk

¡Gracias por contribuir a OpenDesk! Este documento describe el flujo de trabajo del equipo.

## Flujo de trabajo (Git)

1. La rama `main` está **protegida**: nadie hace push directo. Todo entra por Pull Request.
2. Crea una rama desde `main` con prefijo según el tipo de cambio:
   - `feature/<descripcion>` — nueva funcionalidad
   - `fix/<descripcion>` — corrección de bug
   - `docs/<descripcion>` — documentación
3. Haz commits pequeños y descriptivos.
4. Abre un Pull Request hacia `main`.
5. **Requiere al menos 1 aprobación** de otro integrante (code review) antes de hacer merge.

## Convención de commits

Formato: `tipo: descripción breve en presente`

Tipos: `feat`, `fix`, `docs`, `test`, `refactor`, `chore`.

Ejemplos:
- `feat: agregar autenticación con roles`
- `fix: corregir cálculo de SLA en tickets vencidos`
- `docs: actualizar manual de instalación`

## Estilo de código

- Python: seguir PEP 8.
- Nombres de variables y funciones en inglés; mensajes de UI en español.

## Pruebas

Antes de abrir un PR, ejecuta la suite:

```bash
python -m pytest
```

## Reporte de issues

Usa el tablero del proyecto (GitHub Projects) y crea un issue describiendo:
problema, pasos para reproducir y comportamiento esperado.
