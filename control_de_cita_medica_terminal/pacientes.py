import json, os

import busquedas
import historial
from almacenamiento import cargar_json_lista, firma_archivo, guardar_json_atomico

ARCHIVO = os.path.join(os.path.dirname(__file__), "archivos", "pacientes.json")

#: Campos que participan en la búsqueda por texto libre.
CAMPOS_BUSQUEDA = (
    "nombre",
    "apellido",
    "documento",
    "telefono",
    "correo",
    "tipo_sangre",
    "seguro_medico",
    "direccion",
    "fecha_nacimiento",
    "sexo",
)

# Índice hash reutilizable por documento. Se reconstruye cuando cambia el
# archivo, de modo que una búsqueda exacta no recorra toda la lista.
_indice_documentos = None
_firma_indice = None


def cargar_pacientes():
    try:
        with open(ARCHIVO, "r", encoding="utf-8") as archivo:
            datos = json.load(archivo)
            return datos if isinstance(datos, list) else []
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def _guardar_pacientes(pacientes):
    guardar_json_atomico(ARCHIVO, pacientes)
    _invalidar_indice()


def _invalidar_indice():
    global _indice_documentos, _firma_indice
    _indice_documentos = None
    _firma_indice = None


def crear_indice(registros=None):
    """Construye una tabla hash de documentos para una lista de pacientes."""
    registros = cargar_pacientes() if registros is None else registros
    return busquedas.construir_hash(registros, "documento")


def _indice_actual():
    global _indice_documentos, _firma_indice
    firma = firma_archivo(ARCHIVO)
    if _indice_documentos is None or firma != _firma_indice:
        _indice_documentos = crear_indice(cargar_pacientes())
        _firma_indice = firma
    return _indice_documentos


def buscar_por_documento(documento):
    """Búsqueda exacta por documento con tabla hash: O(1) promedio."""
    par = busquedas.hash_buscar(_indice_actual(), documento)
    return par[0] if par else None


def _buscar_par_documento(documento):
    """Devuelve ``(paciente, índice_en_el_archivo)`` o None."""
    return busquedas.hash_buscar(_indice_actual(), documento)


def buscar_pacientes(texto, registros=None):
    """Busca pacientes por texto libre o por documento exacto.

    - Si el texto coincide exactamente con un documento, usa la tabla hash.
    - En cualquier otro caso recorre los registros con búsqueda secuencial,
      exigiendo que todos los términos aparezcan en algún campo.
    """
    usar_cache = registros is None
    registros = cargar_pacientes() if usar_cache else registros
    consulta = busquedas.normalizar(texto)

    if not consulta:
        return busquedas.crear_resultado(registros, "Listado", 0)

    # Camino rápido: documento exacto.
    if " " not in consulta and busquedas.parece_documento(consulta):
        if usar_cache:
            par = _buscar_par_documento(consulta)
        else:
            par = busquedas.hash_buscar(crear_indice(registros), consulta)
        if par:
            return busquedas.crear_resultado([par[0]], "Hash (documento)", 1)

    terminos = consulta.split()

    def coincide(registro):
        texto_registro = busquedas.normalizar(
            " ".join(str(registro.get(campo, "")) for campo in CAMPOS_BUSQUEDA)
        )
        return all(termino in texto_registro for termino in terminos)

    return busquedas.busqueda_secuencial(registros, coincide)


def registrar_paciente(datos):
    pacientes = cargar_pacientes()
    pacientes.append(datos)
    _guardar_pacientes(pacientes)
    historial.registrar_accion(
        "Registrar paciente",
        {
            "tipo": "agregar",
            "entidad": "paciente",
            "posicion": len(pacientes) - 1,
            "datos": dict(datos),
        },
    )
    return datos


def eliminar_paciente(documento):
    registros = cargar_json_lista(ARCHIVO)
    indice = busquedas.construir_hash(registros, "documento")
    par = busquedas.hash_buscar(indice, documento)
    if par is None:
        return False
    paciente, posicion = par

    from citas import contar_citas_paciente

    nombre = f'{paciente.get("nombre", "")} {paciente.get("apellido", "")}'.strip()
    asociadas = contar_citas_paciente(documento, nombre)
    if asociadas:
        raise ValueError(
            f"No se puede eliminar el paciente porque tiene {asociadas} "
            "cita(s) registrada(s). Elimine primero las citas."
        )

    del registros[posicion]
    _guardar_pacientes(registros)
    historial.registrar_accion(
        "Eliminar paciente",
        {
            "tipo": "eliminar",
            "entidad": "paciente",
            "posicion": posicion,
            "datos": dict(paciente),
        },
    )
    return True


def revertir(instantanea):
    """Deshace una acción sobre pacientes a partir de su instantánea."""
    tipo = instantanea.get("tipo")
    posicion = instantanea.get("posicion")
    if not isinstance(posicion, int) or posicion < 0:
        return False
    registros = cargar_json_lista(ARCHIVO)

    if tipo == "eliminar":
        if posicion > len(registros):
            return False
        registros.insert(posicion, instantanea.get("datos"))
        _guardar_pacientes(registros)
        return True

    if tipo == "agregar":
        if posicion >= len(registros) or registros[posicion] != instantanea.get("datos"):
            return False
        del registros[posicion]
        _guardar_pacientes(registros)
        return True

    return False
