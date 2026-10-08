import json
import os


ARCHIVO = os.path.join(os.path.dirname(__file__), "archivos", "medicos.json")


def _texto(mensaje):
    while True:
        valor = input(mensaje).strip()
        if valor:
            return valor
        print("El campo no puede quedar vacío.")


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


def registrar_medico():
    medico = {
        "documento": _texto("Ingrese documento del médico: "),
        "nombre": _texto("Ingrese nombre del médico: "),
        "apellido": _texto("Ingrese apellido del médico: "),
        "telefono": _texto("Ingrese teléfono: "),
        "correo": _texto("Ingrese correo electrónico: "),
        "modulo": _texto("Ingrese módulo del médico: "),
        "especialidad": _texto("Ingrese especialidad: "),
        "consultorio": _texto("Ingrese número de consultorio: "),
        "horario": _texto("Ingrese horario de atención: "),
    }
    medicos = cargar_medicos()
    medicos.append(medico)
    _guardar_medicos(medicos)
    return medico

def mostrar_medico(medico):
    print(
        f"Médico: {medico['nombre']} {medico['apellido']} | "
        f"Módulo: {medico['modulo']} | Especialidad: {medico['especialidad']} | "
        f"Consultorio: {medico['consultorio']}"
    )
