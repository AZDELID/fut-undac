# -*- coding: utf-8 -*-
"""
Configuración de campos del FUT (etiquetas visibles y alias del DSL).

Antes, la etiqueta de cada campo ("Apellidos y Nombres" para
`nombres_apellidos`) estaba escrita directamente dentro de `gui.py`, y
los alias del modo experto ("nombre" -> `nombres_apellidos`) estaban
escritos dentro de `core/dsl.py`. Para cambiar cualquiera de las dos
cosas había que editar código Python.

Este módulo mueve esa información a un archivo de datos
(`data/campos_config.json`) y expone funciones para leerlo y
modificarlo. El CLI (`main.py campos ...`) usa estas funciones, así
que renombrar un campo o agregar un alias ya no requiere tocar
ningún archivo `.py`.

Estructura de cada campo en el JSON:
    {
        "clave": "nombres_apellidos",   # nombre interno (atributo de FUTData) - NO se renombra
        "etiqueta": "Apellidos y Nombres",  # texto que ve el usuario en GUI/wizard/resúmenes
        "obligatorio": true,
        "placeholder": "ESPINOZA BENAVIDES LUIS PABLO",
        "validador": null,              # clave dentro de VALIDADORES en core/modelo.py
        "ayuda": "Primero apellidos, luego nombres tal como figuran en tu DNI",
        "alias": ["nombre", "nombres", "apellidos_y_nombres", "nombres_y_apellidos"]
    }
"""

import json
from pathlib import Path

RUTA_CONFIG = Path(__file__).resolve().parent.parent / "data" / "campos_config.json"


# Valores de fábrica: lo que traía el sistema antes de tener config editable.
# Se usan para crear el archivo la primera vez y como referencia si el JSON
# llega a faltar un campo nuevo del modelo.
CAMPOS_DEFAULT = [
    {"clave": "nombres_apellidos", "etiqueta": "Apellidos y Nombres", "obligatorio": True,
     "placeholder": "ESPINOZA BENAVIDES LUIS PABLO", "validador": None,
     "ayuda": "Primero apellidos, luego nombres tal como figuran en tu DNI",
     "alias": ["nombre", "nombres", "apellidos_y_nombres", "nombres_y_apellidos"]},
    {"clave": "dni", "etiqueta": "D.N.I.", "obligatorio": True,
     "placeholder": "71447115", "validador": "dni",
     "ayuda": "8 dígitos numéricos", "alias": []},
    {"clave": "codigo", "etiqueta": "Código de Matrícula", "obligatorio": True,
     "placeholder": "2304403050", "validador": "codigo",
     "ayuda": "Código numérico de 6 a 12 dígitos",
     "alias": ["cod", "codigo_matricula", "codigo_de_matricula"]},
    {"clave": "celular", "etiqueta": "N° Celular", "obligatorio": True,
     "placeholder": "987654321", "validador": "celular",
     "ayuda": "9 dígitos, debe comenzar con 9",
     "alias": ["tel", "telefono", "celular_telf"]},
    {"clave": "correo", "etiqueta": "Correo Electrónico", "obligatorio": True,
     "placeholder": "pablo@undac.edu.pe", "validador": "correo",
     "ayuda": "Usa tu correo institucional @undac.edu.pe",
     "alias": ["email", "correo_electronico"]},
    {"clave": "facultad", "etiqueta": "Facultad", "obligatorio": True,
     "placeholder": "Ingeniería de Sistemas y Computación", "validador": None,
     "ayuda": "", "alias": []},
    {"clave": "escuela", "etiqueta": "Escuela Profesional", "obligatorio": True,
     "placeholder": "Ingeniería de Sistemas", "validador": None,
     "ayuda": "", "alias": []},
    {"clave": "especialidad", "etiqueta": "Especialidad", "obligatorio": False,
     "placeholder": "Sistemas de Información", "validador": None,
     "ayuda": "Opcional — deja en blanco si no aplica", "alias": []},
    {"clave": "domicilio", "etiqueta": "Domicilio", "obligatorio": True,
     "placeholder": "Jr. 28 de Julio, Cerro de Pasco, Pasco", "validador": None,
     "ayuda": "Calle, Distrito, Provincia y Región", "alias": []},
    {"clave": "cargo_centro_trabajo", "etiqueta": "Cargo / Centro de Trabajo", "obligatorio": False,
     "placeholder": "Estudiante", "validador": None,
     "ayuda": "Opcional — solo si trabajas actualmente",
     "alias": ["cargo", "centro_trabajo"]},
    {"clave": "fundamentacion", "etiqueta": "Fundamentación del Pedido", "obligatorio": True,
     "placeholder": "", "validador": None, "ayuda": "",
     "alias": ["fundamentacion_del_pedido", "fundamento"]},
]


class CamposError(Exception):
    pass


def _asegurar_archivo():
    if not RUTA_CONFIG.exists():
        RUTA_CONFIG.parent.mkdir(parents=True, exist_ok=True)
        guardar_campos(CAMPOS_DEFAULT)


def cargar_campos() -> list:
    """Devuelve la lista de campos configurados (crea el archivo con los
    valores por defecto si todavía no existe)."""
    _asegurar_archivo()
    with open(RUTA_CONFIG, "r", encoding="utf-8") as f:
        return json.load(f)


def guardar_campos(campos: list):
    RUTA_CONFIG.parent.mkdir(parents=True, exist_ok=True)
    with open(RUTA_CONFIG, "w", encoding="utf-8") as f:
        json.dump(campos, f, ensure_ascii=False, indent=2)


def obtener_campo(clave: str, campos: list = None) -> dict:
    campos = campos if campos is not None else cargar_campos()
    for c in campos:
        if c["clave"] == clave:
            return c
    raise CamposError(f"No existe ningún campo interno llamado '{clave}'.")


def renombrar_etiqueta(clave: str, nueva_etiqueta: str) -> dict:
    """Cambia el texto visible de un campo (lo que ve el usuario en el
    formulario), SIN tocar el nombre interno (`clave`), que es el que usa
    el resto del código (FUTData, plantillas, validadores)."""
    campos = cargar_campos()
    campo = obtener_campo(clave, campos)
    campo["etiqueta"] = nueva_etiqueta
    guardar_campos(campos)
    return campo


def agregar_alias(alias: str, clave: str) -> dict:
    """Agrega una palabra alternativa que el modo DSL aceptará como
    equivalente a `clave` (ej: alias='nombre', clave='nombres_apellidos')."""
    campos = cargar_campos()
    campo = obtener_campo(clave, campos)
    alias_norm = _normalizar(alias)
    for c in campos:
        if alias_norm in [_normalizar(a) for a in c.get("alias", [])] or alias_norm == c["clave"]:
            raise CamposError(
                f"'{alias}' ya está en uso como alias/clave de '{c['clave']}'."
            )
    campo.setdefault("alias", []).append(alias_norm)
    guardar_campos(campos)
    return campo


def quitar_alias(alias: str) -> str:
    campos = cargar_campos()
    alias_norm = _normalizar(alias)
    for c in campos:
        if alias_norm in c.get("alias", []):
            c["alias"].remove(alias_norm)
            guardar_campos(campos)
            return c["clave"]
    raise CamposError(f"El alias '{alias}' no existe en ningún campo.")


def obtener_aliases_dsl() -> dict:
    """{alias_normalizado: clave_interna} para todos los campos, listo
    para que core/dsl.py lo use al interpretar el modo experto."""
    resultado = {}
    for c in cargar_campos():
        for a in c.get("alias", []):
            resultado[_normalizar(a)] = c["clave"]
    return resultado


def campos_config_gui() -> list:
    """Devuelve tuplas (clave, etiqueta, obligatorio, placeholder,
    validador, ayuda) en el orden que espera gui.py (CAMPOS_CONFIG)."""
    return [
        (c["clave"], c["etiqueta"], c["obligatorio"], c["placeholder"],
         c["validador"], c["ayuda"])
        for c in cargar_campos()
    ]


def _normalizar(texto: str) -> str:
    import re
    import unicodedata
    texto = texto.strip().lower()
    texto = unicodedata.normalize("NFKD", texto)
    texto = "".join(ch for ch in texto if not unicodedata.combining(ch))
    return re.sub(r"[^a-z0-9]+", "_", texto).strip("_")
