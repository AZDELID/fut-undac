# -*- coding: utf-8 -*-
"""
Conector a la API institucional de UNDAC para autocompletar datos
del estudiante a partir de su código de matrícula.

NOTA IMPORTANTE: el campo "Correo Institucional" que devuelve la API
en realidad trae el correo PERSONAL del estudiante (error conocido de
la API), por lo que NUNCA se usa automáticamente sin advertencia: se
marca como "verificar" para que el usuario lo confirme o corrija.
"""

import urllib.request
import urllib.error
import json

BASE_URL = "http://api.undac.edu.pe/tasks/a3945a7384cbdcd33f49e8f5b8ec29f5/91f33e2776c526b9cca723a63476f028"

TIMEOUT_SEGUNDOS = 8


class APIError(Exception):
    pass


def consultar_estudiante(codigo: str) -> dict:
    """Consulta la API institucional por código de matrícula.

    Devuelve un diccionario normalizado:
        {
            "nombres_apellidos": str,
            "dni": str,
            "correo_personal_detectado": str,  # OJO: la API lo llama "institucional" pero NO lo es
            "facultad": str,
            "escuela": str,
            "domicilio": str,
            "fecha_ingreso": str,
            "curricula": str,
            "raw": dict,  # respuesta original sin procesar
        }

    Lanza APIError si la consulta falla o el código no existe.
    """
    codigo = codigo.strip()
    if not codigo.isdigit():
        raise APIError("El código de matrícula debe ser numérico para consultar la API.")

    url = f"{BASE_URL}/{codigo}"
    try:
        req = urllib.request.Request(url, headers={"Accept": "application/json"})
        with urllib.request.urlopen(req, timeout=TIMEOUT_SEGUNDOS) as resp:
            raw_bytes = resp.read()
    except urllib.error.HTTPError as e:
        if e.code == 403:
            raise APIError(
                "La API rechazó la conexión (403 Forbidden). Es posible que "
                "el servicio solo sea accesible desde la red institucional "
                "de UNDAC (wifi del campus o VPN universitaria)."
            )
        if e.code == 404:
            raise APIError(f"Código de matrícula '{codigo}' no encontrado (404).")
        raise APIError(f"La API respondió con error HTTP {e.code}.")
    except urllib.error.URLError as e:
        raise APIError(
            f"No se pudo conectar a la API de UNDAC: {e.reason}. "
            "Verifica tu conexión a internet o si necesitas estar en la "
            "red institucional."
        )
    except TimeoutError:
        raise APIError("La API tardó demasiado en responder (timeout).")
    except Exception as e:
        raise APIError(f"Error inesperado consultando la API: {e}")

    try:
        data = json.loads(raw_bytes.decode("utf-8"))
    except (json.JSONDecodeError, UnicodeDecodeError):
        raise APIError("La API devolvió una respuesta no válida (¿código inexistente?).")

    if not data or "Nombres" not in data:
        raise APIError(f"No se encontraron datos para el código '{codigo}'.")

    apellido_paterno = data.get("Apellido paterno", "").strip()
    apellido_materno = data.get("Apellido materno", "").strip()
    nombres = data.get("Nombres", "").strip()
    nombres_apellidos = f"{apellido_paterno} {apellido_materno} {nombres}".strip()
    nombres_apellidos = " ".join(nombres_apellidos.split())  # normaliza espacios

    return {
        "nombres_apellidos": nombres_apellidos,
        "dni": data.get("Dni", "").strip(),
        # OJO: este campo viene mal nombrado desde la API (es personal, no institucional)
        "correo_personal_detectado": data.get("Correo Institucional", "").strip(),
        "facultad": data.get("Programa facultad", "").strip(),
        "escuela": data.get("Programa facultad", "").strip(),
        "domicilio": data.get("Domicilio", "").strip(),
        "fecha_ingreso": data.get("Fecha de Ingreso", "").strip(),
        "curricula": data.get("Curricula", "").strip(),
        "raw": data,
    }
