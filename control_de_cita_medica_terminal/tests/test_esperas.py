"""Pruebas de la fila de espera por espacio de agenda (``esperas.py``)."""
import pytest

import esperas


def _cita(estado="Pendiente", posicion=None, medico="Ernesto Gutierres",
          fecha="22/09/2026", hora="10:00", paciente="Paciente"):
    cita = {
        "paciente": paciente,
        "medico": medico,
        "fecha": fecha,
        "hora": hora,
        "estado": estado,
    }
    if posicion is not None:
        cita["posicion_espera"] = posicion
    return cita


# ---------------------------------------------------------------------------
# Espacio de agenda
# ---------------------------------------------------------------------------

def test_clave_espacio_normaliza_el_medico():
    cita = _cita(medico="  ERNESTO   GUTIERRES ", fecha=" 22/09/2026 ", hora=" 10:00 ")
    assert esperas.clave_espacio(cita) == (
        "ernesto   gutierres",
        "22/09/2026",
        "10:00",
    )


def test_clave_espacio_tolera_campos_faltantes():
    assert esperas.clave_espacio({}) == ("", "", "")


def test_espacio_ocupado_por_cita_pendiente():
    citas = [_cita()]
    assert esperas.espacio_ocupado(citas, _cita(paciente="Otro"))


def test_espacio_ocupado_por_cita_en_espera():
    citas = [_cita(estado=esperas.ESTADO_ESPERA, posicion=1)]
    assert esperas.espacio_ocupado(citas, _cita())


@pytest.mark.parametrize("estado", list(esperas.ESTADOS_LIBERADOS))
def test_espacio_libre_si_la_cita_fue_realizada_o_cancelada(estado):
    citas = [_cita(estado=estado)]
    assert not esperas.espacio_ocupado(citas, _cita())


def test_espacio_libre_con_hora_distinta():
    citas = [_cita()]
    assert not esperas.espacio_ocupado(citas, _cita(hora="11:00"))


# ---------------------------------------------------------------------------
# Fila FIFO
# ---------------------------------------------------------------------------

def test_en_espera_ordena_por_posicion():
    citas = [
        _cita(estado=esperas.ESTADO_ESPERA, posicion=3, paciente="Tercero"),
        _cita(estado=esperas.ESTADO_ESPERA, posicion=1, paciente="Primero"),
        _cita(estado=esperas.ESTADO_ESPERA, posicion=2, paciente="Segundo"),
    ]
    fila = esperas.en_espera_del_espacio(citas, esperas.clave_espacio(_cita()))
    assert [cita["paciente"] for cita in fila] == [
        "Primero",
        "Segundo",
        "Tercero",
    ]


def test_en_espera_ignora_otras_citas_y_otros_espacios():
    citas = [
        _cita(paciente="Activa"),
        _cita(
            estado=esperas.ESTADO_ESPERA,
            posicion=1,
            paciente="Espera",
        ),
        _cita(
            estado=esperas.ESTADO_ESPERA,
            posicion=1,
            hora="11:00",
            paciente="Otro espacio",
        ),
    ]
    fila = esperas.en_espera_del_espacio(citas, esperas.clave_espacio(_cita()))
    assert [cita["paciente"] for cita in fila] == ["Espera"]


def test_en_espera_acepta_una_cita_como_espacio():
    citas = [_cita(estado=esperas.ESTADO_ESPERA, posicion=1)]
    assert len(esperas.en_espera_del_espacio(citas, _cita())) == 1


def test_cola_espera_y_total():
    citas = [
        _cita(estado=esperas.ESTADO_ESPERA, posicion=2),
        _cita(estado=esperas.ESTADO_ESPERA, posicion=1),
    ]
    espacio = esperas.clave_espacio(_cita())
    assert esperas.total_en_espera(citas, espacio) == 2
    assert esperas.cola_espera(citas, espacio) == esperas.en_espera_del_espacio(
        citas, espacio
    )


def test_renumerar_deja_posiciones_consecutivas():
    citas = [
        _cita(estado=esperas.ESTADO_ESPERA, posicion=5, paciente="Cinco"),
        _cita(estado=esperas.ESTADO_ESPERA, posicion=9, paciente="Nueve"),
        _cita(paciente="Activa"),
    ]
    esperas.renumerar(citas, esperas.clave_espacio(_cita()))

    assert citas[0]["posicion_espera"] == 1
    assert citas[1]["posicion_espera"] == 2
    assert "posicion_espera" not in citas[2]


# ---------------------------------------------------------------------------
# Resumen de posiciones
# ---------------------------------------------------------------------------

def test_posiciones_ocupadas_devuelve_activa_y_fila():
    activa = _cita(paciente="Activa")
    primera = _cita(estado=esperas.ESTADO_ESPERA, posicion=1, paciente="Uno")
    segunda = _cita(estado=esperas.ESTADO_ESPERA, posicion=2, paciente="Dos")
    otras = _cita(hora="12:00", paciente="Otra hora")

    resumen = esperas.posiciones_ocupadas([activa, primera, segunda, otras])

    espacio = esperas.clave_espacio(activa)
    ocupante, fila = resumen[espacio]
    assert ocupante is activa
    assert [cita["paciente"] for cita in fila] == ["Uno", "Dos"]
    assert resumen[esperas.clave_espacio(otras)] == (otras, [])


def test_posiciones_ocupadas_sin_cita_activa():
    espera = _cita(estado=esperas.ESTADO_ESPERA, posicion=1)
    resumen = esperas.posiciones_ocupadas([espera])
    activa, fila = resumen[esperas.clave_espacio(espera)]
    assert activa is None
    assert fila == [espera]


def test_posiciones_ocupadas_ignora_espacios_solo_liberados():
    cancelada = _cita(estado="Cancelada")
    resumen = esperas.posiciones_ocupadas([cancelada])
    activa, fila = resumen[esperas.clave_espacio(cancelada)]
    assert activa is None
    assert fila == []
