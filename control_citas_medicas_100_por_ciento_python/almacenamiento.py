import json
import os
import tempfile


def cargar_json_lista(ruta):
    try:
        with open(ruta, "r", encoding="utf-8") as archivo:
            datos = json.load(archivo)
    except FileNotFoundError:
        return []
    if not isinstance(datos, list):
        raise ValueError(f"El archivo {ruta} no contiene una lista JSON válida.")
    if not all(isinstance(registro, dict) for registro in datos):
        raise ValueError(f"El archivo {ruta} contiene registros JSON no válidos.")
    return datos


def guardar_json_atomico(ruta, datos):
    directorio = os.path.dirname(ruta)
    os.makedirs(directorio, exist_ok=True)
    temporal = None
    try:
        with tempfile.NamedTemporaryFile(
            mode="w",
            encoding="utf-8",
            dir=directorio,
            prefix=".datos-",
            suffix=".tmp",
            delete=False,
        ) as archivo:
            temporal = archivo.name
            json.dump(datos, archivo, ensure_ascii=False, indent=4)
            archivo.flush()
            os.fsync(archivo.fileno())
        os.replace(temporal, ruta)
    finally:
        if temporal and os.path.exists(temporal):
            os.remove(temporal)
