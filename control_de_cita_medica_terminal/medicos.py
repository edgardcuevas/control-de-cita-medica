import json, os

import busquedas
import historial
from almacenamiento import cargar_json_lista, firma_archivo, guardar_json_atomico

ARCHIVO = os.path.join(os.path.dirname(__file__), "archivos", "medicos.json")

#: Campos que participan en la búsqueda por texto libre.
CAMPOS_BUSQUEDA = (
    "nombre",
    "apellido",
    "documento",
    "telefono",
    "correo",
    "modulo",
    "especialidad",
    "consultorio",
    "horario",
)

# Índice hash reutilizable por documento.
_indice_documentos = None
_firma_indice = None


def cargar_medicos():
    try:
        with open(ARCHIVO, "r", encoding="utf-8") as archivo:
            datos = json.load(archivo)
            return datos if isinstance(datos, list) else []
    except (FileNotFoundError, json.JSONDecodeError):
        return []


def _guardar_medicos(medicos):
    guardar_json_atomico(ARCHIVO, medicos)
    _invalidar_indice()


def _invalidar_indice():
    global _indice_documentos, _firma_indice
    _indice_documentos = None
    _firma_indice = None


def crear_indice(registros=None):
    """Construye una tabla hash de documentos para una lista de médicos."""
    registros = cargar_medicos() if registros is None else registros
    return busquedas.construir_hash(registros, "documento")


def _indice_actual():
    global _indice_documentos, _firma_indice
    firma = firma_archivo(ARCHIVO)
    if _indice_documentos is None or firma != _firma_indice:
        _indice_documentos = crear_indice(cargar_medicos())
        _firma_indice = firma
    return _indice_documentos


def buscar_por_documento(documento):
    """Búsqueda exacta por documento con tabla hash: O(1) promedio."""
    par = _indice_actual().buscar(documento)
    return par[0] if par else None


def _buscar_par_documento(documento):
    """Devuelve ``(médico, índice_en_el_archivo)`` o None."""
    return _indice_actual().buscar(documento)


def buscar_medicos(texto, registros=None):
    """Busca médicos por texto libre o por documento exacto.

    - Documento exacto -> tabla hash.
    - Texto parcial -> búsqueda secuencial por todos los campos.
    """
    usar_cache = registros is None
    registros = cargar_medicos() if usar_cache else registros
    consulta = busquedas.normalizar(texto)

    if not consulta:
        return busquedas.ResultadoBusqueda(registros, "Listado", 0)

    if " " not in consulta and busquedas.parece_documento(consulta):
        if usar_cache:
            par = _buscar_par_documento(consulta)
        else:
            par = crear_indice(registros).buscar(consulta)
        if par:
            return busquedas.ResultadoBusqueda([par[0]], "Hash (documento)", 1)

    terminos = consulta.split()

    def coincide(registro):
        texto_registro = busquedas.normalizar(
            " ".join(str(registro.get(campo, "")) for campo in CAMPOS_BUSQUEDA)
        )
        return all(termino in texto_registro for termino in terminos)

    return busquedas.busqueda_secuencial(registros, coincide)


def registrar_medico(datos):
    medicos = cargar_medicos()
    medicos.append(datos)
    _guardar_medicos(medicos)
    historial.registrar_accion(
        "Registrar médico",
        {
            "tipo": "agregar",
            "entidad": "medico",
            "posicion": len(medicos) - 1,
            "datos": dict(datos),
        },
    )
    return datos


def eliminar_medico(documento):
    registros = cargar_json_lista(ARCHIVO)
    par = busquedas.construir_hash(registros, "documento").buscar(documento)
    if par is None:
        return False
    medico, posicion = par

    from citas import contar_citas_medico

    nombre = f'{medico.get("nombre", "")} {medico.get("apellido", "")}'.strip()
    asociadas = contar_citas_medico(nombre)
    if asociadas:
        raise ValueError(
            f"No se puede eliminar el médico porque tiene {asociadas} "
            "cita(s) registrada(s). Elimine primero las citas."
        )

    del registros[posicion]
    _guardar_medicos(registros)
    historial.registrar_accion(
        "Eliminar médico",
        {
            "tipo": "eliminar",
            "entidad": "medico",
            "posicion": posicion,
            "datos": dict(medico),
        },
    )
    return True


def revertir(instantanea):
    """Deshace una acción sobre médicos a partir de su instantánea."""
    tipo = instantanea.get("tipo")
    posicion = instantanea.get("posicion")
    if not isinstance(posicion, int) or posicion < 0:
        return False
    registros = cargar_json_lista(ARCHIVO)

    if tipo == "eliminar":
        if posicion > len(registros):
            return False
        registros.insert(posicion, instantanea.get("datos"))
        _guardar_medicos(registros)
        return True

    if tipo == "agregar":
        if posicion >= len(registros) or registros[posicion] != instantanea.get("datos"):
            return False
        del registros[posicion]
        _guardar_medicos(registros)
        return True

    return False
