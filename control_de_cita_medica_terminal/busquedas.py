
import unicodedata
from datetime import datetime


def normalizar(texto):

    texto = str(texto)
    descompuesto = unicodedata.normalize("NFKD", texto)
    sin_tildes = "".join(
        caracter for caracter in descompuesto
        if not unicodedata.combining(caracter)
    )
    return " ".join(sin_tildes.casefold().split())


def _texto_clave(valor):

    if isinstance(valor, (tuple, list)):
        return "|".join(normalizar(parte) for parte in valor)
    return normalizar(valor)


def _valor_campo(registro, campo):

    if callable(campo):
        return campo(registro)
    return registro.get(campo, "")


def parece_documento(texto):
    valor = str(texto).strip()
    return any(caracter.isdigit() for caracter in valor) or "-" in valor


def clave_fecha(texto):
    try:
        return datetime.strptime(str(texto).strip(), "%d/%m/%Y").strftime("%Y-%m-%d")
    except (TypeError, ValueError):
        return "9999-99-99"


def crear_resultado(elementos=None, algoritmo="Listado", comparaciones=0):
    """Construye un resultado de búsqueda con un diccionario simple."""
    return {
        "elementos": list(elementos or []),
        "algoritmo": algoritmo,
        "comparaciones": comparaciones,
    }



def busqueda_secuencial(registros, criterio):

    encontrados = []
    comparaciones = 0
    for registro in registros:
        comparaciones += 1
        if criterio(registro):
            encontrados.append(registro)
    return crear_resultado(encontrados, "Secuencial", comparaciones)


# ---------------------------------------------------------------------------
# Búsqueda binaria
# ---------------------------------------------------------------------------

def indice_ordenado(registros, campo):

    pares = []
    for indice, registro in enumerate(registros):
        clave = _texto_clave(_valor_campo(registro, campo))
        pares.append((clave, indice))
    pares.sort(key=lambda par: par[0])
    return pares


def busqueda_binaria(indice, objetivo):

    objetivo = _texto_clave(objetivo)
    izquierda = 0
    derecha = len(indice) - 1
    comparaciones = 0

    while izquierda <= derecha:
        medio = (izquierda + derecha) // 2
        comparaciones += 1
        clave, posicion = indice[medio]
        if clave == objetivo:
            while medio > 0 and indice[medio - 1][0] == objetivo:
                medio -= 1
            return indice[medio][1], comparaciones
        if clave < objetivo:
            izquierda = medio + 1
        else:
            derecha = medio - 1

    return -1, comparaciones


def _limite_inferior(indice, objetivo):
    izquierda = 0
    derecha = len(indice)
    comparaciones = 0
    while izquierda < derecha:
        medio = (izquierda + derecha) // 2
        comparaciones += 1
        if indice[medio][0] < objetivo:
            izquierda = medio + 1
        else:
            derecha = medio
    return izquierda, comparaciones


def _limite_superior(indice, objetivo):
    izquierda = 0
    derecha = len(indice)
    comparaciones = 0
    while izquierda < derecha:
        medio = (izquierda + derecha) // 2
        comparaciones += 1
        if indice[medio][0] <= objetivo:
            izquierda = medio + 1
        else:
            derecha = medio
    return izquierda, comparaciones


def busqueda_por_rango(indice, desde, hasta):

    desde = _texto_clave(desde)
    hasta = _texto_clave(hasta)
    inicio, comparaciones_inicio = _limite_inferior(indice, desde)
    fin, comparaciones_fin = _limite_superior(indice, hasta)
    posiciones = [indice[i][1] for i in range(inicio, fin)]
    return posiciones, comparaciones_inicio + comparaciones_fin


def busqueda_por_prefijo(indice, prefijo):

    prefijo = _texto_clave(prefijo)
    inicio, comparaciones = _limite_inferior(indice, prefijo)
    posiciones = []
    i = inicio
    while i < len(indice) and indice[i][0].startswith(prefijo):
        posiciones.append(indice[i][1])
        comparaciones += 1
        i += 1
    return posiciones, comparaciones


def _es_primo(numero):
    if numero < 2:
        return False
    if numero % 2 == 0:
        return numero == 2
    divisor = 3
    while divisor * divisor <= numero:
        if numero % divisor == 0:
            return False
        divisor += 2
    return True


def _siguiente_primo(numero):
    while not _es_primo(numero):
        numero += 1
    return numero


def _hash_normalizada(tabla, clave_normalizada):
    valor = 5381
    for caracter in clave_normalizada:
        valor = ((valor * 33) + ord(caracter)) & 0xFFFFFFFF
    return valor % tabla["capacidad"]


def crear_tabla_hash(capacidad=17):
    capacidad = _siguiente_primo(max(3, int(capacidad)))
    return {
        "capacidad": capacidad,
        "cubetas": [[] for _ in range(capacidad)],
        "tamano": 0,
        "colisiones": 0,
    }


def _rehash(tabla):
    anteriores = tabla["cubetas"]
    tabla["capacidad"] = _siguiente_primo(tabla["capacidad"] * 2 + 1)
    tabla["cubetas"] = [[] for _ in range(tabla["capacidad"])]
    tabla["tamano"] = 0
    tabla["colisiones"] = 0
    for cubeta in anteriores:
        for clave, valor in cubeta:
            posicion = _hash_normalizada(tabla, clave)
            if tabla["cubetas"][posicion]:
                tabla["colisiones"] += 1
            tabla["cubetas"][posicion].append((clave, valor))
            tabla["tamano"] += 1


def _insertar(tabla, clave, valor, permitir_repetidos=False, solo_ausente=False):
    clave_normalizada = _texto_clave(clave)
    posicion = _hash_normalizada(tabla, clave_normalizada)
    cubeta = tabla["cubetas"][posicion]
    for indice, (existente, _) in enumerate(cubeta):
        if existente == clave_normalizada:
            if permitir_repetidos:
                continue
            if solo_ausente:
                return False
            cubeta[indice] = (clave_normalizada, valor)
            return False
    if not clave_normalizada and permitir_repetidos:
        return False
    if cubeta:
        tabla["colisiones"] += 1
    cubeta.append((clave_normalizada, valor))
    tabla["tamano"] += 1
    if tabla["tamano"] > tabla["capacidad"] * 0.75:
        _rehash(tabla)
    return True


def hash_insertar(tabla, clave, valor):
    return _insertar(tabla, clave, valor)


def hash_insertar_si_ausente(tabla, clave, valor):
    return _insertar(tabla, clave, valor, solo_ausente=True)


def hash_agregar(tabla, clave, valor):
    return _insertar(tabla, clave, valor, permitir_repetidos=True)


def hash_buscar(tabla, clave):
    clave_normalizada = _texto_clave(clave)
    posicion = _hash_normalizada(tabla, clave_normalizada)
    for existente, valor in tabla["cubetas"][posicion]:
        if existente == clave_normalizada:
            return valor
    return None


def hash_buscar_todos(tabla, clave):
    clave_normalizada = _texto_clave(clave)
    posicion = _hash_normalizada(tabla, clave_normalizada)
    return [
        valor for existente, valor in tabla["cubetas"][posicion]
        if existente == clave_normalizada
    ]


def construir_hash(registros, campo, capacidad=None):
    capacidad = capacidad or max(17, len(registros) * 2 + 1)
    tabla = crear_tabla_hash(capacidad)
    for indice, registro in enumerate(registros):
        clave = _valor_campo(registro, campo)
        if _texto_clave(clave):
            hash_insertar_si_ausente(tabla, clave, (registro, indice))
    return tabla


def construir_hash_multiple(registros, campo, capacidad=None):
    capacidad = capacidad or max(17, len(registros) * 2 + 1)
    tabla = crear_tabla_hash(capacidad)
    for indice, registro in enumerate(registros):
        clave = _valor_campo(registro, campo)
        if _texto_clave(clave):
            hash_agregar(tabla, clave, (registro, indice))
    return tabla
