import json
import os
import unicodedata
from datetime import datetime


ARCHIVO = os.path.join(os.path.dirname(__file__), "archivos", "citas.json")


def _texto(mensaje):
    while True:
        valor = input(mensaje).strip()
        if valor:
            return valor
        print("El campo no puede quedar vacío.")


def _fecha(mensaje):
    while True:
        valor = input(mensaje).strip()
        try:
            datetime.strptime(valor, "%d/%m/%Y")
            return valor
        except ValueError:
            print("Use una fecha válida con el formato dd/mm/aaaa.")


def _hora(mensaje):
    while True:
        valor = input(mensaje).strip()
        try:
            datetime.strptime(valor, "%H:%M")
            return valor
        except ValueError:
            print("Use una hora válida con el formato hh:mm.")


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


def _buscar_por_nombre(registros, nombre, tipo):
    consulta = " ".join(
        unicodedata.normalize("NFD", nombre).casefold().split()
    ).encode("ascii", "ignore").decode("ascii")
    encontrados = []
    for registro in registros:
        nombre_completo = f'{registro["nombre"]} {registro["apellido"]}'
        nombres = {
            " ".join(
                unicodedata.normalize("NFD", valor).casefold().split()
            ).encode("ascii", "ignore").decode("ascii")
            for valor in (registro["nombre"], nombre_completo)
        }
        if any(valor.startswith(consulta) for valor in nombres):
            encontrados.append(registro)
    if not encontrados:
        print(f"No existe un {tipo} con ese nombre.")
        return None
    return encontrados[0]


def _buscar_por_documento(registros, documento, tipo, mostrar_error=True):
    for registro in registros:
        if registro["documento"].casefold() == documento.casefold():
            return registro
    if mostrar_error:
        print(f"No existe un {tipo} con ese documento.")
    return None


def agendar_cita():
    import medicos
    import pacientes

    pacientes_guardados = pacientes.cargar_pacientes()
    medicos_guardados = medicos.cargar_medicos()
    if not pacientes_guardados:
        print("Debe registrar al menos un paciente antes de agendar.")
        return None
    if not medicos_guardados:
        print("Debe registrar al menos un médico antes de agendar.")
        return None

    print("\nPacientes registrados:")
    for paciente in pacientes_guardados:
        print(f"- {paciente['nombre']} {paciente['apellido']} ({paciente['documento']})")
    paciente_nombre = _texto("Ingrese el nombre del paciente: ")
    paciente = _buscar_por_nombre(pacientes_guardados, paciente_nombre, "paciente")
    if paciente is None:
        return None

    print("\nMédicos registrados:")
    for medico in medicos_guardados:
        print(f"- {medico['nombre']} {medico['apellido']} | Documento: {medico['documento']}")
    medico_dato = _texto("Ingrese el nombre o documento del médico: ")
    medico = _buscar_por_documento(
        medicos_guardados, medico_dato, "médico", mostrar_error=False
    )
    if medico is None:
        medico = _buscar_por_nombre(medicos_guardados, medico_dato, "médico")
    if medico is None:
        return None

    cita = {
        "paciente": paciente["nombre"] + " " + paciente["apellido"],
        "documento_paciente": paciente["documento"],
        "medico": medico["nombre"] + " " + medico["apellido"],
        "especialidad": medico["especialidad"],
        "modulo": medico["modulo"],
        "fecha": _fecha("Ingrese fecha de la cita (dd/mm/aaaa): "),
        "hora": _hora("Ingrese hora de la cita (hh:mm): "),
        "tipo": _texto("Ingrese tipo de cita (presencial/virtual): "),
        "motivo": _texto("Motivo de la consulta: "),
        "observaciones": _texto("Observaciones adicionales: "),
        "estado": "Pendiente",
    }
    citas = cargar_citas()
    citas.append(cita)
    _guardar_citas(citas)
    return cita


def mostrar_cita(cita):
    print("\n=== Detalle de la Cita ===")
    print(f"Paciente: {cita['paciente']} | Documento: {cita['documento_paciente']}")
    print(f"Médico: {cita['medico']} ({cita['especialidad']})")
    print(f"Módulo: {cita['modulo']}")
    print(f"Fecha: {cita['fecha']} | Hora: {cita['hora']}")
    print(f"Tipo: {cita['tipo']}")
    print(f"Motivo: {cita['motivo']}")
    print(f"Observaciones: {cita['observaciones']}")
    print(f"Estado: {cita.get('estado', 'Pendiente')}")


def mostrar_todas_las_citas():
    citas = cargar_citas()
    if not citas:
        print("No hay citas registradas.")
        return

    print("\n=== Citas registradas ===")
    for posicion, cita in enumerate(citas, start=1):
        print(
            f"{posicion}. {cita['fecha']} {cita['hora']} | "
            f"Paciente: {cita['paciente']} | Médico: {cita['medico']} | "
            f"Estado: {cita.get('estado', 'Pendiente')}"
        )


def _leer_posicion(mensaje, cantidad):
    while True:
        try:
            posicion = int(input(mensaje))
            if 1 <= posicion <= cantidad:
                return posicion - 1
            print(f"Ingrese una posición entre 1 y {cantidad}.")
        except ValueError:
            print("Ingrese un número entero válido.")


def marcar_cita_como_hecha():
    citas = cargar_citas()
    if not citas:
        print("No hay citas registradas para marcar.")
        return

    mostrar_todas_las_citas()
    posicion = _leer_posicion(
        "Ingrese el número de la cita que desea marcar como hecha: ",
        len(citas),
    )
    citas[posicion]["estado"] = "Realizada"
    _guardar_citas(citas)
    print("La cita fue marcada como realizada.")
    mostrar_cita(citas[posicion])
