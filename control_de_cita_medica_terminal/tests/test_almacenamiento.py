"""Pruebas de lectura y escritura de los archivos JSON (``almacenamiento.py``)."""
import json

import pytest

import almacenamiento


# ---------------------------------------------------------------------------
# cargar_json_lista
# ---------------------------------------------------------------------------

def test_cargar_json_lista_archivo_inexistente(tmp_path):
    assert almacenamiento.cargar_json_lista(str(tmp_path / "no-existe.json")) == []


def test_cargar_json_lista_valida(tmp_path):
    ruta = tmp_path / "datos.json"
    datos = [{"nombre": "María"}, {"nombre": "José"}]
    ruta.write_text(json.dumps(datos, ensure_ascii=False), encoding="utf-8")

    assert almacenamiento.cargar_json_lista(str(ruta)) == datos


def test_cargar_json_lista_rechaza_objeto(tmp_path):
    ruta = tmp_path / "datos.json"
    ruta.write_text('{"no": "es una lista"}', encoding="utf-8")

    with pytest.raises(ValueError, match="no contiene una lista"):
        almacenamiento.cargar_json_lista(str(ruta))


def test_cargar_json_lista_rechaza_registros_no_dict(tmp_path):
    ruta = tmp_path / "datos.json"
    ruta.write_text("[1, 2, 3]", encoding="utf-8")

    with pytest.raises(ValueError, match="registros JSON no válidos"):
        almacenamiento.cargar_json_lista(str(ruta))


def test_cargar_json_lista_propaga_json_invalido(tmp_path):
    ruta = tmp_path / "datos.json"
    ruta.write_text("{ esto no es json", encoding="utf-8")

    with pytest.raises(json.JSONDecodeError):
        almacenamiento.cargar_json_lista(str(ruta))


# ---------------------------------------------------------------------------
# guardar_json_atomico
# ---------------------------------------------------------------------------

def test_guardar_json_atomico_crea_el_archivo_y_la_carpeta(tmp_path):
    ruta = tmp_path / "sub" / "carpeta" / "datos.json"
    datos = [{"documento": "A", "nombre": "María"}]

    almacenamiento.guardar_json_atomico(str(ruta), datos)

    assert ruta.exists()
    assert json.loads(ruta.read_text(encoding="utf-8")) == datos


def test_guardar_json_atomico_conserva_acentos(tmp_path):
    ruta = tmp_path / "datos.json"
    almacenamiento.guardar_json_atomico(
        str(ruta), [{"nombre": "Ñandú Pérez", "motivo": "revisión"}]
    )

    texto = ruta.read_text(encoding="utf-8")
    assert "Ñandú Pérez" in texto
    assert "revisión" in texto


def test_guardar_json_atomico_sobrescribe(tmp_path):
    ruta = tmp_path / "datos.json"
    almacenamiento.guardar_json_atomico(str(ruta), [{"n": 1}])
    almacenamiento.guardar_json_atomico(str(ruta), [{"n": 2}])

    assert almacenamiento.cargar_json_lista(str(ruta)) == [{"n": 2}]


def test_guardar_json_atomico_no_deja_temporales(tmp_path):
    carpeta = tmp_path / "archivos"
    almacenamiento.guardar_json_atomico(str(carpeta / "datos.json"), [{"n": 1}])

    assert [ruta.name for ruta in carpeta.iterdir()] == ["datos.json"]


# ---------------------------------------------------------------------------
# firma_archivo
# ---------------------------------------------------------------------------

def test_firma_archivo_inexistente(tmp_path):
    assert almacenamiento.firma_archivo(str(tmp_path / "no-existe.json")) is None


def test_firma_archivo_devuelve_tamano_y_mtime(tmp_path):
    ruta = tmp_path / "datos.json"
    ruta.write_text("[]", encoding="utf-8")

    firma = almacenamiento.firma_archivo(str(ruta))
    assert isinstance(firma, tuple)
    assert len(firma) == 2
    assert firma[1] == 2  # tamaño en bytes de "[]"


def test_firma_archivo_cambia_al_modificar(tmp_path):
    ruta = tmp_path / "datos.json"
    ruta.write_text("[]", encoding="utf-8")
    antes = almacenamiento.firma_archivo(str(ruta))

    ruta.write_text('[{"n": 1}]', encoding="utf-8")
    despues = almacenamiento.firma_archivo(str(ruta))

    assert antes != despues
