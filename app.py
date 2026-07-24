#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FUT-UNDAC Web — versión web (Flask) del asistente de FUT.

Reutiliza toda la lógica ya existente en core/ (catálogo, construcción
del FUT, generación de .docx) y agrega, opcionalmente, redacción
automática de la fundamentación con IA (AWS Bedrock) si hay
credenciales configuradas como variables de entorno.

Ejecutar en local:
    python app.py

En Render, el Procfile ya apunta a:
    gunicorn app:app
"""

import os
import uuid
from io import BytesIO

from flask import Flask, render_template, request, redirect, url_for, send_file, jsonify

from core.catalogo import listar_tramites, obtener_tramite
from core.constructor import construir_fut
from core.modelo import validar_campo, ValidationError
from core.generador import generar_documentos, GeneracionError
from core import campos as campos_mod
from core import api_undac

IA_DISPONIBLE = True
try:
    from core.ia_aws import generar_fundamentacion, BedrockError
except Exception:
    IA_DISPONIBLE = False
    BedrockError = Exception

app = Flask(__name__)
app.secret_key = os.environ.get("SECRET_KEY", "dev-secret-cambia-en-produccion")

# Etiquetas amigables para los campos "extra" de cada trámite (no vienen
# en core/campos.py porque ese archivo solo cubre los campos base).
ETIQUETAS_EXTRA = {
    "periodo": "Periodo académico",
    "motivo_uso": "Motivo de uso",
    "area_adeudo": "Área (Biblioteca, Economía, etc.)",
    "facultad_destino": "Facultad de destino",
    "escuela_destino": "Escuela de destino",
    "motivo_traslado": "Motivo del traslado",
    "universidad_origen": "Universidad de origen",
    "cursos_convalidar": "Cursos a convalidar",
    "motivo_reserva": "Motivo de la reserva",
    "curso_nombre": "Nombre del curso",
    "docente": "Docente",
    "empresa": "Empresa / Institución",
    "cargo_practicas": "Cargo / Área de prácticas",
    "documento_a_devolver": "Documento a devolver",
    "motivo_devolucion": "Motivo de la devolución",
    "motivo_duplicado": "Motivo del duplicado",
    "acta_curso": "Curso del acta",
    "acta_periodo": "Periodo del acta",
    "solicito_libre": "SOLICITO (texto libre)",
    "sumilla_libre": "Sumilla (texto libre)",
    "destinatario_libre": "Destinatario (texto libre)",
    "fundamentacion_libre": "Motivo del pedido (texto libre)",
}


def etiqueta_extra(clave):
    return ETIQUETAS_EXTRA.get(clave, clave.replace("_", " ").capitalize())


def _campos_extra_de(tramite):
    return [{"clave": c, "etiqueta": etiqueta_extra(c)} for c in tramite.get("campos_extra", [])]


def _render_formulario(clave, errores=None, valores=None):
    tramite = obtener_tramite(clave)
    return render_template(
        "formulario.html",
        clave=clave,
        tramite=tramite,
        campos_base=campos_mod.cargar_campos(),
        campos_extra=_campos_extra_de(tramite),
        ia_disponible=IA_DISPONIBLE,
        errores=errores or [],
        valores=valores or {},
    )


@app.route("/")
def index():
    return render_template("index.html", tramites=listar_tramites())


@app.route("/tramite/<clave>")
def formulario(clave):
    try:
        obtener_tramite(clave)
    except KeyError:
        return redirect(url_for("index"))
    return _render_formulario(clave)


@app.route("/api/autocompletar/<codigo>")
def api_autocompletar(codigo):
    try:
        datos = api_undac.consultar_estudiante(codigo)
        return jsonify({"ok": True, "datos": datos})
    except api_undac.APIError as e:
        return jsonify({"ok": False, "error": str(e)}), 400


@app.route("/api/fundamentacion", methods=["POST"])
def api_fundamentacion():
    if not IA_DISPONIBLE:
        return jsonify({"ok": False, "error": "La redacción con IA no está disponible en este servidor."}), 400
    data = request.get_json(force=True) or {}
    try:
        texto = generar_fundamentacion(
            data.get("tramite_clave", ""),
            data,
            data.get("descripcion_libre", ""),
        )
        return jsonify({"ok": True, "texto": texto})
    except BedrockError as e:
        return jsonify({"ok": False, "error": str(e)}), 500


@app.route("/generar", methods=["POST"])
def generar():
    form = request.form.to_dict()
    clave = form.get("tramite_clave", "")
    try:
        obtener_tramite(clave)
    except KeyError:
        return redirect(url_for("index"))

    errores = []
    for c in campos_mod.cargar_campos():
        valor = (form.get(c["clave"], "") or "").strip()
        if c["obligatorio"] and not valor:
            errores.append(f"Falta completar: {c['etiqueta']}")
        elif valor and c.get("validador"):
            try:
                validar_campo(c["clave"], valor)
            except ValidationError as e:
                errores.append(str(e))

    if errores:
        return _render_formulario(clave, errores=errores, valores=form)

    fut = construir_fut(clave, form)
    try:
        salida = generar_documentos(
            fut,
            formatos=("docx",),
            nombre_base=f"FUT_{clave}_{uuid.uuid4().hex[:8]}",
        )
    except GeneracionError as e:
        return _render_formulario(clave, errores=[f"Error al generar el documento: {e}"], valores=form)

    docx_path = salida["docx"]
    contenido = docx_path.read_bytes()
    try:
        docx_path.unlink()
    except OSError:
        pass

    return send_file(
        BytesIO(contenido),
        as_attachment=True,
        download_name=f"{docx_path.stem}.docx",
        mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
    )


@app.errorhandler(404)
def no_encontrado(e):
    return render_template("404.html"), 404


if __name__ == "__main__":
    puerto = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=puerto, debug=True)
