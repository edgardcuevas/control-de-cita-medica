"""Gestión local de cuentas de usuario para MediCitas."""
import hashlib
import json
import os
import tempfile

BASE_DIR = os.path.dirname(os.path.abspath(__file__))
DATA_DIR = os.path.join(BASE_DIR, "archivos")
USUARIOS_FILE = os.path.join(DATA_DIR, "usuarios.json")


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
    finally:
        if os.path.exists(temp_path):
            os.remove(temp_path)


def registrar_usuario(email, password):
    email = email.strip().lower()
    usuarios = cargar_usuarios()
    if any(u.get("email", "").lower() == email for u in usuarios):
        raise ValueError("Ya existe una cuenta registrada con ese correo.")
    salt, digest = _hash_password(password)
    usuarios.append({"email": email, "salt": salt, "password_hash": digest})
    _guardar_usuarios(usuarios)


def autenticar_usuario(email, password):
    email = email.strip().lower()
    for user in cargar_usuarios():
        if user.get("email", "").lower() == email:
            salt = user.get("salt", "")
            _, digest = _hash_password(password, salt)
            if digest == user.get("password_hash"):
                return {"email": user["email"]}
            return None
    return None
