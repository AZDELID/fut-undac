# -*- coding: utf-8 -*-
"""
Orquesta la generación de los archivos finales (.docx y .pdf) a partir
de un FUTData, invocando el script de Node (generar_docx.js) y
LibreOffice para la conversión a PDF.
"""

# -*- coding: utf-8 -*-
"""
Orquesta la generación de los archivos finales (.docx y .pdf) a partir
de un FUTData, usando el generador Python puro (sin dependencia de
Node.js) y LibreOffice para la conversión a PDF.
"""

import re
import shutil
import subprocess
import sys
import unicodedata
from datetime import date
from pathlib import Path

from .generar_docx_py import generar_docx


def _dir_proyecto() -> Path:
    """Determina la carpeta base del proyecto.

    En modo script normal: la carpeta del paquete fut_cli/.
    En modo ejecutable PyInstaller (--onefile): PyInstaller descomprime
    los recursos en una carpeta temporal (sys._MEIPASS) que se borra al
    cerrar el programa, así que la salida NO debe ir ahí. En ese caso
    usamos la carpeta donde está el .exe/binario real.
    """
    if getattr(sys, "frozen", False):
        return Path(sys.executable).resolve().parent
    return Path(__file__).resolve().parent.parent


DIR_PROYECTO = _dir_proyecto()
DIR_SALIDA = DIR_PROYECTO / "output"

# Rutas conocidas donde puede estar el conversor de LibreOffice headless
# usado por el skill de docx en el sandbox de Claude. Si no existe
# (uso normal en la PC del estudiante), se usa 'soffice' del PATH.
_SOFFICE_SCRIPT_SANDBOX = Path("/mnt/skills/public/docx/scripts/office/soffice.py")


class GeneracionError(Exception):
    pass


def _slug(texto: str) -> str:
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(c for c in texto if not unicodedata.combining(c))
    texto = re.sub(r"[^a-zA-Z0-9]+", "_", texto).strip("_").lower()
    return texto or "fut"


def _nombre_archivo(fut) -> str:
    apellido = (fut.nombres_apellidos or "estudiante").split()[0]
    fecha_slug = date.today().strftime("%Y%m%d")
    return f"FUT_{_slug(fut.tramite_clave)}_{_slug(apellido)}_{fecha_slug}"


def _convertir_a_pdf(docx_path: Path, dir_salida: Path) -> Path:
    """Convierte un .docx a .pdf usando LibreOffice headless.
    Detecta automáticamente si está disponible el script del sandbox
    o el binario 'soffice'/'libreoffice' del sistema.

    NOTA IMPORTANTE: 'soffice --headless' puede quedarse colgado para
    siempre (sin devolver el control ni lanzar error) si:
      - ya hay otra instancia de LibreOffice usando el mismo perfil de
        usuario (queda un archivo de bloqueo/lock), o
      - intenta mostrar un diálogo (p. ej. de recuperación tras un
        cierre anterior) que en modo headless nadie puede cerrar.
    Por eso se le pasa SIEMPRE un perfil de usuario temporal y aislado
    (uno nuevo por conversión) y se limita el tiempo de espera con un
    timeout, para que un cuelgue se convierta en un error claro en vez
    de dejar la barra de progreso girando para siempre.
    """
    import tempfile

    pdf_path = docx_path.with_suffix(".pdf")
    perfil_tmp = Path(tempfile.mkdtemp(prefix="fut_undac_soffice_"))
    perfil_uri = perfil_tmp.resolve().as_uri()
    flags_comunes = [
        "--headless", "--norestore", "--nologo", "--nofirststartwizard",
        f"-env:UserInstallation={perfil_uri}",
        "--convert-to", "pdf", "--outdir", str(dir_salida),
    ]

    if _SOFFICE_SCRIPT_SANDBOX.exists():
        cmd = ["python3", str(_SOFFICE_SCRIPT_SANDBOX)] + flags_comunes + [str(docx_path)]
    else:
        binario = shutil.which("soffice") or shutil.which("libreoffice")
        if not binario:
            raise GeneracionError(
                "No se encontró LibreOffice instalado (comando 'soffice' o "
                "'libreoffice'). Instálalo para poder generar PDF, o genera "
                "solo el formato .docx."
            )
        cmd = [binario] + flags_comunes + [str(docx_path)]

    try:
        resultado = subprocess.run(cmd, capture_output=True, text=True, timeout=90)
    except subprocess.TimeoutExpired:
        raise GeneracionError(
            "LibreOffice tardó demasiado y no respondió al convertir a PDF "
            "(más de 90 segundos). Suele pasar si quedó otra instancia de "
            "LibreOffice abierta en segundo plano: ciérrala (o reinicia el "
            "equipo) e inténtalo de nuevo. Mientras tanto puedes generar "
            "solo el formato .docx."
        )
    finally:
        shutil.rmtree(perfil_tmp, ignore_errors=True)

    if resultado.returncode != 0 or not pdf_path.exists():
        raise GeneracionError(f"Error convirtiendo a PDF:\n{resultado.stderr}")
    return pdf_path


def generar_documentos(fut, formatos=("docx", "pdf"), nombre_base=None):
    """Genera el/los archivo(s) solicitados en DIR_SALIDA.

    formatos: tupla con cualquier combinación de "docx", "pdf"
    Devuelve dict {"docx": Path|None, "pdf": Path|None}
    """
    DIR_SALIDA.mkdir(parents=True, exist_ok=True)
    nombre_base = nombre_base or _nombre_archivo(fut)

    docx_path = DIR_SALIDA / f"{nombre_base}.docx"
    pdf_path = DIR_SALIDA / f"{nombre_base}.pdf"

    try:
        generar_docx(fut.to_dict(), str(docx_path))
    except Exception as e:
        raise GeneracionError(f"Error generando .docx: {e}")

    if not docx_path.exists():
        raise GeneracionError("El .docx no se generó correctamente.")

    salida = {"docx": docx_path if "docx" in formatos else None, "pdf": None}

    if "pdf" in formatos:
        salida["pdf"] = _convertir_a_pdf(docx_path, DIR_SALIDA)

    if "docx" not in formatos and docx_path.exists():
        docx_path.unlink(missing_ok=True)
        salida["docx"] = None

    return salida
