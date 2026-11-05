# QTech · Sistema de Certificados (Django + PostgreSQL)

Sistema nuevo en **Python/Django** que sustituye al sistema PHP existente. Incluye:

- **Web pública** en chino e inglés, con contenido editable (hero, servicios, equipo, galería, contacto).
- **Validación pública de certificados** por número de certificado o por código QR.
- **Panel operativo Bootstrap** en `/panel/`, pensado para el uso diario del cliente: certificados, descargas, usuarios y auditoría.
- **Administrador avanzado de Django** en `/control/` para plantillas, tipos de certificado y contenido del sitio.
- **Plantillas HTML por certificado**, con imagen de fondo opcional.
- **Exportación a PDF y HTML** en español, inglés y chino.
- **Interfaz administrativa solo en chino e inglés**; los formularios de captura están en español.

> El sistema PHP anterior se retiró del árbol de trabajo. Su código sigue en el
> historial de Git y el volcado SQL para migrar datos está en `../legacy/`.

---

## 1. Requisitos

- Python 3.12 o superior (probado con Python 3.15).
- PostgreSQL 15 o superior (probado con PostgreSQL 18).
- Dependencias de `requirements.txt`:

```bash
python -m pip install -r requirements.txt
```

En Linux, `gunicorn` se instala automáticamente. En Windows se omite.

### 1.1 Dependencias del servidor de producción

Además de los paquetes de Python, la exportación a PDF necesita **un motor de
renderizado**. El sistema intenta primero **WeasyPrint** y, si no está
disponible o falla, usa **Chromium/Edge en modo headless**. Basta con tener uno
de los dos instalado.

Para WeasyPrint hacen falta las bibliotecas gráficas de **Pango/HarfBuzz** y una
fuente con caracteres chinos. En Debian/Ubuntu:

```bash
sudo apt update
sudo apt install -y python3 python3-venv python3-pip \
  postgresql libpq-dev \
  libpango-1.0-0 libpangoft2-1.0-0 libharfbuzz-subset0 \
  libfontconfig1 libgdk-pixbuf-2.0-0 fonts-noto-cjk
```

En RHEL/AlmaLinux/Rocky:

```bash
sudo dnf install -y python3 python3-pip postgresql-server \
  pango harfbuzz fontconfig gdk-pixbuf2 google-noto-sans-cjk-fonts
```

En macOS (desarrollo):

```bash
brew install pango libffi
```

Si prefieres no instalar Pango, instala un navegador Chromium y el sistema lo
usará como respaldo:

```bash
# Debian/Ubuntu
sudo apt install -y chromium

# RHEL/AlmaLinux/Rocky
sudo dnf install -y chromium
```

En Windows, WeasyPrint requiere el runtime de GTK3. Si no está instalado, el
sistema usa automáticamente **Microsoft Edge** o **Google Chrome** si están
presentes. Puedes indicar una ruta concreta con la variable
`QTEST_CHROMIUM_PATH`:

```powershell
$env:QTEST_CHROMIUM_PATH='C:\Program Files\Google\Chrome\Application\chrome.exe'
```

> Si no hay ni WeasyPrint ni un navegador Chromium/Edge, el resto del sistema
> sigue funcionando: la vista de PDF muestra un error controlado y el HTML se
> puede descargar e imprimir desde el navegador.

Paquetes de Python que se instalan con `requirements.txt`:

| Paquete | Uso |
| --- | --- |
| `Django` | Framework web. |
| `psycopg[binary]` | Conexión a PostgreSQL. |
| `Pillow` | Procesamiento de imágenes subidas. |
| `qrcode` | Códigos QR de validación. |
| `bleach` | Saneamiento de HTML. |
| `whitenoise` | Servicio de archivos estáticos. |
| `python-dotenv` | Lectura del archivo `.env`. |
| `bcrypt` | Contraseñas heredadas del sistema PHP. |
| `argon2-cffi` | Hash de contraseñas nuevas. |
| `weasyprint` | Exportación de certificados a PDF (motor principal). |
| `gunicorn` | Servidor WSGI (solo Linux/macOS). |

---

## 2. Instalación rápida

```bash
cd qtech_django
cp .env.example .env
# Edita .env con tu clave secreta, contraseña de PostgreSQL y dominio.
```

Crea la base de datos (si no existe):

```sql
CREATE DATABASE qtech_certificates;
```

Aplica migraciones y carga los datos iniciales:

```bash
python manage.py migrate
python manage.py seed_defaults
```

Crea el primer usuario administrador:

```bash
python manage.py createsuperuser
```

> El modelo de usuario usa **correo electrónico** como identificador, no nombre de usuario.

Inicia el servidor de desarrollo:

```bash
python manage.py runserver
```

Abre:

- Web pública: <http://127.0.0.1:8000/>
- Validación pública: <http://127.0.0.1:8000/verify/>
- Panel operativo: <http://127.0.0.1:8000/panel/>
- Administrador avanzado: <http://127.0.0.1:8000/control/> (configurable con `ADMIN_URL_PATH`)

### 2.1 Panel operativo y administrador avanzado

El proyecto tiene dos áreas privadas con propósitos distintos:

| Área | URL | Uso |
| --- | --- | --- |
| Panel operativo | `/panel/` | Uso diario: crear/editar certificados, descargar PDF/HTML/QR, suspender, regenerar tokens, ver actividad y gestionar usuarios. |
| Administrador Django | `/control/` | Configuración avanzada: plantillas de certificado, tipos, contenido del sitio, registros de validación y ajustes internos. |

- El panel usa **Bootstrap 5** servido localmente desde `static/vendor/bootstrap/` (sin CDN).
- El acceso exige un usuario activo con `is_staff`. La gestión de usuarios está reservada al rol **superadministrador**.
- Los analistas pueden crear, editar y descargar certificados, pero no administrar usuarios.
- Los usuarios se pueden crear desde **Panel → Usuarios → Nuevo usuario** o con `python manage.py createsuperuser`.
- El panel no aparece en `robots.txt` ni está enlazado desde la web pública.

---

## 3. Variables de entorno principales

| Variable | Descripción |
| --- | --- |
| `DJANGO_SECRET_KEY` | Clave secreta larga y aleatoria. **Obligatoria en producción.** |
| `DJANGO_DEBUG` | `1` en desarrollo, `0` en producción. |
| `DJANGO_ALLOWED_HOSTS` | Dominios separados por coma. |
| `DJANGO_CSRF_TRUSTED_ORIGINS` | Orígenes con esquema, separados por coma. |
| `SITE_BASE_URL` | URL pública usada en los QR. Sin barra final. |
| `ADMIN_URL_PATH` | Ruta del administrador avanzado de Django. Debe terminar en `/`. |
| `QTEST_CHROMIUM_PATH` | Ruta opcional a Chrome/Edge/Chromium para generar PDF cuando WeasyPrint no está disponible. |
| `POSTGRES_*` | Conexión a PostgreSQL. |
| `USE_SQLITE` | `1` solo para pruebas rápidas; no usar en producción. |
| `TRUST_PROXY_HEADERS` | `1` si hay Nginx/Traefik delante con HTTPS. |
| `EMAIL_*` | Servidor de correo para el formulario de contacto. |
| `LEGACY_DB_*` | Base de datos del sistema PHP para importar datos. |

Genera una clave secreta con:

```bash
python -c "from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())"
```

---

## 4. Importar datos del sistema PHP

El comando lee la base `certificaciones_db` configurada en `LEGACY_DB_*` e importa usuarios y certificados sin borrar los datos existentes:

```bash
python manage.py import_legacy
```

Los usuarios importados conservan su contraseña bcrypt de PHP (`php_bcrypt$...`). En el primer inicio de sesión correcto, Django la reemplaza automáticamente por Argon2.

---

## 5. Web pública y carga de imágenes

El propietario puede editar el contenido desde el panel privado:

- **Configuración del sitio**: nombre, eslogan, dirección, correo, teléfono, logo, favicon, textos de inicio y SEO.
- **Diapositivas del hero**.
- **Servicios**.
- **Equipo**.
- **Galería**.
- **Mensajes de contacto**.

### Dimensiones recomendadas de imágenes

| Imagen | Tamaño recomendado | Formato |
| --- | --- | --- |
| Logotipo | 512 × 512 px | PNG con transparencia |
| Favicon | 64 × 64 px | PNG |
| Diapositiva hero | 1920 × 1080 px (16:9) | JPG o WebP |
| Fotografía de equipo | 600 × 600 px (cuadrada) | JPG o WebP |
| Imagen de galería | 1200 × 800 px (3:2) | JPG o WebP |
| Fondo de plantilla de certificado | 1240 × 1754 px (A4 a 150 ppp) | PNG o JPG |

Consejos:

- Usa imágenes optimizadas (menos de 500 KB cuando sea posible) para que la web cargue rápido.
- Mantén el logotipo y el favicon en PNG con fondo transparente.
- Para el fondo del certificado, evita texto o elementos importantes en los bordes: la plantilla aplica márgenes internos.

---

## 6. Certificados y plantillas

### Descarga en PDF y HTML

Cada certificado se puede previsualizar y descargar en **PDF** o como archivo
**HTML autónomo** desde el panel operativo, en español, inglés y chino.

- El PDF se genera con la misma plantilla HTML del certificado, en A4, e
  incluye el logo, el fondo y el código QR embebidos.
- El HTML incluye estilos, logo, fondo y QR embebidos, por lo que puede abrirse
  sin conexión o imprimirse desde el navegador.
- Ninguno de los dos se almacena en el servidor: se generan bajo demanda.

La exportación a PDF usa **WeasyPrint** como motor principal y, si no está
disponible o falla, recurre a **Chromium/Edge en modo headless**. En Windows
basta con tener Edge o Chrome instalado; en Linux se recomienda instalar
`chromium` o las bibliotecas de Pango. La variable `QTEST_CHROMIUM_PATH` permite
indicar la ruta exacta del navegador.

### Plantillas por certificado

Cada certificado puede usar su propia plantilla. En el panel:

1. Abre **Plantillas de certificado**.
2. Crea o edita una plantilla.
3. Sube un archivo `.html`/`.htm` (máximo 1 MB) **o** pega el código directamente.
4. Opcionalmente sube una imagen de fondo.
5. Usa **Vista previa** en inglés o chino para comprobar el resultado.
6. Asigna la plantilla al certificado en el campo **Plantilla**.

Si subes un archivo, su contenido reemplaza el código existente.

### Variables disponibles

```
code                 certificate_type     applicant
manufacturer         manufacturer_address product
product_description  brand                models
models_text          models_display       models_count
test_parameters      test_standards       test_report
issue_date           expiry_date          status
status_label         validation_url       qr_code
logo                 background           site
t                    page_count           annex_pages
generated_at         year
```

También están disponibles `certificate`/`cert`, `labels`, `language`, `show_parameters`, `has_annex`, `annex_count`, `issue_date_iso` y `expiry_date_iso`.

### Etiquetas y filtros permitidos

- Etiquetas: `{% if %}`, `{% else %}`, `{% endif %}`, `{% for %}`, `{% empty %}`, `{% endfor %}`, `{% with %}`, `{% endwith %}`, `{% comment %}`, `{% endcomment %}`.
- Filtros: `default`, `default_if_none`, `escape`, `date`, `time`, `lower`, `upper`, `title`, `capfirst`, `length`, `join`, `linebreaks`, `linebreaksbr`, `truncatechars`, `truncatewords`, `floatformat`, `yesno`, `striptags`, `cut`, `stringformat`, `add`, `first`, `last`.

### Reglas de seguridad de plantillas

Se rechazan las plantillas que contengan:

- Etiquetas `script`, `iframe`, `object`, `embed`, `form`, `input`, `button`, `textarea`, `select`, `option`, `base` o `link`.
- Controladores de eventos (`onclick`, `onload`, etc.).
- URLs `javascript:`, `vbscript:` o `data:text/html`.
- Recursos externos desde CSS (`@import`, `url(https://...)`) o expresiones CSS.
- Acceso a variables reservadas (`user`, `request`, `settings`, `perms`, etc.) o atributos privados (`__`).
- Etiquetas o filtros no incluidos en la lista permitida.

Los datos del certificado se escapan automáticamente al renderizar.

---

## 7. Idiomas

- **Web pública**: chino (`zh-hans`) e inglés (`en`). Cambio mediante `/i18n/set-language/`.
- **Panel privado**: solo chino e inglés. Cualquier intento de usar otro idioma se normaliza a uno permitido.
- **Formularios de captura de certificados**: etiquetas y ayudas en español.

---

## 8. Validación pública

La única parte del sistema de certificados expuesta es:

```
/verify/
```

Acepta:

- `?q=NUMERO-DE-CERTIFICADO`
- `?code=NUMERO-DE-CERTIFICADO`
- `?token=TOKEN-DEL-QR`
- `?lang=en` o `?lang=zh-hans` para cambiar el idioma del resultado. Cualquier
  otro valor se normaliza al chino.

Resultados posibles: vigente, caducado, suspendido, no encontrado y límite de intentos alcanzado. Cada intento se registra en **Registros de validación** dentro del administrador avanzado.

Las áreas privadas no aparecen en `robots.txt` ni están enlazadas desde la web pública.

---

## 9. Pruebas

```bash
python manage.py test
```

La suite cubre seguridad de plantillas, renderizado, QR, exportación a PDF,
validación pública, límites de intentos, formularios, importación de contraseñas
bcrypt, cambio de idioma, el panel operativo (acceso, certificados, descargas y
usuarios) y el administrador avanzado. En total son **73 pruebas**. Las pruebas
que generan un PDF real se omiten automáticamente si no hay ningún motor de PDF
disponible en el equipo.

Para comprobar la configuración de producción:

```bash
# Linux/macOS
DJANGO_DEBUG=0 \
DJANGO_SECRET_KEY="clave-larga-y-aleatoria" \
DJANGO_ALLOWED_HOSTS="qtecheni.com,www.qtecheni.com" \
SITE_BASE_URL="https://qtecheni.com" \
python manage.py check --deploy
```

```powershell
# Windows PowerShell
$env:DJANGO_DEBUG='0'
$env:DJANGO_SECRET_KEY='clave-larga-y-aleatoria'
$env:DJANGO_ALLOWED_HOSTS='qtecheni.com,www.qtecheni.com'
$env:SITE_BASE_URL='https://qtecheni.com'
python manage.py check --deploy
```

---

## 10. Despliegue en producción

### 10.1 Configuración

1. Copia `.env.example` a `.env` y ajusta:
   - `DJANGO_DEBUG=0`
   - `DJANGO_SECRET_KEY` única y larga
   - `DJANGO_ALLOWED_HOSTS` con el dominio real
   - `DJANGO_CSRF_TRUSTED_ORIGINS=https://qtecheni.com`
   - `SITE_BASE_URL=https://qtecheni.com`
   - `ADMIN_URL_PATH` con una ruta difícil de adivinar
   - `POSTGRES_*` con un usuario de base de datos dedicado (no `postgres`)
2. Si hay un proxy inverso con HTTPS, define `TRUST_PROXY_HEADERS=1`.
3. Configura el correo SMTP real para el formulario de contacto.

### 10.2 Archivos estáticos

```bash
python manage.py collectstatic --noinput
```

En producción se usa `CompressedManifestStaticFilesStorage`, que requiere ejecutar `collectstatic` en cada despliegue.

### 10.3 Migraciones y datos

```bash
python manage.py migrate
python manage.py seed_defaults   # solo la primera vez
python manage.py import_legacy   # solo durante la migración
```

### 10.4 Servidor de aplicación

```bash
gunicorn config.wsgi:application \
  --bind 127.0.0.1:8000 \
  --workers 3 \
  --timeout 120
```

Detrás de Nginx o Traefik, publica solo el puerto de Gunicorn en localhost.

Ejemplo de servicio `systemd` (`/etc/systemd/system/qtech.service`):

```ini
[Unit]
Description=QTech certificates (Django)
After=network.target postgresql.service

[Service]
User=www-data
Group=www-data
WorkingDirectory=/var/www/qtech_django
EnvironmentFile=/var/www/qtech_django/.env
ExecStart=/var/www/qtech_django/.venv/bin/gunicorn config.wsgi:application \
  --bind 127.0.0.1:8000 --workers 3 --timeout 120
Restart=always

[Install]
WantedBy=multi-user.target
```

```bash
sudo systemctl daemon-reload
sudo systemctl enable --now qtech
```

### 10.5 Nginx (ejemplo)

```nginx
server {
    listen 443 ssl http2;
    server_name qtecheni.com www.qtecheni.com;

    ssl_certificate     /etc/letsencrypt/live/qtecheni.com/fullchain.pem;
    ssl_certificate_key /etc/letsencrypt/live/qtecheni.com/privkey.pem;

    client_max_body_size 12m;

    location /static/ {
        alias /var/www/qtech_django/staticfiles/;
        expires 30d;
        add_header Cache-Control "public, immutable";
    }

    location / {
        proxy_pass http://127.0.0.1:8000;
        proxy_set_header Host $host;
        proxy_set_header X-Real-IP $remote_addr;
        proxy_set_header X-Forwarded-For $proxy_add_x_forwarded_for;
        proxy_set_header X-Forwarded-Proto $scheme;
    }
}
```

> **No publiques** `media/` ni `private_media/`. Las imágenes públicas se sirven a través de la aplicación; los fondos y plantillas de certificados son privados.

### 10.6 Lista de verificación de seguridad

- [ ] `DJANGO_DEBUG=0` y `check --deploy` sin advertencias.
- [ ] `DJANGO_SECRET_KEY` única, fuera del control de versiones.
- [ ] HTTPS obligatorio y HSTS activo (configurado automáticamente en producción).
- [ ] Cookies de sesión y CSRF solo por HTTPS.
- [ ] `ADMIN_URL_PATH` distinto de `admin/` y no enlazado públicamente.
- [ ] Panel operativo `/panel/` protegido y con usuarios reales creados.
- [ ] Usuario de PostgreSQL dedicado con permisos mínimos.
- [ ] Copias de seguridad automáticas de PostgreSQL y de `private_media/`.
- [ ] `collectstatic` ejecutado en cada despliegue.
- [ ] Correo SMTP configurado y probado.
- [ ] Exportación a PDF probada en español, inglés y chino (WeasyPrint + fuentes CJK, o Chromium/Edge).
- [ ] Revisar periódicamente **Registros de validación** y **Eventos de certificados**.
- [ ] Mantener actualizadas las dependencias de `requirements.txt`.

> **Nota sobre límites de intentos:** el proyecto usa `LocMemCache`, válido para un solo proceso. Si despliegas varios workers o servidores, configura un backend de caché compartido (por ejemplo Redis) en `CACHES` para que los límites de validación e inicio de sesión sean globales.

---

## 11. Estructura del proyecto

```
qtech_django/
├── apps/
│   ├── accounts/        # Usuarios, roles y contraseñas heredadas de PHP
│   ├── certificates/    # Certificados, plantillas, QR, PDF, validación y auditoría
│   ├── core/            # Web pública, contenido, i18n y utilidades
│   └── panel/           # Panel operativo Bootstrap (certificados, usuarios, actividad)
├── config/              # Configuración, URLs y WSGI/ASGI
├── media/               # Imágenes públicas subidas (no publicar directamente)
├── private_media/       # Plantillas y fondos privados (no publicar)
├── static/              # CSS, JS, imágenes y Bootstrap local (sin CDN)
├── templates/           # Plantillas públicas, del panel y del administrador
├── manage.py
└── requirements.txt
```

El manual de usuario está en [`../docs/MANUAL_USUARIO.md`](../docs/MANUAL_USUARIO.md).

---

## 12. Relación con el sistema PHP anterior

- El código PHP se eliminó del árbol de trabajo para no mantener dos
  implementaciones. Sigue disponible en el historial de Git.
- El sistema Django vive en `qtech_django/`.
- El volcado SQL del sistema anterior se conserva en
  `../legacy/certificaciones_db.sql`.
- Los datos se importan con `python manage.py import_legacy`.
- La exportación a PPTX del sistema anterior se sustituyó por plantillas HTML
  y exportación a PDF/HTML, que cubren el mismo caso de uso sin depender de
  archivos `.pptx`.
