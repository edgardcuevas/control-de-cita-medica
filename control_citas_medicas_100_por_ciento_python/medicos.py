import json, os

ARCHIVO = os.path.join(os.path.dirname(__file__), "archivos", "medicos.json")

def cargar_medicos():
    try:
        with open(ARCHIVO, "r", encoding="utf-8") as archivo:
            datos = json.load(archivo)
            return datos if isinstance(datos, list) else []
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def _guardar_medicos(medicos):
    os.makedirs(os.path.dirname(ARCHIVO), exist_ok=True)
    with open(ARCHIVO, "w", encoding="utf-8") as archivo:
        json.dump(medicos, archivo, ensure_ascii=False, indent=4)

def registrar_medico(datos):
    medicos = cargar_medicos()
    medicos.append(datos)
    _guardar_medicos(medicos)
    return datos
