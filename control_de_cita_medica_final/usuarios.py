"""Gestión local de cuentas de usuario para MediCitas."""
import hashlib
import json
import os
import tempfile

import busquedas
from almacenamiento import firma_archivo

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "archivos")
USUARIOS_FILE = os.path.join(DATA_DIR, "usuarios.json")

# Índice hash reutilizable por correo electrónico.
_indice_usuarios = None
_firma_indice = None


def _hash_password(password, salt=None):
    salt = salt or os.urandom(16).hex()
    digest = hashlib.pbkdf2_hmac("sha256", password.encode("utf-8"), salt.encode("utf-8"), 200_000).hex()
    return salt, digest


def cargar_usuarios():
    os.makedirs(DATA_DIR, exist_ok=True)
    if not os.path.exists(USUARIOS_FILE):
        return []
    try:
        with open(USUARIOS_FILE, "r", encoding="utf-8") as f:
            data = json.load(f)
        return data if isinstance(data, list) else []
    except (json.JSONDecodeError, OSError):
        raise RuntimeError("No se pudo leer archivos/usuarios.json. Revisa el archivo antes de continuar.")


def _guardar_usuarios(data):
    os.makedirs(DATA_DIR, exist_ok=True)
    fd, temp_path = tempfile.mkstemp(prefix="usuarios_", suffix=".tmp", dir=DATA_DIR)
    try:
        with os.fdopen(fd, "w", encoding="utf-8") as f:
            json.dump(data, f, ensure_ascii=False, indent=2)
        os.replace(temp_path, USUARIOS_FILE)
        _invalidar_indice()
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


def _invalidar_indice():
    global _indice_usuarios, _firma_indice
    _indice_usuarios = None
    _firma_indice = None


def crear_indice(usuarios=None):
    """Construye una tabla hash de correos para una lista de cuentas."""
    usuarios = cargar_usuarios() if usuarios is None else usuarios
    return busquedas.construir_hash(usuarios, "email")


def _indice_actual():
    global _indice_usuarios, _firma_indice
    firma = firma_archivo(USUARIOS_FILE)
    if _indice_usuarios is None or firma != _firma_indice:
        _indice_usuarios = crear_indice(cargar_usuarios())
        _firma_indice = firma
    return _indice_usuarios


def buscar_usuario(email):
    """Búsqueda exacta de una cuenta por correo con tabla hash."""
    par = _indice_actual().buscar(str(email).strip().lower())
    return par[0] if par else None


def registrar_usuario(email, password):
    email = email.strip().lower()
    if buscar_usuario(email) is not None:
        raise ValueError("Ya existe una cuenta registrada con ese correo.")
    salt, digest = _hash_password(password)
    usuarios = cargar_usuarios()
    usuarios.append({"email": email, "salt": salt, "password_hash": digest})
    _guardar_usuarios(usuarios)


def autenticar_usuario(email, password):
    email = email.strip().lower()
    user = buscar_usuario(email)
    if user is None:
        return None
    salt = user.get("salt", "")
    _, digest = _hash_password(password, salt)
    if digest == user.get("password_hash"):
        return {"email": user["email"]}
    return None
