
import json
import os
import tempfile
from datetime import datetime

import estructuras

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "archivos")
HISTORIAL_FILE = os.path.join(DATA_DIR, "historial.json")
BITACORA_FILE = os.path.join(DATA_DIR, "bitacora.txt")

#: Cuantas acciones se pueden deshacer como maximo (las mas antiguas se descartan).
LIMITE_PILA = 25
#: Cuantas lineas de bitacora se acumulan antes de volcar a disco.
LIMITE_COLA = 10

_pila = estructuras.pila_crear()
_cola = estructuras.cola_crear()


# ---------------------------------------------------------------- Pila

def registrar_accion(etiqueta, instantanea):
    estructuras.pila_apilar(_pila, {
        "etiqueta": etiqueta,
        "instantanea": instantanea,
        "marca": datetime.now().isoformat(timespec="seconds"),
    })
    # Si se supera el limite se descarta la accion mas antigua (el fondo de
    # la pila), nunca la que se acaba de registrar.
    while estructuras.pila_tamano(_pila) > LIMITE_PILA:
        del _pila[0]
    _persistir()
    _encolar_bitacora(etiqueta, instantanea.get("entidad", ""))


def deshacer():
    """Desapila y devuelve la ultima instantanea, o ``None`` si no hay ninguna."""
    if estructuras.pila_esta_vacia(_pila):
        return None
    entrada = estructuras.pila_desapilar(_pila)
    _persistir()
    return entrada


def hay_pendientes():
    """True si hay alguna accion que todavia se puede deshacer."""
    return not estructuras.pila_esta_vacia(_pila)


def etiqueta_pendiente():
    """Devuelve la etiqueta de la proxima accion a deshacer, o ``None``."""
    if estructuras.pila_esta_vacia(_pila):
        return None
    return estructuras.pila_cima(_pila)["etiqueta"]


def limpiar():
    """Vacia la pila de historial."""
    while not estructuras.pila_esta_vacia(_pila):
        estructuras.pila_desapilar(_pila)
    _persistir()


def _persistir():
    """Guarda la pila en archivos/historial.json de forma atomica."""
    os.makedirs(DATA_DIR, exist_ok=True)
    datos = estructuras.pila_volcar(_pila)
    fd, temporal = tempfile.mkstemp(prefix="historial_", suffix=".tmp", dir=DATA_DIR)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as archivo:
            json.dump(datos, archivo, ensure_ascii=False, indent=2)
        os.replace(temporal, HISTORIAL_FILE)
    finally:
        if os.path.exists(temporal):
            os.remove(temporal)


def _cargar():
    """Recupera la pila guardada al iniciar la aplicacion."""
    if not os.path.exists(HISTORIAL_FILE):
        return
    try:
        with open(HISTORIAL_FILE, "r", encoding="utf-8") as archivo:
            datos = json.load(archivo)
    except (json.JSONDecodeError, OSError):
        return
    if not isinstance(datos, list):
        return
    for entrada in reversed(datos[-LIMITE_PILA:]):
        if isinstance(entrada, dict) and "etiqueta" in entrada and "instantanea" in entrada:
            estructuras.pila_apilar(_pila, entrada)


# ---------------------------------------------------------------- Cola

def registrar_bitacora(accion, detalle=""):
    """Encola una linea de bitacora y la vuelca a disco si hay suficientes."""
    _encolar_bitacora(accion, detalle)


def _encolar_bitacora(accion, detalle=""):
    estructuras.cola_encolar(
        _cola,
        f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {accion}"
        + (f" - {detalle}" if detalle else ""),
    )
    while estructuras.cola_tamano(_cola) >= LIMITE_COLA:
        _volcar_bitacora()


def _volcar_bitacora():
    """Vacia la Cola escribiendo todas sus lineas pendientes en bitacora.txt."""
    if estructuras.cola_esta_vacia(_cola):
        return
    lineas = []
    while not estructuras.cola_esta_vacia(_cola):
        lineas.append(estructuras.cola_desencolar(_cola))
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(BITACORA_FILE, "a", encoding="utf-8") as archivo:
        archivo.write("\n".join(lineas) + "\n")


def volcar_bitacora():
    """Fuerza el volcado de la Cola a disco (se usa al cerrar sesion)."""
    _volcar_bitacora()


_cargar()