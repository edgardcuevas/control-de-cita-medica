import json
import os


ARCHIVO = os.path.join(os.path.dirname(__file__), "archivos", "pacientes.json")


def _texto(mensaje):
    while True:
        valor = input(mensaje).strip()
        if valor:
            return valor
        print("El campo no puede quedar vacío.")


def _entero(mensaje, minimo, maximo):
    while True:
        try:
            valor = int(input(mensaje))
            if minimo <= valor <= maximo:
                return valor
            print(f"Ingrese un número entre {minimo} y {maximo}.")
        except ValueError:
            print("Ingrese un número entero válido.")


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


def registrar_paciente():
    paciente = {
        "documento": _texto("Ingrese documento del paciente: "),
        "nombre": _texto("Ingrese nombre del paciente: "),
        "apellido": _texto("Ingrese apellido del paciente: "),
        "edad": _entero("Ingrese edad: ", 0, 120),
        "sexo": _texto("Ingrese sexo: "),
        "fecha_nacimiento": _texto("Ingrese fecha de nacimiento (dd/mm/aaaa): "),
        "telefono": _texto("Ingrese teléfono: "),
        "direccion": _texto("Ingrese dirección: "),
        "correo": _texto("Ingrese correo electrónico: "),
        "tipo_sangre": _texto("Ingrese tipo de sangre: "),
        "seguro_medico": _texto("Ingrese seguro médico: "),
    }
    pacientes = cargar_pacientes()
    pacientes.append(paciente)
    _guardar_pacientes(pacientes)
    return paciente

def mostrar_paciente(paciente):
    print(
        f"Paciente: {paciente['nombre']} {paciente['apellido']} | "
        f"Documento: {paciente['documento']} | Edad: {paciente['edad']} | "
        f"Tel: {paciente['telefono']} | Correo: {paciente['correo']}"
    )
