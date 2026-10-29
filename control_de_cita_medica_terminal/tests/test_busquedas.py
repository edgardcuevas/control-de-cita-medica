"""Pruebas de los algoritmos de búsqueda de ``busquedas.py``."""
import random

import pytest

import busquedas


# ---------------------------------------------------------------------------
# Utilidades de normalización
# ---------------------------------------------------------------------------

@pytest.mark.parametrize(
    "entrada, esperado",
    [
        ("  María   GÜERRERO ", "maria guerrero"),
        ("Pérez", "perez"),
        ("Año 2026", "ano 2026"),
        ("", ""),
        ("   ", ""),
        ("ÑANDÚ", "nandu"),
    ],
)
def test_normalizar(entrada, esperado):
    assert busquedas.normalizar(entrada) == esperado


def test_normalizar_none_se_convierte_en_texto():
    # Comportamiento actual: str(None) == "none".
    assert busquedas.normalizar(None) == "none"


@pytest.mark.parametrize(
    "texto, esperado",
    [
        ("085-110886-4432D", True),
        ("112233445566", True),
        ("DOC-4", True),
        ("Juan", False),
        ("", False),
        ("Pérez", False),
    ],
)
def test_parece_documento(texto, esperado):
    assert busquedas.parece_documento(texto) is esperado


@pytest.mark.parametrize(
    "texto, esperado",
    [
        ("22/09/2026", "2026-09-22"),
        ("01/01/2000", "2000-01-01"),
        ("2026-09-22", "9999-99-99"),
        ("31/02/2026", "9999-99-99"),
        ("", "9999-99-99"),
        (None, "9999-99-99"),
    ],
)
def test_clave_fecha(texto, esperado):
    assert busquedas.clave_fecha(texto) == esperado


def test_crear_resultado():
    assert busquedas.crear_resultado() == {
        "elementos": [],
        "algoritmo": "Listado",
        "comparaciones": 0,
    }
    resultado = busquedas.crear_resultado([1, 2], "Prueba", 7)
    assert resultado["elementos"] == [1, 2]
    assert resultado["algoritmo"] == "Prueba"
    assert resultado["comparaciones"] == 7


# ---------------------------------------------------------------------------
# Búsqueda secuencial
# ---------------------------------------------------------------------------

def test_busqueda_secuencial_filtra_y_cuenta_comparaciones():
    registros = [{"numero": i} for i in range(100)]
    resultado = busquedas.busqueda_secuencial(
        registros, lambda registro: registro["numero"] % 2 == 0
    )

    assert len(resultado["elementos"]) == 50
    assert resultado["algoritmo"] == "Secuencial"
    assert resultado["comparaciones"] == 100
    assert all(
        registro["numero"] % 2 == 0 for registro in resultado["elementos"]
    )


def test_busqueda_secuencial_lista_vacia():
    resultado = busquedas.busqueda_secuencial([], lambda registro: True)
    assert resultado["elementos"] == []
    assert resultado["comparaciones"] == 0


# ---------------------------------------------------------------------------
# Índice ordenado y búsqueda binaria
# ---------------------------------------------------------------------------

def test_indice_ordenado_normaliza_y_conserva_posiciones():
    registros = [{"clave": "Carlos"}, {"clave": "ana"}, {"clave": "Bruno"}]
    indice = busquedas.indice_ordenado(registros, "clave")

    assert indice == [("ana", 1), ("bruno", 2), ("carlos", 0)]


def test_indice_ordenado_acepta_campo_calculado():
    registros = [{"fecha": "05/10/2026"}, {"fecha": "01/10/2026"}]
    indice = busquedas.indice_ordenado(
        registros, lambda registro: busquedas.clave_fecha(registro["fecha"])
    )
    assert indice == [("2026-10-01", 1), ("2026-10-05", 0)]


def test_busqueda_binaria_encuentra_y_devuelve_la_primera_aparicion():
    registros = [{"clave": "a"}, {"clave": "b"}, {"clave": "b"}, {"clave": "c"}]
    indice = busquedas.indice_ordenado(registros, "clave")

    assert busquedas.busqueda_binaria(indice, "a")[0] == 0
    assert busquedas.busqueda_binaria(indice, "b")[0] == 1
    assert busquedas.busqueda_binaria(indice, "c")[0] == 3


def test_busqueda_binaria_no_encontrada_devuelve_menos_uno():
    registros = [{"clave": "a"}, {"clave": "b"}]
    indice = busquedas.indice_ordenado(registros, "clave")

    posicion, comparaciones = busquedas.busqueda_binaria(indice, "z")
    assert posicion == -1
    assert comparaciones > 0


def test_busqueda_binaria_indice_vacio():
    assert busquedas.busqueda_binaria([], "cualquiera") == (-1, 0)


def test_busqueda_binaria_es_case_insensitive():
    registros = [{"clave": "Ana"}, {"clave": "Bea"}]
    indice = busquedas.indice_ordenado(registros, "clave")
    assert busquedas.busqueda_binaria(indice, "ANA")[0] == 0


def test_busqueda_binaria_coincide_con_busqueda_lineal():
    generador = random.Random(20260922)
    for _ in range(100):
        valores = generador.sample(range(10000), generador.randint(0, 120))
        registros = [{"clave": str(valor)} for valor in valores]
        indice = busquedas.indice_ordenado(registros, "clave")

        for objetivo in generador.sample(range(10000), 10):
            posicion, _ = busquedas.busqueda_binaria(indice, str(objetivo))
            esperado = next(
                (
                    i
                    for i, registro in enumerate(registros)
                    if registro["clave"] == str(objetivo)
                ),
                -1,
            )
            assert posicion == esperado, (objetivo, posicion, esperado)


# ---------------------------------------------------------------------------
# Búsqueda por rango y por prefijo
# ---------------------------------------------------------------------------

def test_busqueda_por_rango_es_inclusiva():
    fechas = ["01/10/2026", "05/10/2026", "10/10/2026", "15/10/2026", "20/10/2026"]
    registros = [{"fecha": fecha} for fecha in fechas]
    indice = busquedas.indice_ordenado(
        registros, lambda registro: busquedas.clave_fecha(registro["fecha"])
    )

    posiciones, _ = busquedas.busqueda_por_rango(
        indice, "2026-10-05", "2026-10-15"
    )
    assert posiciones == [1, 2, 3]


def test_busqueda_por_rango_sin_resultados():
    registros = [{"fecha": "01/10/2026"}]
    indice = busquedas.indice_ordenado(
        registros, lambda registro: busquedas.clave_fecha(registro["fecha"])
    )
    posiciones, _ = busquedas.busqueda_por_rango(
        indice, "2027-01-01", "2027-12-31"
    )
    assert posiciones == []


def test_busqueda_por_prefijo():
    registros = [{"k": "Ana"}, {"k": "Anabel"}, {"k": "Bruno"}, {"k": "ana"}]
    indice = busquedas.indice_ordenado(registros, "k")

    posiciones, _ = busquedas.busqueda_por_prefijo(indice, "ana")
    assert sorted(posiciones) == [0, 1, 3]


def test_busqueda_por_prefijo_sin_coincidencias():
    registros = [{"k": "Ana"}]
    indice = busquedas.indice_ordenado(registros, "k")
    assert busquedas.busqueda_por_prefijo(indice, "zzz")[0] == []


# ---------------------------------------------------------------------------
# Tabla hash
# ---------------------------------------------------------------------------

def test_crear_tabla_hash_usa_capacidad_prima():
    assert busquedas.crear_tabla_hash(4)["capacidad"] == 5
    assert busquedas.crear_tabla_hash(7)["capacidad"] == 7
    assert busquedas.crear_tabla_hash(0)["capacidad"] == 3


def test_hash_insertar_y_buscar():
    tabla = busquedas.crear_tabla_hash(capacidad=5)
    assert busquedas.hash_insertar(tabla, "clave", 42) is True

    assert busquedas.hash_buscar(tabla, "clave") == 42
    assert busquedas.hash_buscar(tabla, "no-existe") is None
    assert tabla["tamano"] == 1


def test_hash_insertar_reemplaza_el_valor_existente():
    tabla = busquedas.crear_tabla_hash()
    busquedas.hash_insertar(tabla, "repetida", 1)
    assert busquedas.hash_insertar(tabla, "repetida", 2) is False

    assert busquedas.hash_buscar(tabla, "repetida") == 2
    assert tabla["tamano"] == 1


def test_hash_insertar_si_ausente_no_reemplaza():
    tabla = busquedas.crear_tabla_hash()
    assert busquedas.hash_insertar_si_ausente(tabla, "clave", 1) is True
    assert busquedas.hash_insertar_si_ausente(tabla, "clave", 2) is False

    assert busquedas.hash_buscar(tabla, "clave") == 1


def test_hash_agregar_permite_valores_multiples():
    tabla = busquedas.crear_tabla_hash()
    busquedas.hash_agregar(tabla, "varias", "a")
    busquedas.hash_agregar(tabla, "varias", "b")

    assert busquedas.hash_buscar_todos(tabla, "varias") == ["a", "b"]
    assert busquedas.hash_buscar(tabla, "varias") == "a"


def test_hash_agregar_ignora_claves_vacias():
    tabla = busquedas.crear_tabla_hash()
    assert busquedas.hash_agregar(tabla, "", "valor") is False
    assert tabla["tamano"] == 0


def test_hash_normaliza_mayusculas_y_acentos():
    tabla = busquedas.crear_tabla_hash()
    busquedas.hash_insertar(tabla, "Pérez", "encontrado")

    assert busquedas.hash_buscar(tabla, "PEREZ") == "encontrado"
    assert busquedas.hash_buscar(tabla, "  perez ") == "encontrado"


def test_hash_claves_compuestas():
    tabla = busquedas.crear_tabla_hash()
    busquedas.hash_agregar(tabla, ("Dr. Pérez", "22/09/2026", "10:00"), "cita-1")
    busquedas.hash_agregar(tabla, ("dr. perez", "22/09/2026", "10:00"), "cita-2")

    assert busquedas.hash_buscar_todos(
        tabla, ("DR. PEREZ", "22/09/2026", "10:00")
    ) == ["cita-1", "cita-2"]
    assert busquedas.hash_buscar(tabla, ("otro", "22/09/2026", "10:00")) is None


def test_hash_registra_colisiones():
    tabla = busquedas.crear_tabla_hash(101)
    primera = busquedas._hash_normalizada(tabla, "clave-0")
    segunda = None
    for numero in range(1, 200):
        candidata = f"clave-{numero}"
        if busquedas._hash_normalizada(tabla, candidata) == primera:
            segunda = candidata
            break
    assert segunda is not None, "No se encontró una colisión de prueba"

    busquedas.hash_insertar(tabla, "clave-0", 0)
    busquedas.hash_insertar(tabla, segunda, 1)

    assert tabla["colisiones"] == 1
    assert busquedas.hash_buscar(tabla, "clave-0") == 0
    assert busquedas.hash_buscar(tabla, segunda) == 1


def test_hash_crece_con_rehash_y_conserva_los_valores():
    tabla = busquedas.crear_tabla_hash(capacidad=5)
    for numero in range(200):
        assert busquedas.hash_insertar_si_ausente(tabla, f"clave-{numero}", numero)

    assert tabla["tamano"] == 200
    assert tabla["capacidad"] > 5
    for numero in range(200):
        assert busquedas.hash_buscar(tabla, f"clave-{numero}") == numero


def test_construir_hash_guarda_registro_y_posicion():
    registros = [{"documento": "A"}, {"documento": "B"}]
    tabla = busquedas.construir_hash(registros, "documento")

    registro, posicion = busquedas.hash_buscar(tabla, "b")
    assert registro == {"documento": "B"}
    assert posicion == 1


def test_construir_hash_omite_claves_vacias():
    registros = [{"documento": ""}, {"documento": "A"}]
    tabla = busquedas.construir_hash(registros, "documento")
    assert tabla["tamano"] == 1


def test_construir_hash_respeta_la_primera_aparicion():
    registros = [{"documento": "A", "n": 1}, {"documento": "a", "n": 2}]
    tabla = busquedas.construir_hash(registros, "documento")
    assert busquedas.hash_buscar(tabla, "A")[0]["n"] == 1


def test_construir_hash_multiple_guarda_duplicados():
    registros = [{"clave": "x", "n": 1}, {"clave": "X", "n": 2}]
    tabla = busquedas.construir_hash_multiple(registros, "clave")
    assert busquedas.hash_buscar_todos(tabla, "x") == [
        ({"clave": "x", "n": 1}, 0),
        ({"clave": "X", "n": 2}, 1),
    ]
