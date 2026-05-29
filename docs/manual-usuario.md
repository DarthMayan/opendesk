# Manual de usuario de OpenDesk

## 1. Que es OpenDesk

OpenDesk es una plataforma web para organizar solicitudes de soporte tecnico. Su objetivo es centralizar los tickets de ayuda en un solo lugar, permitiendo que los usuarios reporten incidencias, que el equipo de soporte les de seguimiento y que los responsables puedan consultar el estado general del servicio.

La aplicacion esta pensada para ser sencilla de usar desde el navegador. Permite crear una cuenta, iniciar sesion, registrar tickets, consultar detalles, agregar comentarios, recibir notificaciones y revisar metricas generales del soporte.

## 2. Acceso inicial

Al entrar a OpenDesk, la pantalla de inicio muestra dos acciones principales:

- **Crear cuenta**: permite registrar un nuevo usuario.
- **Iniciar sesion**: permite acceder con una cuenta existente.

Cuando el usuario ya inicio sesion, la barra superior cambia y muestra las opciones disponibles segun su perfil. En esa barra tambien aparecen accesos a **Inicio**, **Tickets**, **Notificaciones**, **Perfil** y **Cerrar sesion**. Los usuarios con perfil administrador tambien ven la opcion **Dashboard**.

## 3. Crear una cuenta

Para crear una cuenta nueva:

1. Haz clic en **Crear cuenta**.
2. Captura tu **Nombre**.
3. Captura tu **Correo**.
4. Selecciona tu **Perfil**.
5. Escribe una **Contrasena**.
6. Repite la contrasena en **Confirmar contrasena**.
7. Haz clic en **Crear cuenta**.

Si los datos son correctos, OpenDesk crea la cuenta e inicia sesion automaticamente.

### Perfiles disponibles

- **Usuario**: reporta incidencias y consulta el avance de sus propias solicitudes.
- **Tecnico**: atiende tickets, agrega seguimiento y actualiza estados operativos.
- **Admin**: supervisa la operacion, consulta metricas, asigna responsables y administra cambios de estado.

## 4. Iniciar sesion

Para entrar con una cuenta existente:

1. Haz clic en **Iniciar sesion**.
2. Escribe tu **Correo**.
3. Escribe tu **Contrasena**.
4. Haz clic en **Entrar**.

Si las credenciales son correctas, el sistema muestra la pagina principal con la sesion activa. Si hay un error, OpenDesk muestra un mensaje indicando que el correo o la contrasena son incorrectos.

## 5. Editar perfil de usuario

Desde la barra superior, haz clic en tu nombre o avatar para entrar a **Informacion del usuario**.

En esta pantalla puedes:

- Consultar el correo registrado.
- Consultar tu perfil o rol.
- Cambiar tu nombre.
- Subir una foto de perfil.
- Cambiar tu contrasena.

Para guardar cambios:

1. Actualiza el campo que necesites.
2. Si quieres cambiar la contrasena, llena **Contrasena actual**, **Nueva contrasena** y **Confirmar nueva contrasena**.
3. Si quieres cambiar tu foto, selecciona una imagen en formato PNG, JPG, GIF o WEBP.
4. Haz clic en **Guardar cambios**.

## 6. Consultar tickets

Para ver los tickets, haz clic en **Tickets** en la barra superior.

La pantalla de tickets muestra:

- Resumen de tickets visibles.
- Conteo de tickets abiertos, en proceso, vencidos, de alta prioridad y sin asignar.
- Filtros de busqueda.
- Tarjetas con la informacion principal de cada ticket.

Cada ticket muestra su estado, prioridad, numero de ticket, creador, responsable, fecha de actualizacion y fecha limite de SLA. Si un ticket ya vencio su tiempo de atencion, aparece marcado como **Vencido** y **Escalado**.

### Filtros disponibles

En el panel de filtros puedes buscar tickets por:

- Texto en titulo o descripcion.
- Estado.
- Prioridad.
- Creador.
- Responsable.
- Tickets sin asignar.

Despues de seleccionar los filtros, haz clic en **Aplicar filtros**. Para regresar a la lista completa, haz clic en **Limpiar**.

## 7. Crear un ticket

Para registrar una nueva incidencia:

1. Entra a **Tickets**.
2. Haz clic en **Nuevo ticket**.
3. Escribe un **Titulo** claro.
4. Agrega una **Descripcion** con el contexto del problema.
5. Selecciona una **Prioridad**.
6. Haz clic en **Crear ticket**.

Las prioridades disponibles son:

- **Baja**: solicitud simple o no urgente.
- **Media**: problema que afecta el trabajo normal.
- **Alta**: incidencia critica que requiere atencion inmediata.

Al crear el ticket, OpenDesk lo registra con estado **Abierto** y guarda el primer evento en el historial.

## 8. Ver detalle de un ticket

Desde la lista de tickets, haz clic en **Ver detalle**.

La pantalla de detalle muestra:

- Numero de ticket.
- Estado.
- Prioridad.
- Titulo.
- Descripcion completa.
- Creador.
- Responsable asignado.
- Fecha de creacion.
- Ultima actualizacion.
- Tiempo SLA.
- Fecha limite.
- Estado de vencimiento.
- Historial de comentarios y cambios.

Tambien se muestra una barra de progreso del SLA, que indica cuanto tiempo de atencion se ha consumido. Si el ticket vence, el sistema lo marca como vencido y escalado.

## 9. Agregar comentarios

En el detalle del ticket, usa la seccion **Comentarios del ticket**.

Para agregar seguimiento:

1. Escribe el comentario en **Agregar comentario**.
2. Haz clic en **Agregar comentario**.

El comentario queda registrado en el historial con el nombre del autor y la fecha. Los comentarios sirven para documentar avances, dudas, respuestas del usuario o acciones realizadas por soporte.

## 10. Editar un ticket

La opcion **Editar ticket** aparece para administradores y para el usuario que creo el ticket.

Para editar:

1. Abre el detalle del ticket.
2. Haz clic en **Editar ticket**.
3. Actualiza el titulo, descripcion o prioridad.
4. Haz clic en **Guardar cambios**.

OpenDesk registra en el historial los cambios realizados, por ejemplo cuando se modifica la prioridad o la informacion principal del ticket.

## 11. Asignar responsable

Esta funcion esta disponible para usuarios con perfil **Admin**.

Para asignar un tecnico:

1. Abre el detalle del ticket.
2. Busca la seccion **Responsable**.
3. En **Asignar a**, selecciona un tecnico.
4. Haz clic en **Guardar responsable**.

Tambien es posible dejar el ticket sin responsable seleccionando **Sin asignar**. Cuando se cambia el responsable, OpenDesk registra el evento en el historial y genera notificaciones para los usuarios relacionados.

## 12. Cambiar estado de un ticket

El cambio de estado depende del perfil del usuario.

Estados disponibles:

- **Abierto**: ticket creado y pendiente de atencion inicial.
- **En proceso**: el ticket ya esta siendo atendido.
- **Resuelto**: soporte marco el problema como solucionado.
- **Cerrado**: el solicitante o administrador finalizo el ciclo del ticket.

Reglas principales:

- Un **Admin** puede cambiar el ticket a otros estados disponibles.
- Un **Tecnico** puede marcar tickets como **En proceso** o **Resuelto**, siempre que el ticket no este cerrado.
- El **Usuario creador** puede cerrar su ticket cuando esta en estado **Resuelto**.

Para cambiar el estado:

1. Abre el detalle del ticket.
2. Busca la seccion **Cambiar estado**.
3. Haz clic en la accion disponible, por ejemplo **Marcar en proceso**, **Marcar resuelto** o **Cerrar ticket**.

El cambio queda registrado en el historial y puede generar notificaciones.

## 13. Notificaciones

La opcion **Notificaciones** aparece en la barra superior cuando hay una sesion activa. Si existen avisos sin leer, se muestra un contador junto al enlace.

Las notificaciones se generan cuando:

- Un ticket cambia de estado.
- Un ticket recibe un comentario.
- Un ticket es asignado o queda sin responsable.

En la pantalla de notificaciones puedes:

- Ver si una notificacion es **Nueva** o **Leida**.
- Consultar el titulo, descripcion, fecha y ticket relacionado.
- Hacer clic en **Ver y marcar leida** para abrir el ticket.
- Usar **Marcar todas como leidas** cuando existan notificaciones pendientes.

## 14. Dashboard de metricas

El **Dashboard** esta disponible para usuarios con perfil **Admin**.

Esta pantalla permite supervisar la operacion general de soporte. Muestra:

- Total de tickets registrados.
- Tickets activos.
- Tickets resueltos o cerrados.
- Tickets sin asignar.
- Tickets vencidos.
- Tiempo promedio de resolucion.
- Distribucion por estado.
- Distribucion por prioridad.
- Comparacion entre abiertos y cerrados.
- Carga de trabajo por tecnico.
- Tickets vencidos por SLA.
- Actividad reciente.

El dashboard ayuda a identificar carga de trabajo, incidencias criticas y posibles retrasos en la atencion.

## 15. Cerrar sesion

Para salir de la aplicacion:

1. Haz clic en **Cerrar sesion** en la barra superior.
2. OpenDesk finaliza la sesion y regresa a la pantalla de inicio.

Se recomienda cerrar sesion al terminar de usar la aplicacion, especialmente si se utiliza una computadora compartida.

## 16. Recomendaciones de uso

- Usa titulos breves y claros al crear tickets.
- Incluye en la descripcion que ocurre, desde cuando pasa y como afecta el trabajo.
- Selecciona prioridad **Alta** solo cuando el problema sea critico.
- Revisa las notificaciones para dar seguimiento oportuno.
- Usa comentarios para dejar evidencia de avances y decisiones.
- Cierra los tickets cuando la solucion haya sido confirmada.

