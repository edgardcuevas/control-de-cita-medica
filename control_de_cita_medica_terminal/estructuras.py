"""Estructuras de datos lineales usadas por MediCitas.

Implementadas a mano (sin ``collections.deque`` ni ``heapq``) para que el
comportamiento LIFO / FIFO sea explicito y auditable.

    Pila          -> apilar / desapilar / cima              (LIFO)
    Cola          -> encolar / desencolar / primero         (FIFO)
    ColaPrioridad -> encolar(clave, valor) / desencolar      (montículo mínimo)
"""

class Pila:
    """Pila (LIFO). El último elemento en entrar es el primero en salir."""

    def __init__(self):
        self._elementos = []

    def apilar(self, elemento):
        """Agrega un elemento en la cima de la pila."""
        self._elementos.append(elemento)

    def desapilar(self):
        """Quita y devuelve la cima. Lanza IndexError si la pila esta vacia."""
        if not self._elementos:
            raise IndexError("No se puede desapilar de una pila vacia.")
        return self._elementos.pop()

    def cima(self):
        """Devuelve la cima sin quitarla. Lanza IndexError si esta vacia."""
        if not self._elementos:
            raise IndexError("No se puede leer la cima de una pila vacia.")
        return self._elementos[-1]

    def esta_vacia(self):
        return not self._elementos

    def tamano(self):
        return len(self._elementos)

    def volcar(self):
        """Devuelve una copia de los elementos, del fondo a la cima."""
        return list(self._elementos)

    def __len__(self):
        return len(self._elementos)

    def __repr__(self):
        return f"Pila({self._elementos!r})"


class Cola:
    """Cola (FIFO). El primer elemento en entrar es el primero en salir.

    ``encolar`` es O(1): en lugar de mover todos los elementos con
    ``list.pop(0)``, se avanza un indice de cabeza y se compacta la lista
    solo cuando el desperdicio supera la mitad del almacen.
    """

    def __init__(self):
        self._elementos = []
        self._cabeza = 0

    def encolar(self, elemento):
        """Agrega un elemento al final de la cola."""
        self._elementos.append(elemento)

    def desencolar(self):
        """Quita y devuelve el primero. Lanza IndexError si esta vacia."""
        if self._cabeza >= len(self._elementos):
            raise IndexError("No se puede desencolar de una cola vacia.")
        elemento = self._elementos[self._cabeza]
        self._elementos[self._cabeza] = None
        self._cabeza += 1
        if self._cabeza >= len(self._elementos):
            self._elementos.clear()
            self._cabeza = 0
        return elemento

    def primero(self):
        """Devuelve el primero sin quitarlo. Lanza IndexError si esta vacia."""
        if self._cabeza >= len(self._elementos):
            raise IndexError("No se puede leer el primero de una cola vacia.")
        return self._elementos[self._cabeza]

    def esta_vacia(self):
        return self._cabeza >= len(self._elementos)

    def tamano(self):
        return len(self._elementos) - self._cabeza

    def __len__(self):
        return self.tamano()

    def __repr__(self):
        return f"Cola({self._elementos[self._cabeza:]!r})"


class ColaPrioridad:
    """Cola de prioridad: siempre sale primero el elemento de menor clave.

    Montículo binario (min-heap) implementado manualmente. La clave debe ser
    comparable con ``<``; en MediCitas se usan tuplas ``(fecha, hora)``.
    """

    def __init__(self):
        self._monticulo = []

    def encolar(self, clave, valor):
        """Inserta un valor con su clave y reordena hacia arriba."""
        monticulo = self._monticulo
        monticulo.append((clave, valor))
        hijo = len(monticulo) - 1
        while hijo > 0:
            padre = (hijo - 1) // 2
            if monticulo[padre][0] <= monticulo[hijo][0]:
                break
            monticulo[padre], monticulo[hijo] = monticulo[hijo], monticulo[padre]
            hijo = padre

    def desencolar(self):
        """Quita y devuelve el valor de menor clave. Lanza IndexError si esta vacia."""
        monticulo = self._monticulo
        if not monticulo:
            raise IndexError("No se puede desencolar de una cola de prioridad vacia.")
        _, valor = monticulo[0]
        ultimo = monticulo.pop()
        if monticulo:
            monticulo[0] = ultimo
            padre = 0
            total = len(monticulo)
            while True:
                hijo_izq = 2 * padre + 1
                hijo_der = 2 * padre + 2
                menor = padre
                if hijo_izq < total and monticulo[hijo_izq][0] < monticulo[menor][0]:
                    menor = hijo_izq
                if hijo_der < total and monticulo[hijo_der][0] < monticulo[menor][0]:
                    menor = hijo_der
                if menor == padre:
                    break
                monticulo[padre], monticulo[menor] = monticulo[menor], monticulo[padre]
                padre = menor
        return valor

    def cima(self):
        """Devuelve el valor de menor clave sin quitarlo."""
        if not self._monticulo:
            raise IndexError("No se puede leer la cima de una cola de prioridad vacia.")
        return self._monticulo[0][1]

    def esta_vacia(self):
        return not self._monticulo

    def tamano(self):
        return len(self._monticulo)

    def __len__(self):
        return len(self._monticulo)

    def __repr__(self):
        return f"ColaPrioridad({[clave for clave, _ in self._monticulo]!r})"