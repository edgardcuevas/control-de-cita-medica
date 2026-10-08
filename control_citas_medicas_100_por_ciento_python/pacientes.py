import json, os

ARCHIVO = os.path.join(os.path.dirname(__file__), "archivos", "pacientes.json")

def cargar_pacientes():
    try:
        with open(ARCHIVO, "r", encoding="utf-8") as archivo:
            datos = json.load(archivo)
            return datos if isinstance(datos, list) else []
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def _guardar_pacientes(pacientes):
    os.makedirs(os.path.dirname(ARCHIVO), exist_ok=True)
    with open(ARCHIVO, "w", encoding="utf-8") as archivo:
        json.dump(pacientes, archivo, ensure_ascii=False, indent=4)

def registrar_paciente(datos):
    pacientes = cargar_pacientes()
    pacientes.append(datos)
    _guardar_pacientes(pacientes)
    return datos
