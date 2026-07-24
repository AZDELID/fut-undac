# -*- coding: utf-8 -*-
"""
Wizard interactivo: guía al estudiante paso a paso para llenar el FUT,
dando consejos y ejemplos en cada campo, y validando lo que escribe.

Este es el modo "asistente" pensado para alguien que no sabe cómo
redactar un trámite formal.
"""

from rich.console import Console
from rich.panel import Panel
from rich.prompt import Prompt, Confirm
from rich.table import Table
from rich import box

from .catalogo import CATALOGO, listar_tramites, obtener_tramite
from .modelo import validar_campo, ValidationError
from .constructor import construir_fut, campos_faltantes_en_texto
from . import perfil as perfil_mod
from . import api_undac

console = Console()


def _preguntar(etiqueta, ayuda=None, ejemplo=None, validador_key=None,
                obligatorio=True, valor_default=None):
    """Pregunta un campo individual mostrando ayuda/ejemplo, valida y
    reintenta hasta obtener un valor correcto."""
    texto_ayuda = ""
    if ayuda:
        texto_ayuda += f"[dim]{ayuda}[/dim]\n"
    if ejemplo:
        texto_ayuda += f"[dim]Ejemplo: {ejemplo}[/dim]"
    if texto_ayuda:
        console.print(texto_ayuda)

    while True:
        valor = Prompt.ask(f"[bold cyan]{etiqueta}[/bold cyan]", default=valor_default or "")
        valor = valor.strip()

        if not valor and valor_default:
            valor = valor_default

        if not valor and not obligatorio:
            return ""

        if not valor and obligatorio:
            console.print("[yellow]Este campo es obligatorio, intenta de nuevo.[/yellow]")
            continue

        if validador_key:
            try:
                valor = validar_campo(validador_key, valor)
            except ValidationError as e:
                console.print(f"[red]✗ {e}[/red]")
                continue

        return valor


def _elegir_tramite():
    console.print()
    console.print(Panel.fit(
        "[bold]¿Qué trámite necesitas?[/bold]\n"
        "[dim]Elige el número, o escribe la palabra clave si ya la conoces.[/dim]",
        border_style="cyan"
    ))

    tabla = Table(box=box.SIMPLE, show_header=True, header_style="bold cyan")
    tabla.add_column("#", width=3)
    tabla.add_column("Clave", style="green")
    tabla.add_column("Trámite")

    tramites = listar_tramites()
    for idx, (clave, nombre) in enumerate(tramites, start=1):
        tabla.add_row(str(idx), clave, nombre)
    console.print(tabla)
    console.print()

    while True:
        eleccion = Prompt.ask("Tu elección (número o clave)").strip().lower()
        if eleccion.isdigit():
            idx = int(eleccion)
            if 1 <= idx <= len(tramites):
                return tramites[idx - 1][0]
            console.print("[yellow]Número fuera de rango.[/yellow]")
            continue
        if eleccion in CATALOGO:
            return eleccion
        console.print("[yellow]No reconozco esa opción, intenta de nuevo.[/yellow]")


def _intentar_autocompletar_por_api(datos):
    console.print()
    usar_api = Confirm.ask(
        "[bold]¿Quieres autocompletar tus datos personales usando tu código de matrícula "
        "(consulta a la API de UNDAC)?[/bold]",
        default=True
    )
    if not usar_api:
        return datos

    codigo = Prompt.ask("Ingresa tu código de matrícula").strip()
    console.print("[dim]Consultando API de UNDAC...[/dim]")
    try:
        info = api_undac.consultar_estudiante(codigo)
    except api_undac.APIError as e:
        console.print(f"[red]✗ {e}[/red]")
        console.print("[yellow]Continuaremos llenando los datos manualmente.[/yellow]")
        return datos

    console.print(Panel.fit(
        f"[bold green]Datos encontrados:[/bold green]\n"
        f"Nombre: {info['nombres_apellidos']}\n"
        f"DNI: {info['dni']}\n"
        f"Facultad/Escuela: {info['facultad']}\n"
        f"Domicilio: {info['domicilio']}",
        border_style="green"
    ))

    confirmar = Confirm.ask("¿Usar estos datos?", default=True)
    if confirmar:
        datos["nombres_apellidos"] = info["nombres_apellidos"]
        datos["dni"] = info["dni"]
        datos["codigo"] = codigo
        datos["facultad"] = info["facultad"]
        datos["escuela"] = info["facultad"]
        datos["domicilio"] = info["domicilio"]

        console.print(
            "\n[yellow]⚠ Aviso: la API trae un campo de correo marcado como "
            "'institucional', pero en realidad corresponde a tu correo PERSONAL "
            "(error conocido del sistema). Te voy a pedir tu correo institucional "
            "real por separado, no lo voy a asumir automáticamente.[/yellow]\n"
        )
        if info.get("correo_personal_detectado"):
            console.print(
                f"[dim]Correo detectado por la API (probablemente personal, "
                f"no institucional): {info['correo_personal_detectado']}[/dim]"
            )
    return datos


def ejecutar_wizard():
    console.print()
    console.print(Panel.fit(
        "[bold]Asistente de Formulario Único de Trámite (FUT) — UNDAC[/bold]\n"
        "Te voy a guiar paso a paso. En cada campo te doy un ejemplo y un "
        "consejo de redacción. No te preocupes si no sabes cómo redactar "
        "el pedido formal: yo te ayudo a construirlo.",
        border_style="bold blue"
    ))

    clave_tramite = _elegir_tramite()
    tramite = obtener_tramite(clave_tramite)

    console.print()
    console.print(Panel.fit(
        f"[bold]{tramite['nombre']}[/bold]\n[dim]{tramite.get('ayuda', '')}[/dim]",
        border_style="cyan"
    ))

    datos = {}

    # --- Perfil guardado ---
    perfiles_existentes = perfil_mod.listar_perfiles()
    if perfiles_existentes:
        usar_guardado = Confirm.ask(
            "\n[bold]Encontré un perfil guardado. ¿Quieres usarlo?[/bold]",
            default=True
        )
        if usar_guardado:
            if len(perfiles_existentes) == 1:
                datos.update(perfiles_existentes[0])
            else:
                console.print("Perfiles disponibles:")
                for i, p in enumerate(perfiles_existentes, start=1):
                    console.print(f"  {i}. {p.get('nombres_apellidos','')} ({p.get('codigo','')})")
                idx = Prompt.ask("¿Cuál usar?", default="1")
                try:
                    datos.update(perfiles_existentes[int(idx) - 1])
                except (ValueError, IndexError):
                    pass

    if not datos.get("nombres_apellidos"):
        datos = _intentar_autocompletar_por_api(datos)

    # --- Datos personales (completar lo que falte) ---
    console.print("\n[bold underline]Datos personales[/bold underline]")

    if not datos.get("nombres_apellidos"):
        datos["nombres_apellidos"] = _preguntar(
            "Apellidos y nombres completos",
            ayuda="Escribe primero apellidos, luego nombres, tal como figuran en tu DNI.",
            ejemplo="ESPINOZA BENAVIDES LUIS PABLO",
        )
    else:
        console.print(f"[dim]Apellidos y nombres: {datos['nombres_apellidos']} (de tu perfil)[/dim]")

    if not datos.get("dni"):
        datos["dni"] = _preguntar("D.N.I. (8 dígitos)", ejemplo="71447115", validador_key="dni")

    if not datos.get("codigo"):
        datos["codigo"] = _preguntar(
            "Código de matrícula", ejemplo="2304403050", validador_key="codigo"
        )

    datos["celular"] = _preguntar(
        "Celular (9 dígitos, empieza con 9)", ejemplo="987654321",
        validador_key="celular", valor_default=datos.get("celular", "")
    )

    datos["correo"] = _preguntar(
        "Correo electrónico institucional",
        ayuda="Usa tu correo @undac.edu.pe si lo tienes; si no, tu correo personal activo.",
        ejemplo="pablo.ramos@undac.edu.pe",
        validador_key="correo",
        valor_default=datos.get("correo", ""),
    )

    if not datos.get("facultad"):
        datos["facultad"] = _preguntar("Facultad", ejemplo="Ingeniería de Sistemas y Computación")
    if not datos.get("escuela"):
        datos["escuela"] = _preguntar("Escuela Profesional", ejemplo="Ingeniería de Sistemas")
    datos["especialidad"] = _preguntar(
        "Especialidad (si no tienes, deja vacío)", obligatorio=False,
        valor_default=datos.get("especialidad", "")
    )

    if not datos.get("domicilio"):
        datos["domicilio"] = _preguntar(
            "Domicilio (Calle, Distrito, Provincia y Región)",
            ejemplo="Jr. 28 de Julio, Cerro de Pasco, Pasco",
        )

    datos["cargo_centro_trabajo"] = _preguntar(
        "Cargo actual y/o centro de trabajo (si trabajas; si no, deja vacío)",
        obligatorio=False,
    )

    # --- Campos específicos del trámite ---
    campos_extra = tramite.get("campos_extra", [])
    campos_opcionales = set(tramite.get("campos_extra_opcionales", []))
    if campos_extra:
        console.print(f"\n[bold underline]Datos específicos de: {tramite['nombre']}[/bold underline]")
        if tramite.get("ayuda"):
            console.print(f"[dim]{tramite['ayuda']}[/dim]\n")
        for campo in campos_extra:
            etiqueta = campo.replace("_", " ").capitalize()
            es_opcional = campo in campos_opcionales
            datos[campo] = _preguntar(etiqueta, obligatorio=not es_opcional)

    # --- Fundamentación: modo asistido ---
    console.print("\n[bold underline]Fundamentación del pedido[/bold underline]")
    console.print(Panel.fit(
        "Este es el campo más difícil de redactar. Tengo una plantilla "
        "legal-formal lista para tu trámite, completada automáticamente "
        "con los datos que diste.\n\n"
        "Puedes: (1) usarla tal cual, (2) editarla a mano, o (3) escribir "
        "tu propio texto desde cero.",
        border_style="cyan"
    ))

    fut_preview = construir_fut(clave_tramite, datos)
    console.print(Panel(fut_preview.fundamentacion, title="Texto sugerido", border_style="green"))

    faltan = campos_faltantes_en_texto(fut_preview.fundamentacion)
    if faltan:
        console.print(f"[yellow]⚠ Faltan datos para completar la plantilla: {', '.join(faltan)}[/yellow]")
        for campo in faltan:
            etiqueta = campo.replace("_", " ").capitalize()
            datos[campo] = _preguntar(etiqueta)
        fut_preview = construir_fut(clave_tramite, datos)
        console.print(Panel(fut_preview.fundamentacion, title="Texto actualizado", border_style="green"))

    opcion = Prompt.ask(
        "¿Qué deseas hacer?",
        choices=["usar", "editar", "propio"],
        default="usar"
    )
    if opcion == "usar":
        pass  # ya quedó en datos vía plantilla
    elif opcion == "editar":
        console.print("[dim]Pega el texto editado (una sola línea, o usa saltos con \\n):[/dim]")
        nuevo = Prompt.ask("Texto", default=fut_preview.fundamentacion)
        datos["fundamentacion"] = nuevo
    else:
        console.print("[dim]Escribe tu propio texto de fundamentación:[/dim]")
        datos["fundamentacion"] = Prompt.ask("Texto")

    # --- Anexo y fecha ---
    datos["anexo"] = _preguntar(
        "Anexos (documentos que adjuntas, separados por coma)",
        ejemplo=tramite.get("anexo_sugerido", "Copia de DNI"),
        obligatorio=False,
        valor_default=tramite.get("anexo_sugerido", ""),
    )

    # --- Guardar perfil ---
    guardar = Confirm.ask("\n¿Guardar estos datos personales como perfil para la próxima vez?", default=True)
    if guardar:
        perfil_mod.guardar_perfil(datos)
        console.print("[green]✓ Perfil guardado.[/green]")

    fut_final = construir_fut(clave_tramite, datos)
    return fut_final
