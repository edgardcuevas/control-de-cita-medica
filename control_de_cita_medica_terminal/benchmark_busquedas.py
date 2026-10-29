"""Comparación de tiempos de búsqueda de MediCitas.

Ejecutar desde esta carpeta:

    python benchmark_busquedas.py

No forma parte de la suite de pytest (vive fuera de ``tests/``).
"""
import time

import busquedas


def benchmark(n=5000):
    """Compara el costo de localizar el último registro de una lista grande."""
    registros = [{"documento": f"DOC-{i:06d}"} for i in range(n)]
    objetivo = f"DOC-{n - 1:06d}"

    inicio = time.perf_counter()
    secuencial = busquedas.busqueda_secuencial(
        registros,
        lambda r: busquedas.normalizar(r["documento"])
        == busquedas.normalizar(objetivo),
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
    busquedas.hash_buscar(tabla, objetivo)
    tiempo_hash = (time.perf_counter() - inicio) * 1000

    print("\nComparación con", n, "registros (buscar el último):")
    print(
        f"  Secuencial   {secuencial['comparaciones']:>6} comparaciones  "
        f"{tiempo_secuencial:8.3f} ms"
    )
    print(
        f"  Binaria      {comparaciones_binaria:>6} comparaciones  "
        f"{tiempo_binaria:8.3f} ms  (índice: {tiempo_indice:.3f} ms)"
    )
    print(
        f"  Hash         {1:>6} comparaciones  "
        f"{tiempo_hash:8.3f} ms  (construcción: {tiempo_hash_construccion:.3f} ms)"
    )


if __name__ == "__main__":
    benchmark()
