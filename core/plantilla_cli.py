# -*- coding: utf-8 -*-
"""
Editor de consola para la plantilla institucional del FUT (encabezado,
pie de página, logo, número de expediente, etc.).

Pensado 100% para terminal (sin GUI): la pantalla se divide en dos
mitades — a la izquierda el formulario de preguntas, a la derecha una
vista previa en vivo de cómo va quedando el FUT. Cada vez que respondes
una pregunta, la pantalla se redibuja y la vista previa refleja el
cambio al instante.

Lo que se configura aquí es una PLANTILLA GLOBAL: se guarda en
~/.fut_undac/plantilla.json (ver core/plantilla.py) y se aplica
automáticamente a TODOS los FUT que generes después, sin importar si
los creas con el wizard, el modo DSL o la GUI.
"""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.prompt import Prompt, Confirm
from rich import box

from . import plantilla as plantilla_mod

console = Console()

ANCHO_MIN_SPLIT = 100  # debajo de esto, se apila en vez de dividir en dos columnas

# Datos de ejemplo usados solo para que la vista previa se vea realista
_EJEMPLO_NOMBRE = "PÉREZ QUISPE, JUAN CARLOS"
_EJEMPLO_CODIGO = "2024012345"
_EJEMPLO_FECHA = "22 de julio de 2026"


# ---------------------------------------------------------------------
# Definición de las preguntas del panel izquierdo
# ---------------------------------------------------------------------
# Cada paso: clave en el dict de plantilla, etiqueta, tipo ('texto' o
# 'sn'), ayuda, y opcionalmente una sub-pregunta de texto que solo se
# hace si la respuesta S/N fue afirmativa (para no pedir un texto que
# no se va a usar).

PASOS = [
    dict(
        clave="encabezado_personalizado", tipo="texto", obligatorio=False,
        etiqueta="Encabezado personalizado",
        ayuda="Texto libre que aparece arriba del FUT, encima del nombre "
              "de la institución (ej: nombre de tu facultad o escuela). "
              "Déjalo vacío si no quieres ninguno.",
    ),
    dict(
        clave="mostrar_logo_escuela", tipo="sn", obligatorio=False,
        etiqueta="Logo de tu facultad/escuela",
        ayuda="¿Quieres mostrar un logo adicional (de tu facultad/escuela) "
              "en la esquina derecha del encabezado? (S/N)",
        subpregunta=dict(
            clave="logo_escuela_path", tipo="texto", obligatorio=False,
            etiqueta="Ruta del archivo del logo",
            ayuda="Ruta a la imagen del logo (ej: C:/logos/mi_escuela.png). "
                  "Déjalo vacío para configurarlo luego desde la GUI.",
        ),
    ),
    dict(
        clave="nombre_institucion", tipo="texto", obligatorio=True,
        etiqueta="Nombre de la institución en el encabezado",
        ayuda="Nombre completo que aparece en grande, junto al logo.",
    ),
    dict(
        clave="texto_pie", tipo="texto", obligatorio=False,
        etiqueta="Pie de página",
        ayuda="Texto libre que aparece al final de cada página del FUT.",
    ),
    dict(
        clave="mostrar_numero_expediente", tipo="sn", obligatorio=False,
        etiqueta="Número de expediente / folio",
        ayuda="¿Quieres reservar una línea para el número de expediente "
              "o folio, arriba a la derecha del encabezado? (S/N)",
        subpregunta=dict(
            clave="prefijo_expediente", tipo="texto", obligatorio=False,
            etiqueta="Prefijo del número de expediente",
            ayuda="Ej: 'N° EXP.' o 'FOLIO N°'.",
        ),
    ),
    dict(
        clave="mostrar_fecha_lugar", tipo="sn", obligatorio=False,
        etiqueta="Fecha y lugar",
        ayuda="¿Quieres que el campo 13 muestre 'FECHA Y LUGAR' en vez de "
              "solo 'FECHA'? (S/N)",
        subpregunta=dict(
            clave="lugar_predeterminado", tipo="texto", obligatorio=False,
            etiqueta="Lugar predeterminado",
            ayuda="Ej: Cerro de Pasco.",
        ),
    ),
    dict(
        clave="cargo_destinatario", tipo="texto", obligatorio=False,
        etiqueta="Cargo del destinatario personalizado",
        ayuda="Si lo llenas, TODOS los FUT usarán este texto como "
              "destinatario (campo 2), en vez del que trae cada trámite "
              "por defecto. Déjalo vacío para usar el automático.",
    ),
    dict(
        clave="mostrar_datos_estudiante", tipo="sn", obligatorio=False,
        etiqueta="Datos del estudiante en el encabezado",
        ayuda="¿Quieres mostrar una línea con nombre y código del "
              "estudiante justo debajo del encabezado (además del campo "
              "3, que siempre aparece)? (S/N)",
    ),
    dict(
        clave="mostrar_lema_anio", tipo="sn", obligatorio=False,
        etiqueta="Nombre del año (lema oficial)",
        ayuda="¿Mostrar el lema oficial del año (el que define el "
              "gobierno, ej: 'Año de...') en el pie de página? (S/N)",
        subpregunta=dict(
            clave="lema_anio", tipo="texto", obligatorio=False,
            etiqueta="Texto del lema del año",
            ayuda="Ej: Año de la Esperanza y el Fortalecimiento de la Democracia.",
        ),
    ),
]


# ---------------------------------------------------------------------
# Vista previa (panel derecho)
# ---------------------------------------------------------------------

def _sino(valor: bool) -> str:
    return "Sí" if valor else "No"


def _panel_preview(datos: dict) -> Panel:
    d = datos
    t = Text()

    encabezado_extra = (d.get("encabezado_personalizado") or "").strip()
    if encabezado_extra:
        t.append(f"        {encabezado_extra}\n", style="dim italic")
    t.append("  [LOGO]   ", style="dim")
    t.append(f"{d.get('nombre_institucion') or '(nombre de la institución)'}\n", style="bold")
    t.append(f"           {d.get('subtitulo') or 'FORMULARIO ÚNICO DE TRÁMITE'}", style="bold")
    if d.get("mostrar_logo_escuela"):
        t.append("          [LOGO ESCUELA]", style="dim")
    t.append("\n" + "─" * 46 + "\n", style="dim")

    if d.get("mostrar_numero_expediente"):
        prefijo = (d.get("prefijo_expediente") or "N° EXP.").strip()
        t.append(f"{prefijo}: ______________\n".rjust(46), style="dim")

    if d.get("mostrar_datos_estudiante"):
        t.append(f"Estudiante: {_EJEMPLO_NOMBRE}  •  Código: {_EJEMPLO_CODIGO}\n", style="dim")

    t.append("                                   SOLICITO: ..............\n", style="dim")
    t.append("\n1. SUMILLA\n", style="bold")
    t.append(".......................................\n", style="dim")
    t.append("2. DESTINATARIO\n", style="bold")
    cargo_dest = (d.get("cargo_destinatario") or "").strip()
    t.append(f"{cargo_dest or '(automático según el trámite elegido)'}\n", style="dim")
    t.append("3. DATOS DEL USUARIO\n", style="bold")
    t.append(f"{_EJEMPLO_NOMBRE}\n", style="dim")
    t.append("   (...continúan los campos 4 al 12...)\n", style="dim italic")

    if d.get("mostrar_fecha_lugar"):
        lugar = (d.get("lugar_predeterminado") or "Cerro de Pasco").strip()
        t.append(f"13. FECHA Y LUGAR: {lugar}, {_EJEMPLO_FECHA}\n", style="bold")
    else:
        t.append(f"13. FECHA: {_EJEMPLO_FECHA}\n", style="bold")
    t.append("14. FIRMA: .......................................\n", style="dim")

    t.append("\n" + "═" * 46 + "\n", style="dim")
    pie_partes = [p for p in (
        d.get("lema_anio", "").strip() if d.get("mostrar_lema_anio") else "",
        d.get("direccion", ""),
        d.get("texto_pie", ""),
    ) if p and str(p).strip()]
    t.append("  •  ".join(pie_partes) or "(pie de página vacío)", style="dim italic")

    return Panel(t, title="[bold]Vista previa del FUT[/bold]", border_style="cyan",
                 subtitle="[dim]con datos de ejemplo[/dim]")


def _panel_formulario(datos: dict, indice_actual: int) -> Panel:
    tabla = Table(box=box.SIMPLE, show_header=False, expand=True)
    tabla.add_column("Campo", style="bold", ratio=2)
    tabla.add_column("Valor actual", ratio=3)
    for i, paso in enumerate(PASOS):
        clave = paso["clave"]
        if paso["tipo"] == "sn":
            valor_txt = _sino(bool(datos.get(clave))) if clave in datos else "—"
        else:
            valor_txt = datos.get(clave) or ("—" if clave not in datos else "(vacío)")
        estilo = "bold yellow" if i == indice_actual else ("green" if clave in datos else "dim")
        marcador = "➤ " if i == indice_actual else "  "
        tabla.add_row(f"{marcador}{paso['etiqueta']}", valor_txt, style=estilo)
    return Panel(tabla, title="[bold]Configurar plantilla del FUT[/bold]", border_style="magenta",
                 subtitle="[dim]se guarda como plantilla global, para todos los FUT[/dim]")


def _dibujar(datos: dict, indice_actual: int):
    console.clear()
    ancho = console.size.width
    izquierda = _panel_formulario(datos, indice_actual)
    derecha = _panel_preview(datos)
    if ancho >= ANCHO_MIN_SPLIT:
        grid = Table.grid(expand=True)
        grid.add_column(ratio=1)
        grid.add_column(ratio=1)
        grid.add_row(izquierda, derecha)
        console.print(grid)
    else:
        # Terminal angosta: no entran dos columnas, se apilan pero se
        # mantiene el mismo contenido (izquierda arriba, derecha abajo).
        console.print(izquierda)
        console.print(derecha)
    console.print()


# ---------------------------------------------------------------------
# Bucle principal
# ---------------------------------------------------------------------

def _preguntar_campo(paso: dict, datos: dict):
    console.print(f"[bold cyan]{paso['etiqueta']}[/bold cyan]")
    if paso.get("ayuda"):
        console.print(f"[dim]{paso['ayuda']}[/dim]")

    if paso["tipo"] == "sn":
        valor = Confirm.ask("¿Sí o no?", default=False)
        datos[paso["clave"]] = valor
        if valor and paso.get("subpregunta"):
            sub = paso["subpregunta"]
            console.print(f"\n[bold cyan]{sub['etiqueta']}[/bold cyan]")
            if sub.get("ayuda"):
                console.print(f"[dim]{sub['ayuda']}[/dim]")
            sub_valor = Prompt.ask(">", default="").strip()
            datos[sub["clave"]] = sub_valor
        return

    # tipo texto
    while True:
        valor = Prompt.ask(">", default="").strip()
        if not valor and paso.get("obligatorio"):
            console.print("[yellow]Este campo es obligatorio, intenta de nuevo.[/yellow]")
            continue
        datos[paso["clave"]] = valor
        return


def ejecutar_editor_plantilla():
    """Punto de entrada: recorre todas las preguntas mostrando la vista
    previa en vivo, y al final guarda la plantilla global."""
    actual = plantilla_mod.obtener_plantilla()
    datos = {}  # solo lo que se va respondiendo en esta sesión

    console.clear()
    console.print(Panel.fit(
        "[bold]Configurador de plantilla del FUT[/bold]\n\n"
        "Vas a responder unas preguntas sobre el encabezado y el pie de "
        "página. A la derecha verás cómo va quedando el FUT en tiempo "
        "real. Al terminar, se guarda como plantilla y se usa "
        "automáticamente en todos los FUT que generes después.\n\n"
        "[dim]Presiona Enter para dejar un campo de texto vacío / sin cambios.[/dim]",
        border_style="cyan", title="FUT-UNDAC",
    ))
    Prompt.ask("\n[dim]Presiona Enter para comenzar[/dim]", default="")

    # Precargamos con los valores ya guardados, para que la vista previa
    # arranque mostrando la configuración actual en vez de vacía.
    datos.update({k: actual[k] for k in (
        "nombre_institucion", "subtitulo", "direccion", "texto_pie",
        "lema_anio", "mostrar_lema_anio",
    ) if k in actual})

    for i, paso in enumerate(PASOS):
        _dibujar(datos, i)
        _preguntar_campo(paso, datos)

    # Vista previa final antes de confirmar guardado
    _dibujar(datos, len(PASOS))
    console.print(Panel.fit(
        "[bold green]Configuración completa.[/bold green]\n"
        "Esto quedará guardado como la plantilla que se usa en TODOS "
        "los FUT (wizard, DSL y GUI), hasta que la cambies de nuevo.",
        border_style="green",
    ))
    if Confirm.ask("¿Guardar esta plantilla?", default=True):
        ruta = plantilla_mod.guardar_plantilla(datos)
        console.print(f"\n[bold green]✓[/bold green] Plantilla guardada en: [dim]{ruta}[/dim]")
    else:
        console.print("\n[yellow]Cambios descartados. No se modificó la plantilla.[/yellow]")


def mostrar_plantilla_actual():
    """Muestra la plantilla guardada actualmente, sin editarla."""
    actual = plantilla_mod.obtener_plantilla()
    _dibujar(actual, -1)
    console.print(f"[dim]Archivo: {plantilla_mod.RUTA_PLANTILLA}[/dim]")


def restaurar_plantilla_por_defecto():
    plantilla_mod.restaurar_plantilla()
    console.print("[green]✓[/green] Plantilla restaurada a los valores de fábrica.")
