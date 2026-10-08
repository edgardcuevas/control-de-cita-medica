import json, os
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

    registros.remove(medico)
    _guardar_medicos(registros)
    return True
