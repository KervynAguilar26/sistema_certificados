# Manual de usuario · Sistema de Certificaciones QTech

## 1. Acceso

El sistema tiene dos áreas privadas:

| Área | URL | Para qué sirve |
| --- | --- | --- |
| Panel operativo | `/panel/` | Trabajo diario: certificados, descargas, usuarios y actividad. |
| Administrador avanzado | `/control/` | Plantillas, tipos de certificado, contenido del sitio y configuración interna. |

- Entra en `https://TU-DOMINIO/panel/` e inicia sesión con tu correo y contraseña.
- El primer superadministrador se crea en el servidor con `python manage.py createsuperuser`.
- La sesión caduca tras 30 minutos de inactividad.
- Ninguna de las dos áreas aparece enlazada desde la web pública ni en `robots.txt`.

### Cambiar el idioma

El panel está disponible en **English** y **中文**. Usa el selector de idioma de la
barra superior o de la pantalla de acceso. La web pública también usa solo estos
dos idiomas; los certificados sí se pueden emitir además en español.

## 2. Panel operativo

Al entrar en `/panel/` verás:

- **Dashboard**: total de certificados, vigentes, vencidos, suspendidos, los que
  vencen en 30 días y las validaciones de los últimos 7 días.
- **Certificados**: búsqueda por número, solicitante, fabricante, producto, marca
  o modelo, con filtro por estado.
- **Actividad**: registro de creación, edición, cambios de estado, regeneración
  de tokens y descargas.
- **Usuarios** (solo superadministrador): alta, edición, activación y cambio de
  contraseña.

La barra lateral también enlaza a la **web pública** y a **Ajustes avanzados**
(`/control/`).

## 3. Certificados

### Crear un certificado

1. Entra en **Certificados → Nuevo certificado**.
2. Completa los datos del solicitante, fabricante, producto y marca.
3. Introduce los modelos separados por comas o saltos de línea, o sube un CSV
   con un modelo por línea.
4. Añade los parámetros, normas e informe de ensayo.
5. Elige la fecha de emisión y la de vencimiento.
6. Selecciona el tipo y la plantilla; si se dejan vacíos se usan los
   predeterminados.
7. Pulsa **Crear certificado**.

El analista que crea el certificado queda registrado automáticamente.

### Editar un certificado

Abre la ficha del certificado y pulsa **Editar**. Al guardar se registra el
cambio en la actividad.

### Descargar el certificado

Desde la ficha del certificado, en la tarjeta **Descargas**, puedes:

- **Previsualizar** el HTML en el navegador.
- **Descargar el PDF** en español, inglés o chino.
- **Descargar el HTML** autónomo en los mismos idiomas.
- **Descargar el código QR** de validación.

El PDF se genera al momento con la misma plantilla HTML, incluye el código QR y
no se almacena en el servidor. Si el servidor no tiene WeasyPrint, se usa
automáticamente Chrome/Edge en modo headless.

### Suspender o reactivar

En la ficha del certificado usa **Suspender certificado** o **Activar
certificado**. Un certificado suspendido aparece como inválido en la validación
pública.

### Regenerar el token

**Regenerar token** cambia el enlace de validación. Los códigos QR ya impresos
dejarán de funcionar, así que úsalo solo si el enlace se ha filtrado o necesitas
invalidarlo.

## 4. Validación pública

La única parte pública del sistema de certificados es `/verify/`. Acepta:

- `?q=NUMERO-DE-CERTIFICADO`
- `?code=NUMERO-DE-CERTIFICADO`
- `?token=TOKEN-DEL-QR`
- `?lang=en` o `?lang=zh-hans` para cambiar el idioma del resultado.

Los intentos quedan registrados en **Registros de validación** dentro del
administrador avanzado.

## 5. Usuarios y roles

Solo el **superadministrador** puede gestionar usuarios desde **Panel → Usuarios**.

- **Superadministrador**: acceso completo, incluida la gestión de usuarios.
- **Analista**: puede crear, editar y descargar certificados, pero no administrar
  usuarios.

Para crear un usuario:

1. Entra en **Usuarios → Nuevo usuario**.
2. Escribe nombre completo, correo, rol y contraseña.
3. Guarda. El usuario ya puede iniciar sesión en `/panel/`.

Para cambiar una contraseña, usa **Cambiar contraseña** en la fila del usuario o
en el menú de tu cuenta. El superadministrador no puede desactivarse ni quitarse
su propio rol.

## 6. Plantillas de certificado

Las plantillas se administran en **Ajustes avanzados → Plantillas de certificado**
(`/control/`).

1. Crea una plantilla y sube un archivo `.html` (máximo 1 MB) o pega el código.
2. Opcionalmente sube una imagen de fondo A4 (1240 × 1754 px).
3. Usa los botones de vista previa en English, Español o 中文.
4. Asigna la plantilla al certificado desde el formulario del panel.

Las plantillas aceptan `{{ marcadores }}` y las etiquetas `{% if %}`, `{% for %}`
y `{% with %}`. Por seguridad se rechazan scripts, iframes, formularios,
controladores de eventos y etiquetas o filtros no permitidos.

## 7. Contenido del sitio

En **Ajustes avanzados → Sitio web** puedes editar la configuración general, las
diapositivas de inicio, los servicios, el equipo, la galería y los mensajes de
contacto. Los cambios se publican de inmediato en la web pública.

## 8. Auditoría

- **Actividad** (en `/panel/`): creación, edición, cambios de estado,
  regeneración de tokens y descargas de certificados.
- **Eventos de certificados** y **Registros de validación** (en `/control/`):
  historial completo con usuario, fecha, IP y detalle.

## 9. Copias de seguridad

Realiza copias periódicas de:

- La base de datos PostgreSQL.
- La carpeta `qtech_django/media/` (imágenes públicas).
- La carpeta `qtech_django/private_media/` (plantillas y fondos privados).
