"""Fila de espera (FIFO) de citas por espacio de agenda.

Un "espacio" es la terna (médico, fecha, hora). Solo puede ocuparlo una cita
activa. Cuando ese espacio ya está tomado, las citas siguientes no se pierden:
entran en una Cola y quedan en estado "En espera", numeradas por orden de
llegada. Cuando la cita activa se completa o se cancela, la primera de la fila
sale de la Cola y pasa a ocupar el espacio.

Este módulo no escribe en disco: solo calcula. Quien persiste es citas.py.
"""
from estructuras import Cola

#: Estado de una cita que quedó en la fila detrás de otra.
ESTADO_ESPERA = "En espera"

#: Estados que YA LIBERARON el espacio: no cuentan como ocupantes.
ESTADOS_LIBERADOS = ("Realizada", "Cancelada")


def clave_espacio(cita):
    """Identifica el espacio de agenda de una cita: (médico, fecha, hora)."""
    return (
        str(cita.get("medico", "")).strip().casefold(),
        str(cita.get("fecha", "")).strip(),
        str(cita.get("hora", "")).strip(),
    )


def espacio_ocupado(citas, nueva):
    """True si ya hay una cita activa o en espera en ese mismo espacio."""
    objetivo = clave_espacio(nueva)
    return any(
        clave_espacio(c) == objetivo and c.get("estado", "Pendiente") not in ESTADOS_LIBERADOS
        for c in citas
    )


def en_espera_del_espacio(citas, espacio):
    """Lista de citas en espera de un espacio, de menor a mayor posición."""
    objetivo = espacio if isinstance(espacio, tuple) else clave_espacio(espacio)
    grupo = [
        c for c in citas
        if c.get("estado") == ESTADO_ESPERA and clave_espacio(c) == objetivo
    ]
    return sorted(grupo, key=lambda c: int(c.get("posicion_espera") or 0))


def cola_espera(citas, espacio):
    """Cola FIFO con las citas EN ESPERA de un espacio, en orden de llegada."""
    cola = Cola()
    for cita in en_espera_del_espacio(citas, espacio):
        cola.encolar(cita)
    return cola


def total_en_espera(citas, espacio):
    """Cuántas personas hay detrás en la fila de ese espacio."""
    return len(en_espera_del_espacio(citas, espacio))


def posiciones_ocupadas(citas):
    """Resumen {espacio: (activa, [citas en espera])} para las listas de espera."""
    resumen = {}
    for cita in citas:
        resumen.setdefault(clave_espacio(cita), []).append(cita)
    filas = {}
    for clave, grupo in resumen.items():
        activa = next(
            (c for c in grupo if c.get("estado") not in ESTADOS_LIBERADOS + (ESTADO_ESPERA,)),
            None,
        )
        filas[clave] = (activa, en_espera_del_espacio(citas, clave))
    return filas


def renumerar(citas, espacio):
    """Recalcula las posiciones 1..n de la fila tras una promoción."""
    for indice, cita in enumerate(en_espera_del_espacio(citas, espacio), start=1):
        cita["posicion_espera"] = indice