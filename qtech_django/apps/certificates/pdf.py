"""Generación de certificados en PDF.

Se usa la misma plantilla HTML que la vista previa. Hay dos motores posibles:

* **WeasyPrint**, si la librería y sus dependencias del sistema (Pango,
  HarfBuzz y fuentes CJK) están instaladas.
* **Chromium/Edge en modo headless**, como alternativa cuando WeasyPrint no
  está disponible. En Windows es lo que permite generar PDF sin instalar GTK.

La detección es perezosa: si ningún motor está disponible, el resto del sistema
sigue funcionando y la vista de PDF muestra un error controlado.
"""

from __future__ import annotations

import logging
import os
import shutil
import subprocess
import tempfile
from pathlib import Path

from django.conf import settings

from .models import Certificate
from .rendering import render_certificate_html

logger = logging.getLogger("qtech")

BROWSER_TIMEOUT = 90

_WINDOWS_BROWSERS = (
    r"C:\Program Files (x86)\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Microsoft\Edge\Application\msedge.exe",
    r"C:\Program Files\Google\Chrome\Application\chrome.exe",
    r"C:\Program Files (x86)\Google\Chrome\Application\chrome.exe",
)

_MACOS_BROWSERS = (
    "/Applications/Google Chrome.app/Contents/MacOS/Google Chrome",
    "/Applications/Microsoft Edge.app/Contents/MacOS/Microsoft Edge",
    "/Applications/Chromium.app/Contents/MacOS/Chromium",
)


class PDFRenderError(Exception):
    """Error controlado al generar un PDF."""


def _weasyprint_available() -> bool:
    try:
        import weasyprint  # noqa: F401
    except Exception:  # pragma: no cover - depende de las librerías del sistema
        return False
    return True


def find_browser() -> str | None:
    """Devuelve la ruta de un navegador Chromium disponible, si lo hay."""

    configured = os.environ.get("QTEST_CHROMIUM_PATH", "").strip()
    if configured and Path(configured).is_file():
        return configured

    for name in (
        "msedge",
        "microsoft-edge",
        "google-chrome",
        "google-chrome-stable",
        "chromium",
        "chromium-browser",
    ):
        found = shutil.which(name)
        if found:
            return found

    candidates = _WINDOWS_BROWSERS if os.name == "nt" else _MACOS_BROWSERS
    for path in candidates:
        if Path(path).is_file():
            return path
    return None


def pdf_backend_available() -> bool:
    """Indica si existe algún motor para generar PDF."""

    return _weasyprint_available() or find_browser() is not None


def _render_with_weasyprint(html: str) -> bytes:
    from weasyprint import HTML

    return HTML(string=html, base_url=str(settings.BASE_DIR)).write_pdf()


def _render_with_browser(html: str, browser: str) -> bytes:
    """Convierte el HTML a PDF con Chromium/Edge en modo headless."""

    with tempfile.TemporaryDirectory(prefix="qtech-pdf-") as temp_dir:
        temp = Path(temp_dir)
        html_path = temp / "certificate.html"
        pdf_path = temp / "certificate.pdf"
        profile_path = temp / "profile"
        html_path.write_text(html, encoding="utf-8")

        command = [
            browser,
            "--headless=new",
            "--disable-gpu",
            "--no-sandbox",
            "--disable-dev-shm-usage",
            "--no-pdf-header-footer",
            f"--user-data-dir={profile_path}",
            f"--print-to-pdf={pdf_path}",
            html_path.as_uri(),
        ]
        creationflags = getattr(subprocess, "CREATE_NO_WINDOW", 0)
        result = subprocess.run(
            command,
            capture_output=True,
            timeout=BROWSER_TIMEOUT,
            creationflags=creationflags,
            check=False,
        )
        if result.returncode != 0 or not pdf_path.is_file():
            stderr = result.stderr.decode("utf-8", errors="replace")[-500:]
            raise PDFRenderError(
                f"El navegador no pudo generar el PDF (código {result.returncode}). "
                f"{stderr}".strip()
            )
        return pdf_path.read_bytes()


def render_certificate_pdf(certificate: Certificate, lang: str = "en") -> bytes:
    """Renderiza el certificado y devuelve los bytes del PDF.

    Se usa la misma plantilla HTML que la vista previa, por lo que cualquier
    cambio en la plantilla se refleja automáticamente en el PDF.
    """

    html = render_certificate_html(certificate, lang=lang)
    errors: list[str] = []

    if _weasyprint_available():
        try:
            return _render_with_weasyprint(html)
        except Exception as exc:  # pragma: no cover - depende del servidor
            errors.append(f"WeasyPrint: {exc}")
            logger.warning(
                "WeasyPrint falló para el certificado %s; se intenta el navegador",
                certificate.code,
                exc_info=True,
            )

    browser = find_browser()
    if browser:
        try:
            return _render_with_browser(html, browser)
        except Exception as exc:  # pragma: no cover - depende del servidor
            errors.append(f"Navegador: {exc}")
            logger.exception(
                "El navegador no pudo generar el PDF del certificado %s",
                certificate.code,
            )

    detail = " | ".join(errors) if errors else "no hay motor de PDF instalado"
    raise PDFRenderError(
        "No se pudo generar el PDF. Instale WeasyPrint (Pango) o un navegador "
        f"Chromium/Edge en el servidor. Detalle: {detail}"
    )
