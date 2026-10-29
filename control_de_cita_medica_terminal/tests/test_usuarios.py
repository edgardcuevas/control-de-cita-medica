"""Pruebas de las cuentas locales (``usuarios.py``)."""
import json

import pytest

import busquedas
import usuarios


def _leer_usuarios():
    return usuarios.cargar_usuarios()


# ---------------------------------------------------------------------------
# Carga del archivo
# ---------------------------------------------------------------------------

def test_cargar_usuarios_sin_archivo_devuelve_lista_vacia():
    assert usuarios.cargar_usuarios() == []


def test_cargar_usuarios_con_contenido_que_no_es_lista(entorno_limpio):
    (entorno_limpio / "usuarios.json").write_text("{}", encoding="utf-8")
    assert usuarios.cargar_usuarios() == []


def test_cargar_usuarios_con_json_corrupto_lanza_runtime_error(entorno_limpio):
    (entorno_limpio / "usuarios.json").write_text("{ roto", encoding="utf-8")

    with pytest.raises(RuntimeError, match="usuarios.json"):
        usuarios.cargar_usuarios()


# ---------------------------------------------------------------------------
# Registro
# ---------------------------------------------------------------------------

def test_registrar_usuario_guarda_el_hash_y_no_la_clave(entorno_limpio):
    usuarios.registrar_usuario("Admin@Clinica.com", "secreto-123")

    registros = _leer_usuarios()
    assert len(registros) == 1
    registro = registros[0]

    assert registro["email"] == "admin@clinica.com"
    assert set(registro) == {"email", "salt", "password_hash"}
    assert len(registro["salt"]) == 32
    assert len(registro["password_hash"]) == 64
    assert registro["password_hash"] != "secreto-123"

    texto = (entorno_limpio / "usuarios.json").read_text(encoding="utf-8")
    assert json.loads(texto) == registros
    assert "secreto-123" not in texto


def test_registrar_email_duplicado_lanza_value_error():
    usuarios.registrar_usuario("admin@clinica.com", "secreto-123")

    with pytest.raises(ValueError, match="Ya existe"):
        usuarios.registrar_usuario("ADMIN@CLINICA.COM", "otra-clave")

    assert len(_leer_usuarios()) == 1


def test_cada_usuario_tiene_salt_distinto():
    usuarios.registrar_usuario("uno@test.com", "clave-1234")
    usuarios.registrar_usuario("dos@test.com", "clave-1234")

    salts = {registro["salt"] for registro in _leer_usuarios()}
    assert len(salts) == 2


# ---------------------------------------------------------------------------
# Búsqueda y autenticación
# ---------------------------------------------------------------------------

def test_buscar_usuario_es_case_insensitive():
    usuarios.registrar_usuario("Admin@Clinica.com", "secreto-123")

    assert usuarios.buscar_usuario("admin@clinica.com")["email"] == (
        "admin@clinica.com"
    )
    assert usuarios.buscar_usuario("  ADMIN@CLINICA.COM ") is not None
    assert usuarios.buscar_usuario("no@existe.com") is None


def test_autenticar_con_credenciales_correctas():
    usuarios.registrar_usuario("admin@clinica.com", "secreto-123")

    assert usuarios.autenticar_usuario(
        "ADMIN@clinica.com", "secreto-123"
    ) == {"email": "admin@clinica.com"}


def test_autenticar_con_clave_incorrecta_devuelve_none():
    usuarios.registrar_usuario("admin@clinica.com", "secreto-123")

    assert usuarios.autenticar_usuario("admin@clinica.com", "otra") is None


def test_autenticar_usuario_inexistente_devuelve_none():
    assert usuarios.autenticar_usuario("nadie@test.com", "clave-1234") is None


def test_crear_indice_de_usuarios():
    usuarios.registrar_usuario("Admin@Clinica.com", "secreto-123")

    tabla = usuarios.crear_indice()
    assert isinstance(tabla, dict)
    assert busquedas.hash_buscar(tabla, "ADMIN@CLINICA.COM")[0]["email"] == (
        "admin@clinica.com"
    )
    assert busquedas.hash_buscar(tabla, "no@existe.com") is None
