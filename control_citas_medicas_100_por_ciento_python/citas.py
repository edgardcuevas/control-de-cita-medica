import json, os

from almacenamiento import cargar_json_lista, guardar_json_atomico

ARCHIVO = os.path.join(os.path.dirname(__file__), "archivos", "citas.json")

def cargar_citas():
    try:
        with open(ARCHIVO, "r", encoding="utf-8") as archivo:
            datos = json.load(archivo)
            if not isinstance(datos, list):
                return []
            for cita in datos:
                cita.setdefault("estado", "Pendiente")
            return datos
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def _guardar_citas(citas):
    guardar_json_atomico(ARCHIVO, citas)


def contar_citas_paciente(documento, nombre=None):
    registros = cargar_json_lista(ARCHIVO)
    documento = str(documento).casefold()
    nombre = (nombre or "").casefold()
    return sum(
        1
        for cita in registros
        if str(cita.get("documento_paciente", "")).casefold() == documento
        or (
            not cita.get("documento_paciente")
            and nombre
            and str(cita.get("paciente", "")).casefold() == nombre
        )
    )


def contar_citas_medico(nombre):
    registros = cargar_json_lista(ARCHIVO)
    nombre = str(nombre).casefold()
    return sum(
        1 for cita in registros if str(cita.get("medico", "")).casefold() == nombre
    )


def eliminar_cita(cita):
    if not isinstance(cita, dict):
        raise ValueError("La cita seleccionada no es válida.")
    registros = cargar_json_lista(ARCHIVO)
    cita_normalizada = dict(cita)
    cita_normalizada.setdefault("estado", "Pendiente")
    for posicion, registro in enumerate(registros):
        registro_normalizado = dict(registro)
        registro_normalizado.setdefault("estado", "Pendiente")
        if registro_normalizado == cita_normalizada:
            del registros[posicion]
            _guardar_citas(registros)
            return True
    return False

def agregar_cita(cita):
    citas = cargar_citas()
    citas.append(cita)
    _guardar_citas(citas)

def marcar_como_realizada(posicion):
    citas = cargar_citas()
    if 0 <= posicion < len(citas):
        citas[posicion]["estado"] = "Realizada"
        _guardar_citas(citas)
