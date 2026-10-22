
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


class ResultadoBusqueda:


    __slots__ = ("elementos", "algoritmo", "comparaciones")

    def __init__(self, elementos=None, algoritmo="Listado", comparaciones=0):
        self.elementos = list(elementos or [])
        self.algoritmo = algoritmo
        self.comparaciones = comparaciones

    def __len__(self):
        return len(self.elementos)

    def __iter__(self):
        return iter(self.elementos)

    def __getitem__(self, indice):
        return self.elementos[indice]

    def __bool__(self):
        return bool(self.elementos)

    def __repr__(self):
        return (
            f"ResultadoBusqueda({len(self.elementos)} elementos, "
            f"{self.algoritmo!r}, {self.comparaciones} comparaciones)"
        )



def busqueda_secuencial(registros, criterio):

    encontrados = []
    comparaciones = 0
    for registro in registros:
        comparaciones += 1
        if criterio(registro):
            encontrados.append(registro)
    return ResultadoBusqueda(encontrados, "Secuencial", comparaciones)


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


class TablaHash:


    def __init__(self, capacidad=17):
        self._capacidad = self._siguiente_primo(max(3, int(capacidad)))
        self._cubetas = [[] for _ in range(self._capacidad)]
        self._tamano = 0
        self.colisiones = 0

    @staticmethod
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

    @classmethod
    def _siguiente_primo(cls, numero):
        while not cls._es_primo(numero):
            numero += 1
        return numero

    def _hash_normalizada(self, clave_normalizada):
        valor = 5381
        for caracter in clave_normalizada:
            valor = ((valor * 33) + ord(caracter)) & 0xFFFFFFFF
        return valor % self._capacidad

    def _verificar_carga(self):
        if self._tamano > self._capacidad * 0.75:
            self._rehash()

    def _rehash(self):
        cubetas_anteriores = self._cubetas
        self._capacidad = self._siguiente_primo(self._capacidad * 2 + 1)
        self._cubetas = [[] for _ in range(self._capacidad)]
        self._tamano = 0
        self.colisiones = 0
        for cubeta in cubetas_anteriores:
            for clave, valor in cubeta:
                posicion = self._hash_normalizada(clave)
                if self._cubetas[posicion]:
                    self.colisiones += 1
                self._cubetas[posicion].append((clave, valor))
                self._tamano += 1

    def insertar(self, clave, valor):
        clave_normalizada = _texto_clave(clave)
        posicion = self._hash_normalizada(clave_normalizada)
        cubeta = self._cubetas[posicion]
        for i, (existente, _) in enumerate(cubeta):
            if existente == clave_normalizada:
                cubeta[i] = (clave_normalizada, valor)
                return False
        if cubeta:
            self.colisiones += 1
        cubeta.append((clave_normalizada, valor))
        self._tamano += 1
        self._verificar_carga()
        return True

    def insertar_si_ausente(self, clave, valor):
        clave_normalizada = _texto_clave(clave)
        posicion = self._hash_normalizada(clave_normalizada)
        cubeta = self._cubetas[posicion]
        for existente, _ in cubeta:
            if existente == clave_normalizada:
                return False
        if cubeta:
            self.colisiones += 1
        cubeta.append((clave_normalizada, valor))
        self._tamano += 1
        self._verificar_carga()
        return True

    def agregar(self, clave, valor):
        clave_normalizada = _texto_clave(clave)
        if not clave_normalizada:
            return False
        posicion = self._hash_normalizada(clave_normalizada)
        cubeta = self._cubetas[posicion]
        if cubeta:
            self.colisiones += 1
        cubeta.append((clave_normalizada, valor))
        self._tamano += 1
        self._verificar_carga()
        return True

    def buscar(self, clave):
        clave_normalizada = _texto_clave(clave)
        posicion = self._hash_normalizada(clave_normalizada)
        for existente, valor in self._cubetas[posicion]:
            if existente == clave_normalizada:
                return valor
        return None

    def buscar_todos(self, clave):
        clave_normalizada = _texto_clave(clave)
        posicion = self._hash_normalizada(clave_normalizada)
        return [
            valor for existente, valor in self._cubetas[posicion]
            if existente == clave_normalizada
        ]

    def contiene(self, clave):
        return self.buscar(clave) is not None

    def tamano(self):
        return self._tamano

    def capacidad(self):
        return self._capacidad

    def factor_carga(self):
        return self._tamano / self._capacidad

    def __len__(self):
        return self._tamano

    def __repr__(self):
        return (
            f"TablaHash(tamano={self._tamano}, capacidad={self._capacidad}, "
            f"colisiones={self.colisiones})"
        )



def construir_hash(registros, campo, capacidad=None):

    capacidad = capacidad or max(17, len(registros) * 2 + 1)
    tabla = TablaHash(capacidad)
    for indice, registro in enumerate(registros):
        clave = _valor_campo(registro, campo)
        if not _texto_clave(clave):
            continue
        tabla.insertar_si_ausente(clave, (registro, indice))
    return tabla


def construir_hash_multiple(registros, campo, capacidad=None):

    capacidad = capacidad or max(17, len(registros) * 2 + 1)
    tabla = TablaHash(capacidad)
    for indice, registro in enumerate(registros):
        clave = _valor_campo(registro, campo)
        if not _texto_clave(clave):
            continue
        tabla.agregar(clave, (registro, indice))
    return tabla
