# Legado del sistema PHP

Esta carpeta solo conserva el volcado SQL necesario para migrar los datos del
sistema PHP anterior al sistema Django:

- `certificaciones_db.sql`: esquema y datos de la base `certificaciones_db`.

El código PHP (`index.php`, `login.php`, `dashboard.php`, `generar_pdf.php`,
`vendor/`, etc.) se eliminó del árbol de trabajo porque el sistema Django ya
cubre sus funciones. Si necesitas consultarlo, está en el historial de Git:

```bash
git log --all --full-history -- "*.php"
git show <commit>:generar_pdf.php
```

## Importar los datos

1. Restaura el volcado en PostgreSQL:

   ```bash
   createdb certificaciones_db
   psql certificaciones_db < legacy/certificaciones_db.sql
   ```

2. Configura `LEGACY_DB_*` en `qtech_django/.env`.

3. Ejecuta:

   ```bash
   cd qtech_django
   python manage.py import_legacy --dry-run
   python manage.py import_legacy
   ```

Cuando la migración esté validada, puedes archivar esta carpeta fuera del
servidor de producción.
