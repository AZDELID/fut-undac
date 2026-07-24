# -*- coding: utf-8 -*-
"""
Modelo de datos del FUT (Formulario Único de Trámite) UNDAC.

FUTData es la estructura única que llenan tanto el wizard interactivo
como el parser del DSL. El generador de documentos (Word/PDF) consume
siempre un objeto FUTData, sin importar cómo se haya construido.
"""

import re
from dataclasses import dataclass, field, asdict
from datetime import date

MESES_ES = {
    1: "enero", 2: "febrero", 3: "marzo", 4: "abril", 5: "mayo", 6: "junio",
    7: "julio", 8: "agosto", 9: "septiembre", 10: "octubre", 11: "noviembre", 12: "diciembre",
}


def fecha_hoy_es():
    hoy = date.today()
    return f"{hoy.day} de {MESES_ES[hoy.month]} de {hoy.year}"


CAMPOS_OBLIGATORIOS_BASE = [
    "tramite_clave", "nombres_apellidos", "dni", "codigo",
    "facultad", "escuela", "domicilio", "fundamentacion",
]


@dataclass
class FUTData:
    # Trámite
    tramite_clave: str = ""
    tramite_nombre: str = ""

    # Cabecera
    solicito: str = ""
    sumilla: str = ""
    destinatario: str = ""

    # Datos del usuario
    nombres_apellidos: str = ""
    cargo_centro_trabajo: str = ""
    dni: str = ""
    codigo: str = ""
    celular: str = ""
    correo: str = ""
    facultad: str = ""
    escuela: str = ""
    especialidad: str = ""
    domicilio: str = ""

    # Cuerpo
    fundamentacion: str = ""
    anexo: str = ""

    # Cierre
    fecha: str = field(default_factory=fecha_hoy_es)
    lugar: str = "Cerro de Pasco"

    # Extras dinámicos del trámite (placeholders propios de cada plantilla)
    extra: dict = field(default_factory=dict)

    def to_dict(self):
        return asdict(self)


# ---------------------------------------------------------------------------
# Validaciones
# ---------------------------------------------------------------------------

class ValidationError(Exception):
    pass


def validar_dni(valor):
    valor = valor.strip()
    if not re.fullmatch(r"\d{8}", valor):
        raise ValidationError("El DNI debe tener exactamente 8 dígitos numéricos.")
    return valor


def validar_codigo(valor):
    valor = valor.strip()
    if not re.fullmatch(r"\d{6,12}", valor):
        raise ValidationError("El código de matrícula debe ser numérico (6 a 12 dígitos).")
    return valor


def validar_celular(valor):
    valor = valor.strip().replace(" ", "")
    if not re.fullmatch(r"9\d{8}", valor):
        raise ValidationError("El celular debe tener 9 dígitos y empezar con 9 (ej: 987654321).")
    return valor


def validar_correo(valor):
    valor = valor.strip()
    if not re.fullmatch(r"[^@\s]+@[^@\s]+\.[^@\s]+", valor):
        raise ValidationError("El correo no tiene un formato válido.")
    return valor


def validar_no_vacio(valor, nombre_campo):
    if not valor or not valor.strip():
        raise ValidationError(f"El campo '{nombre_campo}' no puede estar vacío.")
    return valor.strip()


VALIDADORES = {
    "dni": validar_dni,
    "codigo": validar_codigo,
    "celular": validar_celular,
    "correo": validar_correo,
}


def validar_campo(nombre_campo, valor):
    """Aplica el validador específico si existe; si no, solo verifica no-vacío
    para los campos marcados como obligatorios."""
    if nombre_campo in VALIDADORES:
        return VALIDADORES[nombre_campo](valor)
    return valor.strip() if valor else valor


def validar_fut_completo(fut: FUTData):
    """Verifica que los campos obligatorios base estén presentes y válidos.
    Devuelve lista de errores (vacía si todo está OK)."""
    errores = []
    data = fut.to_dict()
    for campo in CAMPOS_OBLIGATORIOS_BASE:
        valor = data.get(campo, "")
        try:
            validar_campo(campo, valor)
            if not valor or not str(valor).strip():
                errores.append(f"Falta completar: {campo}")
        except ValidationError as e:
            errores.append(f"{campo}: {e}")
    return errores
