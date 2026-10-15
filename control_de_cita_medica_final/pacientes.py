import json, os

import historial
from almacenamiento import cargar_json_lista, guardar_json_atomico

ARCHIVO = os.path.join(os.path.dirname(__file__), "archivos", "pacientes.json")

def cargar_pacientes():
    try:
        with open(ARCHIVO, "r", encoding="utf-8") as archivo:
            datos = json.load(archivo)
            return datos if isinstance(datos, list) else []
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def _guardar_pacientes(pacientes):
    guardar_json_atomico(ARCHIVO, pacientes)

def registrar_paciente(datos):
    pacientes = cargar_pacientes()
    pacientes.append(datos)
    _guardar_pacientes(pacientes)
    historial.registrar_accion(
        "Registrar paciente",
        {
            "tipo": "agregar",
            "entidad": "paciente",
            "posicion": len(pacientes) - 1,
            "datos": dict(datos),
        },
    )
    return datos


def eliminar_paciente(documento):
    registros = cargar_json_lista(ARCHIVO)
    paciente = next(
        (
            registro
            for registro in registros
            if str(registro.get("documento", "")).casefold()
            == str(documento).casefold()
        ),
        None,
    )
    if paciente is None:
        return False

    from citas import contar_citas_paciente

    nombre = f'{paciente.get("nombre", "")} {paciente.get("apellido", "")}'.strip()
    asociadas = contar_citas_paciente(documento, nombre)
    if asociadas:
        raise ValueError(
            f"No se puede eliminar el paciente porque tiene {asociadas} "
            "cita(s) registrada(s). Elimine primero las citas."
        )

    posicion = registros.index(paciente)
    registros.remove(paciente)
    _guardar_pacientes(registros)
    historial.registrar_accion(
        "Eliminar paciente",
        {
            "tipo": "eliminar",
            "entidad": "paciente",
            "posicion": posicion,
            "datos": dict(paciente),
        },
    )
    return True


def revertir(instantanea):
    """Deshace una acción sobre pacientes a partir de su instantánea."""
    tipo = instantanea.get("tipo")
    posicion = instantanea.get("posicion")
    if not isinstance(posicion, int) or posicion < 0:
        return False
    registros = cargar_json_lista(ARCHIVO)

    if tipo == "eliminar":
        if posicion > len(registros):
            return False
        registros.insert(posicion, instantanea.get("datos"))
        _guardar_pacientes(registros)
        return True

    if tipo == "agregar":
        if posicion >= len(registros) or registros[posicion] != instantanea.get("datos"):
            return False
        del registros[posicion]
        _guardar_pacientes(registros)
        return True

    return False