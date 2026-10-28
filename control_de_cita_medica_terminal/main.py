"""MediCitas — Sistema de gestión de citas médicas.

Aplicación de terminal: toda la interacción se hace con menús numerados y
texto, sin ventanas ni interfaz gráfica. La presentación está en este archivo;
las reglas de negocio viven en pacientes.py, medicos.py, citas.py, usuarios.py,
esperas.py, historial.py, estructuras.py y busquedas.py.
"""

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
from estructuras import ColaPrioridad, Pila
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


class Color:
    RESET = "\033[0m"
    NEGRITA = "\033[1m"
    AZUL = "\033[94m"
    VERDE = "\033[92m"
    AMARILLO = "\033[93m"
    ROJO = "\033[91m"
    CIAN = "\033[96m"
    GRIS = "\033[90m"
    BLANCO = "\033[97m"


def c(texto, *estilos):
    if not USAR_COLOR:
        return str(texto)
    return "".join(estilos) + str(texto) + Color.RESET


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

    print(c(formatear(columnas), Color.NEGRITA, Color.GRIS))
    print(c("  " + "  ".join("─" * w for w in anchos), Color.GRIS))
    if not filas:
        print(c("  (sin registros)", Color.GRIS))
    else:
        for fila in filas:
            print(formatear(fila))


# ============================================================
# Entrada y salida auxiliares
# ============================================================

class SalirPrograma(Exception):
    pass


def leer(prompt=""):
    try:
        return input(prompt)
    except (EOFError, KeyboardInterrupt):
        print()
        raise SalirPrograma()


def leer_password(prompt="  Contraseña: "):
    if sys.stdin.isatty():
        try:
            return getpass.getpass(prompt)
        except (EOFError, KeyboardInterrupt):
            print()
            raise SalirPrograma()
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
        raise SalirPrograma()


def confirmar(pregunta, por_defecto=False):
    etiqueta = " [S/n]: " if por_defecto else " [s/N]: "
    respuesta = leer(f"  {pregunta}{etiqueta}").strip().lower()
    if not respuesta:
        return por_defecto
    return respuesta in ("s", "si", "sí", "y", "yes")


# ============================================================
# Aplicación
# ============================================================


class App:
    CLAVES_FILTRO = {
        "t": "Todas",
        "p": "Pendiente",
        "e": ESTADO_ESPERA,
        "r": "Realizada",
        "c": "Cancelada",
    }

    def __init__(self):
        self.usuario = None
        self.pantalla = "login"
        self.pila = Pila()
        self.aviso_pendiente = None
        self.busqueda_pacientes = ""
        self.busqueda_medicos = ""
        self.busqueda_citas = ""
        self.filtro_citas = "Todas"
        self.detalle_paciente = None
        self.detalle_medico = None
        self.cita_actual = None
        self.lista_pacientes = []
        self.lista_medicos = []
        self.lista_citas = []

    # ---------------- Navegación ----------------

    def ir(self, pantalla):
        if pantalla != self.pantalla:
            self.pila.apilar(self.pantalla)
        self.pantalla = pantalla

    def volver(self):
        self.pantalla = (
            self.pila.desapilar() if not self.pila.esta_vacia() else "menu"
        )

    # ---------------- Bucle principal ----------------

    def ejecutar(self):
        try:
            while self.pantalla != "salir":
                limpiar()
                self._cabecera()
                if self.aviso_pendiente:
                    tipo, texto = self.aviso_pendiente
                    self.aviso_pendiente = None
                    color = {
                        "ok": Color.VERDE,
                        "error": Color.ROJO,
                        "aviso": Color.AMARILLO,
                        "info": Color.CIAN,
                    }.get(tipo, Color.CIAN)
                    print()
                    print(c(f"  {texto}", color))
                    print()
                try:
                    getattr(self, "pantalla_" + self.pantalla)()
                except (OSError, ValueError, TypeError, KeyError, RuntimeError) as error:
                    self.aviso_pendiente = (
                        "error",
                        f"No se pudo completar la operación: {error}",
                    )
        except SalirPrograma:
            pass
        finally:
            try:
                historial.volcar_bitacora()
            except OSError:
                pass
            limpiar()
            print(c("\n  Hasta luego. MediCitas.\n", Color.AZUL, Color.NEGRITA))

    def _aviso(self, tipo, texto):
        self.aviso_pendiente = (tipo, texto)

    # ---------------- Cabecera y helpers ----------------

    def _cabecera(self):
        ancho = ancho_terminal()
        print(c("═" * ancho, Color.AZUL))
        print(
            c("  MediCitas", Color.NEGRITA, Color.AZUL)
            + "  ·  Sistema de gestión de citas médicas"
        )
        if self.usuario:
            extra = f"Sesión: {self.usuario.get('email', '')}"
            if not self.pila.esta_vacia():
                extra += "   ·   [0] Volver disponible"
            print(c(f"  {extra}", Color.GRIS))
        print(c("═" * ancho, Color.AZUL))

    def _leer(self, prompt):
        return leer(prompt)

    def _opcion(self):
        return self._leer("  Opción: ").strip()

    def _titulo(self, titulo, subtitulo=""):
        print()
        print(c("  " + titulo.upper(), Color.NEGRITA, Color.AZUL))
        if subtitulo:
            print(c("  " + subtitulo, Color.GRIS))
        print(c("  " + "─" * (ancho_terminal() - 2), Color.GRIS))
        print()

    def _campo_obligatorio(self, etiqueta):
        while True:
            valor = self._leer(f"  {etiqueta}: ").strip()
            if valor.lower() == "cancelar":
                return None
            if valor:
                return valor
            print(c("  Este campo es obligatorio.", Color.ROJO))

    def _campo_entero(self, etiqueta):
        while True:
            valor = self._leer(f"  {etiqueta}: ").strip()
            if valor.lower() == "cancelar":
                return None
            try:
                numero = int(valor)
            except ValueError:
                print(c("  Escribe un número entero.", Color.ROJO))
                continue
            if numero < 0:
                print(c("  No puede ser negativo.", Color.ROJO))
                continue
            return numero

    def _campo_opcion(self, etiqueta, opciones):
        while True:
            print()
            for i, opcion in enumerate(opciones, 1):
                print(f"    {i}) {opcion}")
            valor = self._leer(f"  {etiqueta} [1-{len(opciones)}]: ").strip()
            if valor.lower() == "cancelar":
                return None
            if valor.isdigit() and 1 <= int(valor) <= len(opciones):
                return opciones[int(valor) - 1]
            print(c("  Opción inválida.", Color.ROJO))

    def _campo_fecha(self, etiqueta):
        while True:
            valor = self._leer(f"  {etiqueta} (dd/mm/aaaa): ").strip()
            if valor.lower() == "cancelar":
                return None
            try:
                datetime.strptime(valor, "%d/%m/%Y")
            except ValueError:
                print(c("  Fecha inválida. Usa dd/mm/aaaa.", Color.ROJO))
                continue
            return valor

    def _campo_hora(self, etiqueta):
        while True:
            valor = self._leer(f"  {etiqueta} (hh:mm): ").strip()
            if valor.lower() == "cancelar":
                return None
            try:
                datetime.strptime(valor, "%H:%M")
            except ValueError:
                print(c("  Hora inválida. Usa hh:mm (24 horas).", Color.ROJO))
                continue
            return valor

    def _formulario(self, titulo, campos):
        print()
        print(c(f"  {titulo}", Color.NEGRITA, Color.AZUL))
        print(c("  Escribe 'cancelar' en cualquier campo para volver.", Color.GRIS))
        datos = {}
        for clave, etiqueta, tipo, opciones in campos:
            if tipo == "entero":
                valor = self._campo_entero(etiqueta)
            elif tipo == "opcion":
                valor = self._campo_opcion(etiqueta, opciones)
            else:
                valor = self._campo_obligatorio(etiqueta)
            if valor is None:
                return None
            datos[clave] = valor
        return datos

    def _elegir(self, titulo, elementos, texto_fn):
        print()
        print(c(f"  {titulo}", Color.NEGRITA, Color.AZUL))
        for i, elemento in enumerate(elementos, 1):
            print(f"   [{i}] {texto_fn(elemento)}")
        print("   [0] Cancelar")
        print()
        while True:
            valor = self._leer("  Número: ").strip()
            if valor.lower() in ("0", "cancelar"):
                return None
            if valor.isdigit() and 1 <= int(valor) <= len(elementos):
                return elementos[int(valor) - 1]
            print(c("  Número inválido.", Color.ROJO))

    # ---------------- Auxiliares de datos ----------------

    def _proximas_citas(self, citas_lista, limite=5):
        cola = ColaPrioridad()
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
            cola.encolar(clave, cita)
        ordenadas = []
        while not cola.esta_vacia() and len(ordenadas) < limite:
            ordenadas.append(cola.desencolar())
        return ordenadas

    def _etiqueta_estado(self, cita):
        estado = cita.get("estado", "Pendiente")
        if estado == ESTADO_ESPERA:
            return f"{estado} · {cita.get('posicion_espera', '?')}º"
        return estado

    def _filas_espera(self, citas_lista):
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

    def _indice_de_cita(self, cita):
        registros = citas.cargar_citas()
        for indice, registro in enumerate(registros):
            if registro == cita:
                return indice
        return None

    # ---------------- Pantallas de autenticación ----------------

    def pantalla_login(self):
        if self.usuario is not None:
            self.pantalla = "menu"
            return
        self._titulo("Iniciar sesión", "Accede a tu cuenta para gestionar las citas.")
        print("  [1] Ingresar")
        print("  [2] Crear cuenta")
        print("  [0] Salir")
        print()
        op = self._opcion()
        if op == "1":
            email = self._campo_obligatorio("Correo electrónico")
            if email is None:
                return
            clave = leer_password("  Contraseña: ")
            if not clave:
                self._aviso("error", "Ingresa tu contraseña.")
                return
            try:
                usuario = usuarios.autenticar_usuario(email, clave)
            except RuntimeError as error:
                self._aviso("error", str(error))
                return
            if usuario:
                self.usuario = usuario
                self.pila = Pila()
                self.pantalla = "menu"
                self._aviso("ok", f"Bienvenido, {usuario.get('email', '')}.")
            else:
                self._aviso("error", "El correo o la contraseña son incorrectos.")
        elif op == "2":
            self.ir("registro")
        elif op == "0":
            self.pantalla = "salir"
        else:
            self._aviso("error", "Opción inválida.")

    def pantalla_registro(self):
        self._titulo("Crear cuenta", "Regístrate en MediCitas.")
        print(c("  Escribe 'cancelar' en cualquier campo para volver.", Color.GRIS))
        email = self._campo_obligatorio("Correo electrónico")
        if email is None:
            self.volver()
            return
        email = email.lower()
        clave = leer_password("  Contraseña (mínimo 8 caracteres): ")
        if not clave:
            self._aviso("error", "Ingresa una contraseña.")
            return
        confirmacion = leer_password("  Confirma la contraseña: ")
        if "@" not in email or "." not in email.split("@")[-1]:
            self._aviso("error", "Ingresa una dirección de correo válida.")
            return
        if len(clave) < 8:
            self._aviso("error", "La contraseña debe tener al menos 8 caracteres.")
            return
        if clave != confirmacion:
            self._aviso("error", "Las contraseñas no coinciden.")
            return
        try:
            usuarios.registrar_usuario(email, clave)
        except ValueError as error:
            self._aviso("error", str(error))
            return
        self._aviso("ok", "Cuenta creada correctamente. Ahora inicia sesión.")
        self.volver()

    # ---------------- Menú principal ----------------

    def pantalla_menu(self):
        if self.usuario is None:
            self.pantalla = "login"
            return
        pendiente = historial.etiqueta_pendiente()
        self._titulo("Menú principal", f"Sesión iniciada como {self.usuario.get('email', '')}")
        print("  [1] Panel de control")
        print("  [2] Pacientes")
        print("  [3] Médicos")
        print("  [4] Citas")
        if pendiente:
            print(f"  [5] Deshacer: {pendiente}")
        else:
            print(c("  [5] Deshacer (nada pendiente)", Color.GRIS))
        print("  [6] Cerrar sesión")
        print("  [0] Salir")
        print()
        op = self._opcion()
        if op == "1":
            self.ir("dashboard")
        elif op == "2":
            self.ir("pacientes")
        elif op == "3":
            self.ir("medicos")
        elif op == "4":
            self.ir("citas")
        elif op == "5":
            self._deshacer()
        elif op == "6":
            self._cerrar_sesion()
        elif op == "0":
            self.pantalla = "salir"
        else:
            self._aviso("error", "Opción inválida.")

    def _deshacer(self):
        pendiente = historial.etiqueta_pendiente()
        if pendiente is None:
            self._aviso("info", "No hay acciones pendientes por deshacer.")
            return
        if not confirmar(f"¿Deshacer «{pendiente}»?"):
            self._aviso("info", "Acción cancelada.")
            return
        entrada = historial.deshacer()
        if entrada is None:
            self._aviso("info", "No hay acciones pendientes por deshacer.")
            return
        instantanea = entrada.get("instantanea", {})
        entidad = instantanea.get("entidad")
        modulo = {"cita": citas, "paciente": pacientes, "medico": medicos}.get(entidad)
        try:
            revertido = modulo.revertir(instantanea) if modulo else False
        except (OSError, ValueError, TypeError, KeyError) as error:
            self._aviso("error", f"No se pudo deshacer: {error}")
            return
        if revertido:
            historial.registrar_bitacora(
                "Acción deshecha", entrada.get("etiqueta", "")
            )
            self._aviso("ok", f"Se revirtió: {entrada.get('etiqueta', '')}.")
        else:
            self._aviso(
                "error",
                f"La acción «{entrada.get('etiqueta', '')}» ya no se puede revertir.",
            )

    def _cerrar_sesion(self):
        if not confirmar("¿Deseas cerrar tu sesión?"):
            self._aviso("info", "Cierre de sesión cancelado.")
            return
        historial.volcar_bitacora()
        historial.limpiar()
        self.usuario = None
        self.pila = Pila()
        self.busqueda_pacientes = ""
        self.busqueda_medicos = ""
        self.busqueda_citas = ""
        self.filtro_citas = "Todas"
        self.detalle_paciente = None
        self.detalle_medico = None
        self.cita_actual = None
        self.pantalla = "login"
        self._aviso("info", "Sesión cerrada.")

    # ---------------- Panel de control ----------------

    def pantalla_dashboard(self):
        self._titulo("Panel de control", "Resumen general del sistema de citas médicas")
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

        print(c("  PRÓXIMAS CITAS", Color.NEGRITA, Color.AZUL))
        proximas = self._proximas_citas(cs)
        filas = [
            (
                c.get("paciente", ""),
                c.get("medico", ""),
                c.get("fecha", ""),
                c.get("hora", ""),
                self._etiqueta_estado(c),
            )
            for c in proximas
        ]
        imprimir_tabla(
            ("Paciente", "Médico", "Fecha", "Hora", "Estado"),
            filas,
            maximos=(30, 26, 12, 8, 16),
        )

        filas_espera = self._filas_espera(cs)
        if filas_espera:
            print()
            print(c("  FILAS DE ESPERA", Color.NEGRITA, Color.CIAN))
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
        op = self._opcion()
        if op == "1":
            self.ir("cita_nueva")
        elif op == "2":
            self.ir("citas")
        elif op == "0":
            self.volver()
        else:
            self._aviso("error", "Opción inválida.")

    # ---------------- Pacientes ----------------

    def pantalla_pacientes(self):
        self._titulo("Pacientes", "Registro y gestión de pacientes")
        resultado = pacientes.buscar_pacientes(self.busqueda_pacientes)
        self.lista_pacientes = resultado.elementos
        origen = (
            f"búsqueda «{self.busqueda_pacientes}»"
            if self.busqueda_pacientes
            else "listado completo"
        )
        print(f"  {len(resultado)} resultado(s) · {resultado.algoritmo} · {origen}")
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
            for p in resultado
        ]
        imprimir_tabla(
            ("Paciente", "Documento", "Edad", "Sexo", "Teléfono", "Sangre"),
            filas,
            maximos=(28, 26, 6, 10, 12, 8),
            numerar=True,
        )
        print()
        if resultado:
            print("  Escribe el número del paciente para ver su ficha.")
        print("  [B] Buscar   [L] Limpiar búsqueda   [N] Registrar paciente   [0] Volver")
        print()
        op = self._opcion().lower()
        if op == "0":
            self.volver()
        elif op == "b":
            texto = self._leer("  Buscar (vacío para mostrar todos): ").strip()
            self.busqueda_pacientes = texto
        elif op == "l":
            self.busqueda_pacientes = ""
        elif op == "n":
            self.ir("paciente_nuevo")
        elif op.isdigit() and 1 <= int(op) <= len(resultado):
            paciente = resultado[int(op) - 1]
            self.detalle_paciente = paciente.get("documento", "")
            self.ir("paciente_detalle")
        else:
            self._aviso("error", "Opción inválida.")

    def pantalla_paciente_detalle(self):
        paciente = (
            pacientes.buscar_por_documento(self.detalle_paciente)
            if self.detalle_paciente
            else None
        )
        if paciente is None:
            self._aviso("error", "El paciente ya no existe en el archivo.")
            self.volver()
            return
        nombre = f"{paciente.get('nombre', '')} {paciente.get('apellido', '')}".strip()
        self._titulo("Ficha del paciente", nombre)
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
        op = self._opcion().lower()
        if op == "0":
            self.volver()
        elif op == "e":
            self._eliminar_paciente(paciente, asociadas)
        else:
            self._aviso("error", "Opción inválida.")

    def _eliminar_paciente(self, paciente, asociadas):
        nombre = f"{paciente.get('nombre', '')} {paciente.get('apellido', '')}".strip()
        if asociadas:
            self._aviso(
                "error",
                f"No se puede eliminar: tiene {asociadas} cita(s) registrada(s).",
            )
            return
        if not confirmar(f"¿Eliminar a {nombre}?"):
            self._aviso("info", "Eliminación cancelada.")
            return
        try:
            eliminado = pacientes.eliminar_paciente(paciente.get("documento", ""))
        except ValueError as error:
            self._aviso("error", str(error))
            return
        if not eliminado:
            self._aviso("error", "El paciente ya no existe en el archivo.")
            return
        self._aviso("ok", f"Paciente eliminado: {nombre}. Puedes revertirlo con Deshacer.")
        self.volver()

    def pantalla_paciente_nuevo(self):
        datos = self._formulario(
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
            self.volver()
            return
        try:
            pacientes.registrar_paciente(datos)
        except (OSError, ValueError, TypeError, KeyError) as error:
            self._aviso("error", f"No se pudo registrar el paciente: {error}")
            return
        self._aviso(
            "ok", f"Paciente registrado: {datos['nombre']} {datos['apellido']}."
        )
        self.volver()

    # ---------------- Médicos ----------------

    def pantalla_medicos(self):
        self._titulo("Médicos", "Profesionales registrados en el sistema")
        resultado = medicos.buscar_medicos(self.busqueda_medicos)
        self.lista_medicos = resultado.elementos
        origen = (
            f"búsqueda «{self.busqueda_medicos}»"
            if self.busqueda_medicos
            else "listado completo"
        )
        print(f"  {len(resultado)} resultado(s) · {resultado.algoritmo} · {origen}")
        print()
        filas = [
            (
                f"{m.get('nombre', '')} {m.get('apellido', '')}".strip(),
                m.get("documento", ""),
                m.get("especialidad", ""),
                m.get("consultorio", ""),
                m.get("horario", ""),
            )
            for m in resultado
        ]
        imprimir_tabla(
            ("Médico", "Documento", "Especialidad", "Consultorio", "Horario"),
            filas,
            maximos=(28, 26, 18, 12, 18),
            numerar=True,
        )
        print()
        if resultado:
            print("  Escribe el número del médico para ver su ficha.")
        print("  [B] Buscar   [L] Limpiar búsqueda   [N] Registrar médico   [0] Volver")
        print()
        op = self._opcion().lower()
        if op == "0":
            self.volver()
        elif op == "b":
            texto = self._leer("  Buscar (vacío para mostrar todos): ").strip()
            self.busqueda_medicos = texto
        elif op == "l":
            self.busqueda_medicos = ""
        elif op == "n":
            self.ir("medico_nuevo")
        elif op.isdigit() and 1 <= int(op) <= len(resultado):
            medico = resultado[int(op) - 1]
            self.detalle_medico = medico.get("documento", "")
            self.ir("medico_detalle")
        else:
            self._aviso("error", "Opción inválida.")

    def pantalla_medico_detalle(self):
        medico = (
            medicos.buscar_por_documento(self.detalle_medico)
            if self.detalle_medico
            else None
        )
        if medico is None:
            self._aviso("error", "El médico ya no existe en el archivo.")
            self.volver()
            return
        nombre = f"{medico.get('nombre', '')} {medico.get('apellido', '')}".strip()
        self._titulo("Ficha del médico", nombre)
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
        op = self._opcion().lower()
        if op == "0":
            self.volver()
        elif op == "e":
            self._eliminar_medico(medico, asociadas)
        else:
            self._aviso("error", "Opción inválida.")

    def _eliminar_medico(self, medico, asociadas):
        nombre = f"{medico.get('nombre', '')} {medico.get('apellido', '')}".strip()
        if asociadas:
            self._aviso(
                "error",
                f"No se puede eliminar: tiene {asociadas} cita(s) registrada(s).",
            )
            return
        if not confirmar(f"¿Eliminar al médico {nombre}?"):
            self._aviso("info", "Eliminación cancelada.")
            return
        try:
            eliminado = medicos.eliminar_medico(medico.get("documento", ""))
        except ValueError as error:
            self._aviso("error", str(error))
            return
        if not eliminado:
            self._aviso("error", "El médico ya no existe en el archivo.")
            return
        self._aviso("ok", f"Médico eliminado: {nombre}. Puedes revertirlo con Deshacer.")
        self.volver()

    def pantalla_medico_nuevo(self):
        datos = self._formulario(
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
            self.volver()
            return
        try:
            medicos.registrar_medico(datos)
        except (OSError, ValueError, TypeError, KeyError) as error:
            self._aviso("error", f"No se pudo registrar el médico: {error}")
            return
        self._aviso(
            "ok", f"Médico registrado: {datos['nombre']} {datos['apellido']}."
        )
        self.volver()

    # ---------------- Citas ----------------

    def pantalla_citas(self):
        self._titulo("Citas", "Consulta y seguimiento de citas médicas")
        partes = []
        for clave, nombre in (
            ("t", "Todas"),
            ("p", "Pendiente"),
            ("e", ESTADO_ESPERA),
            ("r", "Realizada"),
            ("c", "Cancelada"),
        ):
            etiqueta = f"[{clave.upper()}] {nombre}"
            if nombre == self.filtro_citas:
                partes.append(c(etiqueta, Color.NEGRITA, Color.AZUL))
            else:
                partes.append(etiqueta)
        print("  " + "   ".join(partes))
        print()
        resultado = citas.buscar_citas(
            self.busqueda_citas,
            None if self.filtro_citas == "Todas" else self.filtro_citas,
        )
        self.lista_citas = resultado.elementos
        origen = (
            f"búsqueda «{self.busqueda_citas}»"
            if self.busqueda_citas
            else "listado completo"
        )
        print(f"  {len(resultado)} resultado(s) · {resultado.algoritmo} · {origen}")
        print()
        filas = [
            (
                ci.get("paciente", ""),
                ci.get("medico", ""),
                ci.get("fecha", ""),
                ci.get("hora", ""),
                self._etiqueta_estado(ci),
            )
            for ci in resultado
        ]
        imprimir_tabla(
            ("Paciente", "Médico", "Fecha", "Hora", "Estado"),
            filas,
            maximos=(28, 26, 12, 8, 18),
            numerar=True,
        )
        print()
        if resultado:
            print("  Escribe el número de la cita para ver su detalle.")
        print("  [B] Buscar   [L] Limpiar búsqueda   [N] Agendar cita   [0] Volver")
        print()
        op = self._opcion().lower()
        if op == "0":
            self.volver()
        elif op in self.CLAVES_FILTRO:
            self.filtro_citas = self.CLAVES_FILTRO[op]
        elif op == "b":
            texto = self._leer("  Buscar (texto o fecha dd/mm/aaaa): ").strip()
            self.busqueda_citas = texto
        elif op == "l":
            self.busqueda_citas = ""
        elif op == "n":
            self.ir("cita_nueva")
        elif op.isdigit() and 1 <= int(op) <= len(resultado):
            cita = resultado[int(op) - 1]
            self.cita_actual = cita
            self.ir("cita_detalle")
        else:
            self._aviso("error", "Opción inválida.")

    def pantalla_cita_nueva(self):
        ps = pacientes.cargar_pacientes()
        ms = medicos.cargar_medicos()
        if not ps or not ms:
            self._aviso("aviso", "Debe existir al menos un paciente y un médico.")
            self.volver()
            return
        self._titulo("Agendar nueva cita", "Selecciona paciente, médico, fecha y hora")
        paciente = self._elegir(
            "Paciente",
            ps,
            lambda p: f"{p.get('nombre', '')} {p.get('apellido', '')}".strip()
            + f"  —  {p.get('documento', '')}",
        )
        if paciente is None:
            self.volver()
            return
        medico = self._elegir(
            "Médico",
            ms,
            lambda m: f"{m.get('nombre', '')} {m.get('apellido', '')}".strip()
            + f"  —  {m.get('especialidad', '')}",
        )
        if medico is None:
            self.volver()
            return
        fecha = self._campo_fecha("Fecha")
        if fecha is None:
            self.volver()
            return
        hora = self._campo_hora("Hora")
        if hora is None:
            self.volver()
            return
        tipo = self._campo_opcion("Tipo de cita", ["presencial", "virtual"])
        if tipo is None:
            self.volver()
            return
        motivo = self._campo_obligatorio("Motivo de consulta")
        if motivo is None:
            self.volver()
            return
        observaciones = self._campo_obligatorio("Observaciones")
        if observaciones is None:
            self.volver()
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
            self._aviso("error", f"No se pudo agendar la cita: {error}")
            return
        if guardada.get("estado") == ESTADO_ESPERA:
            self._aviso(
                "aviso",
                f"Espacio ocupado. La cita quedó En espera en la posición "
                f"{guardada.get('posicion_espera', '?')}. Se promoverá sola "
                "al liberarse el turno.",
            )
        else:
            self._aviso("ok", "Cita agendada correctamente.")
        self.volver()

    def pantalla_cita_detalle(self):
        cita = self.cita_actual
        if not isinstance(cita, dict):
            self._aviso("error", "No hay una cita seleccionada.")
            self.volver()
            return
        estado = cita.get("estado", "Pendiente")
        self._titulo("Detalle de la cita", cita.get("paciente", ""))
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
        print(f"   {'Estado':<16}: {self._etiqueta_estado(cita)}")
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
            print(c("  EN ESPERA", Color.NEGRITA, Color.CIAN))
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
        op = self._opcion().lower()
        if op == "0":
            self.volver()
        elif op == "r" and estado == "Pendiente":
            self._marcar_realizada(cita)
        elif op == "c" and estado in ("Pendiente", ESTADO_ESPERA):
            self._cancelar_cita(cita)
        elif op == "e":
            self._eliminar_cita(cita)
        else:
            self._aviso("error", "Opción inválida.")

    def _marcar_realizada(self, cita):
        indice = self._indice_de_cita(cita)
        if indice is None:
            self._aviso("error", "La cita ya no existe en el archivo.")
            return
        if not confirmar(f"¿Marcar como realizada la cita de {cita.get('paciente', '')}?"):
            self._aviso("info", "Acción cancelada.")
            return
        atendida, hubo_promocion = citas.marcar_como_realizada(indice)
        if atendida is None:
            self._aviso("error", "No se pudo actualizar la cita.")
            return
        if hubo_promocion:
            self._aviso(
                "ok",
                "Cita realizada. La siguiente de la fila pasó a Pendiente y ocupa ese espacio.",
            )
        else:
            self._aviso("ok", "Cita marcada como realizada.")
        self.volver()

    def _cancelar_cita(self, cita):
        if self._indice_de_cita(cita) is None:
            self._aviso("error", "La cita ya no existe en el archivo.")
            return
        if not confirmar(
            f"¿Cancelar la cita de {cita.get('paciente', '')} ({cita.get('fecha', '')} {cita.get('hora', '')})?"
        ):
            self._aviso("info", "Acción cancelada.")
            return
        promocion = citas.cancelar_cita(cita)
        self.volver()
        if promocion is not None:
            self._aviso(
                "ok",
                f"Cita cancelada. {promocion.get('paciente', '')} salió de la "
                "fila de espera y ahora ocupa ese espacio como Pendiente.",
            )
        else:
            self._aviso("ok", "La cita quedó cancelada.")

    def _eliminar_cita(self, cita):
        estado = cita.get("estado", "Pendiente")
        print()
        if estado != "Realizada":
            print(
                c(
                    f"  AVISO: la cita está en estado «{estado}» y aún no se ha completado.",
                    Color.AMARILLO,
                )
            )
        if not confirmar("¿Eliminar esta cita?"):
            self._aviso("info", "Eliminación cancelada.")
            return
        try:
            eliminada = citas.eliminar_cita(cita)
        except (OSError, ValueError, TypeError, KeyError) as error:
            self._aviso("error", f"No se pudo eliminar la cita: {error}")
            return
        if not eliminada:
            self._aviso("error", "La cita ya no existe en el archivo.")
            return
        self._aviso("ok", "Cita eliminada. Puedes revertirlo con Deshacer.")
        self.volver()


if __name__ == "__main__":
    App().ejecutar()
