# -*- coding: utf-8 -*-
"""
core/ia_aws.py — Motor de IA para el FUT-UNDAC usando AWS Bedrock.

Tres funcionalidades principales:
  1. generar_fundamentacion()  — redacta el texto legal personalizado
  2. detectar_tramite()        — identifica el trámite desde lenguaje natural
  3. chat_asistente()          — responde preguntas del estudiante

Requiere:
  pip install boto3
  aws configure  (Access Key + Secret Key + región us-east-1)
  Activar Claude Sonnet en AWS Bedrock > Model access
"""

import json
import re
from typing import Optional

# Modelo recomendado: Claude Sonnet 4.5 en Bedrock.
# IMPORTANTE: en Bedrock hay que usar el ID completo del "inference profile"
# (con el prefijo de región y el sufijo de fecha/versión); el ID corto
# "us.anthropic.claude-sonnet-4-5" no existe y provoca
# ResourceNotFoundException al llamar a invoke_model.
MODELO_ID = "us.anthropic.claude-sonnet-4-5-20250929-v1:0"

# Alternativa más barata si quieres reducir costos:
# MODELO_ID = "us.anthropic.claude-haiku-4-5-20251001-v1:0"

REGION = "us-east-1"

# Contexto institucional que se inyecta en cada llamada
CONTEXTO_UNDAC = """
Eres un asistente especializado en trámites universitarios de la 
Universidad Nacional Daniel Alcides Carrión (UNDAC), ubicada en 
Cerro de Pasco, Perú. Ayudas a los estudiantes a redactar el 
Formulario Único de Trámite (FUT) con lenguaje legal-formal 
correcto según la normativa universitaria peruana.

Reglas importantes:
- Responde siempre en español formal
- Usa el lenguaje jurídico-administrativo apropiado para trámites universitarios peruanos
- Los textos deben empezar con "Que, el suscrito..." para fundamentaciones
- Sé preciso y conciso, sin texto innecesario
- Conoces el Reglamento General de la UNDAC y la Ley Universitaria 30220
"""

TRAMITES_DISPONIBLES = [
    "constancia_matricula", "constancia_no_adeudar", "constancia_egresado",
    "traslado_interno", "traslado_externo", "convalidacion",
    "reserva_matricula", "rectificacion_notas", "carta_presentacion",
    "devolucion_documentos", "duplicado_carne", "subsanacion_actas", "otro"
]


class BedrockError(Exception):
    """Error al conectar o usar AWS Bedrock."""
    pass


def _get_client():
    """Crea el cliente de Bedrock. Lanza BedrockError con mensaje claro si falla."""
    try:
        import boto3
    except ImportError:
        raise BedrockError(
            "boto3 no está instalado. Ejecuta:\n  pip install boto3"
        )

    try:
        import boto3
        client = boto3.client("bedrock-runtime", region_name=REGION)
        return client
    except Exception as e:
        raise BedrockError(
            f"No se pudo conectar a AWS Bedrock.\n"
            f"Verifica que hayas ejecutado 'aws configure' con tus credenciales.\n"
            f"Error: {e}"
        )


def _llamar_bedrock(prompt_sistema: str, prompt_usuario: str,
                    max_tokens: int = 1024, temperatura: float = 0.3) -> str:
    """
    Llama a Claude en AWS Bedrock y retorna el texto de respuesta.
    temperatura baja (0.1-0.3) = más formal y consistente (ideal para texto legal)
    temperatura alta (0.7-1.0) = más creativo (ideal para chat)
    """
    client = _get_client()

    cuerpo = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": max_tokens,
        "temperature": temperatura,
        "system": prompt_sistema,
        "messages": [
            {"role": "user", "content": prompt_usuario}
        ]
    }

    try:
        respuesta = client.invoke_model(
            modelId=MODELO_ID,
            body=json.dumps(cuerpo),
            contentType="application/json",
            accept="application/json"
        )
        resultado = json.loads(respuesta["body"].read())
        return resultado["content"][0]["text"].strip()

    except Exception as e:
        error_str = str(e)
        if "AccessDeniedException" in error_str:
            raise BedrockError(
                "Acceso denegado al modelo. Asegúrate de haber activado "
                f"'{MODELO_ID}' en AWS Bedrock > Model access."
            )
        if "ResourceNotFoundException" in error_str:
            raise BedrockError(
                f"Modelo '{MODELO_ID}' no encontrado. "
                "Verifica que esté disponible en la región us-east-1."
            )
        if "ThrottlingException" in error_str:
            raise BedrockError(
                "Demasiadas solicitudes a AWS. Espera unos segundos e intenta de nuevo."
            )
        raise BedrockError(f"Error al llamar a Bedrock: {e}")


# ─────────────────────────────────────────────────────────────
# FUNCIÓN 1: Generar fundamentación legal
# ─────────────────────────────────────────────────────────────

def generar_fundamentacion(
    tipo_tramite: str,
    datos_estudiante: dict,
    descripcion_libre: str = "",
) -> str:
    """
    Genera el texto de fundamentación del FUT usando IA.

    Args:
        tipo_tramite: clave del trámite (ej. "constancia_matricula")
        datos_estudiante: dict con nombres_apellidos, codigo, escuela, etc.
        descripcion_libre: texto que el estudiante escribió describiendo su situación

    Returns:
        Texto de fundamentación redactado formalmente, listo para el FUT.
    """
    from .catalogo import obtener_tramite
    try:
        tramite = obtener_tramite(tipo_tramite)
        nombre_tramite = tramite["nombre"]
    except KeyError:
        nombre_tramite = tipo_tramite.replace("_", " ").title()

    nombre      = datos_estudiante.get("nombres_apellidos", "el suscrito")
    codigo      = datos_estudiante.get("codigo", "")
    escuela     = datos_estudiante.get("escuela", "")
    facultad    = datos_estudiante.get("facultad", "")
    periodo     = datos_estudiante.get("periodo", "")
    domicilio   = datos_estudiante.get("domicilio", "")

    # Campos extra relevantes según el trámite
    extras = {k: v for k, v in datos_estudiante.items()
              if k not in {"nombres_apellidos","codigo","escuela","facultad",
                           "dni","celular","correo","domicilio","especialidad",
                           "cargo_centro_trabajo","anexo","fundamentacion","periodo"}
              and v and str(v).strip()}

    extras_texto = ""
    if extras:
        extras_texto = "Datos adicionales del trámite:\n"
        for k, v in extras.items():
            extras_texto += f"  - {k.replace('_',' ').capitalize()}: {v}\n"

    descripcion_texto = ""
    if descripcion_libre.strip():
        descripcion_texto = f"""
El estudiante describe su situación así (en sus propias palabras):
\"{descripcion_libre.strip()}\"

Usa esta información para personalizar y enriquecer la fundamentación.
"""

    prompt_usuario = f"""
Redacta la FUNDAMENTACIÓN DEL PEDIDO para el siguiente FUT universitario.

TIPO DE TRÁMITE: {nombre_tramite}

DATOS DEL ESTUDIANTE:
- Apellidos y nombres: {nombre}
- Código de matrícula: {codigo}
- Escuela Profesional: {escuela}
- Facultad: {facultad}
- Periodo académico: {periodo or "vigente"}
{extras_texto}
{descripcion_texto}

INSTRUCCIONES DE FORMATO:
- Empieza EXACTAMENTE con: "Que, el suscrito, identificado con código de matrícula {codigo},"
- Usa lenguaje jurídico-administrativo formal peruano
- Menciona el nombre del trámite en MAYÚSCULAS dentro del texto
- Termina SIEMPRE con: "Por lo expuesto, solicito acceder a mi pedido por ser de justicia."
- Longitud: 3-5 oraciones. No uses viñetas ni listas.
- Devuelve SOLO el texto de la fundamentación, sin títulos ni encabezados.
"""

    return _llamar_bedrock(
        prompt_sistema=CONTEXTO_UNDAC,
        prompt_usuario=prompt_usuario,
        max_tokens=512,
        temperatura=0.2   # Bajo para texto legal consistente
    )


# ─────────────────────────────────────────────────────────────
# FUNCIÓN 2: Detectar trámite desde lenguaje natural
# ─────────────────────────────────────────────────────────────

def detectar_tramite(texto_usuario: str) -> dict:
    """
    Identifica el trámite que necesita el estudiante desde texto libre.

    Args:
        texto_usuario: Lo que el estudiante escribió (ej. "necesito un papel
                       que diga que estoy matriculado para mi beca")

    Returns:
        dict con:
          - tramite_clave: str (ej. "constancia_matricula")
          - tramite_nombre: str (ej. "Constancia de matrícula")
          - datos_extraidos: dict con campos detectados en el texto
          - confianza: str ("alta", "media", "baja")
          - mensaje: str explicando la detección al usuario
    """
    lista_tramites = "\n".join(f"- {c}" for c in TRAMITES_DISPONIBLES)

    prompt_usuario = f"""
Un estudiante universitario de la UNDAC escribió lo siguiente:
"{texto_usuario}"

Analiza su solicitud e identifica:
1. ¿Qué trámite universitario necesita?
2. ¿Qué datos relevantes mencionó?

Responde SOLO con un JSON válido con esta estructura exacta:
{{
  "tramite_clave": "una_de_las_claves_de_abajo",
  "tramite_nombre": "Nombre legible del trámite",
  "datos_extraidos": {{
    "campo": "valor extraído del texto (solo si está explícito)"
  }},
  "confianza": "alta|media|baja",
  "mensaje": "Explicación breve en español para mostrarle al estudiante"
}}

Claves válidas de trámites:
{lista_tramites}

Si no puedes identificar el trámite con certeza, usa "otro" y explica en "mensaje".
Responde ÚNICAMENTE con el JSON, sin texto adicional.
"""

    respuesta = _llamar_bedrock(
        prompt_sistema=CONTEXTO_UNDAC,
        prompt_usuario=prompt_usuario,
        max_tokens=400,
        temperatura=0.1   # Muy bajo para detección precisa
    )

    # Limpiar y parsear JSON
    texto_json = respuesta.strip()
    # Remover bloques de código si los hay
    texto_json = re.sub(r"```(?:json)?", "", texto_json).strip()

    try:
        resultado = json.loads(texto_json)
        # Validar que tenga los campos necesarios
        if "tramite_clave" not in resultado:
            raise ValueError("Falta tramite_clave en la respuesta")
        if resultado["tramite_clave"] not in TRAMITES_DISPONIBLES:
            resultado["tramite_clave"] = "otro"
        return resultado
    except (json.JSONDecodeError, ValueError):
        # Si falla el parseo, retornar respuesta conservadora
        return {
            "tramite_clave": "otro",
            "tramite_nombre": "Trámite no identificado",
            "datos_extraidos": {},
            "confianza": "baja",
            "mensaje": "No pude identificar el trámite con certeza. "
                       "Por favor selecciónalo manualmente de la lista."
        }


# ─────────────────────────────────────────────────────────────
# FUNCIÓN 3: Chat de asistencia al estudiante
# ─────────────────────────────────────────────────────────────

def chat_asistente(
    pregunta: str,
    historial: Optional[list] = None,
    tramite_actual: Optional[str] = None,
) -> str:
    """
    Responde preguntas del estudiante sobre trámites universitarios.

    Args:
        pregunta: Lo que el estudiante pregunta
        historial: Lista de dicts {"rol": "user"|"assistant", "texto": str}
                   para mantener contexto de la conversación
        tramite_actual: Clave del trámite que está haciendo (para dar contexto)

    Returns:
        Respuesta del asistente como texto.
    """
    contexto_tramite = ""
    if tramite_actual:
        try:
            from .catalogo import obtener_tramite
            t = obtener_tramite(tramite_actual)
            contexto_tramite = f"""
El estudiante está actualmente realizando el trámite: {t['nombre']}.
Documentos sugeridos para este trámite: {t.get('anexo_sugerido', 'no especificado')}.
"""
        except Exception:
            pass

    sistema = CONTEXTO_UNDAC + contexto_tramite + """
Responde de forma amigable pero profesional. 
Si la pregunta es sobre documentos, requisitos o procedimientos, sé específico.
Si no sabes algo con certeza, dilo claramente y sugiere consultar con la oficina correspondiente.
Respuestas cortas y directas (máximo 3-4 oraciones salvo que sea necesario más).
"""

    # Construir mensajes con historial
    mensajes = []
    if historial:
        for msg in historial[-6:]:  # Últimos 6 mensajes para no exceder tokens
            rol_bedrock = "user" if msg.get("rol") == "user" else "assistant"
            mensajes.append({"role": rol_bedrock, "content": msg["texto"]})

    mensajes.append({"role": "user", "content": pregunta})

    client = _get_client()

    cuerpo = {
        "anthropic_version": "bedrock-2023-05-31",
        "max_tokens": 600,
        "temperature": 0.6,   # Más conversacional
        "system": sistema,
        "messages": mensajes
    }

    try:
        respuesta = client.invoke_model(
            modelId=MODELO_ID,
            body=json.dumps(cuerpo),
            contentType="application/json",
            accept="application/json"
        )
        resultado = json.loads(respuesta["body"].read())
        return resultado["content"][0]["text"].strip()
    except Exception as e:
        raise BedrockError(f"Error en chat: {e}")


# ─────────────────────────────────────────────────────────────
# FUNCIÓN AUXILIAR: verificar conexión
# ─────────────────────────────────────────────────────────────

def verificar_conexion() -> dict:
    """
    Verifica que AWS Bedrock esté configurado correctamente.
    Retorna dict con {"ok": bool, "mensaje": str, "modelo": str}
    """
    try:
        respuesta = _llamar_bedrock(
            prompt_sistema="Eres un asistente de prueba.",
            prompt_usuario="Responde solo con: OK",
            max_tokens=10,
            temperatura=0.0
        )
        return {
            "ok": True,
            "mensaje": f"Conexión exitosa con AWS Bedrock.",
            "modelo": MODELO_ID,
            "respuesta_prueba": respuesta
        }
    except BedrockError as e:
        return {
            "ok": False,
            "mensaje": str(e),
            "modelo": MODELO_ID,
            "respuesta_prueba": None
        }
