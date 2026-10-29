"""Estructuras de datos implementadas con listas y funciones.

    Pila (LIFO): pila_crear, pila_apilar, pila_desapilar, pila_cima
    Cola (FIFO): cola_crear, cola_encolar, cola_desencolar, cola_primero
    Cola de prioridad: monticulo_crear, monticulo_encolar, monticulo_desencolar
"""


def pila_crear():
    return []


def pila_apilar(pila, elemento):
    pila.append(elemento)


def pila_desapilar(pila):
    if not pila:
        raise IndexError("No se puede desapilar de una pila vacia.")
    return pila.pop()


def pila_cima(pila):
    if not pila:
        raise IndexError("No se puede leer la cima de una pila vacia.")
    return pila[-1]


def pila_esta_vacia(pila):
    return not pila


def pila_tamano(pila):
    return len(pila)


def pila_volcar(pila):
    return list(pila)


def cola_crear():
    return []


def cola_encolar(cola, elemento):
    cola.append(elemento)


def cola_desencolar(cola):
    if not cola:
        raise IndexError("No se puede desencolar de una cola vacia.")
    return cola.pop(0)


def cola_primero(cola):
    if not cola:
        raise IndexError("No se puede leer el primero de una cola vacia.")
    return cola[0]


def cola_esta_vacia(cola):
    return not cola


def cola_tamano(cola):
    return len(cola)


def monticulo_crear():
    return []


def monticulo_encolar(monticulo, clave, valor):
    monticulo.append((clave, valor))
    hijo = len(monticulo) - 1
    while hijo > 0:
        padre = (hijo - 1) // 2
        if monticulo[padre][0] <= monticulo[hijo][0]:
            break
        monticulo[padre], monticulo[hijo] = monticulo[hijo], monticulo[padre]
        hijo = padre


def monticulo_desencolar(monticulo):
    if not monticulo:
        raise IndexError("No se puede desencolar de un monticulo vacio.")
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


def monticulo_cima(monticulo):
    if not monticulo:
        raise IndexError("No se puede leer la cima de un monticulo vacio.")
    return monticulo[0][1]


def monticulo_esta_vacio(monticulo):
    return not monticulo


def monticulo_tamano(monticulo):
    return len(monticulo)
