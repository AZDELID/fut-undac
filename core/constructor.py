# -*- coding: utf-8 -*-
"""
Construye un FUTData completo combinando:
  - la plantilla del trámite elegido (catalogo.py)
  - los datos concretos del usuario (provenientes del wizard o del DSL)

Aplica el formateo de placeholders {como_este} usando los valores
disponibles, dejando un marcador visible "__FALTA:campo__" si falta
algún dato para que no se pierda silenciosamente.
"""

import re
from .catalogo import obtener_tramite
from .modelo import FUTData
from . import plantilla as plantilla_mod


class ConstructorError(Exception):
    pass


class _DefaultDict(dict):
    """Permite usar str.format_map sin lanzar KeyError; deja un
    marcador visible para los placeholders faltantes."""
    def __missing__(self, key):
        return f"__FALTA:{key}__"


def _formatear(plantilla: str, contexto: dict) -> str:
    texto = plantilla.format_map(_DefaultDict(contexto))
    # Si un placeholder opcional quedó vacío, pueden quedar espacios
    # dobles o un espacio suelto antes de coma/punto (ej. "EGRESADO ,").
    # Limpiamos esos artefactos de formateo sin tocar el contenido real.
    texto = re.sub(r"[ \t]{2,}", " ", texto)
    texto = re.sub(r" +([,.;:])", r"\1", texto)
    return texto


def construir_fut(clave_tramite: str, datos_usuario: dict) -> FUTData:
    """
    datos_usuario: diccionario plano con claves como
        nombres_apellidos, dni, codigo, celular, correo,
        facultad, escuela, especialidad, domicilio,
        cargo_centro_trabajo, anexo, fecha,
        y cualquier campo_extra propio del trámite (ej. periodo, motivo_uso)

    Si datos_usuario incluye 'fundamentacion' con texto no vacío,
    ese texto se usa tal cual (modo libre) en vez de la plantilla
    del trámite.
    """
    tramite = obtener_tramite(clave_tramite)

    contexto = dict(datos_usuario)  # copia
    contexto.setdefault("codigo", "")
    contexto.setdefault("escuela", "")
    contexto.setdefault("facultad", "")
    # Los campos extra marcados como opcionales por el trámite nunca deben
    # quedar como placeholder "__FALTA__" si el usuario no los proporcionó;
    # se tratan como texto vacío válido.
    for campo_opcional in tramite.get("campos_extra_opcionales", []):
        contexto.setdefault(campo_opcional, "")

    fut = FUTData()
    fut.tramite_clave = clave_tramite
    fut.tramite_nombre = tramite["nombre"]

    fut.solicito = _formatear(tramite["solicito"], contexto)
    fut.sumilla = _formatear(tramite["sumilla"], contexto)
    cargo_destinatario_plantilla = plantilla_mod.obtener_plantilla().get("cargo_destinatario", "").strip()
    fut.destinatario = cargo_destinatario_plantilla or _formatear(tramite["destinatario"], contexto)

    fut.nombres_apellidos = datos_usuario.get("nombres_apellidos", "")
    fut.cargo_centro_trabajo = datos_usuario.get("cargo_centro_trabajo", "")
    fut.dni = datos_usuario.get("dni", "")
    fut.codigo = datos_usuario.get("codigo", "")
    fut.celular = datos_usuario.get("celular", "")
    fut.correo = datos_usuario.get("correo", "")
    fut.facultad = datos_usuario.get("facultad", "")
    fut.escuela = datos_usuario.get("escuela", "")
    fut.especialidad = datos_usuario.get("especialidad", "")
    fut.domicilio = datos_usuario.get("domicilio", "")
    fut.anexo = datos_usuario.get("anexo", tramite.get("anexo_sugerido", ""))

    if datos_usuario.get("fecha"):
        fut.fecha = datos_usuario["fecha"]

    texto_libre = datos_usuario.get("fundamentacion", "").strip()
    if texto_libre:
        fut.fundamentacion = texto_libre
    else:
        fut.fundamentacion = _formatear(tramite["fundamentacion_plantilla"], contexto)

    # Guarda los campos extra usados, para trazabilidad / edición posterior
    campos_extra_def = tramite.get("campos_extra", [])
    fut.extra = {c: datos_usuario.get(c, "") for c in campos_extra_def}

    return fut


def campos_faltantes_en_texto(texto: str):
    """Detecta marcadores __FALTA:campo__ dejados por _formatear."""
    return re.findall(r"__FALTA:([a-zA-Z0-9_]+)__", texto or "")
