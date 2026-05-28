"""Extraccion de texto de archivos PDF.

Aisla el uso de la libreria pypdf para que el resto del codigo no dependa de ella.
"""
import io

from pypdf import PdfReader


class PdfError(Exception):
    """Error al leer o extraer texto de un PDF."""


def extract_text(data: bytes) -> str:
    """Extrae todo el texto de un PDF (recibido como bytes) y lo devuelve limpio."""
    try:
        reader = PdfReader(io.BytesIO(data))
    except Exception as exc:  # pypdf lanza varios tipos de error
        raise PdfError(f"No se pudo leer el PDF: {exc}") from exc

    partes: list[str] = []
    for pagina in reader.pages:
        texto = pagina.extract_text() or ""
        if texto.strip():
            partes.append(texto.strip())

    texto_completo = "\n\n".join(partes).strip()

    if not texto_completo:
        raise PdfError(
            "El PDF no contiene texto extraible "
            "(puede ser un PDF escaneado/imagen; haria falta OCR)."
        )

    return texto_completo
