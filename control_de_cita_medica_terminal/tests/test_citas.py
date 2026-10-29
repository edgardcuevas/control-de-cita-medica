"""Pruebas del módulo de citas: búsquedas, agenda, fila de espera y deshacer."""
import pytest

import citas
import esperas
import historial


def _cita(estado="Pendiente", posicion=None, hora="10:00", paciente="Paciente",
          documento="DOC-1", medico="Ernesto Gutierres"):
    cita = {
        "paciente": paciente,
        "documento_paciente": documento,
        "medico": medico,
        "especialidad": "diabetologo",
        "modulo": "5",
        "fecha": "22/09/2026",
        "hora": hora,
        "tipo": "presencial",
        "motivo": "consulta",
        "observaciones": "ninguna",
        "estado": estado,
    }
    if posicion is not None:
        cita["posicion_espera"] = posicion
    return cita


# ---------------------------------------------------------------------------
# Búsquedas en memoria
# ---------------------------------------------------------------------------

def test_buscar_sin_texto_devuelve_el_listado(citas_ejemplo):
    resultado = citas.buscar_citas(registros=citas_ejemplo)

    assert resultado["elementos"] == citas_ejemplo
    assert resultado["algoritmo"] == "Listado"
    assert resultado["comparaciones"] == 0


def test_buscar_por_fecha_exacta_usa_binaria(citas_ejemplo):
    resultado = citas.buscar_citas("22/09/2026", registros=citas_ejemplo)

    assert len(resultado["elementos"]) == 2
    assert resultado["algoritmo"] == "Binaria (fecha)"


def test_buscar_por_texto_usa_secuencial(citas_ejemplo):
    resultado = citas.buscar_citas("maria", registros=citas_ejemplo)

    assert len(resultado["elementos"]) == 2
    assert resultado["algoritmo"] == "Secuencial"


def test_buscar_por_motivo(citas_ejemplo):
    resultado = citas.buscar_citas("revision", registros=citas_ejemplo)

    assert len(resultado["elementos"]) == 1
    assert resultado["elementos"][0]["paciente"].startswith("Juan")


def test_buscar_por_medico_ignora_acentos_y_mayusculas(citas_ejemplo):
    resultado = citas.buscar_citas("ERNESTO", registros=citas_ejemplo)
    assert len(resultado["elementos"]) == 2


def test_buscar_combina_texto_y_estado(citas_ejemplo):
    resultado = citas.buscar_citas("maria", "Pendiente", registros=citas_ejemplo)
    assert resultado["elementos"] == []


def test_buscar_solo_por_estado(citas_ejemplo):
    resultado = citas.buscar_citas(estado="En espera", registros=citas_ejemplo)

    assert len(resultado["elementos"]) == 1
    assert resultado["elementos"][0]["estado"] == "En espera"
    assert resultado["algoritmo"] == "Listado"


def test_buscar_fecha_y_estado(citas_ejemplo):
    resultado = citas.buscar_citas(
        "22/09/2026", "Realizada", registros=citas_ejemplo
    )

    assert len(resultado["elementos"]) == 1
    assert resultado["algoritmo"] == "Binaria (fecha)"


def test_buscar_texto_sin_resultados(citas_ejemplo):
    resultado = citas.buscar_citas("cardiologia", registros=citas_ejemplo)
    assert resultado["elementos"] == []


def test_buscar_por_fecha_rango(citas_ejemplo):
    resultado = citas.buscar_por_fecha(
        "01/09/2026", "30/09/2026", registros=citas_ejemplo
    )

    assert len(resultado["elementos"]) == 2
    assert resultado["algoritmo"] == "Binaria (fecha)"


def test_buscar_por_fecha_rango_invertido(citas_ejemplo):
    resultado = citas.buscar_por_fecha(
        "30/09/2026", "01/09/2026", registros=citas_ejemplo
    )
    assert len(resultado["elementos"]) == 2


def test_buscar_por_fecha_invalida(citas_ejemplo):
    resultado = citas.buscar_por_fecha(
        "01/09/2026", "no es fecha", registros=citas_ejemplo
    )

    assert resultado["elementos"] == []
    assert resultado["algoritmo"] == "Binaria (fecha)"
    assert resultado["comparaciones"] == 0


def test_buscar_por_espacio_normaliza_el_medico(citas_ejemplo):
    resultado = citas.buscar_por_espacio(
        "  ERNESTO GUTIERRES ", "22/09/2026", "10:00", registros=citas_ejemplo
    )

    assert len(resultado["elementos"]) == 1
    assert resultado["algoritmo"] == "Hash (espacio)"
    assert resultado["elementos"][0]["estado"] == "Realizada"


def test_buscar_por_espacio_devuelve_la_cita_en_espera(citas_ejemplo):
    resultado = citas.buscar_por_espacio(
        "Ernesto Gutierres", "22/09/2026", "11:00", registros=citas_ejemplo
    )

    assert len(resultado["elementos"]) == 1
    assert resultado["elementos"][0]["estado"] == esperas.ESTADO_ESPERA


def test_buscar_por_espacio_sin_resultados(citas_ejemplo):
    resultado = citas.buscar_por_espacio(
        "Ernesto Gutierres", "23/09/2026", "10:00", registros=citas_ejemplo
    )

    assert resultado["elementos"] == []
    assert resultado["comparaciones"] == 1


# ---------------------------------------------------------------------------
# Carga del archivo
# ---------------------------------------------------------------------------

def test_cargar_citas_completa_estado_y_limpia_posiciones(escribir_json):
    escribir_json(
        citas,
        [
            {"paciente": "Sin estado", "fecha": "01/10/2026", "hora": "09:00"},
            {
                "paciente": "Pendiente con posición",
                "fecha": "01/10/2026",
                "hora": "10:00",
                "estado": "Pendiente",
                "posicion_espera": 3,
            },
            {
                "paciente": "En espera",
                "fecha": "01/10/2026",
                "hora": "11:00",
                "estado": esperas.ESTADO_ESPERA,
                "posicion_espera": 1,
            },
        ],
    )

    registros = citas.cargar_citas()

    assert registros[0]["estado"] == "Pendiente"
    assert "posicion_espera" not in registros[0]
    assert "posicion_espera" not in registros[1]
    assert registros[2]["posicion_espera"] == 1


def test_cargar_citas_archivo_inexistente_devuelve_lista_vacia():
    assert citas.cargar_citas() == []


def test_cargar_citas_rechaza_contenido_que_no_es_lista(entorno_limpio):
    (entorno_limpio / "citas.json").write_text("{}", encoding="utf-8")
    assert citas.cargar_citas() == []


# ---------------------------------------------------------------------------
# Búsquedas y conteos contra el archivo
# ---------------------------------------------------------------------------

def test_buscar_citas_en_archivo_usa_el_indice(escribir_json, citas_ejemplo):
    escribir_json(citas, citas_ejemplo)

    assert len(citas.buscar_citas("22/09/2026")["elementos"]) == 2
    assert len(citas.buscar_citas("maria")["elementos"]) == 2


def test_el_indice_de_fechas_se_reconstruye(escribir_json, citas_ejemplo):
    escribir_json(citas, citas_ejemplo[:1])
    assert len(citas.buscar_citas("22/09/2026")["elementos"]) == 1

    escribir_json(citas, citas_ejemplo)
    assert len(citas.buscar_citas("22/09/2026")["elementos"]) == 2


def test_contar_citas_paciente(escribir_json, citas_ejemplo):
    escribir_json(citas, citas_ejemplo)

    assert citas.contar_citas_paciente("085-110886-4432D") == 2
    assert citas.contar_citas_paciente("085-110886-4432d") == 2
    assert citas.contar_citas_paciente("Juan") == 1
    assert citas.contar_citas_paciente("no-existe") == 0


def test_contar_citas_paciente_por_nombre_si_falta_documento(escribir_json):
    escribir_json(
        citas,
        [
            {
                "paciente": "María Esperanza Guerrero Mendez",
                "documento_paciente": "",
                "medico": "Ernesto Gutierres",
                "fecha": "22/09/2026",
                "hora": "10:00",
            }
        ],
    )

    assert (
        citas.contar_citas_paciente(
            "085-110886-4432D", "María Esperanza Guerrero Mendez"
        )
        == 1
    )
    assert citas.contar_citas_paciente("085-110886-4432D") == 0


def test_contar_citas_medico(escribir_json, citas_ejemplo):
    escribir_json(citas, citas_ejemplo)

    assert citas.contar_citas_medico("Ernesto Gutierres") == 2
    assert citas.contar_citas_medico("ernesto gutierres") == 2
    assert citas.contar_citas_medico("Marlon Surtiava") == 1
    assert citas.contar_citas_medico("nadie") == 0


# ---------------------------------------------------------------------------
# Agendar citas y fila de espera
# ---------------------------------------------------------------------------

def test_agregar_cita_en_espacio_libre_queda_pendiente(cita_base):
    guardada = citas.agregar_cita(cita_base)

    assert guardada["estado"] == "Pendiente"
    assert "posicion_espera" not in guardada
    assert citas.cargar_citas() == [guardada]
    assert historial.etiqueta_pendiente() == "Agendar cita"


@pytest.mark.parametrize("posicion", [1, 2, 3])
def test_agregar_cita_en_espacio_ocupado_entra_en_la_fila(cita_base, posicion):
    citas.agregar_cita(cita_base)
    for _ in range(posicion - 1):
        citas.agregar_cita({**cita_base, "paciente": "Relleno"})

    guardada = citas.agregar_cita(
        {**cita_base, "paciente": f"Paciente {posicion}"}
    )

    assert guardada["estado"] == esperas.ESTADO_ESPERA
    assert guardada["posicion_espera"] == posicion


def test_agregar_cita_en_hora_distinta_queda_pendiente(cita_base):
    citas.agregar_cita(cita_base)
    guardada = citas.agregar_cita({**cita_base, "hora": "11:00"})

    assert guardada["estado"] == "Pendiente"


def test_agregar_cita_normaliza_el_espacio(cita_base):
    citas.agregar_cita(cita_base)
    guardada = citas.agregar_cita(
        {
            **cita_base,
            "medico": "  ERNESTO GUTIERRES ",
            "fecha": " 22/09/2026 ",
            "hora": "10:00 ",
        }
    )

    assert guardada["estado"] == esperas.ESTADO_ESPERA


def test_agregar_cita_ignora_el_estado_recibido(cita_base):
    guardada = citas.agregar_cita(
        {**cita_base, "estado": "Realizada", "posicion_espera": 9}
    )

    assert guardada["estado"] == "Pendiente"
    assert "posicion_espera" not in guardada


def test_agregar_cita_no_modifica_el_diccionario_original(cita_base):
    original = dict(cita_base)
    citas.agregar_cita(cita_base)
    assert cita_base == original


# ---------------------------------------------------------------------------
# Marcar como realizada
# ---------------------------------------------------------------------------

def test_marcar_realizada_promueve_al_primero_de_la_fila(escribir_json):
    escribir_json(
        citas,
        [
            _cita(paciente="Activa"),
            _cita(paciente="Espera 1", estado=esperas.ESTADO_ESPERA, posicion=1),
            _cita(paciente="Espera 2", estado=esperas.ESTADO_ESPERA, posicion=2),
        ],
    )

    atendida, hubo_promocion = citas.marcar_como_realizada(0)

    assert atendida["paciente"] == "Activa"
    assert atendida["estado"] == "Realizada"
    assert hubo_promocion is True

    registros = citas.cargar_citas()
    assert registros[0]["estado"] == "Realizada"
    assert registros[1]["paciente"] == "Espera 1"
    assert registros[1]["estado"] == "Pendiente"
    assert "posicion_espera" not in registros[1]
    assert registros[2]["estado"] == esperas.ESTADO_ESPERA
    assert registros[2]["posicion_espera"] == 1
    assert historial.etiqueta_pendiente() == "Marcar cita como realizada"


def test_marcar_realizada_sin_fila_no_promueve(escribir_json):
    escribir_json(citas, [_cita()])

    atendida, hubo_promocion = citas.marcar_como_realizada(0)

    assert atendida["estado"] == "Realizada"
    assert hubo_promocion is False


def test_marcar_realizada_de_una_cita_en_espera_no_promueve(escribir_json):
    escribir_json(
        citas,
        [
            _cita(paciente="Activa"),
            _cita(paciente="Espera 1", estado=esperas.ESTADO_ESPERA, posicion=1),
            _cita(paciente="Espera 2", estado=esperas.ESTADO_ESPERA, posicion=2),
        ],
    )

    atendida, hubo_promocion = citas.marcar_como_realizada(1)

    assert atendida["paciente"] == "Espera 1"
    assert hubo_promocion is False
    registros = citas.cargar_citas()
    assert registros[0]["estado"] == "Pendiente"
    assert registros[2]["posicion_espera"] == 2


def test_marcar_realizada_con_posicion_invalida(escribir_json):
    escribir_json(citas, [_cita()])

    assert citas.marcar_como_realizada(5) == (None, None)
    assert citas.marcar_como_realizada(-1) == (None, None)


# ---------------------------------------------------------------------------
# Cancelar citas
# ---------------------------------------------------------------------------

def test_cancelar_cita_promueve_al_primero_de_la_fila(escribir_json):
    escribir_json(
        citas,
        [
            _cita(paciente="Activa"),
            _cita(paciente="Espera 1", estado=esperas.ESTADO_ESPERA, posicion=1),
            _cita(paciente="Espera 2", estado=esperas.ESTADO_ESPERA, posicion=2),
        ],
    )

    promovida = citas.cancelar_cita(citas.cargar_citas()[0])

    assert promovida["paciente"] == "Espera 1"
    registros = citas.cargar_citas()
    assert registros[0]["estado"] == "Cancelada"
    assert registros[1]["estado"] == "Pendiente"
    assert "posicion_espera" not in registros[1]
    assert registros[2]["posicion_espera"] == 1
    assert historial.etiqueta_pendiente() == "Cancelar cita"


def test_cancelar_cita_sin_fila_devuelve_none(escribir_json):
    escribir_json(citas, [_cita()])

    assert citas.cancelar_cita(citas.cargar_citas()[0]) is None
    assert citas.cargar_citas()[0]["estado"] == "Cancelada"


def test_cancelar_cita_en_espera_no_renumera(escribir_json):
    escribir_json(
        citas,
        [
            _cita(paciente="Activa"),
            _cita(paciente="Espera 1", estado=esperas.ESTADO_ESPERA, posicion=1),
            _cita(paciente="Espera 2", estado=esperas.ESTADO_ESPERA, posicion=2),
        ],
    )

    assert citas.cancelar_cita(citas.cargar_citas()[1]) is None

    registros = citas.cargar_citas()
    assert registros[1]["estado"] == "Cancelada"
    assert registros[2]["posicion_espera"] == 2


def test_cancelar_cita_inexistente_devuelve_none(escribir_json):
    escribir_json(citas, [_cita()])

    fantasma = _cita(paciente="Fantasma")
    assert citas.cancelar_cita(fantasma) is None
    assert len(citas.cargar_citas()) == 1


def test_cancelar_cita_invalida_lanza_value_error():
    with pytest.raises(ValueError):
        citas.cancelar_cita("no es una cita")


# ---------------------------------------------------------------------------
# Eliminar citas
# ---------------------------------------------------------------------------

def test_eliminar_cita(escribir_json):
    escribir_json(citas, [_cita(paciente="Uno"), _cita(paciente="Dos")])
    registro = citas.cargar_citas()[0]

    assert citas.eliminar_cita(registro) is True
    registros = citas.cargar_citas()
    assert [cita["paciente"] for cita in registros] == ["Dos"]
    assert historial.etiqueta_pendiente() == "Eliminar cita"


def test_eliminar_cita_sin_estado_guardado(escribir_json):
    escribir_json(citas, [{"paciente": "Uno", "fecha": "22/09/2026", "hora": "10:00"}])

    assert citas.eliminar_cita(
        {"paciente": "Uno", "fecha": "22/09/2026", "hora": "10:00"}
    ) is True
    assert citas.cargar_citas() == []


def test_eliminar_cita_inexistente(escribir_json):
    escribir_json(citas, [_cita(paciente="Uno")])
    assert citas.eliminar_cita(_cita(paciente="Otro")) is False


def test_eliminar_cita_invalida_lanza_value_error():
    with pytest.raises(ValueError):
        citas.eliminar_cita(None)


# ---------------------------------------------------------------------------
# Deshacer
# ---------------------------------------------------------------------------

def test_revertir_agregar(escribir_json, cita_base):
    escribir_json(citas, [])
    guardada = citas.agregar_cita(cita_base)
    entrada = historial.deshacer()

    assert citas.revertir(entrada["instantanea"]) is True
    assert citas.cargar_citas() == []
    assert guardada["estado"] == "Pendiente"


def test_revertir_agregar_ya_modificado_devuelve_false(escribir_json, cita_base):
    escribir_json(citas, [])
    citas.agregar_cita(cita_base)
    entrada = historial.deshacer()
    citas.eliminar_cita(citas.cargar_citas()[0])

    assert citas.revertir(entrada["instantanea"]) is False


def test_revertir_eliminar(escribir_json):
    escribir_json(citas, [_cita(paciente="Uno"), _cita(paciente="Dos")])
    citas.eliminar_cita(citas.cargar_citas()[0])
    entrada = historial.deshacer()

    assert citas.revertir(entrada["instantanea"]) is True
    assert [cita["paciente"] for cita in citas.cargar_citas()] == ["Uno", "Dos"]


def test_revertir_estado_restaura_la_fila(escribir_json):
    escribir_json(
        citas,
        [
            _cita(paciente="Atendida", estado="Realizada"),
            _cita(paciente="Promovida", estado="Pendiente"),
            _cita(paciente="Sigue esperando", estado=esperas.ESTADO_ESPERA, posicion=1),
        ],
    )
    instantanea = {
        "tipo": "estado",
        "entidad": "cita",
        "posicion": 0,
        "estado_anterior": "Pendiente",
        "promocion": {
            "posicion": 1,
            "estado_anterior": esperas.ESTADO_ESPERA,
            "posicion_espera": 1,
        },
        "fila_antes": [
            {"posicion": 1, "posicion_espera": 1},
            {"posicion": 2, "posicion_espera": 2},
        ],
    }

    assert citas.revertir(instantanea) is True

    registros = citas.cargar_citas()
    assert registros[0]["estado"] == "Pendiente"
    assert registros[1]["estado"] == esperas.ESTADO_ESPERA
    assert registros[1]["posicion_espera"] == 1
    assert registros[2]["posicion_espera"] == 2


def test_revertir_con_posicion_invalida_o_tipo_desconocido(escribir_json):
    escribir_json(citas, [_cita()])

    assert citas.revertir({"tipo": "estado", "posicion": -1}) is False
    assert citas.revertir({"tipo": "estado", "posicion": 9}) is False
    assert citas.revertir({"tipo": "otro", "posicion": 0}) is False
