"""Pruebas de los algoritmos de búsqueda de MediCitas.

Ejecutar desde esta carpeta:

    python pruebas_busquedas.py

No abre la interfaz ni modifica los archivos JSON: las funciones de dominio
reciben listas de prueba mediante el parámetro ``registros``.
"""
import random
import time

import busquedas
import citas
import medicos
import pacientes


PACIENTES = [
    {
        "documento": "085-110886-4432D",
        "nombre": "María Esperanza",
        "apellido": "Guerrero Mendez",
        "edad": 40,
        "sexo": "femenino",
        "telefono": "76751188",
        "correo": "maria@test.com",
        "tipo_sangre": "O-",
        "seguro_medico": "no tiene",
        "direccion": "San Juan",
        "fecha_nacimiento": "15/06/1986",
    },
    {
        "documento": "Juan",
        "nombre": "Juan Alfonso",
        "apellido": "Cortes",
        "edad": 20,
        "sexo": "masculino",
        "telefono": "67543211",
        "correo": "juan@test.com",
        "tipo_sangre": "O+",
        "seguro_medico": "no tiene",
        "direccion": "San Juan",
        "fecha_nacimiento": "11/03/1999",
    },
    {
        "documento": "112233445566",
        "nombre": "Carlos",
        "apellido": "Pérez",
        "edad": 35,
        "sexo": "masculino",
        "telefono": "70000000",
        "correo": "carlos@test.com",
        "tipo_sangre": "A+",
        "seguro_medico": "seguro privado",
        "direccion": "Centro",
        "fecha_nacimiento": "01/02/1991",
    },
    {
        "documento": "DOC-4",
        "nombre": "Juan",
        "apellido": "Ramos",
        "edad": 28,
        "sexo": "masculino",
        "telefono": "70000004",
        "correo": "juan.ramos@test.com",
        "tipo_sangre": "B+",
        "seguro_medico": "no tiene",
        "direccion": "Norte",
        "fecha_nacimiento": "05/05/1998",
    },
]

MEDICOS = [
    {
        "documento": "086-241112-876G",
        "nombre": "Ernesto",
        "apellido": "Gutierres",
        "telefono": "76543211",
        "correo": "ernesto@test.com",
        "modulo": "5",
        "especialidad": "diabetologo",
        "consultorio": "4",
        "horario": "6 am a 3 pm",
    },
    {
        "documento": "112233445566",
        "nombre": "Marlon",
        "apellido": "Surtiava",
        "telefono": "76751188",
        "correo": "marlon@test.com",
        "modulo": "modulo 3",
        "especialidad": "cirujano",
        "consultorio": "5",
        "horario": "3:00 a 18:00",
    },
]

CITAS = [
    {
        "paciente": "María Esperanza Guerrero Mendez",
        "documento_paciente": "085-110886-4432D",
        "medico": "Ernesto Gutierres",
        "especialidad": "diabetologo",
        "modulo": "5",
        "fecha": "22/09/2026",
        "hora": "10:00",
        "tipo": "presencial",
        "motivo": "consulta mensual",
        "observaciones": "ninguna",
        "estado": "Realizada",
    },
    {
        "paciente": "Juan Alfonso Cortes Cortes",
        "documento_paciente": "Juan",
        "medico": "Marlon Surtiava",
        "especialidad": "cirujano",
        "modulo": "modulo 3",
        "fecha": "09/12/2026",
        "hora": "03:00",
        "tipo": "presencial",
        "motivo": "revision",
        "observaciones": "ninguna",
        "estado": "Pendiente",
    },
    {
        "paciente": "María Esperanza Guerrero Mendez",
        "documento_paciente": "085-110886-4432D",
        "medico": "Ernesto Gutierres",
        "especialidad": "diabetologo",
        "modulo": "5",
        "fecha": "22/09/2026",
        "hora": "11:00",
        "tipo": "presencial",
        "motivo": "control",
        "observaciones": "ninguna",
        "estado": "En espera",
        "posicion_espera": 1,
    },
]


def test_normalizacion():
    assert busquedas.normalizar("  María   GÜERRERO ") == "maria guerrero"
    assert busquedas.normalizar("Pérez") == "perez"
    assert busquedas.normalizar("") == ""
    assert busquedas.normalizar(None) == "none"
    assert busquedas.parece_documento("085-110886-4432D") is True
    assert busquedas.parece_documento("112233445566") is True
    assert busquedas.parece_documento("Juan") is False


def test_busqueda_secuencial():
    registros = [{"numero": i} for i in range(100)]
    resultado = busquedas.busqueda_secuencial(
        registros, lambda registro: registro["numero"] % 2 == 0
    )
    assert len(resultado) == 50
    assert resultado.algoritmo == "Secuencial"
    assert resultado.comparaciones == 100
    assert all(registro["numero"] % 2 == 0 for registro in resultado)


def test_busqueda_binaria_aleatoria():
    for _ in range(200):
        valores = random.sample(range(10000), random.randint(0, 120))
        registros = [{"clave": str(valor)} for valor in valores]
        indice = busquedas.indice_ordenado(registros, "clave")
        for objetivo in random.sample(range(10000), 15):
            posicion, _ = busquedas.busqueda_binaria(indice, str(objetivo))
            esperado = next(
                (i for i, r in enumerate(registros) if r["clave"] == str(objetivo)),
                -1,
            )
            assert posicion == esperado, (objetivo, posicion, esperado)


def test_busqueda_binaria_duplicados():
    registros = [{"clave": "a"}, {"clave": "b"}, {"clave": "b"}, {"clave": "c"}]
    indice = busquedas.indice_ordenado(registros, "clave")
    posicion, _ = busquedas.busqueda_binaria(indice, "b")
    assert posicion == 1


def test_busqueda_por_rango():
    fechas = ["01/10/2026", "05/10/2026", "10/10/2026", "15/10/2026", "20/10/2026"]
    registros = [{"fecha": fecha} for fecha in fechas]
    indice = busquedas.indice_ordenado(
        registros, lambda r: busquedas.clave_fecha(r["fecha"])
    )
    posiciones, _ = busquedas.busqueda_por_rango(
        indice, "2026-10-05", "2026-10-15"
    )
    assert posiciones == [1, 2, 3]
    assert busquedas.busqueda_por_rango(indice, "2027-01-01", "2027-12-31")[0] == []


def test_busqueda_por_prefijo():
    registros = [{"k": "Ana"}, {"k": "Anabel"}, {"k": "Bruno"}, {"k": "ana"}]
    indice = busquedas.indice_ordenado(registros, "k")
    posiciones, _ = busquedas.busqueda_por_prefijo(indice, "ana")
    assert sorted(posiciones) == [0, 1, 3]


def test_tabla_hash():
    tabla = busquedas.TablaHash(capacidad=5)
    for i in range(200):
        assert tabla.insertar_si_ausente(f"clave-{i}", i)
    for i in range(200):
        assert tabla.buscar(f"clave-{i}") == i
    assert tabla.buscar("no-existe") is None
    assert len(tabla) == 200
    assert tabla.capacidad() > 5

    # Reemplazo y valores múltiples.
    tabla.insertar("repetida", 1)
    tabla.insertar("repetida", 2)
    assert tabla.buscar("repetida") == 2
    tabla.agregar("varias", "a")
    tabla.agregar("varias", "b")
    assert tabla.buscar_todos("varias") == ["a", "b"]

    # Claves compuestas (espacio de agenda).
    tabla.agregar(("Dr. Pérez", "22/09/2026", "10:00"), "cita-1")
    tabla.agregar(("dr. perez", "22/09/2026", "10:00"), "cita-2")
    assert tabla.buscar_todos(("DR. PEREZ", "22/09/2026", "10:00")) == [
        "cita-1", "cita-2"
    ]


def test_busquedas_pacientes():
    resultado = pacientes.buscar_pacientes("maria", registros=PACIENTES)
    assert len(resultado) == 1
    assert resultado.algoritmo == "Secuencial"

    resultado = pacientes.buscar_pacientes("MARIA GUERRERO", registros=PACIENTES)
    assert len(resultado) == 1

    resultado = pacientes.buscar_pacientes("perez", registros=PACIENTES)
    assert len(resultado) == 1
    assert resultado[0]["documento"] == "112233445566"

    resultado = pacientes.buscar_pacientes("085-110886-4432D", registros=PACIENTES)
    assert len(resultado) == 1
    assert resultado.algoritmo == "Hash (documento)"

    # "juan" no debe confundirse con el documento llamado "Juan": al no
    # parecer un documento, se usa la búsqueda secuencial y aparecen los dos.
    resultado = pacientes.buscar_pacientes("juan", registros=PACIENTES)
    assert len(resultado) >= 2
    assert resultado.algoritmo == "Secuencial"
    nombres = {p["nombre"] for p in resultado}
    assert "Juan Alfonso" in nombres and "Juan" in nombres

    resultado = pacientes.buscar_pacientes("no existe", registros=PACIENTES)
    assert len(resultado) == 0


def test_busquedas_medicos():
    resultado = medicos.buscar_medicos("diabetologo", registros=MEDICOS)
    assert len(resultado) == 1
    assert resultado.algoritmo == "Secuencial"

    resultado = medicos.buscar_medicos("cirujano", registros=MEDICOS)
    assert len(resultado) == 1

    resultado = medicos.buscar_medicos("086-241112-876G", registros=MEDICOS)
    assert len(resultado) == 1
    assert resultado.algoritmo == "Hash (documento)"

    resultado = medicos.buscar_medicos("modulo 3", registros=MEDICOS)
    assert len(resultado) == 1


def test_busquedas_citas():
    resultado = citas.buscar_citas("22/09/2026", registros=CITAS)
    assert len(resultado) == 2
    assert resultado.algoritmo == "Binaria (fecha)"

    resultado = citas.buscar_citas("maria", registros=CITAS)
    assert len(resultado) == 2
    assert resultado.algoritmo == "Secuencial"

    resultado = citas.buscar_citas("maria", "Pendiente", registros=CITAS)
    assert len(resultado) == 0

    resultado = citas.buscar_citas("revision", registros=CITAS)
    assert len(resultado) == 1
    assert resultado[0]["paciente"].startswith("Juan")

    resultado = citas.buscar_por_fecha("01/09/2026", "30/09/2026", registros=CITAS)
    assert len(resultado) == 2
    assert resultado.algoritmo == "Binaria (fecha)"

    resultado = citas.buscar_por_espacio(
        "ernesto gutierres", "22/09/2026", "10:00", registros=CITAS
    )
    assert len(resultado) == 1
    assert resultado.algoritmo == "Hash (espacio)"

    resultado = citas.buscar_por_espacio(
        "Ernesto Gutierres", "22/09/2026", "11:00", registros=CITAS
    )
    assert len(resultado) == 1
    assert resultado[0]["estado"] == "En espera"


def test_indice_usuarios():
    usuarios = [{"email": "Admin@Clinica.com"}, {"email": "otro@test.com"}]
    tabla = busquedas.construir_hash(usuarios, "email")
    assert tabla.buscar("admin@clinica.com")[0]["email"] == "Admin@Clinica.com"
    assert tabla.buscar("ADMIN@CLINICA.COM") is not None
    assert tabla.buscar("no@existe.com") is None


def benchmark():
    """Compara el costo de localizar el último registro de una lista grande."""
    n = 5000
    registros = [{"documento": f"DOC-{i:06d}"} for i in range(n)]
    objetivo = f"DOC-{n - 1:06d}"

    inicio = time.perf_counter()
    secuencial = busquedas.busqueda_secuencial(
        registros,
        lambda r: busquedas.normalizar(r["documento"]) == busquedas.normalizar(objetivo),
    )
    tiempo_secuencial = (time.perf_counter() - inicio) * 1000

    inicio = time.perf_counter()
    indice = busquedas.indice_ordenado(registros, "documento")
    tiempo_indice = (time.perf_counter() - inicio) * 1000
    inicio = time.perf_counter()
    _, comparaciones_binaria = busquedas.busqueda_binaria(indice, objetivo)
    tiempo_binaria = (time.perf_counter() - inicio) * 1000

    inicio = time.perf_counter()
    tabla = busquedas.construir_hash(registros, "documento")
    tiempo_hash_construccion = (time.perf_counter() - inicio) * 1000
    inicio = time.perf_counter()
    tabla.buscar(objetivo)
    tiempo_hash = (time.perf_counter() - inicio) * 1000

    print("\nComparación con", n, "registros (buscar el último):")
    print(f"  Secuencial   {secuencial.comparaciones:>6} comparaciones  "
          f"{tiempo_secuencial:8.3f} ms")
    print(f"  Binaria      {comparaciones_binaria:>6} comparaciones  "
          f"{tiempo_binaria:8.3f} ms  (índice: {tiempo_indice:.3f} ms)")
    print(f"  Hash         {1:>6} comparaciones  "
          f"{tiempo_hash:8.3f} ms  (construcción: {tiempo_hash_construccion:.3f} ms)")


def main():
    pruebas = [
        test_normalizacion,
        test_busqueda_secuencial,
        test_busqueda_binaria_aleatoria,
        test_busqueda_binaria_duplicados,
        test_busqueda_por_rango,
        test_busqueda_por_prefijo,
        test_tabla_hash,
        test_busquedas_pacientes,
        test_busquedas_medicos,
        test_busquedas_citas,
        test_indice_usuarios,
    ]
    for prueba in pruebas:
        prueba()
        print(f"OK  {prueba.__name__}")
    benchmark()
    print("\nTodas las pruebas pasaron.")


if __name__ == "__main__":
    main()
