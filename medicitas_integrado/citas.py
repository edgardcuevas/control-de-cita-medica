import json, os

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
    os.makedirs(os.path.dirname(ARCHIVO), exist_ok=True)
    with open(ARCHIVO, "w", encoding="utf-8") as archivo:
        json.dump(citas, archivo, ensure_ascii=False, indent=4)

def agregar_cita(cita):
    citas = cargar_citas()
    citas.append(cita)
    _guardar_citas(citas)

def marcar_como_realizada(posicion):
    citas = cargar_citas()
    if 0 <= posicion < len(citas):
        citas[posicion]["estado"] = "Realizada"
        _guardar_citas(citas)
