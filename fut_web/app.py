#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
FUT-UNDAC — versión web (Flask)
Réplica de la interfaz de escritorio (gui.py) para poder publicarla en
Render u otro hosting. Reutiliza el mismo motor de generación de
documentos (core/) que la app de escritorio.
"""
import os
import io
import uuid
import zipfile
import tempfile
from pathlib import Path

# IMPORTANTE: en entornos serverless (Vercel) el código de la app se
# despliega en un filesystem de solo lectura; únicamente /tmp es
# escribible. core/perfil.py y core/plantilla.py calculan su carpeta de
# guardado con Path.home() AL IMPORTARSE, así que forzamos HOME=/tmp
# *antes* de importarlos para que apunten a una ruta escribible en
# cualquier entorno (Vercel, Render, local).
os.environ.setdefault("HOME", tempfile.gettempdir())

from flask import (
    Flask, render_template, request, redirect, url_for,
    session, send_file, jsonify, abort
)

from core.catalogo import CATALOGO, listar_tramites, obtener_tramite
from core.campos import campos_config_gui
from core.constructor import construir_fut, campos_faltantes_en_texto
from core.modelo import validar_campo, ValidationError
from core import generador
from core.generador import generar_documentos, GeneracionError
from core import perfil as perfil_mod
from core import api_undac

APP_DIR = Path(__file__).resolve().parent

# Redirige también la carpeta de salida de documentos a /tmp: en Vercel
# es lo único escribible; en Render/local también funciona igual.
OUTPUT_DIR = Path(tempfile.gettempdir()) / "fut_undac_output"
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)
generador.DIR_SALIDA = OUTPUT_DIR

app = Flask(__name__)
# En producción define SECRET_KEY como variable de entorno. Si no está
# definida usamos una fija por defecto (no aleatoria): en serverless cada
# "cold start" es un proceso nuevo, y una clave aleatoria distinta en cada
# uno invalidaría la sesión del usuario a mitad del formulario.
app.secret_key = os.environ.get("SECRET_KEY", "fut-undac-clave-por-defecto-cambiame")

ICONOS = {
    "constancia_matricula":    "📋",
    "constancia_no_adeudar":   "✅",
    "constancia_egresado":     "🎓",
    "traslado_interno":        "🔄",
    "traslado_externo":        "🚀",
    "convalidacion":           "📚",
    "reserva_matricula":       "📅",
    "rectificacion_notas":     "✏️",
    "carta_presentacion":      "📄",
    "devolucion_documentos":   "📦",
    "duplicado_carne":         "🪪",
    "subsanacion_actas":       "📝",
    "otro":                    "⚙️",
}

FRECUENTES = ["constancia_matricula", "constancia_no_adeudar",
              "carta_presentacion", "constancia_egresado",
              "traslado_interno", "convalidacion"]

CAMPOS_CONFIG = [f for f in campos_config_gui() if f[0] != "fundamentacion"]
ANCHO_COMPLETO = {"nombres_apellidos", "domicilio", "cargo_centro_trabajo"}


def _tramites_catalogo():
    items = []
    for clave, nombre in listar_tramites():
        items.append({
            "clave": clave,
            "nombre": nombre,
            "icono": ICONOS.get(clave, "📄"),
            "frecuente": clave in FRECUENTES,
        })
    items.sort(key=lambda t: (not t["frecuente"], t["nombre"]))
    return items


@app.route("/")
def index():
    q = request.args.get("q", "").strip().lower()
    tramites = _tramites_catalogo()
    if q:
        tramites = [t for t in tramites if q in t["nombre"].lower()]
    return render_template("index.html", tramites=tramites, q=q,
                            total=len(CATALOGO))


@app.route("/tramite/<clave>", methods=["GET", "POST"])
def datos_personales(clave):
    try:
        tramite = obtener_tramite(clave)
    except KeyError:
        abort(404)

    sesion_key = f"fut_datos_{clave}"
    datos_sesion = session.get(sesion_key, {})

    if request.method == "POST":
        datos = {}
        errores = {}
        for campo_clave, etiqueta, obligatorio, _ej, validador, _ayuda in CAMPOS_CONFIG:
            valor = request.form.get(campo_clave, "").strip()
            if obligatorio and not valor:
                errores[campo_clave] = f"'{etiqueta}' es obligatorio."
            elif valor and validador:
                try:
                    valor = validar_campo(campo_clave, valor)
                except ValidationError as e:
                    errores[campo_clave] = str(e)
            datos[campo_clave] = valor

        for campo in tramite.get("campos_extra", []):
            datos[campo] = request.form.get(campo, "").strip()
            opcionales = set(tramite.get("campos_extra_opcionales", []))
            if campo not in opcionales and not datos[campo]:
                errores[campo] = "Este dato es obligatorio para el trámite."

        datos["anexo"] = request.form.get("anexo", "").strip() or tramite.get("anexo_sugerido", "")

        if errores:
            datos_sesion.update(datos)
            session[sesion_key] = datos_sesion
            perfiles = perfil_mod.listar_perfiles()
            return render_template(
                "datos.html", tramite=tramite, clave=clave,
                campos=CAMPOS_CONFIG, datos=datos_sesion, errores=errores,
                ancho_completo=ANCHO_COMPLETO,
                perfil=perfiles[0] if perfiles else {},
            )

        if request.form.get("guardar_perfil"):
            perfil_mod.guardar_perfil(datos)

        datos_sesion.update(datos)
        session[sesion_key] = datos_sesion
        return redirect(url_for("fundamentacion", clave=clave))

    perfiles = perfil_mod.listar_perfiles()
    perfil_guardado = perfiles[0] if perfiles else {}
    return render_template(
        "datos.html", tramite=tramite, clave=clave,
        campos=CAMPOS_CONFIG, datos=datos_sesion, errores={},
        ancho_completo=ANCHO_COMPLETO, perfil=perfil_guardado,
    )


@app.route("/tramite/<clave>/autocompletar")
def autocompletar_api(clave):
    codigo = request.args.get("codigo", "").strip()
    if not codigo:
        return jsonify({"ok": False, "error": "Ingresa un código de matrícula."})
    try:
        info = api_undac.consultar_estudiante(codigo)
    except api_undac.APIError as e:
        return jsonify({"ok": False, "error": str(e)})
    return jsonify({"ok": True, "datos": info})


@app.route("/tramite/<clave>/fundamentacion", methods=["GET", "POST"])
def fundamentacion(clave):
    try:
        tramite = obtener_tramite(clave)
    except KeyError:
        abort(404)

    sesion_key = f"fut_datos_{clave}"
    datos_sesion = session.get(sesion_key)
    if not datos_sesion:
        return redirect(url_for("datos_personales", clave=clave))

    fut_previo = construir_fut(clave, {**datos_sesion, "fundamentacion": ""})
    sugerida = fut_previo.fundamentacion
    faltantes = campos_faltantes_en_texto(sugerida)

    if request.method == "POST":
        texto = request.form.get("fundamentacion", "").strip()
        if not texto:
            return render_template(
                "fundamentacion.html", tramite=tramite, clave=clave,
                sugerida=sugerida, faltantes=faltantes,
                error="La fundamentación no puede quedar vacía.",
                valor=texto,
            )
        datos_sesion["fundamentacion"] = texto
        session[sesion_key] = datos_sesion
        return redirect(url_for("vista_previa", clave=clave))

    valor = datos_sesion.get("fundamentacion") or sugerida
    return render_template(
        "fundamentacion.html", tramite=tramite, clave=clave,
        sugerida=sugerida, faltantes=faltantes, error=None, valor=valor,
    )


@app.route("/tramite/<clave>/preview")
def vista_previa(clave):
    try:
        tramite = obtener_tramite(clave)
    except KeyError:
        abort(404)

    sesion_key = f"fut_datos_{clave}"
    datos_sesion = session.get(sesion_key)
    if not datos_sesion or not datos_sesion.get("fundamentacion"):
        return redirect(url_for("datos_personales", clave=clave))

    fut = construir_fut(clave, datos_sesion)
    return render_template("preview.html", tramite=tramite, clave=clave, fut=fut)


@app.route("/tramite/<clave>/generar", methods=["POST"])
def generar(clave):
    """Genera el documento y lo devuelve como descarga en la MISMA
    petición (no lo deja guardado en disco para servirlo después).
    Esto es imprescindible en entornos serverless (Vercel): cada
    request puede caer en una instancia distinta, así que no se puede
    confiar en que un archivo escrito en una petición siga existiendo
    en la siguiente."""
    try:
        tramite = obtener_tramite(clave)
    except KeyError:
        abort(404)

    sesion_key = f"fut_datos_{clave}"
    datos_sesion = session.get(sesion_key)
    if not datos_sesion or not datos_sesion.get("fundamentacion"):
        return redirect(url_for("datos_personales", clave=clave))

    formato = request.form.get("formato", "docx")
    fut = construir_fut(clave, datos_sesion)
    nombre_base = f"FUT_{uuid.uuid4().hex[:8]}"

    try:
        salida = generar_documentos(fut, formatos=("docx",), nombre_base=nombre_base)
        docx_path = salida["docx"]
        docx_bytes = docx_path.read_bytes()
    except GeneracionError as e:
        return render_template("preview.html", tramite=tramite, clave=clave,
                                fut=fut, error_generacion=str(e))
    finally:
        _limpiar(docx_path.parent if 'docx_path' in dir() else None)

    nombre_descarga = f"FUT_{clave}"

    if formato == "docx":
        return send_file(io.BytesIO(docx_bytes), as_attachment=True,
                          download_name=f"{nombre_descarga}.docx",
                          mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document")

    # pdf o ambos: requieren LibreOffice instalado en el servidor.
    # No disponible en el deploy simple de Vercel/Render Python — solo
    # en el deploy con el Dockerfile incluido (que trae LibreOffice).
    try:
        pdf_bytes = _convertir_docx_a_pdf_bytes(docx_bytes, nombre_base)
    except GeneracionError as e:
        if formato == "pdf":
            return render_template("preview.html", tramite=tramite, clave=clave,
                                    fut=fut, error_generacion=str(e))
        # "ambos" con PDF no disponible -> entrega solo el Word igual.
        return send_file(io.BytesIO(docx_bytes), as_attachment=True,
                          download_name=f"{nombre_descarga}.docx",
                          mimetype="application/vnd.openxmlformats-officedocument.wordprocessingml.document")

    if formato == "pdf":
        return send_file(io.BytesIO(pdf_bytes), as_attachment=True,
                          download_name=f"{nombre_descarga}.pdf", mimetype="application/pdf")

    # ambos -> un .zip con los dos archivos
    buf = io.BytesIO()
    with zipfile.ZipFile(buf, "w", zipfile.ZIP_DEFLATED) as z:
        z.writestr(f"{nombre_descarga}.docx", docx_bytes)
        z.writestr(f"{nombre_descarga}.pdf", pdf_bytes)
    buf.seek(0)
    return send_file(buf, as_attachment=True,
                      download_name=f"{nombre_descarga}.zip", mimetype="application/zip")


def _convertir_docx_a_pdf_bytes(docx_bytes: bytes, nombre_base: str) -> bytes:
    from core.generador import _convertir_a_pdf
    carpeta = OUTPUT_DIR / f"pdf_{uuid.uuid4().hex[:8]}"
    carpeta.mkdir(parents=True, exist_ok=True)
    docx_path = carpeta / f"{nombre_base}.docx"
    docx_path.write_bytes(docx_bytes)
    try:
        pdf_path = _convertir_a_pdf(docx_path, carpeta)
        return pdf_path.read_bytes()
    finally:
        _limpiar(carpeta)


def _limpiar(carpeta):
    if not carpeta:
        return
    import shutil
    shutil.rmtree(carpeta, ignore_errors=True)


@app.route("/tramite/<clave>/reiniciar")
def reiniciar(clave):
    session.pop(f"fut_datos_{clave}", None)
    session.pop(f"fut_resultado_{clave}", None)
    return redirect(url_for("index"))


@app.route("/salud")
def salud():
    return {"status": "ok", "tramites": len(CATALOGO)}


if __name__ == "__main__":
    port = int(os.environ.get("PORT", 5000))
    app.run(host="0.0.0.0", port=port, debug=True)
