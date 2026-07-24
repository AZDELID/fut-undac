# -*- coding: utf-8 -*-
"""
Catálogo de trámites para el FUT de la UNDAC.

Cada trámite trae plantillas pre-redactadas para los campos más difíciles
de llenar para un estudiante (SOLICITO, SUMILLA, DESTINATARIO,
FUNDAMENTACIÓN), usando placeholders entre llaves {como_este} que se
completan con los datos del usuario o que el usuario edita directamente.

Para añadir un trámite nuevo basta con agregar una entrada a CATALOGO.
"""

CATALOGO = {

    "constancia_matricula": {
        "nombre": "Constancia de matrícula",
        "solicito": "CONSTANCIA DE MATRÍCULA",
        "sumilla": "Solicito constancia de matrícula del periodo académico {periodo}.",
        "destinatario": "Sr./Sra. Decano(a) de la Facultad de {facultad}",
        "anexo_sugerido": "Recibo de pago por derecho de constancia, copia de DNI",
        "fundamentacion_plantilla": (
            "Que, el suscrito, identificado con código de matrícula {codigo}, "
            "matriculado en la Escuela Profesional de {escuela}, periodo académico "
            "{periodo}, solicita se sirva expedir la CONSTANCIA DE MATRÍCULA "
            "correspondiente, para los fines de {motivo_uso}.\n\n"
            "Por lo expuesto, solicito acceder a mi pedido por ser de justicia."
        ),
        "ayuda": (
            "Indica para qué necesitas la constancia (ej: 'trámites de beca', "
            "'postulación a prácticas', 'presentación ante entidad bancaria')."
        ),
        "campos_extra": ["periodo", "motivo_uso"],
    },

    "constancia_no_adeudar": {
        "nombre": "Constancia de no adeudar (biblioteca/economía)",
        "solicito": "CONSTANCIA DE NO ADEUDAR",
        "sumilla": "Solicito constancia de no adeudar material bibliográfico ni bienes a la institución.",
        "destinatario": "Sr./Sra. Responsable de {area_adeudo}",
        "anexo_sugerido": "Carné universitario, recibo de pago",
        "fundamentacion_plantilla": (
            "Que, el suscrito, identificado con código de matrícula {codigo}, "
            "estudiante de la Escuela Profesional de {escuela}, solicita se sirva "
            "expedir la CONSTANCIA DE NO ADEUDAR correspondiente al área de "
            "{area_adeudo}, para los fines de {motivo_uso}.\n\n"
            "Por lo expuesto, solicito acceder a mi pedido por ser de justicia."
        ),
        "ayuda": "Especifica el área (Biblioteca Central, Economía, Bienestar Universitario, etc.) y el motivo.",
        "campos_extra": ["area_adeudo", "motivo_uso"],
    },

    "constancia_egresado": {
        "nombre": "Constancia de egresado / tercio-quinto superior",
        "solicito": "CONSTANCIA DE EGRESADO",
        "sumilla": "Solicito constancia de egresado y/o ubicación en tercio/quinto superior.",
        "destinatario": "Sr./Sra. Decano(a) de la Facultad de {facultad}",
        "anexo_sugerido": "Récord académico, copia de DNI",
        "fundamentacion_plantilla": (
            "Que, el suscrito, identificado con código de matrícula {codigo}, "
            "habiendo concluido satisfactoriamente el plan curricular de la "
            "Escuela Profesional de {escuela}, solicita se sirva expedir la "
            "CONSTANCIA DE EGRESADO {tercio_quinto_texto}, para los fines de "
            "{motivo_uso}.\n\n"
            "Por lo expuesto, solicito acceder a mi pedido por ser de justicia."
        ),
        "ayuda": (
            "Indica si también necesitas que conste tu ubicación en tercio o "
            "quinto superior (responde algo como 'y mi ubicación en el tercio "
            "superior' o deja en blanco si solo necesitas la constancia de "
            "egresado), y para qué la usarás."
        ),
        "campos_extra": ["tercio_quinto_texto", "motivo_uso"],
        "campos_extra_opcionales": ["tercio_quinto_texto"],
    },

    "traslado_interno": {
        "nombre": "Traslado interno (entre facultades/escuelas)",
        "solicito": "TRASLADO INTERNO",
        "sumilla": "Solicito traslado interno de la Escuela Profesional de {escuela_origen} a la Escuela Profesional de {escuela_destino}.",
        "destinatario": "Sr./Sra. Rector(a) de la Universidad Nacional Daniel Alcides Carrión",
        "anexo_sugerido": "Récord académico, certificado de estudios, copia de DNI, recibo de pago",
        "fundamentacion_plantilla": (
            "Que, el suscrito, identificado con código de matrícula {codigo}, "
            "actualmente matriculado en la Escuela Profesional de {escuela_origen}, "
            "solicita se autorice su TRASLADO INTERNO a la Escuela Profesional de "
            "{escuela_destino}, por motivos de {motivo_traslado}, cumpliendo con "
            "los requisitos académicos y administrativos establecidos en el "
            "Reglamento de la Universidad.\n\n"
            "Por lo expuesto, solicito acceder a mi pedido por ser de justicia."
        ),
        "ayuda": "Indica la escuela de origen, la de destino y el motivo del cambio (vocacional, rendimiento, etc.).",
        "campos_extra": ["escuela_origen", "escuela_destino", "motivo_traslado"],
    },

    "traslado_externo": {
        "nombre": "Traslado externo (de otra universidad)",
        "solicito": "TRASLADO EXTERNO",
        "sumilla": "Solicito traslado externo procedente de {universidad_origen} a la Escuela Profesional de {escuela}.",
        "destinatario": "Sr./Sra. Rector(a) de la Universidad Nacional Daniel Alcides Carrión",
        "anexo_sugerido": "Certificado de estudios, sílabos, récord académico, copia de DNI, recibo de pago",
        "fundamentacion_plantilla": (
            "Que, el suscrito, procedente de la universidad {universidad_origen}, "
            "donde cursó estudios en la carrera de {carrera_origen}, solicita se "
            "autorice su TRASLADO EXTERNO a la Escuela Profesional de {escuela} "
            "de esta casa de estudios, cumpliendo con los requisitos académicos y "
            "administrativos establecidos en el Reglamento de la Universidad.\n\n"
            "Por lo expuesto, solicito acceder a mi pedido por ser de justicia."
        ),
        "ayuda": "Indica la universidad y carrera de procedencia, y la escuela UNDAC a la que deseas ingresar.",
        "campos_extra": ["universidad_origen", "carrera_origen"],
    },

    "convalidacion": {
        "nombre": "Convalidación de cursos",
        "solicito": "CONVALIDACIÓN DE ASIGNATURAS",
        "sumilla": "Solicito convalidación de asignaturas cursadas en {universidad_origen}.",
        "destinatario": "Sr./Sra. Decano(a) de la Facultad de {facultad}",
        "anexo_sugerido": "Sílabos, certificado de estudios, récord académico, recibo de pago",
        "fundamentacion_plantilla": (
            "Que, el suscrito, identificado con código de matrícula {codigo}, "
            "estudiante de la Escuela Profesional de {escuela}, solicita la "
            "CONVALIDACIÓN de las asignaturas cursadas y aprobadas en "
            "{universidad_origen}, detalladas en los documentos adjuntos "
            "(sílabos y certificado de estudios), por guardar equivalencia de "
            "contenidos con el plan curricular vigente.\n\n"
            "Por lo expuesto, solicito acceder a mi pedido por ser de justicia."
        ),
        "ayuda": "Indica la universidad de procedencia; detalla los cursos específicos en el Anexo o adjunto.",
        "campos_extra": ["universidad_origen"],
    },

    "reserva_matricula": {
        "nombre": "Reserva de matrícula",
        "solicito": "RESERVA DE MATRÍCULA",
        "sumilla": "Solicito reserva de matrícula correspondiente al periodo académico {periodo}.",
        "destinatario": "Sr./Sra. Decano(a) de la Facultad de {facultad}",
        "anexo_sugerido": "Documento sustentatorio del motivo (médico, laboral, etc.), copia de DNI",
        "fundamentacion_plantilla": (
            "Que, el suscrito, identificado con código de matrícula {codigo}, "
            "estudiante de la Escuela Profesional de {escuela}, debido a "
            "{motivo_reserva}, se ve en la necesidad de solicitar la RESERVA DE "
            "MATRÍCULA correspondiente al periodo académico {periodo}, "
            "comprometiéndose a reincorporarse en el periodo siguiente conforme "
            "al Reglamento de la Universidad.\n\n"
            "Por lo expuesto, solicito acceder a mi pedido por ser de justicia."
        ),
        "ayuda": "Indica el motivo (salud, trabajo, viaje, motivos personales/económicos) y el periodo a reservar.",
        "campos_extra": ["periodo", "motivo_reserva"],
    },

    "rectificacion_notas": {
        "nombre": "Rectificación de notas",
        "solicito": "RECTIFICACIÓN DE NOTAS",
        "sumilla": "Solicito rectificación de nota en el curso de {curso}, periodo {periodo}.",
        "destinatario": "Sr./Sra. Decano(a) de la Facultad de {facultad}",
        "anexo_sugerido": "Copia del acta o registro de notas, evidencia del error (de ser el caso)",
        "fundamentacion_plantilla": (
            "Que, el suscrito, identificado con código de matrícula {codigo}, "
            "estudiante de la Escuela Profesional de {escuela}, solicita la "
            "RECTIFICACIÓN DE NOTA registrada en el curso de {curso}, "
            "correspondiente al periodo académico {periodo}, debido a "
            "{motivo_rectificacion}, conforme se puede apreciar en la "
            "documentación adjunta.\n\n"
            "Por lo expuesto, solicito acceder a mi pedido por ser de justicia."
        ),
        "ayuda": "Indica el curso, el periodo y explica brevemente el error (de digitación, de cálculo, omisión de acta, etc.).",
        "campos_extra": ["curso", "periodo", "motivo_rectificacion"],
    },

    "carta_presentacion": {
        "nombre": "Carta de presentación (prácticas pre-profesionales)",
        "solicito": "CARTA DE PRESENTACIÓN",
        "sumilla": "Solicito carta de presentación para realizar prácticas pre-profesionales en {institucion_practicas}.",
        "destinatario": "Sr./Sra. Decano(a) de la Facultad de {facultad}",
        "anexo_sugerido": "Solicitud o requerimiento de la empresa/institución, copia de DNI",
        "fundamentacion_plantilla": (
            "Que, el suscrito, identificado con código de matrícula {codigo}, "
            "estudiante de la Escuela Profesional de {escuela}, habiendo "
            "cumplido con el avance curricular requerido, solicita se le expida "
            "CARTA DE PRESENTACIÓN dirigida a {institucion_practicas}, a fin de "
            "realizar sus prácticas pre-profesionales en dicha institución.\n\n"
            "Por lo expuesto, solicito acceder a mi pedido por ser de justicia."
        ),
        "ayuda": "Indica el nombre completo de la empresa o institución donde realizarás las prácticas.",
        "campos_extra": ["institucion_practicas"],
    },

    "devolucion_documentos": {
        "nombre": "Devolución de documentos",
        "solicito": "DEVOLUCIÓN DE DOCUMENTOS",
        "sumilla": "Solicito devolución de documentos personales presentados en expediente de {motivo_expediente}.",
        "destinatario": "Sr./Sra. Decano(a) de la Facultad de {facultad}",
        "anexo_sugerido": "Copia del cargo de presentación original, copia de DNI",
        "fundamentacion_plantilla": (
            "Que, el suscrito, identificado con código de matrícula {codigo}, "
            "habiendo presentado documentación personal en el expediente "
            "correspondiente a {motivo_expediente}, y no requiriendo dicha "
            "documentación en lo sucesivo en esta dependencia, solicita la "
            "DEVOLUCIÓN de los documentos originales presentados.\n\n"
            "Por lo expuesto, solicito acceder a mi pedido por ser de justicia."
        ),
        "ayuda": "Indica para qué trámite habías presentado originalmente esos documentos.",
        "campos_extra": ["motivo_expediente"],
    },

    "duplicado_carne": {
        "nombre": "Duplicado de carné universitario",
        "solicito": "DUPLICADO DE CARNÉ UNIVERSITARIO",
        "sumilla": "Solicito duplicado de carné universitario por motivo de {motivo_duplicado}.",
        "destinatario": "Sr./Sra. Jefe(a) de la Oficina de Bienestar Universitario",
        "anexo_sugerido": "Recibo de pago, copia de DNI, denuncia policial (si es por robo/pérdida)",
        "fundamentacion_plantilla": (
            "Que, el suscrito, identificado con código de matrícula {codigo}, "
            "estudiante de la Escuela Profesional de {escuela}, solicita la "
            "expedición de un DUPLICADO de su carné universitario, debido a "
            "{motivo_duplicado}, comprometiéndose a hacer uso responsable del "
            "mismo.\n\nPor lo expuesto, solicito acceder a mi pedido por ser de justicia."
        ),
        "ayuda": "Indica el motivo: pérdida, robo, deterioro o cambio de datos.",
        "campos_extra": ["motivo_duplicado"],
    },

    "subsanacion_actas": {
        "nombre": "Subsanación de actas",
        "solicito": "SUBSANACIÓN DE ACTA",
        "sumilla": "Solicito subsanación de omisión/error en acta del curso {curso}, periodo {periodo}.",
        "destinatario": "Sr./Sra. Decano(a) de la Facultad de {facultad}",
        "anexo_sugerido": "Copia de acta observada, documentación sustentatoria",
        "fundamentacion_plantilla": (
            "Que, el suscrito, identificado con código de matrícula {codigo}, "
            "estudiante de la Escuela Profesional de {escuela}, habiendo "
            "advertido {motivo_subsanacion} en el acta correspondiente al curso "
            "de {curso}, periodo académico {periodo}, solicita se sirva disponer "
            "la SUBSANACIÓN respectiva conforme a la documentación adjunta.\n\n"
            "Por lo expuesto, solicito acceder a mi pedido por ser de justicia."
        ),
        "ayuda": "Indica el curso, el periodo y describe brevemente la omisión o error detectado en el acta.",
        "campos_extra": ["curso", "periodo", "motivo_subsanacion"],
    },

    "otro": {
        "nombre": "Otro trámite (libre / no listado)",
        "solicito": "{solicito_libre}",
        "sumilla": "{sumilla_libre}",
        "destinatario": "{destinatario_libre}",
        "anexo_sugerido": "",
        "fundamentacion_plantilla": (
            "Que, el suscrito, identificado con código de matrícula {codigo}, "
            "estudiante de la Escuela Profesional de {escuela}, solicita "
            "{fundamentacion_libre}.\n\n"
            "Por lo expuesto, solicito acceder a mi pedido por ser de justicia."
        ),
        "ayuda": "Trámite libre: redacta tú el pedido. El sistema te ayuda con el formato legal-formal.",
        "campos_extra": ["solicito_libre", "sumilla_libre", "destinatario_libre", "fundamentacion_libre"],
    },
}


def listar_tramites():
    """Devuelve lista de (clave, nombre) para mostrar en menús."""
    return [(k, v["nombre"]) for k, v in CATALOGO.items()]


def obtener_tramite(clave):
    clave = clave.strip().lower()
    if clave not in CATALOGO:
        raise KeyError(f"Trámite '{clave}' no existe en el catálogo.")
    return CATALOGO[clave]
