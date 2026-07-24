# -*- coding: utf-8 -*-
"""
Modo experto: procesa un bloque DSL (texto plano con sintaxis
'FUT: clave' + 'CAMPO: valor') y genera el FUT, mostrando errores
claros si algo falta o está mal formado.
"""

from rich.console import Console
from rich.panel import Panel
from rich.syntax import Syntax

from .dsl import parsear_dsl, DSLError, ejemplo_dsl
from .catalogo import CATALOGO, obtener_tramite
from .constructor import construir_fut, campos_faltantes_en_texto
from .modelo import validar_campo, ValidationError, CAMPOS_OBLIGATORIOS_BASE

console = Console()


def mostrar_ayuda_dsl():
    console.print(Panel.fit(
        "[bold]Modo experto (DSL)[/bold]\n"
        "Escribe (o pega) un bloque con la sintaxis CAMPO: valor.\n"
        "La primera línea siempre declara el trámite: FUT: <clave>\n\n"
        "Trámites disponibles: " + ", ".join(CATALOGO.keys()),
        border_style="cyan"
    ))
    console.print(Syntax(ejemplo_dsl(), "yaml", theme="ansi_dark", word_wrap=True))


def procesar_dsl_texto(texto: str):
    """Parsea el texto DSL, construye el FUT y valida.
    Devuelve (fut, errores) — errores es lista vacía si todo OK.
    Lanza DSLError si el formato del DSL es inválido (no si faltan datos)."""
    datos = parsear_dsl(texto)
    clave_tramite = datos.pop("fut")

    if clave_tramite not in CATALOGO:
        disponibles = ", ".join(CATALOGO.keys())
        raise DSLError(
            f"Trámite '{clave_tramite}' no existe en el catálogo.\n"
            f"Disponibles: {disponibles}"
        )

    errores = []

    # Validar campos con validador específico (dni, codigo, celular, correo)
    for campo in ("dni", "codigo", "celular", "correo"):
        if campo in datos and datos[campo]:
            try:
                datos[campo] = validar_campo(campo, datos[campo])
            except ValidationError as e:
                errores.append(f"{campo}: {e}")

    fut = construir_fut(clave_tramite, datos)

    # Verificar campos obligatorios base
    for campo in CAMPOS_OBLIGATORIOS_BASE:
        if campo == "tramite_clave":
            continue
        valor = getattr(fut, campo, "")
        if not valor or not str(valor).strip():
            errores.append(f"Falta el campo obligatorio: {campo}")

    # Verificar placeholders sin completar en los textos generados
    for campo_texto in ("solicito", "sumilla", "destinatario", "fundamentacion"):
        faltan = campos_faltantes_en_texto(getattr(fut, campo_texto))
        for f in faltan:
            errores.append(f"Falta el dato '{f}' usado en el campo '{campo_texto}'")

    return fut, errores


def ejecutar_modo_experto_desde_archivo(ruta_archivo: str):
    with open(ruta_archivo, "r", encoding="utf-8") as f:
        texto = f.read()
    return procesar_dsl_texto(texto)
