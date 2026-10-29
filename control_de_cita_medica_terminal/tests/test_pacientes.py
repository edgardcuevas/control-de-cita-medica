"""Pruebas del módulo de pacientes: búsquedas, altas, bajas y deshacer."""
import pytest

import citas
import historial
import pacientes


# ---------------------------------------------------------------------------
# Búsquedas en memoria (parámetro ``registros``)
# ---------------------------------------------------------------------------

def test_buscar_sin_texto_devuelve_el_listado(pacientes_ejemplo):
    resultado = pacientes.buscar_pacientes("", registros=pacientes_ejemplo)

    assert resultado["elementos"] == pacientes_ejemplo
    assert resultado["algoritmo"] == "Listado"
    assert resultado["comparaciones"] == 0


def test_buscar_por_nombre_parcial(pacientes_ejemplo):
    resultado = pacientes.buscar_pacientes("maria", registros=pacientes_ejemplo)

    assert len(resultado["elementos"]) == 1
    assert resultado["elementos"][0]["nombre"] == "María Esperanza"
    assert resultado["algoritmo"] == "Secuencial"


def test_buscar_por_varios_terminos(pacientes_ejemplo):
    resultado = pacientes.buscar_pacientes(
        "MARIA GUERRERO", registros=pacientes_ejemplo
    )
    assert len(resultado["elementos"]) == 1


def test_buscar_ignora_acentos(pacientes_ejemplo):
    resultado = pacientes.buscar_pacientes("perez", registros=pacientes_ejemplo)

    assert len(resultado["elementos"]) == 1
    assert resultado["elementos"][0]["documento"] == "112233445566"


def test_buscar_por_documento_exacto_usa_hash(pacientes_ejemplo):
    resultado = pacientes.buscar_pacientes(
        "085-110886-4432D", registros=pacientes_ejemplo
    )

    assert len(resultado["elementos"]) == 1
    assert resultado["algoritmo"] == "Hash (documento)"
    assert resultado["comparaciones"] == 1


def test_buscar_documento_es_case_insensitive(pacientes_ejemplo):
    resultado = pacientes.buscar_pacientes(
        "085-110886-4432d", registros=pacientes_ejemplo
    )
    assert resultado["algoritmo"] == "Hash (documento)"


def test_buscar_documento_inexistente_cae_a_secuencial(pacientes_ejemplo):
    resultado = pacientes.buscar_pacientes(
        "999-999-999", registros=pacientes_ejemplo
    )
    assert resultado["elementos"] == []
    assert resultado["algoritmo"] == "Secuencial"


def test_buscar_por_telefono(pacientes_ejemplo):
    resultado = pacientes.buscar_pacientes("700000", registros=pacientes_ejemplo)
    assert len(resultado["elementos"]) == 2


def test_buscar_texto_que_no_coincide(pacientes_ejemplo):
    resultado = pacientes.buscar_pacientes("no existe", registros=pacientes_ejemplo)
    assert resultado["elementos"] == []


def test_buscar_juan_no_confunde_el_documento_llamado_juan(pacientes_ejemplo):
    resultado = pacientes.buscar_pacientes("juan", registros=pacientes_ejemplo)

    assert len(resultado["elementos"]) >= 2
    assert resultado["algoritmo"] == "Secuencial"
    nombres = {paciente["nombre"] for paciente in resultado["elementos"]}
    assert {"Juan Alfonso", "Juan"} <= nombres


# ---------------------------------------------------------------------------
# Búsquedas contra el archivo (con índice en caché)
# ---------------------------------------------------------------------------

def test_buscar_por_documento_en_archivo(escribir_json, pacientes_ejemplo):
    escribir_json(pacientes, pacientes_ejemplo)

    paciente = pacientes.buscar_por_documento("Juan")
    assert paciente is not None
    assert paciente["nombre"] == "Juan Alfonso"
    assert pacientes.buscar_por_documento("juan")["nombre"] == "Juan Alfonso"
    assert pacientes.buscar_por_documento("no-existe") is None


def test_el_indice_se_reconstruye_si_cambia_el_archivo(
    escribir_json, pacientes_ejemplo
):
    escribir_json(pacientes, pacientes_ejemplo[:1])
    assert len(pacientes.buscar_pacientes("")["elementos"]) == 1

    escribir_json(pacientes, pacientes_ejemplo)
    assert len(pacientes.buscar_pacientes("")["elementos"]) == 4


# ---------------------------------------------------------------------------
# Altas y bajas
# ---------------------------------------------------------------------------

def test_registrar_paciente_guarda_y_deja_historial(paciente_base):
    devuelto = pacientes.registrar_paciente(paciente_base)

    assert devuelto == paciente_base
    assert pacientes.cargar_pacientes() == [paciente_base]
    assert historial.etiqueta_pendiente() == "Registrar paciente"


def test_registrar_varios_pacientes(paciente_base, pacientes_ejemplo):
    pacientes.registrar_paciente(paciente_base)
    pacientes.registrar_paciente(pacientes_ejemplo[1])

    assert len(pacientes.cargar_pacientes()) == 2
    assert {
        registro["documento"] for registro in pacientes.cargar_pacientes()
    } == {"085-110886-4432D", "Juan"}


def test_eliminar_paciente_sin_citas(paciente_base):
    pacientes.registrar_paciente(paciente_base)

    assert pacientes.eliminar_paciente("085-110886-4432D") is True
    assert pacientes.cargar_pacientes() == []
    assert historial.etiqueta_pendiente() == "Eliminar paciente"


def test_eliminar_paciente_inexistente_devuelve_false(paciente_base):
    pacientes.registrar_paciente(paciente_base)
    assert pacientes.eliminar_paciente("no-existe") is False
    assert len(pacientes.cargar_pacientes()) == 1


def test_eliminar_paciente_con_citas_lanza_value_error(
    escribir_json, paciente_base, cita_base
):
    escribir_json(pacientes, [paciente_base])
    escribir_json(citas, [cita_base])

    with pytest.raises(ValueError, match="tiene 1 cita"):
        pacientes.eliminar_paciente("085-110886-4432D")

    assert pacientes.cargar_pacientes() == [paciente_base]


def test_eliminar_paciente_cuenta_citas_por_nombre_si_falta_documento(
    escribir_json, paciente_base
):
    escribir_json(pacientes, [paciente_base])
    escribir_json(
        citas,
        [
            {
                "paciente": "María Esperanza Guerrero Mendez",
                "documento_paciente": "",
                "medico": "Ernesto Gutierres",
                "fecha": "22/09/2026",
                "hora": "10:00",
            }
        ],
    )

    with pytest.raises(ValueError):
        pacientes.eliminar_paciente("085-110886-4432D")


# ---------------------------------------------------------------------------
# Deshacer
# ---------------------------------------------------------------------------

def test_revertir_alta(paciente_base):
    pacientes.registrar_paciente(paciente_base)
    entrada = historial.deshacer()

    assert pacientes.revertir(entrada["instantanea"]) is True
    assert pacientes.cargar_pacientes() == []


def test_revertir_alta_ya_modificada_devuelve_false(paciente_base):
    pacientes.registrar_paciente(paciente_base)
    entrada = historial.deshacer()
    pacientes.eliminar_paciente("085-110886-4432D")

    assert pacientes.revertir(entrada["instantanea"]) is False


def test_revertir_baja(paciente_base):
    pacientes.registrar_paciente(paciente_base)
    pacientes.eliminar_paciente("085-110886-4432D")
    entrada = historial.deshacer()

    assert pacientes.revertir(entrada["instantanea"]) is True
    assert pacientes.cargar_pacientes() == [paciente_base]


def test_revertir_posicion_invalida_devuelve_false():
    assert pacientes.revertir({"tipo": "agregar", "posicion": -1}) is False
    assert pacientes.revertir({"tipo": "agregar", "posicion": "cero"}) is False


def test_revertir_tipo_desconocido_devuelve_false(paciente_base):
    pacientes.registrar_paciente(paciente_base)
    assert pacientes.revertir({"tipo": "otro", "posicion": 0}) is False
