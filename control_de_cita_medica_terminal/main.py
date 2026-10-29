
import getpass
import os
import shutil
import sys
from datetime import datetime

import citas
import esperas
import historial
import medicos
import pacientes
import usuarios
import estructuras
from esperas import ESTADO_ESPERA


# ============================================================
# Configuración UTF-8 (Windows) y colores ANSI
# ============================================================

try:
    sys.stdout.reconfigure(encoding="utf-8", errors="replace")
    sys.stdin.reconfigure(encoding="utf-8", errors="replace")
except Exception:
    pass


def _activar_ansi():
    if os.name != "nt":
        return
    try:
        # Asegura que la consola interprete correctamente los acentos.
        os.system("chcp 65001 >nul")
    except Exception:
        pass
    try:
        import ctypes

        kernel32 = ctypes.windll.kernel32
        handle = kernel32.GetStdHandle(-11)
        modo = ctypes.c_uint32()
        if kernel32.GetConsoleMode(handle, ctypes.byref(modo)):
            kernel32.SetConsoleMode(handle, modo.value | 0x0004)
    except Exception:
        pass


_activar_ansi()

USAR_COLOR = sys.stdout.isatty() and "NO_COLOR" not in os.environ


COLORES = {
    "RESET": "\033[0m",
    "NEGRITA": "\033[1m",
    "AZUL": "\033[94m",
    "VERDE": "\033[92m",
    "AMARILLO": "\033[93m",
    "ROJO": "\033[91m",
    "CIAN": "\033[96m",
    "GRIS": "\033[90m",
    "BLANCO": "\033[97m",
}

def c(texto, *estilos):
    if not USAR_COLOR:
        return str(texto)
    return "".join(estilos) + str(texto) + COLORES["RESET"]


def limpiar():
    if not sys.stdout.isatty():
        return
    sys.stdout.write("\033[2J\033[H")
    sys.stdout.flush()


def ancho_terminal():
    return max(60, min(120, shutil.get_terminal_size((90, 25)).columns - 2))


def recortar(texto, ancho):
    texto = str(texto)
    if ancho <= 0:
        return ""
    if len(texto) <= ancho:
        return texto
    if ancho == 1:
        return "…"
    return texto[: ancho - 1] + "…"


def imprimir_tabla(columnas, filas, maximos=None, numerar=False, alinear=None):
    columnas = list(columnas)
    filas = [tuple(str(v) for v in fila) for fila in filas]
    if numerar:
        columnas = ["#"] + columnas
        filas = [(str(i),) + fila for i, fila in enumerate(filas, 1)]
    ncol = len(columnas)
    if maximos is None:
        maximos = [32] * ncol
    elif numerar:
        maximos = [4] + list(maximos)
    else:
        maximos = list(maximos)
    if alinear is None:
        alinear = ["<"] * ncol
    if numerar:
        alinear = [">"] + list(alinear)

    anchos = []
    for i, col in enumerate(columnas):
        valores = [len(fila[i]) for fila in filas]
        ancho = max([len(col)] + valores) if valores else len(col)
        ancho = min(ancho, maximos[i])
        ancho = max(ancho, min(len(col), 8), 3)
        anchos.append(ancho)

    disponible = ancho_terminal()
    while sum(anchos) + 2 * (len(anchos) - 1) > disponible:
        indice = max(range(len(anchos)), key=lambda j: anchos[j])
        minimo = max(3, len(columnas[indice]) // 2)
        if anchos[indice] <= minimo:
            break
        anchos[indice] -= 1

    def formatear(valores):
        celdas = []
        for i, valor in enumerate(valores):
            texto = recortar(valor, anchos[i])
            alineacion = alinear[i] if i < len(alinear) else "<"
            if alineacion == ">":
                texto = texto.rjust(anchos[i])
            elif alineacion == "^":
                texto = texto.center(anchos[i])
            else:
                texto = texto.ljust(anchos[i])
            celdas.append(texto)
        return "  " + "  ".join(celdas)

    print(c(formatear(columnas), COLORES["NEGRITA"], COLORES["GRIS"]))
    print(c("  " + "  ".join("─" * w for w in anchos), COLORES["GRIS"]))
    if not filas:
        print(c("  (sin registros)", COLORES["GRIS"]))
    else:
        for fila in filas:
            print(formatear(fila))


# ============================================================
# Entrada y salida auxiliares
# ============================================================

def leer(prompt=""):
    try:
        return input(prompt)
    except (EOFError, KeyboardInterrupt):
        print()
        raise EOFError


def leer_password(prompt="  Contraseña: "):
    if sys.stdin.isatty():
        try:
            return getpass.getpass(prompt)
        except (EOFError, KeyboardInterrupt):
            print()
            raise EOFError
        except Exception:
            pass
    return leer(prompt)


def pausa():
    if not sys.stdin.isatty():
        return
    try:
        input("\n  Presiona Enter para continuar…")
    except (EOFError, KeyboardInterrupt):
        print()
        raise EOFError


def confirmar(pregunta, por_defecto=False):
    etiqueta = " [S/n]: " if por_defecto else " [s/N]: "
    respuesta = leer(f"  {pregunta}{etiqueta}").strip().lower()
    if not respuesta:
        return por_defecto
    return respuesta in ("s", "si", "sí", "y", "yes")


# ============================================================
# Aplicación
# ============================================================


CLAVES_FILTRO = {
    "t": "Todas",
    "p": "Pendiente",
    "e": ESTADO_ESPERA,
    "r": "Realizada",
    "c": "Cancelada",
}

_estado = {}


def inicializar_estado():
    _estado.update({
        "usuario": None,
        "pantalla": "login",
        "pila": [],
        "aviso_pendiente": None,
        "busqueda_pacientes": "",
        "busqueda_medicos": "",
        "busqueda_citas": "",
        "filtro_citas": "Todas",
        "detalle_paciente": None,
        "detalle_medico": None,
        "cita_actual": None,
        "lista_pacientes": [],
        "lista_medicos": [],
        "lista_citas": []
    })



def ir(pantalla):
    if pantalla != _estado["pantalla"]:
        estructuras.pila_apilar(_estado["pila"], _estado["pantalla"])
    _estado["pantalla"] = pantalla

def volver():
    _estado["pantalla"] = (
        estructuras.pila_desapilar(_estado["pila"]) if not estructuras.pila_esta_vacia(_estado["pila"]) else "menu"
    )

# ---------------- Bucle principal ----------------

def ejecutar():
    try:
        while _estado["pantalla"] != "salir":
            limpiar()
            _cabecera()
            if _estado["aviso_pendiente"]:
                tipo, texto = _estado["aviso_pendiente"]
                _estado["aviso_pendiente"] = None
                color = {
                    "ok": COLORES["VERDE"],
                    "error": COLORES["ROJO"],
                    "aviso": COLORES["AMARILLO"],
                    "info": COLORES["CIAN"],
                }.get(tipo, COLORES["CIAN"])
                print()
                print(c(f"  {texto}", color))
                print()
            try:
                globals()["pantalla_" + _estado["pantalla"]]()
            except (OSError, ValueError, TypeError, KeyError, RuntimeError) as error:
                _estado["aviso_pendiente"] = (
                    "error",
                    f"No se pudo completar la operación: {error}",
                )
    except EOFError:
        pass
    finally:
        try:
            historial.volcar_bitacora()
        except OSError:
            pass
        limpiar()
        print(c("\n  Hasta luego. MediCitas.\n", COLORES["AZUL"], COLORES["NEGRITA"]))

def _aviso(tipo, texto):
    _estado["aviso_pendiente"] = (tipo, texto)

# ---------------- Cabecera y helpers ----------------

def _cabecera():
    ancho = ancho_terminal()
    print(c("═" * ancho, COLORES["AZUL"]))
    print(
        c("  MediCitas", COLORES["NEGRITA"], COLORES["AZUL"])
        + "  ·  Sistema de gestión de citas médicas"
    )
    if _estado["usuario"]:
        extra = f"Sesión: {_estado['usuario'].get('email', '')}"
        if not estructuras.pila_esta_vacia(_estado["pila"]):
            extra += "   ·   [0] Volver disponible"
        print(c(f"  {extra}", COLORES["GRIS"]))
    print(c("═" * ancho, COLORES["AZUL"]))

def _leer(prompt):
    return leer(prompt)

def _opcion():
    return _leer("  Opción: ").strip()

def _titulo(titulo, subtitulo=""):
    print()
    print(c("  " + titulo.upper(), COLORES["NEGRITA"], COLORES["AZUL"]))
    if subtitulo:
        print(c("  " + subtitulo, COLORES["GRIS"]))
    print(c("  " + "─" * (ancho_terminal() - 2), COLORES["GRIS"]))
    print()

def _campo_obligatorio(etiqueta):
    while True:
        valor = _leer(f"  {etiqueta}: ").strip()
        if valor.lower() == "cancelar":
            return None
        if valor:
            return valor
        print(c("  Este campo es obligatorio.", COLORES["ROJO"]))

def _campo_entero(etiqueta):
    while True:
        valor = _leer(f"  {etiqueta}: ").strip()
        if valor.lower() == "cancelar":
            return None
        try:
            numero = int(valor)
        except ValueError:
            print(c("  Escribe un número entero.", COLORES["ROJO"]))
            continue
        if numero < 0:
            print(c("  No puede ser negativo.", COLORES["ROJO"]))
            continue
        return numero

def _campo_opcion(etiqueta, opciones):
    while True:
        print()
        for i, opcion in enumerate(opciones, 1):
            print(f"    {i}) {opcion}")
        valor = _leer(f"  {etiqueta} [1-{len(opciones)}]: ").strip()
        if valor.lower() == "cancelar":
            return None
        if valor.isdigit() and 1 <= int(valor) <= len(opciones):
            return opciones[int(valor) - 1]
        print(c("  Opción inválida.", COLORES["ROJO"]))

def _campo_fecha(etiqueta):
    while True:
        valor = _leer(f"  {etiqueta} (dd/mm/aaaa): ").strip()
        if valor.lower() == "cancelar":
            return None
        try:
            datetime.strptime(valor, "%d/%m/%Y")
        except ValueError:
            print(c("  Fecha inválida. Usa dd/mm/aaaa.", COLORES["ROJO"]))
            continue
        return valor

def _campo_hora(etiqueta):
    while True:
        valor = _leer(f"  {etiqueta} (hh:mm): ").strip()
        if valor.lower() == "cancelar":
            return None
        try:
            datetime.strptime(valor, "%H:%M")
        except ValueError:
            print(c("  Hora inválida. Usa hh:mm (24 horas).", COLORES["ROJO"]))
            continue
        return valor

def _formulario(titulo, campos):
    print()
    print(c(f"  {titulo}", COLORES["NEGRITA"], COLORES["AZUL"]))
    print(c("  Escribe 'cancelar' en cualquier campo para volver.", COLORES["GRIS"]))
    datos = {}
    for clave, etiqueta, tipo, opciones in campos:
        if tipo == "entero":
            valor = _campo_entero(etiqueta)
        elif tipo == "opcion":
            valor = _campo_opcion(etiqueta, opciones)
        else:
            valor = _campo_obligatorio(etiqueta)
        if valor is None:
            return None
        datos[clave] = valor
    return datos

def _elegir(titulo, elementos, texto_fn):
    print()
    print(c(f"  {titulo}", COLORES["NEGRITA"], COLORES["AZUL"]))
    for i, elemento in enumerate(elementos, 1):
        print(f"   [{i}] {texto_fn(elemento)}")
    print("   [0] Cancelar")
    print()
    while True:
        valor = _leer("  Número: ").strip()
        if valor.lower() in ("0", "cancelar"):
            return None
        if valor.isdigit() and 1 <= int(valor) <= len(elementos):
            return elementos[int(valor) - 1]
        print(c("  Número inválido.", COLORES["ROJO"]))

# ---------------- Auxiliares de datos ----------------

def _proximas_citas(citas_lista, limite=5):
    cola = estructuras.monticulo_crear()
    for indice, cita in enumerate(citas_lista):
        try:
            fecha = datetime.strptime(str(cita.get("fecha", "")), "%d/%m/%Y")
        except ValueError:
            clave = (9999, 12, 31, "23:59", indice)
        else:
            clave = (
                fecha.year,
                fecha.month,
                fecha.day,
                str(cita.get("hora", "")) or "23:59",
                indice,
            )
        estructuras.monticulo_encolar(cola, clave, cita)
    ordenadas = []
    while not estructuras.monticulo_esta_vacio(cola) and len(ordenadas) < limite:
        ordenadas.append(estructuras.monticulo_desencolar(cola))
    return ordenadas

def _etiqueta_estado(cita):
    estado = cita.get("estado", "Pendiente")
    if estado == ESTADO_ESPERA:
        return f"{estado} · {cita.get('posicion_espera', '?')}º"
    return estado

def _filas_espera(citas_lista):
    filas = esperas.posiciones_ocupadas(citas_lista)
    resultado = []
    for (_, fecha, hora), (activa, en_fila) in filas.items():
        if not en_fila:
            continue
        resultado.append(
            (
                activa["medico"] if activa else "—",
                fecha,
                hora,
                f"{len(en_fila)} en fila",
                " > ".join(
                    f"{c.get('posicion_espera', '?')}. {c.get('paciente', '')}"
                    for c in en_fila
                ),
            )
        )
    return resultado

def _indice_de_cita(cita):
    registros = citas.cargar_citas()
    for indice, registro in enumerate(registros):
        if registro == cita:
            return indice
    return None

# ---------------- Pantallas de autenticación ----------------

def pantalla_login():
    if _estado["usuario"] is not None:
        _estado["pantalla"] = "menu"
        return
    _titulo("Iniciar sesión", "Accede a tu cuenta para gestionar las citas.")
    print("  [1] Ingresar")
    print("  [2] Crear cuenta")
    print("  [0] Salir")
    print()
    op = _opcion()
    if op == "1":
        email = _campo_obligatorio("Correo electrónico")
        if email is None:
            return
        clave = leer_password("  Contraseña: ")
        if not clave:
            _aviso("error", "Ingresa tu contraseña.")
            return
        try:
            usuario = usuarios.autenticar_usuario(email, clave)
        except RuntimeError as error:
            _aviso("error", str(error))
            return
        if usuario:
            _estado["usuario"] = usuario
            _estado["pila"] = estructuras.pila_crear()
            _estado["pantalla"] = "menu"
            _aviso("ok", f"Bienvenido, {usuario.get('email', '')}.")
        else:
            _aviso("error", "El correo o la contraseña son incorrectos.")
    elif op == "2":
        ir("registro")
    elif op == "0":
        _estado["pantalla"] = "salir"
    else:
        _aviso("error", "Opción inválida.")

def pantalla_registro():
    _titulo("Crear cuenta", "Regístrate en MediCitas.")
    print(c("  Escribe 'cancelar' en cualquier campo para volver.", COLORES["GRIS"]))
    email = _campo_obligatorio("Correo electrónico")
    if email is None:
        volver()
        return
    email = email.lower()
    clave = leer_password("  Contraseña (mínimo 8 caracteres): ")
    if not clave:
        _aviso("error", "Ingresa una contraseña.")
        return
    confirmacion = leer_password("  Confirma la contraseña: ")
    if "@" not in email or "." not in email.split("@")[-1]:
        _aviso("error", "Ingresa una dirección de correo válida.")
        return
    if len(clave) < 8:
        _aviso("error", "La contraseña debe tener al menos 8 caracteres.")
        return
    if clave != confirmacion:
        _aviso("error", "Las contraseñas no coinciden.")
        return
    try:
        usuarios.registrar_usuario(email, clave)
    except ValueError as error:
        _aviso("error", str(error))
        return
    _aviso("ok", "Cuenta creada correctamente. Ahora inicia sesión.")
    volver()

# ---------------- Menú principal ----------------

def pantalla_menu():
    if _estado["usuario"] is None:
        _estado["pantalla"] = "login"
        return
    pendiente = historial.etiqueta_pendiente()
    _titulo("Menú principal", f"Sesión iniciada como {_estado['usuario'].get('email', '')}")
    print("  [1] Panel de control")
    print("  [2] Pacientes")
    print("  [3] Médicos")
    print("  [4] Citas")
    if pendiente:
        print(f"  [5] Deshacer: {pendiente}")
    else:
        print(c("  [5] Deshacer (nada pendiente)", COLORES["GRIS"]))
    print("  [6] Cerrar sesión")
    print("  [0] Salir")
    print()
    op = _opcion()
    if op == "1":
        ir("dashboard")
    elif op == "2":
        ir("pacientes")
    elif op == "3":
        ir("medicos")
    elif op == "4":
        ir("citas")
    elif op == "5":
        _deshacer()
    elif op == "6":
        _cerrar_sesion()
    elif op == "0":
        _estado["pantalla"] = "salir"
    else:
        _aviso("error", "Opción inválida.")

def _deshacer():
    pendiente = historial.etiqueta_pendiente()
    if pendiente is None:
        _aviso("info", "No hay acciones pendientes por deshacer.")
        return
    if not confirmar(f"¿Deshacer «{pendiente}»?"):
        _aviso("info", "Acción cancelada.")
        return
    entrada = historial.deshacer()
    if entrada is None:
        _aviso("info", "No hay acciones pendientes por deshacer.")
        return
    instantanea = entrada.get("instantanea", {})
    entidad = instantanea.get("entidad")
    modulo = {"cita": citas, "paciente": pacientes, "medico": medicos}.get(entidad)
    try:
        revertido = modulo.revertir(instantanea) if modulo else False
    except (OSError, ValueError, TypeError, KeyError) as error:
        _aviso("error", f"No se pudo deshacer: {error}")
        return
    if revertido:
        historial.registrar_bitacora(
            "Acción deshecha", entrada.get("etiqueta", "")
        )
        _aviso("ok", f"Se revirtió: {entrada.get('etiqueta', '')}.")
    else:
        _aviso(
            "error",
            f"La acción «{entrada.get('etiqueta', '')}» ya no se puede revertir.",
        )

def _cerrar_sesion():
    if not confirmar("¿Deseas cerrar tu sesión?"):
        _aviso("info", "Cierre de sesión cancelado.")
        return
    historial.volcar_bitacora()
    historial.limpiar()
    _estado["usuario"] = None
    _estado["pila"] = estructuras.pila_crear()
    _estado["busqueda_pacientes"] = ""
    _estado["busqueda_medicos"] = ""
    _estado["busqueda_citas"] = ""
    _estado["filtro_citas"] = "Todas"
    _estado["detalle_paciente"] = None
    _estado["detalle_medico"] = None
    _estado["cita_actual"] = None
    _estado["pantalla"] = "login"
    _aviso("info", "Sesión cerrada.")

# ---------------- Panel de control ----------------

def pantalla_dashboard():
    _titulo("Panel de control", "Resumen general del sistema de citas médicas")
    ps = pacientes.cargar_pacientes()
    ms = medicos.cargar_medicos()
    cs = citas.cargar_citas()
    pendientes = sum(1 for c in cs if c.get("estado") == "Pendiente")
    en_espera = sum(1 for c in cs if c.get("estado") == ESTADO_ESPERA)
    print(
        f"   {'Pacientes registrados':<23}: {len(ps):<6}"
        f"{'Citas totales':<18}: {len(cs)}"
    )
    print(
        f"   {'Médicos':<23}: {len(ms):<6}"
        f"{'Citas pendientes':<18}: {pendientes}"
    )
    print(f"   {'En espera':<23}: {en_espera}")
    print()

    print(c("  PRÓXIMAS CITAS", COLORES["NEGRITA"], COLORES["AZUL"]))
    proximas = _proximas_citas(cs)
    filas = [
        (
            c.get("paciente", ""),
            c.get("medico", ""),
            c.get("fecha", ""),
            c.get("hora", ""),
            _etiqueta_estado(c),
        )
        for c in proximas
    ]
    imprimir_tabla(
        ("Paciente", "Médico", "Fecha", "Hora", "Estado"),
        filas,
        maximos=(30, 26, 12, 8, 16),
    )

    filas_espera = _filas_espera(cs)
    if filas_espera:
        print()
        print(c("  FILAS DE ESPERA", COLORES["NEGRITA"], COLORES["CIAN"]))
        imprimir_tabla(
            ("Médico", "Fecha", "Hora", "En fila", "Orden"),
            filas_espera,
            maximos=(28, 12, 8, 10, 40),
        )
    print()
    print("  [1] Agendar nueva cita")
    print("  [2] Ver todas las citas")
    print("  [0] Volver")
    print()
    op = _opcion()
    if op == "1":
        ir("cita_nueva")
    elif op == "2":
        ir("citas")
    elif op == "0":
        volver()
    else:
        _aviso("error", "Opción inválida.")

# ---------------- Pacientes ----------------

def pantalla_pacientes():
    _titulo("Pacientes", "Registro y gestión de pacientes")
    resultado = pacientes.buscar_pacientes(_estado["busqueda_pacientes"])
    _estado["lista_pacientes"] = resultado["elementos"]
    origen = (
        f"búsqueda «{_estado['busqueda_pacientes']}»"
        if _estado["busqueda_pacientes"]
        else "listado completo"
    )
    print(
        f"  {len(resultado['elementos'])} resultado(s) · "
        f"{resultado['algoritmo']} · {origen}"
    )
    print()
    filas = [
        (
            f"{p.get('nombre', '')} {p.get('apellido', '')}".strip(),
            p.get("documento", ""),
            p.get("edad", ""),
            p.get("sexo", ""),
            p.get("telefono", ""),
            p.get("tipo_sangre", ""),
        )
        for p in resultado["elementos"]
    ]
    imprimir_tabla(
        ("Paciente", "Documento", "Edad", "Sexo", "Teléfono", "Sangre"),
        filas,
        maximos=(28, 26, 6, 10, 12, 8),
        numerar=True,
    )
    print()
    if resultado["elementos"]:
        print("  Escribe el número del paciente para ver su ficha.")
    print("  [B] Buscar   [L] Limpiar búsqueda   [N] Registrar paciente   [0] Volver")
    print()
    op = _opcion().lower()
    if op == "0":
        volver()
    elif op == "b":
        texto = _leer("  Buscar (vacío para mostrar todos): ").strip()
        _estado["busqueda_pacientes"] = texto
    elif op == "l":
        _estado["busqueda_pacientes"] = ""
    elif op == "n":
        ir("paciente_nuevo")
    elif op.isdigit() and 1 <= int(op) <= len(resultado["elementos"]):
        paciente = resultado["elementos"][int(op) - 1]
        _estado["detalle_paciente"] = paciente.get("documento", "")
        ir("paciente_detalle")
    else:
        _aviso("error", "Opción inválida.")

def pantalla_paciente_detalle():
    paciente = (
        pacientes.buscar_por_documento(_estado["detalle_paciente"])
        if _estado["detalle_paciente"]
        else None
    )
    if paciente is None:
        _aviso("error", "El paciente ya no existe en el archivo.")
        volver()
        return
    nombre = f"{paciente.get('nombre', '')} {paciente.get('apellido', '')}".strip()
    _titulo("Ficha del paciente", nombre)
    campos = [
        ("Documento", "documento"),
        ("Nombre", "nombre"),
        ("Apellido", "apellido"),
        ("Edad", "edad"),
        ("Sexo", "sexo"),
        ("Nacimiento", "fecha_nacimiento"),
        ("Teléfono", "telefono"),
        ("Correo", "correo"),
        ("Dirección", "direccion"),
        ("Sangre", "tipo_sangre"),
        ("Seguro médico", "seguro_medico"),
    ]
    for etiqueta, clave in campos:
        print(f"   {etiqueta:<16}: {paciente.get(clave, '')}")
    asociadas = citas.contar_citas_paciente(
        paciente.get("documento", ""), nombre
    )
    print()
    print(f"   Citas asociadas : {asociadas}")
    print()
    print("  [E] Eliminar paciente   [0] Volver")
    print()
    op = _opcion().lower()
    if op == "0":
        volver()
    elif op == "e":
        _eliminar_paciente(paciente, asociadas)
    else:
        _aviso("error", "Opción inválida.")

def _eliminar_paciente(paciente, asociadas):
    nombre = f"{paciente.get('nombre', '')} {paciente.get('apellido', '')}".strip()
    if asociadas:
        _aviso(
            "error",
            f"No se puede eliminar: tiene {asociadas} cita(s) registrada(s).",
        )
        return
    if not confirmar(f"¿Eliminar a {nombre}?"):
        _aviso("info", "Eliminación cancelada.")
        return
    try:
        eliminado = pacientes.eliminar_paciente(paciente.get("documento", ""))
    except ValueError as error:
        _aviso("error", str(error))
        return
    if not eliminado:
        _aviso("error", "El paciente ya no existe en el archivo.")
        return
    _aviso("ok", f"Paciente eliminado: {nombre}. Puedes revertirlo con Deshacer.")
    volver()

def pantalla_paciente_nuevo():
    datos = _formulario(
        "Registrar nuevo paciente",
        [
            ("documento", "Documento", "texto", None),
            ("nombre", "Nombre", "texto", None),
            ("apellido", "Apellido", "texto", None),
            ("edad", "Edad", "entero", None),
            ("sexo", "Sexo", "opcion", ["masculino", "femenino"]),
            ("fecha_nacimiento", "Fecha de nacimiento", "texto", None),
            ("telefono", "Teléfono", "texto", None),
            ("direccion", "Dirección", "texto", None),
            ("correo", "Correo electrónico", "texto", None),
            ("tipo_sangre", "Tipo de sangre", "texto", None),
            ("seguro_medico", "Seguro médico", "texto", None),
        ],
    )
    if datos is None:
        volver()
        return
    try:
        pacientes.registrar_paciente(datos)
    except (OSError, ValueError, TypeError, KeyError) as error:
        _aviso("error", f"No se pudo registrar el paciente: {error}")
        return
    _aviso(
        "ok", f"Paciente registrado: {datos['nombre']} {datos['apellido']}."
    )
    volver()

# ---------------- Médicos ----------------

def pantalla_medicos():
    _titulo("Médicos", "Profesionales registrados en el sistema")
    resultado = medicos.buscar_medicos(_estado["busqueda_medicos"])
    _estado["lista_medicos"] = resultado["elementos"]
    origen = (
        f"búsqueda «{_estado['busqueda_medicos']}»"
        if _estado["busqueda_medicos"]
        else "listado completo"
    )
    print(
        f"  {len(resultado['elementos'])} resultado(s) · "
        f"{resultado['algoritmo']} · {origen}"
    )
    print()
    filas = [
        (
            f"{m.get('nombre', '')} {m.get('apellido', '')}".strip(),
            m.get("documento", ""),
            m.get("especialidad", ""),
            m.get("consultorio", ""),
            m.get("horario", ""),
        )
        for m in resultado["elementos"]
    ]
    imprimir_tabla(
        ("Médico", "Documento", "Especialidad", "Consultorio", "Horario"),
        filas,
        maximos=(28, 26, 18, 12, 18),
        numerar=True,
    )
    print()
    if resultado["elementos"]:
        print("  Escribe el número del médico para ver su ficha.")
    print("  [B] Buscar   [L] Limpiar búsqueda   [N] Registrar médico   [0] Volver")
    print()
    op = _opcion().lower()
    if op == "0":
        volver()
    elif op == "b":
        texto = _leer("  Buscar (vacío para mostrar todos): ").strip()
        _estado["busqueda_medicos"] = texto
    elif op == "l":
        _estado["busqueda_medicos"] = ""
    elif op == "n":
        ir("medico_nuevo")
    elif op.isdigit() and 1 <= int(op) <= len(resultado["elementos"]):
        medico = resultado["elementos"][int(op) - 1]
        _estado["detalle_medico"] = medico.get("documento", "")
        ir("medico_detalle")
    else:
        _aviso("error", "Opción inválida.")

def pantalla_medico_detalle():
    medico = (
        medicos.buscar_por_documento(_estado["detalle_medico"])
        if _estado["detalle_medico"]
        else None
    )
    if medico is None:
        _aviso("error", "El médico ya no existe en el archivo.")
        volver()
        return
    nombre = f"{medico.get('nombre', '')} {medico.get('apellido', '')}".strip()
    _titulo("Ficha del médico", nombre)
    campos = [
        ("Documento", "documento"),
        ("Nombre", "nombre"),
        ("Apellido", "apellido"),
        ("Teléfono", "telefono"),
        ("Correo", "correo"),
        ("Módulo", "modulo"),
        ("Especialidad", "especialidad"),
        ("Consultorio", "consultorio"),
        ("Horario", "horario"),
    ]
    for etiqueta, clave in campos:
        print(f"   {etiqueta:<16}: {medico.get(clave, '')}")
    asociadas = citas.contar_citas_medico(nombre)
    print()
    print(f"   Citas asociadas : {asociadas}")
    print()
    print("  [E] Eliminar médico   [0] Volver")
    print()
    op = _opcion().lower()
    if op == "0":
        volver()
    elif op == "e":
        _eliminar_medico(medico, asociadas)
    else:
        _aviso("error", "Opción inválida.")

def _eliminar_medico(medico, asociadas):
    nombre = f"{medico.get('nombre', '')} {medico.get('apellido', '')}".strip()
    if asociadas:
        _aviso(
            "error",
            f"No se puede eliminar: tiene {asociadas} cita(s) registrada(s).",
        )
        return
    if not confirmar(f"¿Eliminar al médico {nombre}?"):
        _aviso("info", "Eliminación cancelada.")
        return
    try:
        eliminado = medicos.eliminar_medico(medico.get("documento", ""))
    except ValueError as error:
        _aviso("error", str(error))
        return
    if not eliminado:
        _aviso("error", "El médico ya no existe en el archivo.")
        return
    _aviso("ok", f"Médico eliminado: {nombre}. Puedes revertirlo con Deshacer.")
    volver()

def pantalla_medico_nuevo():
    datos = _formulario(
        "Registrar nuevo médico",
        [
            ("documento", "Documento", "texto", None),
            ("nombre", "Nombre", "texto", None),
            ("apellido", "Apellido", "texto", None),
            ("telefono", "Teléfono", "texto", None),
            ("correo", "Correo electrónico", "texto", None),
            ("modulo", "Módulo", "texto", None),
            ("especialidad", "Especialidad", "texto", None),
            ("consultorio", "Consultorio", "texto", None),
            ("horario", "Horario", "texto", None),
        ],
    )
    if datos is None:
        volver()
        return
    try:
        medicos.registrar_medico(datos)
    except (OSError, ValueError, TypeError, KeyError) as error:
        _aviso("error", f"No se pudo registrar el médico: {error}")
        return
    _aviso(
        "ok", f"Médico registrado: {datos['nombre']} {datos['apellido']}."
    )
    volver()

# ---------------- Citas ----------------

def pantalla_citas():
    _titulo("Citas", "Consulta y seguimiento de citas médicas")
    partes = []
    for clave, nombre in (
        ("t", "Todas"),
        ("p", "Pendiente"),
        ("e", ESTADO_ESPERA),
        ("r", "Realizada"),
        ("c", "Cancelada"),
    ):
        etiqueta = f"[{clave.upper()}] {nombre}"
        if nombre == _estado["filtro_citas"]:
            partes.append(c(etiqueta, COLORES["NEGRITA"], COLORES["AZUL"]))
        else:
            partes.append(etiqueta)
    print("  " + "   ".join(partes))
    print()
    resultado = citas.buscar_citas(
        _estado["busqueda_citas"],
        None if _estado["filtro_citas"] == "Todas" else _estado["filtro_citas"],
    )
    _estado["lista_citas"] = resultado["elementos"]
    origen = (
        f"búsqueda «{_estado['busqueda_citas']}»"
        if _estado["busqueda_citas"]
        else "listado completo"
    )
    print(
        f"  {len(resultado['elementos'])} resultado(s) · "
        f"{resultado['algoritmo']} · {origen}"
    )
    print()
    filas = [
        (
            ci.get("paciente", ""),
            ci.get("medico", ""),
            ci.get("fecha", ""),
            ci.get("hora", ""),
            _etiqueta_estado(ci),
        )
        for ci in resultado["elementos"]
    ]
    imprimir_tabla(
        ("Paciente", "Médico", "Fecha", "Hora", "Estado"),
        filas,
        maximos=(28, 26, 12, 8, 18),
        numerar=True,
    )
    print()
    if resultado["elementos"]:
        print("  Escribe el número de la cita para ver su detalle.")
    print("  [B] Buscar   [L] Limpiar búsqueda   [N] Agendar cita   [0] Volver")
    print()
    op = _opcion().lower()
    if op == "0":
        volver()
    elif op in CLAVES_FILTRO:
        _estado["filtro_citas"] = CLAVES_FILTRO[op]
    elif op == "b":
        texto = _leer("  Buscar (texto o fecha dd/mm/aaaa): ").strip()
        _estado["busqueda_citas"] = texto
    elif op == "l":
        _estado["busqueda_citas"] = ""
    elif op == "n":
        ir("cita_nueva")
    elif op.isdigit() and 1 <= int(op) <= len(resultado["elementos"]):
        cita = resultado["elementos"][int(op) - 1]
        _estado["cita_actual"] = cita
        ir("cita_detalle")
    else:
        _aviso("error", "Opción inválida.")

def pantalla_cita_nueva():
    ps = pacientes.cargar_pacientes()
    ms = medicos.cargar_medicos()
    if not ps or not ms:
        _aviso("aviso", "Debe existir al menos un paciente y un médico.")
        volver()
        return
    _titulo("Agendar nueva cita", "Selecciona paciente, médico, fecha y hora")
    paciente = _elegir(
        "Paciente",
        ps,
        lambda p: f"{p.get('nombre', '')} {p.get('apellido', '')}".strip()
        + f"  —  {p.get('documento', '')}",
    )
    if paciente is None:
        volver()
        return
    medico = _elegir(
        "Médico",
        ms,
        lambda m: f"{m.get('nombre', '')} {m.get('apellido', '')}".strip()
        + f"  —  {m.get('especialidad', '')}",
    )
    if medico is None:
        volver()
        return
    fecha = _campo_fecha("Fecha")
    if fecha is None:
        volver()
        return
    hora = _campo_hora("Hora")
    if hora is None:
        volver()
        return
    tipo = _campo_opcion("Tipo de cita", ["presencial", "virtual"])
    if tipo is None:
        volver()
        return
    motivo = _campo_obligatorio("Motivo de consulta")
    if motivo is None:
        volver()
        return
    observaciones = _campo_obligatorio("Observaciones")
    if observaciones is None:
        volver()
        return

    datos = {
        "paciente": f"{paciente.get('nombre', '')} {paciente.get('apellido', '')}".strip(),
        "documento_paciente": paciente.get("documento", ""),
        "medico": f"{medico.get('nombre', '')} {medico.get('apellido', '')}".strip(),
        "especialidad": medico.get("especialidad", ""),
        "modulo": medico.get("modulo", ""),
        "fecha": fecha,
        "hora": hora,
        "tipo": tipo,
        "motivo": motivo,
        "observaciones": observaciones,
        "estado": "Pendiente",
    }
    try:
        guardada = citas.agregar_cita(datos)
    except (OSError, ValueError, TypeError, KeyError) as error:
        _aviso("error", f"No se pudo agendar la cita: {error}")
        return
    if guardada.get("estado") == ESTADO_ESPERA:
        _aviso(
            "aviso",
            f"Espacio ocupado. La cita quedó En espera en la posición "
            f"{guardada.get('posicion_espera', '?')}. Se promoverá sola "
            "al liberarse el turno.",
        )
    else:
        _aviso("ok", "Cita agendada correctamente.")
    volver()

def pantalla_cita_detalle():
    cita = _estado["cita_actual"]
    if not isinstance(cita, dict):
        _aviso("error", "No hay una cita seleccionada.")
        volver()
        return
    estado = cita.get("estado", "Pendiente")
    _titulo("Detalle de la cita", cita.get("paciente", ""))
    campos = [
        ("Paciente", "paciente"),
        ("Documento", "documento_paciente"),
        ("Médico", "medico"),
        ("Especialidad", "especialidad"),
        ("Fecha", "fecha"),
        ("Hora", "hora"),
        ("Módulo", "modulo"),
        ("Tipo", "tipo"),
    ]
    for etiqueta, clave in campos:
        print(f"   {etiqueta:<16}: {cita.get(clave, '')}")
    print(f"   {'Estado':<16}: {_etiqueta_estado(cita)}")
    print()
    print(f"   {'Motivo':<16}: {cita.get('motivo', '')}")
    print(f"   {'Observaciones':<16}: {cita.get('observaciones', '')}")
    if estado == ESTADO_ESPERA:
        print()
        todas = citas.cargar_citas()
        espacio = esperas.clave_espacio(cita)
        en_fila = esperas.en_espera_del_espacio(todas, espacio)
        activa = next(
            (
                x
                for x in todas
                if esperas.clave_espacio(x) == espacio
                and x.get("estado")
                not in ("Realizada", "Cancelada", ESTADO_ESPERA)
            ),
            None,
        )
        print(c("  EN ESPERA", COLORES["NEGRITA"], COLORES["CIAN"]))
        print(
            f"   Posición {cita.get('posicion_espera', '?')} de {len(en_fila)}"
        )
        if activa:
            print(f"   Ocupa el turno: {activa.get('paciente', '')}")
        else:
            print(
                "   El espacio está libre; se promoverá al cerrarse la cita activa."
            )
    print()
    acciones = []
    if estado == "Pendiente":
        acciones.append("[R] Marcar realizada")
    if estado in ("Pendiente", ESTADO_ESPERA):
        acciones.append("[C] Cancelar cita")
    acciones.append("[E] Eliminar cita")
    print("  " + "   ".join(acciones + ["[0] Volver"]))
    print()
    op = _opcion().lower()
    if op == "0":
        volver()
    elif op == "r" and estado == "Pendiente":
        _marcar_realizada(cita)
    elif op == "c" and estado in ("Pendiente", ESTADO_ESPERA):
        _cancelar_cita(cita)
    elif op == "e":
        _eliminar_cita(cita)
    else:
        _aviso("error", "Opción inválida.")

def _marcar_realizada(cita):
    indice = _indice_de_cita(cita)
    if indice is None:
        _aviso("error", "La cita ya no existe en el archivo.")
        return
    if not confirmar(f"¿Marcar como realizada la cita de {cita.get('paciente', '')}?"):
        _aviso("info", "Acción cancelada.")
        return
    atendida, hubo_promocion = citas.marcar_como_realizada(indice)
    if atendida is None:
        _aviso("error", "No se pudo actualizar la cita.")
        return
    if hubo_promocion:
        _aviso(
            "ok",
            "Cita realizada. La siguiente de la fila pasó a Pendiente y ocupa ese espacio.",
        )
    else:
        _aviso("ok", "Cita marcada como realizada.")
    volver()

def _cancelar_cita(cita):
    if _indice_de_cita(cita) is None:
        _aviso("error", "La cita ya no existe en el archivo.")
        return
    if not confirmar(
        f"¿Cancelar la cita de {cita.get('paciente', '')} ({cita.get('fecha', '')} {cita.get('hora', '')})?"
    ):
        _aviso("info", "Acción cancelada.")
        return
    promocion = citas.cancelar_cita(cita)
    volver()
    if promocion is not None:
        _aviso(
            "ok",
            f"Cita cancelada. {promocion.get('paciente', '')} salió de la "
            "fila de espera y ahora ocupa ese espacio como Pendiente.",
        )
    else:
        _aviso("ok", "La cita quedó cancelada.")

def _eliminar_cita(cita):
    estado = cita.get("estado", "Pendiente")
    print()
    if estado != "Realizada":
        print(
            c(
                f"  AVISO: la cita está en estado «{estado}» y aún no se ha completado.",
                COLORES["AMARILLO"],
            )
        )
    if not confirmar("¿Eliminar esta cita?"):
        _aviso("info", "Eliminación cancelada.")
        return
    try:
        eliminada = citas.eliminar_cita(cita)
    except (OSError, ValueError, TypeError, KeyError) as error:
        _aviso("error", f"No se pudo eliminar la cita: {error}")
        return
    if not eliminada:
        _aviso("error", "La cita ya no existe en el archivo.")
        return
    _aviso("ok", "Cita eliminada. Puedes revertirlo con Deshacer.")
    volver()

if __name__ == "__main__":
    inicializar_estado()
    ejecutar()
