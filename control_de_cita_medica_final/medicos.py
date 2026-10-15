import json, os

import historial
from almacenamiento import cargar_json_lista, guardar_json_atomico

ARCHIVO = os.path.join(os.path.dirname(__file__), "archivos", "medicos.json")

def cargar_medicos():
    try:
        with open(ARCHIVO, "r", encoding="utf-8") as archivo:
            datos = json.load(archivo)
            return datos if isinstance(datos, list) else []
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def _guardar_medicos(medicos):
    guardar_json_atomico(ARCHIVO, medicos)

def registrar_medico(datos):
    medicos = cargar_medicos()
    medicos.append(datos)
    _guardar_medicos(medicos)
    historial.registrar_accion(
        "Registrar médico",
        {
            "tipo": "agregar",
            "entidad": "medico",
            "posicion": len(medicos) - 1,
            "datos": dict(datos),
        },
    )
    return datos


def eliminar_medico(documento):
    registros = cargar_json_lista(ARCHIVO)
    medico = next(
        (
            registro
            for registro in registros
            if str(registro.get("documento", "")).casefold()
            == str(documento).casefold()
        ),
        None,
    )
    if medico is None:
        return False

    from citas import contar_citas_medico

    nombre = f'{medico.get("nombre", "")} {medico.get("apellido", "")}'.strip()
    asociadas = contar_citas_medico(nombre)
    if asociadas:
        raise ValueError(
            f"No se puede eliminar el médico porque tiene {asociadas} "
            "cita(s) registrada(s). Elimine primero las citas."
        )

    posicion = registros.index(medico)
    registros.remove(medico)
    _guardar_medicos(registros)
    historial.registrar_accion(
        "Eliminar médico",
        {
            "tipo": "eliminar",
            "entidad": "medico",
            "posicion": posicion,
            "datos": dict(medico),
        },
    )
    return True


def revertir(instantanea):
    """Deshace una acción sobre médicos a partir de su instantánea."""
    tipo = instantanea.get("tipo")
    posicion = instantanea.get("posicion")
    if not isinstance(posicion, int) or posicion < 0:
        return False
    registros = cargar_json_lista(ARCHIVO)

    if tipo == "eliminar":
        if posicion > len(registros):
            return False
        registros.insert(posicion, instantanea.get("datos"))
        _guardar_medicos(registros)
        return True

    if tipo == "agregar":
        if posicion >= len(registros) or registros[posicion] != instantanea.get("datos"):
            return False
        del registros[posicion]
        _guardar_medicos(registros)
        return True

    return False