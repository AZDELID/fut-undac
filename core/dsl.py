# -*- coding: utf-8 -*-
"""
DSL (mini-lenguaje) para el modo experto del generador de FUT.

Gramática (informal, por línea):

    FUT: <clave_tramite>
    CAMPO: valor
    CAMPO: ' triple-comilla '
    texto
    multilinea
    ' triple-comilla '
    # comentario (se ignora)

Reglas:
  - La primera línea NO comentada debe ser "FUT: <clave>".
  - Cada línea siguiente es "CLAVE: valor".
  - Las claves pueden ser los nombres de FUTData o las claves de
    "campos_extra" definidas por el trámite en el catálogo.
  - Para texto largo (ej. FUNDAMENTACION) se admite bloque multilínea
    delimitado por comillas triples \"\"\" ... \"\"\".
  - Las claves no distinguen mayúsculas/minúsculas ni tildes/espacios:
    "Nombres y Apellidos" -> "nombres_apellidos".
  - Líneas vacías o que empiezan con # se ignoran.

Ejemplo:

    FUT: constancia_matricula
    NOMBRES_APELLIDOS: Pablo Ramos Ore
    DNI: 71447115
    CODIGO: 2304403050
    FACULTAD: Ingeniería de Sistemas y Computación
    ESCUELA: Ingeniería de Sistemas
    DOMICILIO: 28 de Julio, Cerro de Pasco
    PERIODO: 2026-I
    MOTIVO_USO: trámite de beca
"""

import re
import unicodedata

from core.campos import obtener_aliases_dsl


class DSLError(Exception):
    pass


def _normalizar_clave(clave: str) -> str:
    clave = clave.strip().lower()
    clave = unicodedata.normalize("NFKD", clave)
    clave = "".join(c for c in clave if not unicodedata.combining(c))
    clave = re.sub(r"[^a-z0-9]+", "_", clave).strip("_")
    return clave


def _cargar_aliases() -> dict:
    """Alias comunes -> nombre de campo interno en FUTData.

    Se leen desde data/campos_config.json (editable con
    `python main.py campos alias ...`), no están escritos aquí. Esto
    permite agregar/quitar alias sin tocar este archivo .py.
    """
    return obtener_aliases_dsl()


def parsear_dsl(texto: str) -> dict:
    """Parsea el texto del DSL y devuelve un diccionario plano
    {clave_normalizada: valor}. Incluye 'fut' con la clave del trámite.

    Lanza DSLError si el formato es inválido.
    """
    if not texto or not texto.strip():
        raise DSLError("El bloque DSL está vacío.")

    lineas = texto.splitlines()
    resultado = {}

    i = 0
    n = len(lineas)

    # Saltar comentarios/vacíos iniciales
    while i < n and (not lineas[i].strip() or lineas[i].strip().startswith("#")):
        i += 1

    if i >= n:
        raise DSLError("No se encontró contenido en el DSL.")

    primera = lineas[i].strip()
    m = re.match(r'^FUT\s*:\s*(.+)$', primera, re.IGNORECASE)
    if not m:
        raise DSLError(
            "La primera línea debe declarar el trámite con 'FUT: <clave_tramite>'. "
            f"Se encontró: '{primera}'"
        )
    resultado["fut"] = _normalizar_clave(m.group(1))
    i += 1

    aliases = _cargar_aliases()

    while i < n:
        linea = lineas[i]
        cruda = linea.strip()
        if not cruda or cruda.startswith("#"):
            i += 1
            continue

        m = re.match(r'^([^:]+):\s*(.*)$', linea)
        if not m:
            raise DSLError(f"Línea inválida (se esperaba 'CLAVE: valor'): '{linea}'")

        clave_raw, valor = m.group(1), m.group(2)
        clave = _normalizar_clave(clave_raw)
        clave = aliases.get(clave, clave)

        # Bloque multilínea con comillas triples
        if valor.strip().startswith('"""'):
            resto_primera = valor.strip()[3:]
            bloque = [resto_primera] if resto_primera else []
            i += 1
            cerrado = resto_primera.endswith('"""') and len(resto_primera) >= 3
            if cerrado:
                bloque[-1] = bloque[-1][:-3]
            else:
                while i < n:
                    if lineas[i].strip().endswith('"""'):
                        contenido = lineas[i].rstrip()
                        contenido = contenido[: contenido.rfind('"""')]
                        bloque.append(contenido)
                        i += 1
                        cerrado = True
                        break
                    bloque.append(lineas[i])
                    i += 1
                if not cerrado:
                    raise DSLError(f"Bloque multilínea de '{clave_raw}' no fue cerrado con \"\"\".")
            resultado[clave] = "\n".join(bloque).strip()
            continue

        resultado[clave] = valor.strip()
        i += 1

    if "fut" not in resultado or not resultado["fut"]:
        raise DSLError("Falta declarar 'FUT: <clave_tramite>' al inicio.")

    return resultado


def ejemplo_dsl(clave_tramite: str = "constancia_matricula") -> str:
    """Genera un ejemplo de DSL usable, útil para mostrarle al usuario
    cómo se escribe el modo experto."""
    return f'''FUT: {clave_tramite}
NOMBRES_APELLIDOS: Pablo Ramos Ore
DNI: 71447115
CODIGO: 2304403050
CELULAR: 987654321
CORREO: pablo.ramos@undac.edu.pe
FACULTAD: Ingeniería de Sistemas y Computación
ESCUELA: Ingeniería de Sistemas
DOMICILIO: Jr. 28 de Julio, Cerro de Pasco, Pasco
PERIODO: 2026-I
MOTIVO_USO: trámite de beca
ANEXO: Copia de DNI, recibo de pago
FUNDAMENTACION: """
Texto libre opcional. Si lo omites, el sistema usa la plantilla
del trámite y completa los espacios con los datos de arriba.
"""
'''
