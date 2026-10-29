"""Configuración común de las pruebas de MediCitas.

Cada prueba se ejecuta con los archivos JSON redirigidos a una carpeta
temporal, de modo que nunca se tocan los datos reales de ``archivos/``.
"""
import copy

import pytest

import almacenamiento
import citas
import historial
import medicos
import pacientes
import usuarios

# ---------------------------------------------------------------------------
# Datos de ejemplo
# ---------------------------------------------------------------------------

PACIENTES = [
    {
        "documento": "085-110886-4432D",
        "nombre": "María Esperanza",
        "apellido": "Guerrero Mendez",
        "edad": 40,
        "sexo": "femenino",
        "telefono": "76751188",
        "correo": "maria@test.com",
        "tipo_sangre": "O-",
        "seguro_medico": "no tiene",
        "direccion": "San Juan",
        "fecha_nacimiento": "15/06/1986",
    },
    {
        "documento": "Juan",
        "nombre": "Juan Alfonso",
        "apellido": "Cortes",
        "edad": 20,
        "sexo": "masculino",
        "telefono": "67543211",
        "correo": "juan@test.com",
        "tipo_sangre": "O+",
        "seguro_medico": "no tiene",
        "direccion": "San Juan",
        "fecha_nacimiento": "11/03/1999",
    },
    {
        "documento": "112233445566",
        "nombre": "Carlos",
        "apellido": "Pérez",
        "edad": 35,
        "sexo": "masculino",
        "telefono": "70000000",
        "correo": "carlos@test.com",
        "tipo_sangre": "A+",
        "seguro_medico": "seguro privado",
        "direccion": "Centro",
        "fecha_nacimiento": "01/02/1991",
    },
    {
        "documento": "DOC-4",
        "nombre": "Juan",
        "apellido": "Ramos",
        "edad": 28,
        "sexo": "masculino",
        "telefono": "70000004",
        "correo": "juan.ramos@test.com",
        "tipo_sangre": "B+",
        "seguro_medico": "no tiene",
        "direccion": "Norte",
        "fecha_nacimiento": "05/05/1998",
    },
]

MEDICOS = [
    {
        "documento": "086-241112-876G",
        "nombre": "Ernesto",
        "apellido": "Gutierres",
        "telefono": "76543211",
        "correo": "ernesto@test.com",
        "modulo": "5",
        "especialidad": "diabetologo",
        "consultorio": "4",
        "horario": "6 am a 3 pm",
    },
    {
        "documento": "112233445566",
        "nombre": "Marlon",
        "apellido": "Surtiava",
        "telefono": "76751188",
        "correo": "marlon@test.com",
        "modulo": "modulo 3",
        "especialidad": "cirujano",
        "consultorio": "5",
        "horario": "3:00 a 18:00",
    },
]

CITAS = [
    {
        "paciente": "María Esperanza Guerrero Mendez",
        "documento_paciente": "085-110886-4432D",
        "medico": "Ernesto Gutierres",
        "especialidad": "diabetologo",
        "modulo": "5",
        "fecha": "22/09/2026",
        "hora": "10:00",
        "tipo": "presencial",
        "motivo": "consulta mensual",
        "observaciones": "ninguna",
        "estado": "Realizada",
    },
    {
        "paciente": "Juan Alfonso Cortes Cortes",
        "documento_paciente": "Juan",
        "medico": "Marlon Surtiava",
        "especialidad": "cirujano",
        "modulo": "modulo 3",
        "fecha": "09/12/2026",
        "hora": "03:00",
        "tipo": "presencial",
        "motivo": "revision",
        "observaciones": "ninguna",
        "estado": "Pendiente",
    },
    {
        "paciente": "María Esperanza Guerrero Mendez",
        "documento_paciente": "085-110886-4432D",
        "medico": "Ernesto Gutierres",
        "especialidad": "diabetologo",
        "modulo": "5",
        "fecha": "22/09/2026",
        "hora": "11:00",
        "tipo": "presencial",
        "motivo": "control",
        "observaciones": "ninguna",
        "estado": "En espera",
        "posicion_espera": 1,
    },
]

MODULOS_CON_INDICE = (pacientes, medicos, citas, usuarios)


def _invalidar_indices():
    for modulo in MODULOS_CON_INDICE:
        modulo._invalidar_indice()


def _vaciar_historial():
    historial._pila.clear()
    historial._cola.clear()


# ---------------------------------------------------------------------------
# Aislamiento de archivos
# ---------------------------------------------------------------------------

@pytest.fixture(autouse=True)
def entorno_limpio(tmp_path, monkeypatch):
    """Redirige todos los archivos de datos a una carpeta temporal."""
    carpeta = tmp_path / "archivos"
    carpeta.mkdir()

    monkeypatch.setattr(pacientes, "ARCHIVO", str(carpeta / "pacientes.json"))
    monkeypatch.setattr(medicos, "ARCHIVO", str(carpeta / "medicos.json"))
    monkeypatch.setattr(citas, "ARCHIVO", str(carpeta / "citas.json"))
    monkeypatch.setattr(usuarios, "DATA_DIR", str(carpeta))
    monkeypatch.setattr(usuarios, "USUARIOS_FILE", str(carpeta / "usuarios.json"))
    monkeypatch.setattr(historial, "DATA_DIR", str(carpeta))
    monkeypatch.setattr(historial, "HISTORIAL_FILE", str(carpeta / "historial.json"))
    monkeypatch.setattr(historial, "BITACORA_FILE", str(carpeta / "bitacora.txt"))

    _invalidar_indices()
    _vaciar_historial()

    yield carpeta

    _vaciar_historial()
    _invalidar_indices()


@pytest.fixture
def escribir_json():
    """Guarda una lista de registros en el archivo de un módulo."""

    def _escribir(modulo, registros):
        almacenamiento.guardar_json_atomico(modulo.ARCHIVO, registros)
        modulo._invalidar_indice()
        return registros

    return _escribir


# ---------------------------------------------------------------------------
# Fixtures de datos
# ---------------------------------------------------------------------------

@pytest.fixture
def pacientes_ejemplo():
    return copy.deepcopy(PACIENTES)


@pytest.fixture
def medicos_ejemplo():
    return copy.deepcopy(MEDICOS)


@pytest.fixture
def citas_ejemplo():
    return copy.deepcopy(CITAS)


@pytest.fixture
def paciente_base():
    return copy.deepcopy(PACIENTES[0])


@pytest.fixture
def medico_base():
    return copy.deepcopy(MEDICOS[0])


@pytest.fixture
def cita_base():
    """Cita sin estado: ``agregar_cita`` decide el estado final."""
    cita = copy.deepcopy(CITAS[0])
    cita.pop("estado", None)
    cita.pop("posicion_espera", None)
    return cita
