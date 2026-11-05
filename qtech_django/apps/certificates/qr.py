"""Generación de códigos QR para los certificados."""

from __future__ import annotations

import base64
from functools import lru_cache
from io import BytesIO

import qrcode
from qrcode.constants import ERROR_CORRECT_M


def make_qr_png(data: str) -> bytes:
    qr = qrcode.QRCode(
        version=None,
        error_correction=ERROR_CORRECT_M,
        box_size=10,
        border=2,
    )
    qr.add_data(data)
    qr.make(fit=True)
    image = qr.make_image(fill_color="black", back_color="white")
    buffer = BytesIO()
    image.save(buffer, format="PNG")
    return buffer.getvalue()


@lru_cache(maxsize=512)
def make_qr_data_uri(data: str) -> str:
    png = make_qr_png(data)
    return "data:image/png;base64," + base64.b64encode(png).decode("ascii")
