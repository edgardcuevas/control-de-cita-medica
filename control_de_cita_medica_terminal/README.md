# MediCitas — Control de Citas Médicas

Sistema de gestión de citas médicas que funciona **íntegramente en la
terminal**, con menús numerados y sin ventanas. Incluye pacientes, médicos,
citas, usuarios, filas de espera, búsqueda y deshacer.

## Requisitos

- Python 3.10 o superior.
- No requiere paquetes externos ni interfaz gráfica.

## Ejecutar en Windows

Haz doble clic en `INICIAR.bat` o, en una terminal:

```bash
python main.py
```

## Primer uso

1. Elige **Crear cuenta** en la pantalla de inicio de sesión.
2. Registra un correo y una contraseña de al menos 8 caracteres.
3. Vuelve a iniciar sesión con esas credenciales.

Las cuentas se guardan en `archivos/usuarios.json`. Las contraseñas se almacenan
como hashes PBKDF2-SHA256 con sal aleatoria.

## Navegación

- Los menús se operan escribiendo el número de la opción y presionando Enter.
- `0` vuelve a la pantalla anterior (usa una pila LIFO).
- `5` en el menú principal deshace la última acción, si hay una pendiente.
- Escribe `cancelar` en cualquier campo de un formulario para volver.
- `Ctrl+C` sale del programa de forma segura (vuelca la bitácora).

## Funciones disponibles

- **Panel de control**: contadores, próximas 5 citas y filas de espera.
- **Pacientes**: listado, búsqueda, registro, ficha y eliminación con validación.
- **Médicos**: listado, búsqueda, registro, ficha y eliminación con validación.
- **Citas**: filtros por estado, búsqueda por texto o fecha, agendado, detalle,
  marcar como realizada, cancelar y eliminar.
- **Deshacer**: revierte altas, eliminaciones y cambios de estado.
- **Fila de espera**: si un espacio `(médico, fecha, hora)` está ocupado, la nueva
  cita entra en la fila y se promueve sola al liberar el espacio.

## Implementación

La lógica propia está organizada de forma procedimental: se usan funciones y
listas o diccionarios, sin definir clases propias. Se conservan las búsquedas
secuencial, binaria, por rango, por prefijo y mediante tabla hash. Las pilas y
colas se representan con listas; las próximas citas se ordenan con un montículo
mínimo implementado como funciones.

## Datos

Los archivos JSON se leen y escriben en la carpeta `archivos/`. Todos los datos
del sistema están ahí; para respaldarlos basta con copiar esa carpeta.

## Verificación

```bash
python pruebas_busquedas.py
```

Las pruebas verifican los algoritmos de búsqueda, la tabla hash y las
operaciones LIFO, FIFO y de cola de prioridad.
