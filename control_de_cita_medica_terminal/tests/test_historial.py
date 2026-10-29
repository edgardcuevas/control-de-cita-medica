"""Pruebas de la pila de deshacer y la bitácora (``historial.py``)."""
import json
import os

import historial


# ---------------------------------------------------------------------------
# Pila de deshacer
# ---------------------------------------------------------------------------

def test_sin_acciones_no_hay_pendientes():
    assert historial.hay_pendientes() is False
    assert historial.etiqueta_pendiente() is None
    assert historial.deshacer() is None


def test_registrar_accion_guarda_la_entrada():
    historial.registrar_accion("Alta de prueba", {"tipo": "agregar", "entidad": "cita"})

    assert historial.hay_pendientes() is True
    assert historial.etiqueta_pendiente() == "Alta de prueba"

    entrada = historial.deshacer()
    assert entrada["etiqueta"] == "Alta de prueba"
    assert entrada["instantanea"] == {"tipo": "agregar", "entidad": "cita"}
    assert "marca" in entrada
    assert historial.hay_pendientes() is False


def test_deshacer_es_lifo():
    for etiqueta in ("primera", "segunda", "tercera"):
        historial.registrar_accion(etiqueta, {"tipo": "x"})

    assert historial.deshacer()["etiqueta"] == "tercera"
    assert historial.deshacer()["etiqueta"] == "segunda"
    assert historial.deshacer()["etiqueta"] == "primera"
    assert historial.deshacer() is None


def test_limpiar_vacia_la_pila():
    historial.registrar_accion("primera", {"tipo": "x"})
    historial.registrar_accion("segunda", {"tipo": "x"})

    historial.limpiar()

    assert historial.hay_pendientes() is False
    assert historial.deshacer() is None


def test_la_pila_respeta_el_limite():
    for numero in range(historial.LIMITE_PILA + 5):
        historial.registrar_accion(f"accion-{numero}", {"tipo": "x"})

    etiquetas = [historial.deshacer()["etiqueta"] for _ in range(historial.LIMITE_PILA)]

    assert etiquetas == [
        f"accion-{numero}"
        for numero in range(historial.LIMITE_PILA + 4, 4, -1)
    ]
    assert historial.deshacer() is None


# ---------------------------------------------------------------------------
# Persistencia
# ---------------------------------------------------------------------------

def test_la_pila_se_persiste_en_disco():
    historial.registrar_accion("primera", {"tipo": "x"})
    historial.registrar_accion("segunda", {"tipo": "x"})

    datos = json.loads(open(historial.HISTORIAL_FILE, encoding="utf-8").read())

    assert [entrada["etiqueta"] for entrada in datos] == ["primera", "segunda"]


def test_limpiar_persiste_lista_vacia():
    historial.registrar_accion("primera", {"tipo": "x"})
    historial.limpiar()

    assert json.loads(open(historial.HISTORIAL_FILE, encoding="utf-8").read()) == []


# ---------------------------------------------------------------------------
# Bitácora
# ---------------------------------------------------------------------------

def test_registrar_accion_encola_detalle_de_la_entidad():
    historial.registrar_accion("Alta", {"tipo": "agregar", "entidad": "paciente"})
    historial.volcar_bitacora()

    contenido = open(historial.BITACORA_FILE, encoding="utf-8").read()
    assert "Alta" in contenido
    assert "paciente" in contenido


def test_la_bitacora_se_vuelca_al_llegar_al_limite():
    for numero in range(historial.LIMITE_COLA):
        historial.registrar_accion(f"accion-{numero}", {"tipo": "x"})

    lineas = [
        linea
        for linea in open(historial.BITACORA_FILE, encoding="utf-8").read().splitlines()
        if linea.strip()
    ]
    assert len(lineas) == historial.LIMITE_COLA
    assert all(linea.startswith("[") for linea in lineas)
    assert "accion-9" in lineas[-1]


def test_volcar_bitacora_escribe_lo_pendiente():
    historial.registrar_bitacora("Revisión manual", "detalle extra")
    historial.volcar_bitacora()

    contenido = open(historial.BITACORA_FILE, encoding="utf-8").read()
    assert "Revisión manual - detalle extra" in contenido


def test_volcar_bitacora_sin_pendientes_no_crea_archivo():
    historial.volcar_bitacora()
    assert not os.path.exists(historial.BITACORA_FILE)
