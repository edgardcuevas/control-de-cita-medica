"""Pruebas de las estructuras lineales implementadas en ``estructuras.py``."""
import pytest

import estructuras


# ---------------------------------------------------------------------------
# Pila (LIFO)
# ---------------------------------------------------------------------------

def test_pila_crear_esta_vacia():
    pila = estructuras.pila_crear()
    assert pila == []
    assert estructuras.pila_esta_vacia(pila)
    assert estructuras.pila_tamano(pila) == 0


def test_pila_apilar_y_desapilar_en_orden_lifo():
    pila = estructuras.pila_crear()
    estructuras.pila_apilar(pila, "primero")
    estructuras.pila_apilar(pila, "segundo")
    estructuras.pila_apilar(pila, "tercero")

    assert estructuras.pila_tamano(pila) == 3
    assert estructuras.pila_desapilar(pila) == "tercero"
    assert estructuras.pila_desapilar(pila) == "segundo"
    assert estructuras.pila_desapilar(pila) == "primero"
    assert estructuras.pila_esta_vacia(pila)


def test_pila_cima_devuelve_el_ultimo_sin_quitarlo():
    pila = estructuras.pila_crear()
    estructuras.pila_apilar(pila, 1)
    estructuras.pila_apilar(pila, 2)

    assert estructuras.pila_cima(pila) == 2
    assert estructuras.pila_tamano(pila) == 2


def test_pila_volcar_devuelve_copia_sin_modificarla():
    pila = estructuras.pila_crear()
    estructuras.pila_apilar(pila, "a")
    estructuras.pila_apilar(pila, "b")

    volcado = estructuras.pila_volcar(pila)
    assert volcado == ["a", "b"]
    volcado.append("c")
    assert estructuras.pila_tamano(pila) == 2


def test_pila_vacia_lanza_index_error():
    pila = estructuras.pila_crear()
    with pytest.raises(IndexError):
        estructuras.pila_desapilar(pila)
    with pytest.raises(IndexError):
        estructuras.pila_cima(pila)


# ---------------------------------------------------------------------------
# Cola (FIFO)
# ---------------------------------------------------------------------------

def test_cola_crear_esta_vacia():
    cola = estructuras.cola_crear()
    assert estructuras.cola_esta_vacia(cola)
    assert estructuras.cola_tamano(cola) == 0


def test_cola_es_fifo():
    cola = estructuras.cola_crear()
    estructuras.cola_encolar(cola, "primero")
    estructuras.cola_encolar(cola, "segundo")
    estructuras.cola_encolar(cola, "tercero")

    assert estructuras.cola_primero(cola) == "primero"
    assert estructuras.cola_desencolar(cola) == "primero"
    assert estructuras.cola_desencolar(cola) == "segundo"
    assert estructuras.cola_desencolar(cola) == "tercero"
    assert estructuras.cola_esta_vacia(cola)


def test_cola_vacia_lanza_index_error():
    cola = estructuras.cola_crear()
    with pytest.raises(IndexError):
        estructuras.cola_desencolar(cola)
    with pytest.raises(IndexError):
        estructuras.cola_primero(cola)


def test_cola_tamano():
    cola = estructuras.cola_crear()
    for numero in range(5):
        estructuras.cola_encolar(cola, numero)
    assert estructuras.cola_tamano(cola) == 5


# ---------------------------------------------------------------------------
# Montículo (cola de prioridad)
# ---------------------------------------------------------------------------

def test_monticulo_crear_esta_vacio():
    monticulo = estructuras.monticulo_crear()
    assert monticulo == []
    assert estructuras.monticulo_esta_vacio(monticulo)
    assert estructuras.monticulo_tamano(monticulo) == 0


def test_monticulo_desencola_en_orden_de_clave():
    monticulo = estructuras.monticulo_crear()
    for clave, valor in ((3, "tercero"), (1, "primero"), (2, "segundo")):
        estructuras.monticulo_encolar(monticulo, clave, valor)

    assert estructuras.monticulo_cima(monticulo) == "primero"
    assert estructuras.monticulo_tamano(monticulo) == 3
    assert [
        estructuras.monticulo_desencolar(monticulo) for _ in range(3)
    ] == ["primero", "segundo", "tercero"]
    assert estructuras.monticulo_esta_vacio(monticulo)


def test_monticulo_con_claves_compuestas():
    monticulo = estructuras.monticulo_crear()
    claves = [
        (2026, 9, 22, "11:00", 2),
        (2026, 9, 22, "10:00", 0),
        (2026, 1, 5, "08:00", 1),
    ]
    for indice, clave in enumerate(claves):
        estructuras.monticulo_encolar(monticulo, clave, indice)

    ordenadas = [
        estructuras.monticulo_desencolar(monticulo) for _ in range(len(claves))
    ]
    assert ordenadas == [2, 1, 0]


def test_monticulo_vacio_lanza_index_error():
    monticulo = estructuras.monticulo_crear()
    with pytest.raises(IndexError):
        estructuras.monticulo_desencolar(monticulo)
    with pytest.raises(IndexError):
        estructuras.monticulo_cima(monticulo)
