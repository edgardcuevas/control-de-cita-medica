# Roadmap — MediCitas

Desarrollo del sistema de gestión de citas médicas que funciona **íntegramente
en terminal**, con menús numerados y sin interfaz gráfica.

Marca cada tarea con `[x]` cuando esté terminada.

---

## Fase 1 · Estructura del proyecto

- [x] Crear la carpeta `control_de_cita_medica_terminal`.
- [x] Implementar los módulos de dominio:
  - [x] `pacientes.py`
  - [x] `medicos.py`
  - [x] `citas.py`
  - [x] `usuarios.py`
  - [x] `esperas.py`
  - [x] `historial.py`
  - [x] `estructuras.py`
  - [x] `busquedas.py`
  - [x] `almacenamiento.py`
  - [x] `pruebas_busquedas.py`
- [x] Crear la carpeta `archivos/` para la persistencia:
  - [x] `usuarios.json`
  - [x] `pacientes.json`
  - [x] `medicos.json`
  - [x] `citas.json`
  - [x] `historial.json`
- [x] Mantener el proyecto autocontenido, sin dependencias de otras carpetas.

## Fase 2 · Base de la aplicación de terminal

- [x] Crear `main.py` como capa de presentación de terminal.
- [x] Configurar salida UTF-8 para acentos en Windows.
- [x] Activar colores ANSI y limpieza de pantalla.
- [x] Implementar helpers de entrada:
  - [x] lectura segura con `Ctrl+C` / fin de entrada
  - [x] contraseña oculta con `getpass`
  - [x] confirmaciones `s/N`
  - [x] pausas y mensajes de error/éxito
- [x] Implementar tablas alineadas con ajuste al ancho de la terminal.
- [x] Implementar navegación con `Pila` y opción `0. Volver`.
- [x] Manejo centralizado de errores (`OSError`, `ValueError`, `KeyError`, etc.).

## Fase 3 · Sesión de usuario

- [x] Pantalla de inicio de sesión con correo y contraseña oculta.
- [x] Pantalla de creación de cuenta con las mismas validaciones:
  - [x] correo con formato válido
  - [x] contraseña de al menos 8 caracteres
  - [x] confirmación de contraseña
  - [x] correo duplicado rechazado
- [x] Cierre de sesión con volcado de bitácora y limpieza de la pila de deshacer.

## Fase 4 · Panel de control

- [x] Contadores: pacientes, médicos, citas totales, pendientes y en espera.
- [x] Próximas 5 citas ordenadas con `ColaPrioridad` por fecha y hora.
- [x] Filas de espera: médico, fecha, hora, cantidad y orden de pacientes.
- [x] Accesos rápidos a nueva cita y listado de citas.

## Fase 5 · Pacientes

- [x] Listado en tabla con documento, edad, sexo, teléfono y sangre.
- [x] Búsqueda por texto libre y por documento exacto.
- [x] Indicador del algoritmo usado y número de resultados.
- [x] Limpiar búsqueda.
- [x] Registrar paciente con todos los campos requeridos.
- [x] Ver ficha completa del paciente.
- [x] Mostrar cuántas citas tiene asociadas.
- [x] Eliminar paciente con confirmación y bloqueo si tiene citas.

## Fase 6 · Médicos

- [x] Listado en tabla con documento, especialidad, consultorio y horario.
- [x] Búsqueda por texto libre y por documento exacto.
- [x] Limpiar búsqueda.
- [x] Registrar médico con todos los campos requeridos.
- [x] Ver ficha completa del médico.
- [x] Mostrar cuántas citas tiene asociadas.
- [x] Eliminar médico con confirmación y bloqueo si tiene citas.

## Fase 7 · Citas

- [x] Listado con columna de estado y posición en la fila (`En espera · 2º`).
- [x] Filtros: Todas, Pendiente, En espera, Realizada y Cancelada.
- [x] Búsqueda por texto libre y por fecha `dd/mm/aaaa` (búsqueda binaria).
- [x] Limpiar búsqueda.
- [x] Agendar cita seleccionando paciente y médico de una lista.
- [x] Validar fecha `dd/mm/aaaa` y hora `hh:mm`.
- [x] Registrar tipo de cita, motivo y observaciones.
- [x] Si el espacio `(médico, fecha, hora)` está ocupado, la cita entra en la fila de espera.
- [x] Ver detalle completo de la cita.
- [x] Mostrar posición en la fila y quién ocupa el turno.
- [x] Marcar cita como realizada y promover al siguiente de la fila.
- [x] Cancelar cita y promover al siguiente de la fila.
- [x] Eliminar cita con advertencia si no está realizada.

## Fase 8 · Deshacer

- [x] Mostrar en el menú la etiqueta de la acción pendiente.
- [x] Deshacer altas, eliminaciones y cambios de estado.
- [x] Revertir promociones y renumeraciones de la fila de espera.
- [x] Registrar la acción deshecha en la bitácora.

## Fase 9 · Arranque y documentación

- [x] Crear `INICIAR.bat` con UTF-8 y ejecución de `main.py`.
- [x] Redactar `README.md` con requisitos, uso y navegación.
- [x] Documentar menús, atajos y flujo de uso.
- [x] Crear `DOCUMENTACION.md` con arquitectura, módulos, conexiones y decisiones.
- [x] Confirmar que no se requiere ninguna dependencia externa.

## Fase 10 · Verificación

- [x] Ejecutar `python pruebas_busquedas.py` sin fallos.
- [x] Prueba de humo: crear cuenta e iniciar sesión.
- [x] Prueba de humo: listar pacientes, médicos y citas.
- [x] Prueba de humo: agendar dos citas en el mismo espacio y comprobar la fila de espera.
- [x] Prueba de humo: marcar realizada y comprobar la promoción.
- [x] Prueba de humo: deshacer la última acción.
- [x] Prueba de humo: eliminar un registro y deshacerlo.
- [x] Comprobar que `main.py` no importa bibliotecas de interfaz gráfica.

---

## Estado

| Fase | Estado |
| --- | --- |
| 1. Preparación | Completado |
| 2. Base terminal | Completado |
| 3. Sesión | Completado |
| 4. Panel | Completado |
| 5. Pacientes | Completado |
| 6. Médicos | Completado |
| 7. Citas | Completado |
| 8. Deshacer | Completado |
| 9. Arranque y docs | Completado |
| 10. Verificación | Completado |

## Resultado

- Proyecto implementado en `control_de_cita_medica_terminal/`.
- `python pruebas_busquedas.py`: todas las pruebas pasaron.
- Pruebas de humo ejecutadas: inicio de sesión, registro, listados, búsqueda,
  agendado, fila de espera, promoción, cancelación, eliminación y deshacer.
- `main.py` no importa bibliotecas de interfaz gráfica.
