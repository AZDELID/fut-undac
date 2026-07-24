# -*- coding: utf-8 -*-
"""
Gestión de la plantilla institucional del FUT (encabezado y pie de
página del documento generado).

Permite personalizar, sin tocar código, los textos que el generador
de .docx usa para el encabezado (nombre de la institución, subtítulo)
y el pie de página (dirección, año/período académico, texto libre).

Se guarda en ~/.fut_undac/plantilla.json — de forma análoga a
core/perfil.py — para que los cambios persistan entre ejecuciones.
"""

import json
from pathlib import Path

DIR_CONFIG = Path.home() / ".fut_undac"
RUTA_PLANTILLA = DIR_CONFIG / "plantilla.json"


def plantilla_por_defecto() -> dict:
    """Valores originales de fábrica (los que trae el proyecto)."""
    return {
        # ---- Encabezado ----
        "encabezado_personalizado": "",
        "nombre_institucion": "UNIVERSIDAD NACIONAL DANIEL ALCIDES CARRIÓN",
        "subtitulo": "FORMULARIO ÚNICO DE TRÁMITE",
        "mostrar_logo_undac": True,
        "mostrar_logo_escuela": False,
        "logo_escuela_path": "",
        # ---- Número de expediente / folio ----
        "mostrar_numero_expediente": False,
        "prefijo_expediente": "N° EXP.",
        # ---- Fecha y lugar ----
        "mostrar_fecha_lugar": False,
        "lugar_predeterminado": "Cerro de Pasco",
        # ---- Destinatario ----
        "cargo_destinatario": "",
        # ---- Datos del estudiante en el encabezado ----
        "mostrar_datos_estudiante": False,
        # ---- Pie de página ----
        "direccion": "Jr. 28 de Julio S/N, Cerro de Pasco, Pasco, Perú",
        "anio_periodo": "2026",
        "texto_pie": "Oficina de Trámite Documentario — UNDAC",
        "mostrar_pie": True,
        "color_pie": "6b7280",
        # Lema oficial del año en curso (Perú). Se puede activar/desactivar
        # y editar libremente, ya que el gobierno lo cambia cada año.
        "mostrar_lema_anio": True,
        "lema_anio": "Año de la Esperanza y el Fortalecimiento de la Democracia",
        # ---- Otros ----
        "mostrar_marca_agua": True,
    }


CAMPOS_PLANTILLA = list(plantilla_por_defecto().keys())

# Logos de escuela/facultad incluidos de fábrica con el proyecto, para que
# el usuario pueda elegirlos desde la GUI sin tener que buscar el archivo
# en su equipo. La clave es el nombre visible; el valor es la ruta relativa
# dentro de data/.
LOGOS_INCLUIDOS = {
    "Ingeniería de Sistemas": "logos/sistemas_logo.png",
}


def ruta_logo_incluido(nombre_archivo_relativo: str):
    """Resuelve un nombre relativo (p.ej. 'logos/sistemas_logo.png') a una
    ruta absoluta dentro de data/. Devuelve None si no existe."""
    base = Path(__file__).resolve().parent.parent / "data"
    ruta = base / nombre_archivo_relativo
    return ruta if ruta.exists() else None


def _asegurar_directorio():
    DIR_CONFIG.mkdir(parents=True, exist_ok=True)


def obtener_plantilla() -> dict:
    """Devuelve la configuración actual, combinando lo guardado con los
    valores por defecto (por si se agregan campos nuevos en el futuro)."""
    base = plantilla_por_defecto()
    if RUTA_PLANTILLA.exists():
        try:
            with open(RUTA_PLANTILLA, "r", encoding="utf-8") as f:
                guardado = json.load(f)
            base.update({k: v for k, v in guardado.items() if k in base})
        except (json.JSONDecodeError, OSError):
            pass
    return base


def guardar_plantilla(datos: dict) -> Path:
    """Guarda la configuración de plantilla (encabezado/pie de página)."""
    _asegurar_directorio()
    actual = plantilla_por_defecto()
    actual.update({k: datos.get(k, actual[k]) for k in CAMPOS_PLANTILLA})
    with open(RUTA_PLANTILLA, "w", encoding="utf-8") as f:
        json.dump(actual, f, ensure_ascii=False, indent=2)
    return RUTA_PLANTILLA


def restaurar_plantilla() -> Path:
    """Elimina la configuración guardada, volviendo a los valores de fábrica."""
    if RUTA_PLANTILLA.exists():
        RUTA_PLANTILLA.unlink()
    return RUTA_PLANTILLA
