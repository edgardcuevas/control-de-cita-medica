# Documentación técnica — MediCitas Terminal

**Ruta documentada:** `control_de_cita_medica_terminal/`
**Tipo de aplicación:** sistema de gestión de citas médicas por consola
**Punto de entrada:** `main.py` (o `INICIAR.bat` en Windows)
**Interfaz:** menús numerados en terminal, sin ventanas ni interfaz gráfica
**Dependencias externas:** ninguna

---

## 1. Resumen general

`control_de_cita_medica_terminal` es el sistema MediCitas: una aplicación de
gestión de citas médicas que funciona **íntegramente en la terminal**. Toda la
interacción se realiza con menús numerados, texto y tablas alineadas; no hay
ventanas ni componentes gráficos.

La aplicación permite:

- iniciar sesión y crear cuentas de usuario;
- registrar, buscar, consultar y eliminar pacientes;
- registrar, buscar, consultar y eliminar médicos;
- agendar citas médicas;
- filtrar y buscar citas por estado, texto libre o fecha;
- marcar citas como realizadas;
- cancelar citas;
- gestionar una fila de espera cuando un espacio de agenda está ocupado;
- deshacer la última acción;
- conservar una bitácora de las operaciones.

La arquitectura es deliberadamente sencilla: un único archivo de presentación
(`main.py`) y varios módulos de dominio que no saben nada de la interfaz. Esa
separación permite que la lógica de negocio se pueda entender, probar y
modificar sin tocar la presentación.

### 1.1. Alcance del proyecto

El proyecto es **autocontenido**: todo lo que necesita para funcionar está
dentro de esta carpeta.

- tiene sus propios archivos JSON en `archivos/`;
- tiene su propio historial de deshacer;
- tiene su propia bitácora;
- no importa módulos de otras carpetas;
- no requiere ningún otro proyecto para ejecutarse.

Los datos viven en `archivos/` y se pueden respaldar copiando esa carpeta.

---

## 2. Tecnologías utilizadas

| Tecnología | Uso |
| --- | --- |
| **Python 3.10+** | Lenguaje de la aplicación. Probado con Python 3.14. |
| **Biblioteca estándar** | Todo el sistema funciona sin `pip install`. |
| **JSON** | Persistencia de pacientes, médicos, citas y usuarios. |
| **ANSI escape sequences** | Colores y limpieza de pantalla en la terminal. |
| **UTF-8** | Acentos, símbolos de tabla y compatibilidad en Windows. |
| **PBKDF2-HMAC-SHA256** | Hash de contraseñas con sal aleatoria. |
| **Batch de Windows** | `INICIAR.bat` para arrancar con doble clic. |

Módulos de la biblioteca estándar usados:

- `json`, `os`, `tempfile` — lectura/escritura de datos y archivos temporales.
- `datetime` — validación y orden de fechas y horas.
- `unicodedata` — normalización de texto para búsquedas.
- `getpass` — entrada de contraseña sin mostrarla.
- `hashlib` y `os.urandom` — derivación de contraseñas y generación de sal.
- `shutil`, `sys` — ancho de terminal, entrada/salida y configuración UTF-8.
- `ctypes` — activación de secuencias ANSI en consolas Windows.
- `random`, `time` — pruebas y benchmark (`pruebas_busquedas.py`).

**No se usa:** ninguna biblioteca o framework gráfico, Flask, Django, Rich,
Textual, Questionary, Colorama, `pip`, bases de datos externas ni servicios en
la nube.

---

## 3. Árbol de carpetas y división del proyecto

```text
control_de_cita_medica_terminal/
├── main.py                  # Presentación: menús, pantallas, tablas y flujo
├── pacientes.py             # Dominio: pacientes y su persistencia
├── medicos.py               # Dominio: médicos y su persistencia
├── citas.py                 # Dominio: citas, estados y fila de espera
├── usuarios.py              # Dominio: cuentas, login y hash de contraseñas
├── esperas.py               # Reglas puras de la fila de espera
├── historial.py             # Pila de deshacer y cola de bitácora
├── estructuras.py           # Pila, Cola y ColaPrioridad implementadas a mano
├── busquedas.py             # Búsqueda secuencial, binaria y tabla hash
├── almacenamiento.py        # Lectura/escritura atómica de JSON
├── pruebas_busquedas.py     # Pruebas y benchmark de los algoritmos
├── INICIAR.bat              # Lanzador de Windows con UTF-8
├── README.md                # Guía rápida de uso
└── archivos/
    ├── pacientes.json       # Registros de pacientes
    ├── medicos.json         # Registros de médicos
    ├── citas.json           # Citas y estado de la fila
    ├── usuarios.json        # Correos, sales y hashes de contraseñas
    ├── historial.json       # Pila persistente de acciones para deshacer
    └── bitacora.txt         # Registro append-only (se genera al usar la app)
```

> `__pycache__/` puede aparecer automáticamente: son archivos compilados que
> genera Python y no forman parte del código fuente. Se pueden borrar sin
> afectar el funcionamiento.

### 3.1. División por responsabilidades

| Capa | Archivos | Responsabilidad |
| --- | --- | --- |
| **Entrada / presentación** | `main.py`, `INICIAR.bat` | Menús, lectura de datos, tablas, colores, mensajes y navegación. |
| **Dominio** | `pacientes.py`, `medicos.py`, `citas.py`, `usuarios.py`, `esperas.py`, `historial.py` | Reglas del negocio y operaciones sobre los registros. |
| **Infraestructura** | `busquedas.py`, `estructuras.py`, `almacenamiento.py` | Algoritmos, estructuras de datos y acceso a disco. |
| **Datos** | `archivos/*.json`, `archivos/bitacora.txt` | Persistencia concreta. |
| **Pruebas** | `pruebas_busquedas.py` | Verificación de los algoritmos. |
| **Documentación** | `README.md` y este archivo (en la raíz) | Uso y explicación técnica. |

La dirección de dependencias es siempre desde la presentación hacia el dominio
y desde el dominio hacia la infraestructura. Ningún módulo de dominio importa
`main.py`, por lo que la lógica se puede reutilizar en otra interfaz.

---

## 4. Arquitectura y conexiones entre módulos

### 4.1. Diagrama general

```text
                         ┌──────────────────┐
                         │   INICIAR.bat    │
                         └────────┬─────────┘
                                  │ inicia
                         ┌────────▼─────────┐
                         │     main.py      │
                         │  (presentación)  │
                         └────────┬─────────┘
             ┌──────────────┬─────┼──────────────┬──────────────┐
             ▼              ▼     ▼              ▼              ▼
       pacientes.py   medicos.py  citas.py   usuarios.py   historial.py
             │              │     │              │              │
             └──────┬───────┴─────┴──────┬───────┘              │
                    ▼                    ▼                      ▼
              busquedas.py          esperas.py ─────────► estructuras.py
                    │                    │                      ▲
                    └──────────┬─────────┘                      │
                               ▼                                │
                       almacenamiento.py                        │
                               │                                │
                               ▼                                │
                      archivos/*.json                    historial.py
```

### 4.2. Dependencias directas

| Módulo | Importa a |
| --- | --- |
| `main.py` | `pacientes`, `medicos`, `citas`, `usuarios`, `historial`, `esperas`, `estructuras` |
| `pacientes.py` | `busquedas`, `historial`, `almacenamiento`; `citas` de forma perezosa |
| `medicos.py` | `busquedas`, `historial`, `almacenamiento`; `citas` de forma perezosa |
| `citas.py` | `busquedas`, `historial`, `esperas`, `almacenamiento` |
| `usuarios.py` | `busquedas`, `almacenamiento` |
| `historial.py` | `estructuras` |
| `esperas.py` | `estructuras` |
| `busquedas.py` | Biblioteca estándar (`unicodedata`, `datetime`) |
| `estructuras.py` | Nada (implementación pura) |
| `almacenamiento.py` | Biblioteca estándar (`json`, `os`, `tempfile`) |
| `pruebas_busquedas.py` | `busquedas`, `citas`, `medicos`, `pacientes` |

### 4.3. Por qué `citas` se importa de forma perezosa

`pacientes.py` y `medicos.py` necesitan contar citas asociadas antes de
eliminar un registro. Si importaran `citas` en la cabecera del archivo, se
produciría un ciclo:

```text
pacientes → citas → ... → pacientes
```

Para evitarlo, dentro de `eliminar_paciente()` y `eliminar_medico()` se hace:

```python
from citas import contar_citas_paciente  # o contar_citas_medico
```

La importación se resuelve en tiempo de ejecución, cuando el módulo ya está
cargado. Es una decisión consciente para mantener los módulos independientes.

---

## 5. Flujo de ejecución

1. `INICIAR.bat` (o el usuario) ejecuta `python main.py`.
2. `main.py` configura UTF-8, activa ANSI en Windows y crea una instancia de `App`.
3. `App.ejecutar()` entra en un bucle:
   - limpia la pantalla;
   - dibuja la cabecera;
   - muestra el aviso pendiente, si lo hay;
   - ejecuta el método `pantalla_<estado>` correspondiente.
4. Cada pantalla lee una opción y cambia el estado (`self.pantalla`) o llama a
   un módulo de dominio.
5. Al salir, se vuelca la cola de bitácora y se despide.

### 5.1. Máquina de estados de las pantallas

La navegación no usa llamadas recursivas entre menús. En su lugar, `App`
mantiene:

- `self.pantalla`: nombre de la pantalla actual;
- `self.pila`: una `Pila` con las pantallas anteriores.

Métodos:

- `ir(destino)`: apila la pantalla actual y cambia a `destino`.
- `volver()`: desapila la última pantalla y vuelve a ella.

Esto permite que la opción `0` funcione de forma uniforme en todos los niveles y
que el comportamiento sea realmente LIFO.

### 5.2. Pantallas existentes

| Estado | Método | Función |
| --- | --- | --- |
| `login` | `pantalla_login` | Iniciar sesión o ir a registro. |
| `registro` | `pantalla_registro` | Crear una cuenta. |
| `menu` | `pantalla_menu` | Menú principal. |
| `dashboard` | `pantalla_dashboard` | Resumen y filas de espera. |
| `pacientes` | `pantalla_pacientes` | Listado y búsqueda. |
| `paciente_detalle` | `pantalla_paciente_detalle` | Ficha y eliminación. |
| `paciente_nuevo` | `pantalla_paciente_nuevo` | Formulario de alta. |
| `medicos` | `pantalla_medicos` | Listado y búsqueda. |
| `medico_detalle` | `pantalla_medico_detalle` | Ficha y eliminación. |
| `medico_nuevo` | `pantalla_medico_nuevo` | Formulario de alta. |
| `citas` | `pantalla_citas` | Listado, filtros y búsqueda. |
| `cita_detalle` | `pantalla_cita_detalle` | Detalle y acciones. |
| `cita_nueva` | `pantalla_cita_nueva` | Formulario de agendado. |

---

## 6. Explicación de cada módulo

### 6.1. `main.py` — interfaz de terminal

**Responsabilidad:** todo lo que el usuario ve y escribe. No contiene reglas de
negocio: delega en los módulos de dominio.

**Tamaño:** aproximadamente 1.153 líneas.

#### Configuración inicial

- Reconfigura `sys.stdin` y `sys.stdout` a UTF-8 para acentos y símbolos.
- En Windows, ejecuta `chcp 65001` para que la consola interprete UTF-8.
- Activa el modo ANSI de la consola con `ctypes` y `SetConsoleMode`.
- Define `USAR_COLOR`, que se desactiva si la salida no es una terminal o si
  existe la variable de entorno `NO_COLOR`.

#### Utilidades globales

| Función | Función |
| --- | --- |
| `c(texto, *estilos)` | Aplica color ANSI si está habilitado. |
| `limpiar()` | Limpia la pantalla solo si hay terminal interactiva. |
| `ancho_terminal()` | Calcula un ancho seguro entre 60 y 120 columnas. |
| `recortar(texto, ancho)` | Recorta celdas largas con `…`. |
| `imprimir_tabla(...)` | Dibuja tablas alineadas y ajusta anchos. |
| `leer(prompt)` | `input()` con manejo de `Ctrl+C` y fin de entrada. |
| `leer_password(prompt)` | `getpass` si hay terminal; si no, lectura normal. |
| `pausa()` | Pausa opcional; el flujo principal no la usa para no bloquear. |
| `confirmar(pregunta)` | Confirmación `s/N`. |
| `SalirPrograma` | Excepción interna para salir limpiamente. |

#### Clase `App`

Estado principal:

- `usuario`: cuenta autenticada.
- `pantalla`: pantalla actual.
- `pila`: navegación LIFO.
- `aviso_pendiente`: mensaje que se mostrará en la siguiente pantalla.
- `busqueda_pacientes`, `busqueda_medicos`, `busqueda_citas`: texto de búsqueda
  conservado al navegar.
- `filtro_citas`: filtro activo (`Todas`, `Pendiente`, etc.).
- `detalle_paciente`, `detalle_medico`, `cita_actual`: contexto de las fichas.

Métodos destacados:

- **`ejecutar()`**: bucle principal. Captura errores de dominio y los convierte
  en avisos; al salir, vuelca la bitácora.
- **`_cabecera()`**: dibuja el encabezado y el estado de la sesión.
- **`_titulo()`**: título y subtítulo de cada pantalla.
- **`_campo_obligatorio()`**, **`_campo_entero()`**, **`_campo_opcion()`**,
  **`_campo_fecha()`**, **`_campo_hora()`**: validaciones de formularios.
- **`_formulario()`**: construye formularios completos a partir de una lista de
  campos; devuelve `None` si el usuario escribe `cancelar`.
- **`_elegir()`**: selección numerada de pacientes o médicos.
- **`_proximas_citas()`**: ordena las citas con `ColaPrioridad`.
- **`_etiqueta_estado()`**: agrega la posición cuando la cita está en espera.
- **`_filas_espera()`**: resume las filas activas.
- **`_indice_de_cita()`**: localiza el índice real de una cita comparando
  diccionarios, para que `marcar_como_realizada()` reciba la posición correcta.
- **`_deshacer()`**: toma la última acción y llama al `revertir()` del módulo
  correspondiente.
- **`_cerrar_sesion()`**: vuelca la bitácora, limpia la pila de deshacer y
  vuelve al login.

#### Manejo de errores

El bucle principal envuelve cada pantalla:

```python
except (OSError, ValueError, TypeError, KeyError, RuntimeError) as error:
    self.aviso_pendiente = ("error", f"No se pudo completar la operación: {error}")
```

Así, un archivo corrupto, un registro inesperado o una operación inválida no
cierran el programa: se informa y se continúa. `Ctrl+C` y el fin de entrada se
capturan como `SalirPrograma` para cerrar de forma ordenada.

#### Tablas

`imprimir_tabla()`:

1. Convierte todas las celdas a texto.
2. Calcula el ancho máximo por columna, con topes configurables.
3. Reduce columnas si el total supera el ancho de la terminal.
4. Recorta celdas largas y las alinea.
5. Dibuja encabezado, separador y filas.

No usa ninguna librería externa de tablas.

---

### 6.2. `almacenamiento.py` — acceso atómico a JSON

**Responsabilidad:** leer y escribir listas JSON de forma segura.

**Se conecta con:** `pacientes.py`, `medicos.py`, `citas.py`, `usuarios.py`.

#### Funciones

| Función | Comportamiento |
| --- | --- |
| `firma_archivo(ruta)` | Devuelve `(mtime_ns, tamaño)` o `None` si no existe. |
| `cargar_json_lista(ruta)` | Lee una lista de diccionarios y valida su forma. |
| `guardar_json_atomico(ruta, datos)` | Escribe en un temporal, hace `fsync` y reemplaza el original. |

#### Por qué escritura atómica

Si el programa se interrumpe a mitad de una escritura, un JSON truncado dejaría
el sistema sin datos. El patrón usado es:

1. crear un archivo temporal en el mismo directorio;
2. escribir todo el contenido;
3. forzar `fsync`;
4. `os.replace(temporal, definitivo)` (operación atómica en el sistema de
   archivos);
5. borrar el temporal si algo falla.

Esto garantiza que el archivo definitivo siempre sea un JSON completo, o el
anterior, pero nunca una mezcla.

#### Firma de archivo

Los módulos de dominio cachean índices en memoria. Para saber si el archivo
cambió por fuera, comparan `(mtime_ns, tamaño)`. Si la firma cambia, el índice
se reconstruye automáticamente.

---

### 6.3. `estructuras.py` — pilas, colas y cola de prioridad

**Responsabilidad:** implementar a mano las estructuras lineales usadas por el
sistema, sin `collections.deque` ni `heapq`.

**Se conecta con:** `historial.py` (Pila y Cola) y `esperas.py` (Cola).
`main.py` también usa `Pila` para navegar y `ColaPrioridad` para ordenar citas.

#### `Pila` (LIFO)

- `apilar(elemento)`: agrega al final.
- `desapilar()`: quita y devuelve el último.
- `cima()`: consulta el último sin quitarlo.
- `esta_vacia()`, `tamano()`, `volcar()`.

Complejidad: `O(1)` en las operaciones principales.

Se usa para:

- la navegación entre pantallas (`main.py`);
- la pila de acciones para deshacer (`historial.py`).

#### `Cola` (FIFO)

- `encolar(elemento)`: agrega al final.
- `desencolar()`: quita el primero.
- `primero()`: consulta el primero.
- `esta_vacia()`, `tamano()`.

Para que `desencolar()` sea `O(1)`, la cola no hace `pop(0)`. Mantiene un índice
de cabeza (`_cabeza`) y compacta la lista solo cuando el espacio desperdiciado
supera la mitad del almacenamiento.

Se usa para:

- la cola de bitácora (`historial.py`);
- la fila de espera de un espacio de agenda (`esperas.py`).

#### `ColaPrioridad` (montículo mínimo)

- `encolar(clave, valor)`: inserta y sube el elemento.
- `desencolar()`: extrae el de menor clave y reordena hacia abajo.
- `cima()`, `esta_vacia()`, `tamano()`.

Es un montículo binario implementado a mano. En `main.py` se usa con claves
`(año, mes, día, hora, índice)` para mostrar las próximas citas, no las últimas
registradas.

Complejidad: `O(log n)` por inserción/extracción.

---

### 6.4. `busquedas.py` — algoritmos de búsqueda

**Responsabilidad:** normalizar texto y ofrecer tres estrategias de búsqueda.

**Se conecta con:** `pacientes.py`, `medicos.py`, `citas.py`, `usuarios.py`.
`pruebas_busquedas.py` lo prueba directamente.

#### Normalización

`normalizar(texto)`:

1. convierte a texto;
2. aplica `NFKD` para separar tildes;
3. elimina marcas de combinación;
4. aplica `casefold()`;
5. colapsa espacios repetidos.

Así, `"María"`, `"MARIA"` y `"maria"` se consideran iguales.

#### `ResultadoBusqueda`

Objeto con:

- `elementos`: lista encontrada;
- `algoritmo`: etiqueta legible (`Listado`, `Secuencial`, `Binaria (fecha)`,
  `Hash (documento)`, `Hash (espacio)`);
- `comparaciones`: métrica usada en pruebas y benchmark.

Implementa `__len__`, `__iter__`, `__getitem__` y `__bool__`, por lo que se usa
como una lista en `main.py`.

#### Búsqueda secuencial — `O(n)`

`busqueda_secuencial(registros, criterio)` recorre todos los registros y cuenta
comparaciones. Se usa para texto libre: todos los términos deben aparecer en
algún campo del registro.

#### Búsqueda binaria — `O(log n)`

- `indice_ordenado(registros, campo)` crea una lista de pares
  `(clave_ordenada, posición_original)` y la ordena.
- `busqueda_binaria(indice, objetivo)` busca una clave exacta.
- `busqueda_por_rango(indice, desde, hasta)` usa límites inferior y superior
  para devolver un rango inclusivo, incluso con duplicados.
- `busqueda_por_prefijo(indice, prefijo)` devuelve las claves que comienzan con
  un texto.

En citas, la clave es la fecha en formato ISO (`AAAA-MM-DD`). Por eso escribir
`dd/mm/aaaa` en el buscador activa la búsqueda binaria.

#### Tabla hash con encadenamiento — `O(1)` promedio

- Capacidad inicial: siguiente número primo.
- Función hash tipo djb2: `valor = valor * 33 + ord(carácter)`.
- Colisiones: listas enlazadas por cubeta (encadenamiento).
- Rehash automático cuando el factor de carga supera `0.75`.
- `insertar`, `insertar_si_ausente`, `agregar`, `buscar`, `buscar_todos`,
  `contiene`, `tamano`, `capacidad`, `factor_carga`.

Se usa para claves exactas:

- documento de pacientes;
- documento de médicos;
- correo de usuarios;
- espacio de agenda `(médico, fecha, hora)`.

#### Funciones auxiliares

- `parece_documento(texto)`: heurística para decidir si el texto parece un
  documento (contiene dígitos o guiones).
- `clave_fecha(texto)`: convierte `dd/mm/aaaa` a ISO o devuelve
  `9999-99-99` si no es válida.
- `construir_hash(registros, campo)`: índice por una clave única.
- `construir_hash_multiple(registros, campo)`: índice que admite varias citas
  por espacio.

---

### 6.5. `esperas.py` — reglas puras de la fila de espera

**Responsabilidad:** calcular la fila de espera sin escribir en disco.

**Se conecta con:** `citas.py` (lo usa para decidir estados y promociones) y
`estructuras.py` (`Cola`).

#### Concepto de espacio

Un **espacio de agenda** es la terna:

```text
(médico, fecha, hora)
```

Solo una cita activa puede ocuparlo. Si ya está ocupado, la nueva cita no se
rechaza: entra en una cola FIFO con estado `En espera` y un número de posición.

#### Funciones

| Función | Comportamiento |
| --- | --- |
| `clave_espacio(cita)` | Devuelve `(médico_normalizado, fecha, hora)`. |
| `espacio_ocupado(citas, nueva)` | `True` si hay otra cita no liberada en ese espacio. |
| `en_espera_del_espacio(citas, espacio)` | Lista ordenada por `posicion_espera`. |
| `cola_espera(citas, espacio)` | Devuelve una `Cola` FIFO con las citas en espera. |
| `total_en_espera(citas, espacio)` | Cantidad de personas detrás. |
| `posiciones_ocupadas(citas)` | Resumen `{espacio: (activa, [en espera])}`. |
| `renumerar(citas, espacio)` | Recalcula posiciones `1..n` tras una promoción. |

Estados que liberan el espacio: `Realizada` y `Cancelada`. El estado
`En espera` **sí cuenta como ocupante** para evitar que dos citas activas
compartan el mismo espacio.

---

### 6.6. `historial.py` — deshacer y bitácora

**Responsabilidad:** guardar las acciones para deshacer y registrar la
bitácora de operaciones.

**Se conecta con:** `estructuras.py` (`Pila` y `Cola`), y es usado por
`pacientes.py`, `medicos.py` y `citas.py`; `main.py` llama a `deshacer()`.

#### Pila de deshacer

- `registrar_accion(etiqueta, instantanea)`: apila una entrada con etiqueta,
  instantánea y marca de tiempo.
- `deshacer()`: desapila y devuelve la última entrada.
- `hay_pendientes()`, `etiqueta_pendiente()`: consulta para la interfaz.
- `limpiar()`: vacía la pila.
- `_persistir()`: guarda la pila en `archivos/historial.json` de forma atómica.
- `_cargar()`: recupera la pila al iniciar la aplicación.

Límite: **25 acciones**. Cuando se supera, se descarta la más antigua.

Cada entrada tiene esta forma:

```json
{
  "etiqueta": "Eliminar paciente",
  "instantanea": {
    "tipo": "eliminar",
    "entidad": "paciente",
    "posicion": 2,
    "datos": { "...": "..." }
  },
  "marca": "2026-10-28T08:16:34"
}
```

#### Cola de bitácora

- `registrar_bitacora(accion, detalle)` encola una línea.
- `_encolar_bitacora()` vuelca automáticamente al llegar a **10 líneas**.
- `volcar_bitacora()` fuerza el volcado (se usa al salir o cerrar sesión).
- El destino es `archivos/bitacora.txt`, en modo append.

Formato de línea:

```text
[2026-10-28 08:16:34] Registrar médico - medico
```

#### Persistencia de la pila

`historial.json` guarda la pila completa, por lo que se puede deshacer una
acción incluso después de cerrar y volver a abrir el programa. Al cerrar
sesión, `main.py` llama a `historial.limpiar()`, por lo que la pila se vacía
deliberadamente.

---

### 6.7. `usuarios.py` — cuentas y autenticación

**Responsabilidad:** registrar cuentas y verificar credenciales.

**Se conecta con:** `busquedas.py` (índice por correo) y `almacenamiento.py`
(firma de archivo).

#### Almacenamiento

Archivo: `archivos/usuarios.json`.

Cada usuario:

```json
{
  "email": "usuario@dominio.com",
  "salt": "sal_aleatoria_en_hex",
  "password_hash": "hash_pbkdf2_en_hex"
}
```

#### Funciones

| Función | Comportamiento |
| --- | --- |
| `_hash_password(password, salt=None)` | Genera sal de 16 bytes y deriva con PBKDF2-HMAC-SHA256, 200.000 iteraciones. |
| `cargar_usuarios()` | Lee el archivo; lanza `RuntimeError` si está corrupto. |
| `_guardar_usuarios(data)` | Escritura atómica. |
| `crear_indice()` / `_indice_actual()` | Tabla hash por correo, invalidada por firma de archivo. |
| `buscar_usuario(email)` | Búsqueda exacta por correo con hash. |
| `registrar_usuario(email, password)` | Valida duplicados, hashea y guarda. |
| `autenticar_usuario(email, password)` | Recalcula el hash con la sal y compara. |

#### Seguridad

- La contraseña **nunca** se guarda en texto plano.
- Cada cuenta tiene una sal distinta.
- El login se hace por correo normalizado a minúsculas.
- La contraseña se solicita con `getpass` para no mostrarla en pantalla.

---

### 6.8. `pacientes.py` — dominio de pacientes

**Responsabilidad:** cargar, buscar, registrar y eliminar pacientes.

**Se conecta con:** `almacenamiento.py`, `busquedas.py`, `historial.py` y,
de forma perezosa, `citas.py`.

#### Archivo

`archivos/pacientes.json` es una lista de objetos con estos campos:

```text
documento, nombre, apellido, edad, sexo, fecha_nacimiento,
telefono, direccion, correo, tipo_sangre, seguro_medico
```

#### Índice hash

- `_indice_documentos` cachea una tabla hash por documento.
- `_firma_indice` guarda la firma del archivo.
- `_indice_actual()` reconstruye el índice si el archivo cambió.
- `buscar_por_documento(documento)` es `O(1)` promedio.

#### Búsqueda

`buscar_pacientes(texto)`:

1. normaliza el texto;
2. si está vacío, devuelve el listado completo;
3. si el texto parece un documento exacto, usa la tabla hash;
4. si no, usa búsqueda secuencial por todos los campos de `CAMPOS_BUSQUEDA`.

#### Altas y bajas

- `registrar_paciente(datos)` agrega al final y registra la acción en el
  historial.
- `eliminar_paciente(documento)`:
  1. localiza el paciente por hash;
  2. cuenta sus citas con `contar_citas_paciente()`;
  3. si tiene citas, lanza `ValueError` y no elimina;
  4. si no tiene, elimina y registra la instantánea con su posición original.
- `revertir(instantanea)` deshace un alta o una baja:
  - `agregar`: elimina el registro si sigue en la misma posición y coincide;
  - `eliminar`: lo reinserta en la posición original.

---

### 6.9. `medicos.py` — dominio de médicos

**Responsabilidad:** cargar, buscar, registrar y eliminar médicos.

**Se conecta con:** `almacenamiento.py`, `busquedas.py`, `historial.py` y,
de forma perezosa, `citas.py`.

Es estructuralmente idéntico a `pacientes.py`.

#### Archivo

`archivos/medicos.json`:

```text
documento, nombre, apellido, telefono, correo,
modulo, especialidad, consultorio, horario
```

#### Diferencias con pacientes

- El índice hash es por `documento`.
- La búsqueda secuencial cubre los campos de médicos.
- Antes de eliminar, cuenta citas con `contar_citas_medico(nombre)`.
- `revertir()` funciona igual: reinserta o elimina según la instantánea.

---

### 6.10. `citas.py` — dominio de citas y fila de espera

**Responsabilidad:** es el módulo más complejo. Gestiona citas, estados,
búsquedas, promociones de la fila y deshacer.

**Se conecta con:** `almacenamiento.py`, `busquedas.py`, `historial.py` y
`esperas.py`.

#### Archivo

`archivos/citas.json`:

```text
paciente, documento_paciente, medico, especialidad, modulo,
fecha, hora, tipo, motivo, observaciones, estado
```

Campo opcional:

```text
posicion_espera   # solo cuando estado == "En espera"
```

`cargar_citas()` normaliza los registros:

- si falta `estado`, se asume `Pendiente`;
- si el estado no es `En espera`, se elimina `posicion_espera`.

#### Índice de fechas

- `crear_indice_fechas()` usa `busquedas.indice_ordenado` con
  `busquedas.clave_fecha`.
- `_indice_fechas_actual()` cachea el índice y lo invalida por firma de archivo.

#### Búsqueda

`buscar_citas(texto="", estado=None)`:

1. si `estado` no es `Todas`, filtra primero por estado;
2. si el texto está vacío, devuelve el listado filtrado;
3. si el texto es una fecha `dd/mm/aaaa`, usa búsqueda binaria por rango;
4. en otro caso, usa búsqueda secuencial por todos los campos.

`buscar_por_fecha(desde, hasta)` permite rangos inclusivos.
`buscar_por_espacio(medico, fecha, hora)` usa una tabla hash múltiple.

#### Cantidades

- `contar_citas_paciente(documento, nombre)` cuenta por documento o, si falta,
  por nombre.
- `contar_citas_medico(nombre)` cuenta por nombre del médico.

#### Agendar

`agregar_cita(cita)`:

1. carga las citas;
2. calcula el espacio `(médico, fecha, hora)`;
3. si el espacio está ocupado, asigna `estado = "En espera"` y
   `posicion_espera = total_en_espera + 1`;
4. si está libre, asigna `estado = "Pendiente"`;
5. guarda y registra la acción.

Devuelve la cita guardada, con su estado y posición.

#### Atender

`marcar_como_realizada(posicion)`:

1. cambia el estado a `Realizada`;
2. guarda una foto de la fila del espacio;
3. si la cita era `Pendiente`, promueve a la primera de la fila;
4. registra la acción con la promoción y la foto para poder deshacer.

#### Cancelar

`cancelar_cita(cita)`:

1. busca la cita comparando diccionarios (ignora `posicion_espera`);
2. cambia el estado a `Cancelada`;
3. si era la cita activa (`Pendiente`), promueve al siguiente de la fila;
4. registra la acción.

#### Promoción de la fila

`_promover_siguiente(registros, espacio)`:

- toma la `Cola` de espera del espacio;
- si está vacía, no hace nada;
- toma la primera cita;
- la pasa a `Pendiente`;
- elimina su `posicion_espera`;
- renumera las demás;
- devuelve una instantánea de la promoción.

`_foto_fila()` guarda las posiciones de **todas** las citas en espera del
espacio antes de la promoción. Esto es necesario para deshacer correctamente la
renumeración.

#### Deshacer

`revertir(instantanea)` admite tres tipos:

- `agregar`: elimina la cita si sigue en la misma posición y coincide;
- `eliminar`: reinserta la cita en su posición original;
- `estado`: restaura el estado anterior, revierte la promoción y restaura las
  posiciones exactas de la fila con `fila_antes`.

---

### 6.11. `pruebas_busquedas.py` — pruebas y benchmark

**Responsabilidad:** verificar los algoritmos y medir su rendimiento sin tocar
los JSON reales.

**Se conecta con:** `busquedas.py`, `citas.py`, `medicos.py`, `pacientes.py`.

Pruebas incluidas:

- `test_normalizacion`
- `test_busqueda_secuencial`
- `test_busqueda_binaria_aleatoria`
- `test_busqueda_binaria_duplicados`
- `test_busqueda_por_rango`
- `test_busqueda_por_prefijo`
- `test_tabla_hash`
- `test_busquedas_pacientes`
- `test_busquedas_medicos`
- `test_busquedas_citas`
- `test_indice_usuarios`

Además, `benchmark()` compara búsqueda secuencial, binaria y hash con 5.000
registros de prueba.

Los tests pasan listas propias mediante el parámetro `registros` de las
funciones de dominio, por lo que **no modifican** los archivos de `archivos/`.

Ejecución:

```bash
python pruebas_busquedas.py
```

---

### 6.12. `INICIAR.bat` — lanzador de Windows

```bat
@echo off
cd /d "%~dp0"
chcp 65001 >nul
python main.py
pause
```

- `cd /d "%~dp0"` sitúa el proceso en la carpeta del proyecto.
- `chcp 65001` activa UTF-8 en la consola.
- `python main.py` inicia la aplicación.
- `pause` mantiene la ventana abierta al terminar o fallar.

Es opcional: también se puede ejecutar `python main.py` manualmente.

---

### 6.13. `README.md` — guía de usuario

Resumen de:

- requisitos;
- cómo ejecutar;
- primer uso;
- navegación;
- funciones;
- ubicación de los datos;
- cómo ejecutar las pruebas.

Está orientado al usuario final, no al desarrollador. Este documento cubre la
parte técnica.

---

### 6.14. `archivos/` — datos persistentes

| Archivo | Contenido | Quién escribe |
| --- | --- | --- |
| `pacientes.json` | Lista de pacientes. | `pacientes.py` |
| `medicos.json` | Lista de médicos. | `medicos.py` |
| `citas.json` | Lista de citas y posiciones de espera. | `citas.py` |
| `usuarios.json` | Cuentas con sal y hash. | `usuarios.py` |
| `historial.json` | Pila de acciones para deshacer. | `historial.py` |
| `bitacora.txt` | Registro histórico de operaciones. | `historial.py` |

Los JSON se escriben con `indent=4` y `ensure_ascii=False`, por lo que los
acentos se conservan legibles.

`bitacora.txt` se crea automáticamente la primera vez que se registra una
acción. No es necesario crearlo a mano.

---

## 7. Modelo de datos

### 7.1. Paciente

```json
{
  "documento": "085-110886-4432D",
  "nombre": "María Esperanza",
  "apellido": "Guerrero Mendez",
  "edad": 40,
  "sexo": "femenino",
  "fecha_nacimiento": "15/06/1986",
  "telefono": "76751188",
  "direccion": "San Juan",
  "correo": "maria@test.com",
  "tipo_sangre": "O-",
  "seguro_medico": "no tiene"
}
```

### 7.2. Médico

```json
{
  "documento": "086-241112-876G",
  "nombre": "Ernesto",
  "apellido": "Gutierres",
  "telefono": "76543211",
  "correo": "ernesto@test.com",
  "modulo": "5",
  "especialidad": "diabetologo",
  "consultorio": "4",
  "horario": "6 am a 3 pm"
}
```

### 7.3. Cita

```json
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
  "estado": "Pendiente"
}
```

Si está en espera, agrega:

```json
"estado": "En espera",
"posicion_espera": 1
```

### 7.4. Usuario

```json
{
  "email": "usuario@dominio.com",
  "salt": "27d92269015e688d1b5e0b77ff553936",
  "password_hash": "4f2f3f1b799cc1e40c6cb3fa062040796ea9b5612f837a55e27ce76b8a5510b0"
}
```

### 7.5. Estados de una cita

| Estado | Significado | ¿Ocupa el espacio? |
| --- | --- | --- |
| `Pendiente` | Cita activa esperando atención. | Sí |
| `En espera` | Está en la fila detrás de otra cita. | Sí |
| `Realizada` | Ya se atendió. | No |
| `Cancelada` | Se canceló. | No |

---

## 8. Estructuras de datos y algoritmos

| Estructura / algoritmo | Archivo | Uso | Complejidad |
| --- | --- | --- | --- |
| Pila (LIFO) | `estructuras.py` | Navegación y deshacer. | `O(1)` |
| Cola (FIFO) | `estructuras.py` | Fila de espera y bitácora. | `O(1)` |
| Cola de prioridad (min-heap) | `estructuras.py` | Próximas citas del panel. | `O(log n)` |
| Búsqueda secuencial | `busquedas.py` | Texto libre. | `O(n)` |
| Búsqueda binaria | `busquedas.py` | Fecha exacta o rango. | `O(log n)` |
| Tabla hash con encadenamiento | `busquedas.py` | Documento, correo y espacio. | `O(1)` promedio |
| Renumeración de fila | `esperas.py` | Posiciones `1..n`. | `O(k)` |

### 8.1. Dónde se usa cada una

- **Pila de navegación:** `App.pila` en `main.py`. Permite volver a la pantalla
  anterior con `0`.
- **Pila de deshacer:** `historial._pila`. Cada alta, baja o cambio de estado
  guarda una instantánea.
- **Cola de bitácora:** `historial._cola`. Agrupa líneas y las vuelca por
  lotes.
- **Cola de espera:** `esperas.cola_espera()`. Mantiene el orden de llegada.
- **Cola de prioridad:** `App._proximas_citas()`. Ordena por fecha y hora.
- **Hash:** documentos de pacientes y médicos, correo de usuarios y espacio de
  agenda.
- **Binaria:** fechas de citas.

---

## 9. Persistencia y consistencia

### 9.1. Archivos y responsables

```text
main.py
  ├─ pacientes.py ──► archivos/pacientes.json
  ├─ medicos.py ────► archivos/medicos.json
  ├─ citas.py ──────► archivos/citas.json
  ├─ usuarios.py ───► archivos/usuarios.json
  └─ historial.py ──► archivos/historial.json
                    └► archivos/bitacora.txt
```

### 9.2. Escritura atómica

Todas las escrituras de datos pasan por `guardar_json_atomico()` o por el
equivalente de `usuarios.py` e `historial.py`:

1. archivo temporal en el mismo directorio;
2. escritura completa;
3. `fsync`;
4. reemplazo atómico con `os.replace`;
5. limpieza del temporal.

### 9.3. Cachés e invalidación

- Pacientes y médicos cachean una tabla hash por documento.
- Citas cachea un índice ordenado por fecha.
- Usuarios cachea una tabla hash por correo.

Cada caché guarda la firma `(mtime_ns, tamaño)` del archivo. Si el archivo
cambia (por ejemplo, porque se editó a mano o porque otra instancia lo
modificó), la próxima búsqueda reconstruye el índice.

### 9.4. Concurrencia

El sistema está pensado para **un solo usuario a la vez**. No hay bloqueos de
archivo ni control de versiones. Si se abren dos instancias y ambas escriben,
la última en guardar puede sobrescribir los cambios de la otra. Para el uso
previsto (una clínica, una terminal) es suficiente.

---

## 10. Seguridad

- Las contraseñas se derivan con **PBKDF2-HMAC-SHA256**, 200.000 iteraciones y
  sal aleatoria de 16 bytes.
- No se guarda la contraseña original en ningún archivo.
- La entrada de contraseña usa `getpass`, por lo que no se muestra en pantalla.
- El correo se normaliza a minúsculas para evitar duplicados por mayúsculas.
- Los datos clínicos se guardan en JSON legible; la confidencialidad depende de
  los permisos del sistema de archivos, no del programa.
- No hay recuperación de contraseña automática: si se pierde, debe gestionarla
  el administrador.

---

## 11. Validaciones y manejo de errores

### 11.1. En la interfaz (`main.py`)

- Campos obligatorios: no se acepta vacío.
- Edad: entero no negativo.
- Fecha: `dd/mm/aaaa` validada con `datetime.strptime`.
- Hora: `hh:mm` en formato de 24 horas.
- Sexo y tipo de cita: selección de una lista.
- Eliminaciones: confirmación `s/N`.
- El usuario puede escribir `cancelar` en un formulario para volver.
- Los errores de dominio se muestran como avisos y no cierran la aplicación.

### 11.2. En el dominio

- `ValueError` si se intenta eliminar un paciente o médico con citas.
- `RuntimeError` si `usuarios.json` no se puede leer.
- `ValueError` si una cita no es un diccionario válido.
- `False` cuando un registro ya no existe.
- Instantáneas de deshacer que verifican posición y contenido antes de revertir.

### 11.3. En el almacenamiento

- `cargar_json_lista()` valida que el archivo contenga una lista de
  diccionarios.
- Si el archivo no existe, devuelve `[]`.
- Si el JSON está corrupto, el error se propaga y `main.py` lo muestra.

---

## 12. Decisiones de diseño

Esta sección explica **por qué** el código está hecho así.

### 12.1. Separar la presentación del dominio

La lógica de pacientes, médicos, citas, esperas, búsquedas y usuarios está en
módulos independientes; `main.py` solo se ocupa de mostrar menús, leer datos y
presentar resultados. Esta separación evita mezclar reglas de negocio con
detalles de consola y permite probar el dominio sin abrir la aplicación.

**Ventaja:** cada módulo se puede entender y modificar por separado.
**Consecuencia:** la interfaz debe respetar los contratos que exponen los
módulos de dominio.

### 12.2. Proyecto autocontenido

Todos los módulos y los datos están dentro de `control_de_cita_medica_terminal`.
El programa no depende de archivos externos ni de otras carpetas: se puede
mover, copiar o entregar como una unidad completa.

### 12.3. Menús numerados en lugar de flechas

Se eligieron menús con números y letras porque:

- funcionan en cualquier terminal;
- no requieren detección de teclas especiales;
- son más fáciles de probar con entrada redirigida;
- no dependen de `curses` ni de librerías externas.

La navegación con flechas habría requerido una capa adicional de lectura de
teclado y no aportaba valor al flujo principal.

### 12.4. Máquina de estados en lugar de llamadas recursivas

Cada pantalla es un método y el estado global indica cuál se dibuja. Así se
evita que los menús se llamen recursivamente y se mantiene una pila de
navegación explícita. También hace que `0. Volver` sea uniforme.

La pila `App.pila` reutiliza la clase `Pila` del proyecto, de modo que la
navegación sigue siendo un ejemplo real de LIFO.

### 12.5. Avisos en la siguiente pantalla, sin pausas

En lugar de imprimir un mensaje y esperar Enter después de cada operación, el
mensaje se guarda en `aviso_pendiente` y aparece al volver a dibujar. Esto hace
la navegación más fluida y evita que el usuario tenga que confirmar cada acción.

La función `pausa()` queda disponible para mensajes que realmente necesiten una
pausa visual, pero el flujo principal no la usa.

### 12.6. Colores ANSI con degradación elegante

- Si la salida no es una terminal, los colores se desactivan.
- Si existe `NO_COLOR`, también se desactivan.
- En Windows se intenta activar el modo VT de la consola.
- `INICIAR.bat` y `chcp 65001` aseguran UTF-8.

Así el programa se ve bien en una terminal real y sigue siendo legible cuando
se redirige la salida a un archivo o a una prueba automatizada.

### 12.7. Tablas propias y ajuste al ancho

No se usó `rich` ni `tabulate` para mantener cero dependencias. La función
`imprimir_tabla()` calcula anchos, reduce columnas si hace falta y recorta
textos largos con `…`. Es una solución suficiente para los datos del sistema.

### 12.8. Formato JSON legible y estable

`pacientes.json`, `medicos.json`, `citas.json` y `usuarios.json` usan listas de
objetos con campos descriptivos. Las citas solo agregan el campo opcional
`posicion_espera`, y únicamente cuando están en espera.

**Ventaja:** los datos se pueden inspeccionar, respaldar y editar sin
herramientas especiales.

### 12.9. Datos centralizados en `archivos/`

Toda la persistencia vive en una sola carpeta. Así los respaldos son simples
(copiar `archivos/`) y el código no dispersa rutas por el proyecto.

### 12.10. `getpass` con respaldo

Si hay terminal interactiva, se usa `getpass` para ocultar la contraseña. Si la
entrada está redirigida (por ejemplo, en una prueba), se usa `input()` normal.
Así se puede automatizar la verificación sin perder seguridad en el uso real.

### 12.11. La palabra `cancelar` como salida de formularios

En lugar de agregar una opción numérica extra a cada formulario, se acepta
`cancelar` en cualquier campo. Es fácil de recordar y evita confusiones con
valores reales.

### 12.12. Deshacer persistente pero limitado

La pila se guarda en disco para sobrevivir al cierre, pero se limita a 25
acciones para que el archivo no crezca sin control. Al cerrar sesión se limpia
deliberadamente, porque las acciones pertenecen a la sesión del usuario.

### 12.13. Fila de espera como cola real

Cuando un espacio está ocupado, la cita nueva no se rechaza ni se sobrescribe:
entra en una `Cola` FIFO. Al atender o cancelar la cita activa, la primera de la
fila se promueve. Esto refleja el comportamiento de una agenda real y permite
que el sistema sea útil incluso con horarios duplicados.

### 12.14. Búsquedas con estrategia según el dato

- Texto libre: secuencial, porque hay que revisar varios campos.
- Fecha exacta: binaria, porque el índice ya está ordenado.
- Documento, correo o espacio: hash, porque la clave es exacta.

La interfaz muestra la etiqueta del algoritmo usado (`Secuencial`,
`Binaria (fecha)`, `Hash (documento)`), lo que hace visible la decisión y
facilita explicar el sistema.

### 12.15. Sin dependencias externas

El objetivo era que el sistema se pudiera ejecutar con el Python estándar. No se
usan frameworks de consola, ORM, bases de datos ni servicios. Esto simplifica
la instalación y la entrega.

---

## 13. Flujo de uso resumido

### 13.1. Inicio

1. Ejecutar `INICIAR.bat` o `python main.py`.
2. Elegir `1` para ingresar o `2` para crear una cuenta.
3. Introducir correo y contraseña.

### 13.2. Menú principal

```text
[1] Panel de control
[2] Pacientes
[3] Médicos
[4] Citas
[5] Deshacer: <acción pendiente>
[6] Cerrar sesión
[0] Salir
```

### 13.3. Teclas y convenciones

| Entrada | Significado |
| --- | --- |
| `0` | Volver a la pantalla anterior o salir. |
| `B` | Buscar en pacientes, médicos o citas. |
| `L` | Limpiar la búsqueda. |
| `N` | Registrar paciente, médico o cita. |
| `T` | Filtro Todas. |
| `P` | Filtro Pendiente. |
| `E` | Filtro En espera. |
| `R` | Filtro Realizada. |
| `C` | Filtro Cancelada. |
| `cancelar` | Cancelar un formulario y volver. |
| `Ctrl+C` | Salir de forma segura. |

### 13.4. Agendar una cita

1. `4` → Citas → `N`.
2. Elegir paciente por número.
3. Elegir médico por número.
4. Escribir fecha `dd/mm/aaaa` y hora `hh:mm`.
5. Elegir tipo (`presencial` o `virtual`).
6. Escribir motivo y observaciones.
7. Si el espacio está libre, queda `Pendiente`.
8. Si está ocupado, queda `En espera` con su posición.

### 13.5. Atender o cancelar

1. Entrar a Citas y seleccionar una cita.
2. `R` para marcarla como realizada.
3. `C` para cancelarla.
4. Si había alguien en la fila, se promueve automáticamente.

### 13.6. Deshacer

1. Ir al menú principal.
2. Elegir `5`.
3. Confirmar con `s`.
4. La última acción se revierte y se registra en la bitácora.

---

## 14. Pruebas y verificación

### 14.1. Pruebas automáticas

```bash
cd control_de_cita_medica_terminal
python pruebas_busquedas.py
```

Resultado esperado: todas las pruebas en `OK` y un benchmark comparativo.

### 14.2. Verificación manual recomendada

- Crear una cuenta y volver a iniciar sesión.
- Registrar un paciente y un médico.
- Agendar dos citas en el mismo médico, fecha y hora.
- Comprobar que la segunda queda `En espera · 1º`.
- Marcar la primera como realizada y verificar que la segunda pasa a
  `Pendiente`.
- Cancelar la cita activa y comprobar la promoción.
- Eliminar un paciente sin citas y deshacer la eliminación.
- Intentar eliminar un paciente con citas y comprobar el bloqueo.
- Buscar una fecha `dd/mm/aaaa` y verificar el texto `Binaria (fecha)`.
- Salir y volver a entrar para comprobar que los datos persisten.

### 14.3. Comprobación de dependencias

```bash
findstr /i "^import " main.py
```

Las únicas importaciones deben ser la biblioteca estándar y los módulos del
propio proyecto.

---

## 15. Limitaciones conocidas

1. **Una sola instancia:** no hay bloqueo de archivos; dos instancias pueden
   sobrescribirse.
2. **Sin paginación:** todos los registros se cargan en memoria y se muestran
   en una sola tabla.
3. **Recorte de texto:** las celdas muy largas se recortan con `…`; no hay
   ajuste de línea.
4. **Posiciones con huecos:** si se cancela o elimina una cita que está en
   espera, las posiciones restantes conservan su número hasta la próxima
   promoción, que las renumera.
5. **Deshacer limitado:** máximo 25 acciones y se limpia al cerrar sesión.
6. **Comparación de hashes:** la verificación usa `==`; para un entorno local es
   aceptable, pero podría endurecerse con `hmac.compare_digest`.
7. **Sin recuperación de contraseña:** debe gestionarla el administrador.
8. **Datos clínicos en JSON legible:** la protección depende de los permisos del
   sistema de archivos.
9. **Interfaz orientada a Windows:** el código Python es multiplataforma, pero
   `INICIAR.bat` y `chcp` son específicos de Windows. En Linux/macOS se ejecuta
   con `python main.py`.

---

## 16. Posibles mejoras

- Añadir paginación o filtros adicionales para listados largos.
- Renumerar la fila también al cancelar o eliminar una cita en espera.
- Usar `hmac.compare_digest` para comparar hashes.
- Añadir exportación a CSV.
- Añadir un modo de solo lectura o roles de usuario.
- Añadir pruebas de integración de la interfaz con entrada simulada.
- Añadir un comando `--version` o `--help`.
- Internacionalizar los textos.

---

## 17. Glosario

| Término | Significado |
| --- | --- |
| **Espacio de agenda** | Combinación `(médico, fecha, hora)`. |
| **Cita activa** | Cita en estado `Pendiente` que ocupa el espacio. |
| **Fila de espera** | Cola FIFO de citas `En espera` para un espacio. |
| **Promoción** | Paso de la primera cita de la fila a `Pendiente`. |
| **Instantánea** | Datos mínimos guardados para poder deshacer una acción. |
| **Bitácora** | Registro append-only de operaciones. |
| **Firma de archivo** | Par `(mtime_ns, tamaño)` para invalidar cachés. |
| **Normalización** | Quitar tildes, mayúsculas y espacios extra para comparar texto. |

---

## 18. Conclusión

El sistema MediCitas funciona íntegramente en la terminal mediante menús
numerados, tablas propias y avisos no bloqueantes. La separación entre `main.py`
y los módulos de dominio permite entender, probar y modificar cada parte por
separado.

Las decisiones principales —separar presentación y dominio, centralizar los
datos en `archivos/`, usar estructuras de datos propias y no depender de
paquetes externos— buscan que el proyecto sea fácil de ejecutar, fácil de
explicar y fácil de mantener.
