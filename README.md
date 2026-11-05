# Sistema de Certificaciones QTech

Sistema de certificados en **Python/Django + PostgreSQL**. Incluye:

- **Web pública** en chino e inglés, con contenido editable.
- Validación pública de certificados por número o por código QR.
- Panel privado de certificados con auditoría de acciones.
- Plantillas HTML por certificado, con vista previa y exportación a **PDF**.
- Exportación de certificados en HTML autónomo (sin conexión).

## Inicio rápido

```bash
cd qtech_django
python -m pip install -r requirements.txt
cp .env.example .env
python manage.py migrate
python manage.py seed_defaults
python manage.py createsuperuser
python manage.py runserver
```

- Web pública: <http://127.0.0.1:8000/>
- Validación: <http://127.0.0.1:8000/verify/>
- Panel privado: <http://127.0.0.1:8000/control/>

La documentación completa (variables de entorno, importación de datos,
plantillas, seguridad y despliegue) está en
[`qtech_django/README.md`](qtech_django/README.md).

## Producción

Resumen de dependencias del servidor:

```bash
# Debian / Ubuntu
sudo apt install python3 python3-venv python3-pip postgresql \
  libpango-1.0-0 libpangoft2-1.0-0 libharfbuzz-subset0 \
  libfontconfig1 libgdk-pixbuf-2.0-0 fonts-noto-cjk

python -m pip install -r qtech_django/requirements.txt
```

En el README de `qtech_django/` está la lista detallada, la configuración de
Nginx/Gunicorn y la lista de verificación de seguridad.

## Sistema PHP anterior

El sistema PHP anterior se retiró del repositorio para evitar código muerto.
Sigue disponible en el historial de Git y su volcado de base de datos se
conserva en [`legacy/certificaciones_db.sql`](legacy/certificaciones_db.sql)
para ejecutar `python manage.py import_legacy` durante la migración de datos.
