# MediCitas — Control de Citas Médicas

Aplicación de escritorio desarrollada en Python con Tkinter/ttk. Incluye pantallas de inicio de sesión y creación de cuenta inspiradas en las nuevas maquetas visuales, además de los módulos de Dashboard, pacientes, médicos y citas.

## Requisitos
- Python 3.10 o superior recomendado.
- Tkinter (incluido normalmente en la instalación de Python para Windows).
- No requiere paquetes externos.

## Ejecutar en Windows
Haz doble clic en `INICIAR.bat` o ejecuta en una terminal:

```bash
python main.py
```

## Primer uso
1. En la pantalla de inicio de sesión, selecciona **Crear cuenta**.
2. Registra un correo y una contraseña de al menos 8 caracteres.
3. Vuelve a iniciar sesión con esas credenciales.

Las cuentas se guardan en `archivos/usuarios.json`. Las contraseñas se almacenan como hashes PBKDF2-SHA256 con sal aleatoria, no como texto legible.

## Gestión de eliminaciones
- **Pacientes, médicos y citas** se pueden eliminar desde la columna **Acción (×)** de sus tablas, y los médicos además desde el botón **×** de su tarjeta.
- Toda eliminación pide confirmación en un diálogo propio que advierte *«Esta acción no se puede deshacer.»*.
- No se permite eliminar un **paciente o un médico que tenga citas asociadas**: primero hay que eliminar esas citas.
- Al eliminar una cita que **no está completada** (estado Pendiente o Cancelada), el diálogo muestra una advertencia en amarillo indicando que es una cita sin terminar. La eliminación sigue siendo posible.
- Los archivos JSON se escriben de forma **atómica** (archivo temporal + reemplazo), por lo que una interrupción no deja los datos a medias.
- Aun así, si te equivocas, puedes revertir el borrado con **↶ Deshacer** o **Ctrl+Z** (ver *Estructuras de datos*).

## Estructuras de datos (pilas y filas)
El sistema implementa estructuras de datos lineales propias en `estructuras.py` —Pila (LIFO), Cola (FIFO) y ColaPrioridad (montículo binario)—, escritas a mano sin `collections.deque` ni `heapq`. Se usan en tres lugares:

- **ColaPrioridad** ordena el panel *«Próximas citas»* del Dashboard por fecha y hora, de modo que muestra las citas más próximas y no las últimas registradas.
- **Pila** de navegación: el botón **← Atrás** de la barra superior retrocede a la pantalla anterior, en orden LIFO.
- **Pila** de deshacer: cada alta, eliminación o cambio de estado guarda una instantánea que se puede revertir. Admite las últimas **25** acciones y sobrevive al cierre de la aplicación.
- **Cola** de bitácora: las acciones se registran en `archivos/bitacora.txt` por lotes, conservando el orden.
- **Cola** de espera de pacientes: un espacio de agenda es *(médico, fecha, hora)* y solo cabe una cita. Si ya está ocupado, el nuevo paciente **no se pisa ni se rechaza**: entra en la fila con estado *«En espera»* y su número de posición. Al atender o cancelar la cita activa, la primera de la fila sube sola a *«Pendiente»* y las demás se renumeran.

## Fila de espera
- En el Dashboard hay una tarjeta **«En espera»** y un panel **«Filas de espera»** con el orden de cada fila.
- En *Citas* hay una quinta pestaña **«En espera»**, y la columna Estado muestra la posición (`En espera · 2º`).
- El detalle de una cita en espera indica en qué posición está y quién ocupa el turno.
- El botón **✕ Cancelar cita** libera el espacio y hace subir al siguiente de la fila.

Estas instantáneas se guardan aparte, en `archivos/historial.json`. **No hay que migrar ningún dato**: `pacientes.json`, `medicos.json` y `citas.json` mantienen su formato. Las citas solo suman un campo opcional `posicion_espera`, y únicamente cuando están en espera.

La explicación completa —dónde se aplicó cada estructura, con ejemplos y análisis de complejidad— está en **`ESTRUCTURAS.txt`**.

## Almacenamiento
Los pacientes, médicos y citas siguen almacenándose en los archivos JSON existentes de la carpeta `archivos/`. No se necesita migrar esos datos.

## Nota sobre recuperación de contraseña
La opción «Olvidé mi contraseña» muestra un aviso informativo. La recuperación real por correo requiere configurar un servicio de correo o un procedimiento administrativo seguro; no se simula un envío de correo.
