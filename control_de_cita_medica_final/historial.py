
import json
import os
import tempfile
from datetime import datetime

from estructuras import Pila, Cola

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "archivos")
HISTORIAL_FILE = os.path.join(DATA_DIR, "historial.json")
BITACORA_FILE = os.path.join(DATA_DIR, "bitacora.txt")

#: Cuantas acciones se pueden deshacer como maximo (las mas antiguas se descartan).
LIMITE_PILA = 25
#: Cuantas lineas de bitacora se acumulan antes de volcar a disco.
LIMITE_COLA = 10

_pila = Pila()
_cola = Cola()


# ---------------------------------------------------------------- Pila

def registrar_accion(etiqueta, instantanea):
    _pila.apilar({
        "etiqueta": etiqueta,
        "instantanea": instantanea,
        "marca": datetime.now().isoformat(timespec="seconds"),
    })
    while _pila.tamano() > LIMITE_PILA:
        _pila.desapilar()
    _persistir()
    _encolar_bitacora(etiqueta, instantanea.get("entidad", ""))


def deshacer():
    """Desapila y devuelve la ultima instantanea, o ``None`` si no hay ninguna."""
    if _pila.esta_vacia():
        return None
    entrada = _pila.desapilar()
    _persistir()
    return entrada


def hay_pendientes():
    """True si hay alguna accion que todavia se puede deshacer."""
    return not _pila.esta_vacia()


def etiqueta_pendiente():
    """Devuelve la etiqueta de la proxima accion a deshacer, o ``None``."""
    if _pila.esta_vacia():
        return None
    return _pila.cima()["etiqueta"]


def limpiar():
    """Vacia la pila de historial."""
    while not _pila.esta_vacia():
        _pila.desapilar()
    _persistir()


def _persistir():
    """Guarda la pila en archivos/historial.json de forma atomica."""
    os.makedirs(DATA_DIR, exist_ok=True)
    datos = _pila.volcar()
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
            _pila.apilar(entrada)


# ---------------------------------------------------------------- Cola

def registrar_bitacora(accion, detalle=""):
    """Encola una linea de bitacora y la vuelca a disco si hay suficientes."""
    _encolar_bitacora(accion, detalle)


def _encolar_bitacora(accion, detalle=""):
    _cola.encolar(f"[{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}] {accion}"
                  + (f" - {detalle}" if detalle else ""))
    while _cola.tamano() >= LIMITE_COLA:
        _volcar_bitacora()


def _volcar_bitacora():
    """Vacia la Cola escribiendo todas sus lineas pendientes en bitacora.txt."""
    if _cola.esta_vacia():
        return
    lineas = []
    while not _cola.esta_vacia():
        lineas.append(_cola.desencolar())
    os.makedirs(DATA_DIR, exist_ok=True)
    with open(BITACORA_FILE, "a", encoding="utf-8") as archivo:
        archivo.write("\n".join(lineas) + "\n")


def volcar_bitacora():
    """Fuerza el volcado de la Cola a disco (se usa al cerrar sesion)."""
    _volcar_bitacora()


_cargar()