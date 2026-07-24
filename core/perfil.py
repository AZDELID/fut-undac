# -*- coding: utf-8 -*-
"""
Gestión de perfiles locales del estudiante (datos persistentes entre usos).

Se guarda en ~/.fut_undac/perfiles/<codigo>.json para no tener que
reescribir nombre, DNI, facultad, etc. cada vez que se genera un FUT.
"""

import json
import os
from pathlib import Path

DIR_PERFILES = Path.home() / ".fut_undac" / "perfiles"

CAMPOS_PERFIL = [
    "nombres_apellidos", "dni", "codigo", "celular", "correo",
    "facultad", "escuela", "especialidad", "domicilio",
]


def _asegurar_directorio():
    DIR_PERFILES.mkdir(parents=True, exist_ok=True)


def ruta_perfil(codigo: str) -> Path:
    return DIR_PERFILES / f"{codigo.strip()}.json"


def guardar_perfil(datos: dict):
    """Guarda solo los campos persistentes de perfil, indexado por código."""
    codigo = datos.get("codigo", "").strip()
    if not codigo:
        return None
    _asegurar_directorio()
    perfil = {k: datos.get(k, "") for k in CAMPOS_PERFIL}
    ruta = ruta_perfil(codigo)
    with open(ruta, "w", encoding="utf-8") as f:
        json.dump(perfil, f, ensure_ascii=False, indent=2)
    return ruta


def cargar_perfil(codigo: str):
    ruta = ruta_perfil(codigo)
    if not ruta.exists():
        return None
    with open(ruta, "r", encoding="utf-8") as f:
        return json.load(f)


def listar_perfiles():
    _asegurar_directorio()
    perfiles = []
    for archivo in DIR_PERFILES.glob("*.json"):
        try:
            with open(archivo, "r", encoding="utf-8") as f:
                data = json.load(f)
                perfiles.append(data)
        except (json.JSONDecodeError, OSError):
            continue
    return perfiles


def perfil_existe(codigo: str) -> bool:
    return ruta_perfil(codigo).exists()
