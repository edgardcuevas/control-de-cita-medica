import json, os

import busquedas
import historial
import esperas
from almacenamiento import cargar_json_lista, firma_archivo, guardar_json_atomico
from esperas import ESTADO_ESPERA

ARCHIVO = os.path.join(os.path.dirname(__file__), "archivos", "citas.json")

#: Campos que participan en la búsqueda por texto libre.
CAMPOS_BUSQUEDA = (
    "paciente",
    "documento_paciente",
    "medico",
    "especialidad",
    "modulo",
    "fecha",
    "hora",
    "tipo",
    "motivo",
    "observaciones",
    "estado",
)

# Índice de fechas reutilizable por la búsqueda binaria.
_indice_fechas = None
_firma_indice = None

def cargar_citas():
    try:
        with open(ARCHIVO, "r", encoding="utf-8") as archivo:
            datos = json.load(archivo)
            if not isinstance(datos, list):
                return []
            for cita in datos:
                cita.setdefault("estado", "Pendiente")
                # Solo las citas en espera llevan número de posición.
                if cita["estado"] != ESTADO_ESPERA:
                    cita.pop("posicion_espera", None)
            return datos
    except (FileNotFoundError, json.JSONDecodeError):
        return []

def _guardar_citas(citas):
    guardar_json_atomico(ARCHIVO, citas)
    _invalidar_indice()


def _invalidar_indice():
    global _indice_fechas, _firma_indice
    _indice_fechas = None
    _firma_indice = None


def crear_indice_fechas(registros=None):
    """Índice ordenado por fecha ISO para la búsqueda binaria."""
    registros = cargar_citas() if registros is None else registros
    return busquedas.indice_ordenado(
        registros, lambda cita: busquedas.clave_fecha(cita.get("fecha", ""))
    )


def _indice_fechas_actual():
    global _indice_fechas, _firma_indice
    firma = firma_archivo(ARCHIVO)
    if _indice_fechas is None or firma != _firma_indice:
        _indice_fechas = crear_indice_fechas(cargar_citas())
        _firma_indice = firma
    return _indice_fechas


def _fecha_iso(texto):
    """Devuelve la fecha en formato ISO o None si no es dd/mm/aaaa."""
    clave = busquedas.clave_fecha(texto)
    return None if clave == "9999-99-99" else clave


def buscar_citas(texto="", estado=None, registros=None):
    """Busca citas por texto libre, estado y fecha exacta.

    - Fecha ``dd/mm/aaaa`` -> búsqueda binaria sobre un índice de fechas.
    - Cualquier otro texto -> búsqueda secuencial por todos los campos.
    - ``estado`` se aplica antes de buscar y admite los cuatro estados.
    """
    usar_cache = registros is None
    registros = cargar_citas() if usar_cache else registros
    filtrados = registros
    if estado and estado != "Todas":
        filtrados = [
            cita for cita in registros
            if cita.get("estado", "Pendiente") == estado
        ]

    consulta = busquedas.normalizar(texto)
    if not consulta:
        return busquedas.crear_resultado(filtrados, "Listado", 0)

    fecha_iso = _fecha_iso(texto)
    if fecha_iso:
        if usar_cache and not (estado and estado != "Todas"):
            indice = _indice_fechas_actual()
        else:
            indice = crear_indice_fechas(filtrados)
        posiciones, comparaciones = busquedas.busqueda_por_rango(
            indice, fecha_iso, fecha_iso
        )
        return busquedas.crear_resultado(
            [filtrados[posicion] for posicion in posiciones],
            "Binaria (fecha)",
            comparaciones,
        )

    terminos = consulta.split()

    def coincide(cita):
        texto_cita = busquedas.normalizar(
            " ".join(str(cita.get(campo, "")) for campo in CAMPOS_BUSQUEDA)
        )
        return all(termino in texto_cita for termino in terminos)

    return busquedas.busqueda_secuencial(filtrados, coincide)


def buscar_por_fecha(desde, hasta, registros=None):
    """Busca citas entre dos fechas inclusivas con búsqueda binaria."""
    usar_cache = registros is None
    registros = cargar_citas() if usar_cache else registros
    iso_desde = _fecha_iso(desde)
    iso_hasta = _fecha_iso(hasta)
    if not iso_desde or not iso_hasta:
        return busquedas.crear_resultado([], "Binaria (fecha)", 0)
    if iso_desde > iso_hasta:
        iso_desde, iso_hasta = iso_hasta, iso_desde

    indice = (
        _indice_fechas_actual()
        if usar_cache
        else crear_indice_fechas(registros)
    )
    posiciones, comparaciones = busquedas.busqueda_por_rango(
        indice, iso_desde, iso_hasta
    )
    return busquedas.crear_resultado(
        [registros[posicion] for posicion in posiciones],
        "Binaria (fecha)",
        comparaciones,
    )


def buscar_por_espacio(medico, fecha, hora, registros=None):
    """Devuelve todas las citas de un espacio (médico, fecha, hora) usando hash."""
    registros = cargar_citas() if registros is None else registros
    tabla = busquedas.construir_hash_multiple(registros, esperas.clave_espacio)
    clave = esperas.clave_espacio(
        {"medico": medico, "fecha": fecha, "hora": hora}
    )
    pares = busquedas.hash_buscar_todos(tabla, clave)
    pares.sort(key=lambda par: par[1])
    return busquedas.crear_resultado(
        [par[0] for par in pares],
        "Hash (espacio)",
        max(1, len(pares)),
    )


def contar_citas_paciente(documento, nombre=None):
    registros = cargar_json_lista(ARCHIVO)
    documento = str(documento).casefold()
    nombre = (nombre or "").casefold()
    return sum(
        1
        for cita in registros
        if str(cita.get("documento_paciente", "")).casefold() == documento
        or (
            not cita.get("documento_paciente")
            and nombre
            and str(cita.get("paciente", "")).casefold() == nombre
        )
    )


def contar_citas_medico(nombre):
    registros = cargar_json_lista(ARCHIVO)
    nombre = str(nombre).casefold()
    return sum(
        1 for cita in registros if str(cita.get("medico", "")).casefold() == nombre
    )


def eliminar_cita(cita):
    if not isinstance(cita, dict):
        raise ValueError("La cita seleccionada no es válida.")
    registros = cargar_json_lista(ARCHIVO)
    cita_normalizada = dict(cita)
    cita_normalizada.setdefault("estado", "Pendiente")
    for posicion, registro in enumerate(registros):
        registro_normalizado = dict(registro)
        registro_normalizado.setdefault("estado", "Pendiente")
        if registro_normalizado == cita_normalizada:
            del registros[posicion]
            _guardar_citas(registros)
            historial.registrar_accion(
                "Eliminar cita",
                {
                    "tipo": "eliminar",
                    "entidad": "cita",
                    "posicion": posicion,
                    "datos": dict(registro),
                },
            )
            return True
    return False

def _foto_fila(registros, espacio):
    """Instantánea de las posiciones de TODAS las citas en espera del espacio.

    Sin esto no se podría deshacer una promoción: al promover a la primera se
    renumeran las demás, y hay que poder devolverlas a su posición original.
    """
    return [
        {"posicion": indice, "posicion_espera": cita.get("posicion_espera")}
        for indice, cita in enumerate(registros)
        if cita.get("estado") == ESTADO_ESPERA
        and esperas.clave_espacio(cita) == espacio
    ]


def _promover_siguiente(registros, espacio):
    """Saca la primera cita de la fila FIFO de espera y la pone en el espacio.

    Devuelve la instantánea de lo cambiado (para poder deshacerlo) o None si
    la fila estaba vacía.
    """
    cola = esperas.cola_espera(registros, espacio)
    if not cola:
        return None
    siguiente = cola[0]
    for indice, cita in enumerate(registros):
        if cita is siguiente:
            promocion = {
                "posicion": indice,
                "estado_anterior": ESTADO_ESPERA,
                "posicion_espera": cita.get("posicion_espera"),
            }
            cita["estado"] = "Pendiente"
            cita.pop("posicion_espera", None)
            esperas.renumerar(registros, espacio)
            return promocion
    return None


def agregar_cita(cita):
    """Agrega una cita. Si el espacio de agenda está ocupado, entra en la fila.

    Devuelve la cita tal como quedó guardada, con su estado y, si quedó en
    espera, su posición en la fila.
    """
    citas = cargar_citas()
    nueva = dict(cita)
    espacio = esperas.clave_espacio(nueva)
    if esperas.espacio_ocupado(citas, nueva):
        nueva["estado"] = ESTADO_ESPERA
        nueva["posicion_espera"] = esperas.total_en_espera(citas, espacio) + 1
    else:
        nueva["estado"] = "Pendiente"
        nueva.pop("posicion_espera", None)
    citas.append(nueva)
    _guardar_citas(citas)
    historial.registrar_accion(
        "Agendar cita",
        {
            "tipo": "agregar",
            "entidad": "cita",
            "posicion": len(citas) - 1,
            "datos": dict(nueva),
        },
    )
    return nueva


def marcar_como_realizada(posicion):
    """Atiende la cita activa y hace subir a la primera de la fila, si la hay.

    Devuelve (cita_atendida, hubo_promocion). hubo_promocion es True si alguien
    salió de la fila de espera al liberarse el espacio.
    """
    citas = cargar_citas()
    if not 0 <= posicion < len(citas):
        return None, None
    atendida = citas[posicion]
    estado_anterior = atendida.get("estado", "Pendiente")
    atendida["estado"] = "Realizada"
    atendida.pop("posicion_espera", None)
    espacio = esperas.clave_espacio(atendida)
    fila_antes = _foto_fila(citas, espacio)
    # Solo se promueve si era la cita que ocupaba el espacio. Si el usuario
    # atiende directamente a alguien que estaba en espera, la fila no cambia.
    promocion = (
        _promover_siguiente(citas, espacio) if estado_anterior == "Pendiente" else None
    )
    _guardar_citas(citas)
    historial.registrar_accion(
        "Marcar cita como realizada",
        {
            "tipo": "estado",
            "entidad": "cita",
            "posicion": posicion,
            "estado_anterior": estado_anterior,
            "promocion": promocion,
            "fila_antes": fila_antes,
        },
    )
    return atendida, (promocion is not None)


def cancelar_cita(cita):
    """Cancela una cita y libera su espacio de agenda.

    Devuelve la cita promovida desde la fila de espera, o None si no había
    ninguna esperando.
    """
    if not isinstance(cita, dict):
        raise ValueError("La cita seleccionada no es válida.")
    registros = cargar_json_lista(ARCHIVO)
    objetivo = dict(cita)
    objetivo.setdefault("estado", "Pendiente")
    objetivo.pop("posicion_espera", None)
    for posicion, registro in enumerate(registros):
        comparable = dict(registro)
        comparable.setdefault("estado", "Pendiente")
        comparable.pop("posicion_espera", None)
        if comparable != objetivo:
            continue
        estado_anterior = registro.get("estado", "Pendiente")
        espacio = esperas.clave_espacio(registro)
        fila_antes = _foto_fila(registros, espacio)
        registro["estado"] = "Cancelada"
        registro.pop("posicion_espera", None)
        promocion = (
            _promover_siguiente(registros, espacio) if estado_anterior == "Pendiente" else None
        )
        _guardar_citas(registros)
        historial.registrar_accion(
            "Cancelar cita",
            {
                "tipo": "estado",
                "entidad": "cita",
                "posicion": posicion,
                "estado_anterior": estado_anterior,
                "promocion": promocion,
                "fila_antes": fila_antes,
            },
        )
        # La fila avanza: se devuelve la cita promovida (o None si no había).
        return registros[promocion["posicion"]] if promocion else None
    return None


def revertir(instantanea):
    """Deshace una acción sobre citas a partir de su instantánea."""
    tipo = instantanea.get("tipo")
    posicion = instantanea.get("posicion")
    if not isinstance(posicion, int) or posicion < 0:
        return False
    registros = cargar_json_lista(ARCHIVO)

    if tipo == "eliminar":
        if posicion > len(registros):
            return False
        registros.insert(posicion, instantanea.get("datos"))
        _guardar_citas(registros)
        return True

    if tipo == "agregar":
        if posicion >= len(registros) or registros[posicion] != instantanea.get("datos"):
            return False
        del registros[posicion]
        _guardar_citas(registros)
        return True

    if tipo == "estado":
        if posicion >= len(registros):
            return False
        estado_anterior = instantanea.get("estado_anterior", "Pendiente")
        registros[posicion]["estado"] = estado_anterior
        registros[posicion].pop("posicion_espera", None)
        # La cita promovida vuelve a la fila.
        promocion = instantanea.get("promocion")
        if isinstance(promocion, dict):
            destino = promocion.get("posicion")
            if isinstance(destino, int) and 0 <= destino < len(registros):
                registros[destino]["estado"] = ESTADO_ESPERA
        # Y se restauran las posiciones exactas de toda la fila, incluida la
        # renumeración que provocó la promoción.
        for item in instantanea.get("fila_antes") or []:
            indice = item.get("posicion")
            if not isinstance(indice, int) or not 0 <= indice < len(registros):
                continue
            anterior = item.get("posicion_espera")
            if anterior is None:
                registros[indice].pop("posicion_espera", None)
            else:
                registros[indice]["posicion_espera"] = anterior
        _guardar_citas(registros)
        return True

    return False