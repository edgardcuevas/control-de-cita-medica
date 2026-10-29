"""Pruebas del módulo de médicos: búsquedas, altas, bajas y deshacer."""
import pytest

import citas
import historial
import medicos


# ---------------------------------------------------------------------------
# Búsquedas en memoria (parámetro ``registros``)
# ---------------------------------------------------------------------------

def test_buscar_sin_texto_devuelve_el_listado(medicos_ejemplo):
    resultado = medicos.buscar_medicos("", registros=medicos_ejemplo)

    assert resultado["elementos"] == medicos_ejemplo
    assert resultado["algoritmo"] == "Listado"


def test_buscar_por_especialidad(medicos_ejemplo):
    resultado = medicos.buscar_medicos("diabetologo", registros=medicos_ejemplo)

    assert len(resultado["elementos"]) == 1
    assert resultado["elementos"][0]["nombre"] == "Ernesto"
    assert resultado["algoritmo"] == "Secuencial"


def test_buscar_por_especialidad_con_acentos(medicos_ejemplo):
    resultado = medicos.buscar_medicos("DIABETÓLOGO", registros=medicos_ejemplo)
    assert len(resultado["elementos"]) == 1


def test_buscar_por_documento_exacto_usa_hash(medicos_ejemplo):
    resultado = medicos.buscar_medicos(
        "086-241112-876G", registros=medicos_ejemplo
    )

    assert len(resultado["elementos"]) == 1
    assert resultado["algoritmo"] == "Hash (documento)"


def test_buscar_documento_inexistente(medicos_ejemplo):
    resultado = medicos.buscar_medicos("000-000", registros=medicos_ejemplo)
    assert resultado["elementos"] == []


def test_buscar_por_modulo(medicos_ejemplo):
    resultado = medicos.buscar_medicos("modulo 3", registros=medicos_ejemplo)
    assert len(resultado["elementos"]) == 1
    assert resultado["elementos"][0]["nombre"] == "Marlon"


def test_buscar_sin_resultados(medicos_ejemplo):
    resultado = medicos.buscar_medicos("cardiologo", registros=medicos_ejemplo)
    assert resultado["elementos"] == []


# ---------------------------------------------------------------------------
# Búsquedas contra el archivo
# ---------------------------------------------------------------------------

def test_buscar_por_documento_en_archivo(escribir_json, medicos_ejemplo):
    escribir_json(medicos, medicos_ejemplo)

    medico = medicos.buscar_por_documento("086-241112-876G")
    assert medico is not None
    assert medico["nombre"] == "Ernesto"
    assert medicos.buscar_por_documento("086-241112-876g")["nombre"] == "Ernesto"
    assert medicos.buscar_por_documento("no-existe") is None


def test_el_indice_se_reconstruye_si_cambia_el_archivo(
    escribir_json, medicos_ejemplo
):
    escribir_json(medicos, medicos_ejemplo[:1])
    assert len(medicos.buscar_medicos("")["elementos"]) == 1

    escribir_json(medicos, medicos_ejemplo)
    assert len(medicos.buscar_medicos("")["elementos"]) == 2


# ---------------------------------------------------------------------------
# Altas y bajas
# ---------------------------------------------------------------------------

def test_registrar_medico_guarda_y_deja_historial(medico_base):
    devuelto = medicos.registrar_medico(medico_base)

    assert devuelto == medico_base
    assert medicos.cargar_medicos() == [medico_base]
    assert historial.etiqueta_pendiente() == "Registrar médico"


def test_eliminar_medico_sin_citas(medico_base):
    medicos.registrar_medico(medico_base)

    assert medicos.eliminar_medico("086-241112-876G") is True
    assert medicos.cargar_medicos() == []
    assert historial.etiqueta_pendiente() == "Eliminar médico"


def test_eliminar_medico_inexistente_devuelve_false(medico_base):
    medicos.registrar_medico(medico_base)
    assert medicos.eliminar_medico("no-existe") is False
    assert len(medicos.cargar_medicos()) == 1


def test_eliminar_medico_con_citas_lanza_value_error(
    escribir_json, medico_base, cita_base
):
    escribir_json(medicos, [medico_base])
    escribir_json(citas, [cita_base])

    with pytest.raises(ValueError, match="tiene 1 cita"):
        medicos.eliminar_medico("086-241112-876G")

    assert medicos.cargar_medicos() == [medico_base]


# ---------------------------------------------------------------------------
# Deshacer
# ---------------------------------------------------------------------------

def test_revertir_alta(medico_base):
    medicos.registrar_medico(medico_base)
    entrada = historial.deshacer()

    assert medicos.revertir(entrada["instantanea"]) is True
    assert medicos.cargar_medicos() == []


def test_revertir_baja(medico_base):
    medicos.registrar_medico(medico_base)
    medicos.eliminar_medico("086-241112-876G")
    entrada = historial.deshacer()

    assert medicos.revertir(entrada["instantanea"]) is True
    assert medicos.cargar_medicos() == [medico_base]


def test_revertir_posicion_invalida_y_tipo_desconocido(medico_base):
    medicos.registrar_medico(medico_base)
    assert medicos.revertir({"tipo": "agregar", "posicion": -3}) is False
    assert medicos.revertir({"tipo": "otro", "posicion": 0}) is False
