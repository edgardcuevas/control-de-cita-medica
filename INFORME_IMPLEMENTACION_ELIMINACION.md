# Informe de implementación

## Sistema de eliminación de registros

**Proyecto:** Control de Citas Médicas  
**Fecha:** 8 de octubre de 2026  
**Interfaz:** Python con Tkinter/ttk  
**Persistencia:** archivos JSON

---

## 1. Resumen ejecutivo

Se incorporó al sistema una función para eliminar pacientes, médicos y citas desde la interfaz gráfica. Las acciones se presentan de forma compacta y solicitan confirmación antes de modificar los datos.

Para proteger la relación entre registros, el sistema impide eliminar pacientes o médicos que todavía tengan citas asociadas. Las citas deben eliminarse primero de manera explícita. Los cambios confirmados se guardan en los archivos JSON existentes y las vistas correspondientes se vuelven a cargar sin reiniciar la aplicación.

## 2. Objetivos

- Permitir la eliminación de pacientes, médicos y citas desde Tkinter.
- Evitar eliminaciones accidentales mediante una confirmación con las opciones **Cancelar** y **Eliminar**.
- Preservar la consistencia entre pacientes, médicos y citas.
- Conservar el formato y la ubicación de los archivos JSON.
- Informar al usuario cuando una eliminación no pueda completarse.

## 3. Alcance y funcionamiento

### 3.1 Pacientes

Cada fila de la tabla de pacientes incluye una acción pequeña **×** al extremo derecho. Al seleccionarla, el sistema comprueba primero si existen citas vinculadas con el documento del paciente. Si hay alguna, muestra una advertencia con la cantidad de citas e indica que deben eliminarse antes.

Si no existen citas relacionadas, muestra la confirmación con el nombre del paciente. Al confirmar, elimina el registro, guarda el JSON y reconstruye la lista.

### 3.2 Médicos

Las tarjetas de médicos incluyen una acción discreta **×**. El sistema comprueba si el médico tiene citas asociadas y bloquea la operación cuando encuentra registros vinculados. Si no tiene citas, solicita confirmación antes de eliminarlo y actualizar la vista.

### 3.3 Citas

La tabla de citas muestra una acción compacta **×** por fila. La confirmación identifica la cita por paciente, médico y fecha/hora. Cuando se confirma la eliminación, el archivo de citas se actualiza y el listado vuelve a cargarse, conservando el filtro activo.

### 3.4 Actualización del Dashboard

El Dashboard obtiene sus cifras a partir de los registros JSON al mostrarse. Por ello, al volver al Dashboard después de una eliminación, sus totales de pacientes, médicos, citas e ítems pendientes reflejan los datos actuales.

## 4. Relaciones y consistencia

La eliminación de pacientes y médicos **no elimina citas automáticamente**. Si el registro tiene citas asociadas, se cancela su eliminación y se indica al usuario que quite primero esas citas. Esto evita dejar citas huérfanas o borrar información relacionada sin autorización.

- **Paciente–cita:** se usa el documento del paciente guardado en la cita. Para registros antiguos que no tengan ese documento, se utiliza como respaldo el nombre del paciente.
- **Médico–cita:** el formato actual de las citas almacena el nombre del médico, pero no su documento. Por esa razón, la asociación se verifica por nombre completo, sin modificar el formato existente de los JSON.

**Consideración:** como el médico se identifica en las citas por su nombre y no por un identificador único, dos médicos con el mismo nombre completo no se pueden distinguir inequívocamente en los datos actuales. La implementación conserva el formato solicitado; una futura mejora del modelo podría guardar el documento del médico en cada cita.

## 5. Persistencia y manejo de errores

Se mantiene la estructura JSON existente:

- `control_citas_medicas_100_por_ciento_python/archivos/pacientes.json`
- `control_citas_medicas_100_por_ciento_python/archivos/medicos.json`
- `control_citas_medicas_100_por_ciento_python/archivos/citas.json`

La escritura se centraliza en una utilidad que valida la forma de los datos y guarda primero en un archivo temporal dentro del mismo directorio. Una vez completada la escritura, reemplaza el archivo de destino. Así se reduce el riesgo de dejar un JSON parcialmente escrito si ocurre un error durante el guardado.

Si un archivo está malformado o la operación de lectura/escritura falla, la eliminación no se completa silenciosamente: la interfaz informa el problema y permanece abierta.

## 6. Archivos y funciones principales

| Archivo | Responsabilidad |
|---|---|
| `control_citas_medicas_100_por_ciento_python/main.py` | Confirmaciones, acciones de eliminación en tablas y tarjetas, mensajes al usuario y actualización de vistas. |
| `control_citas_medicas_100_por_ciento_python/pacientes.py` | `eliminar_paciente(documento)`: elimina el paciente solo si no tiene citas. |
| `control_citas_medicas_100_por_ciento_python/medicos.py` | `eliminar_medico(documento)`: elimina el médico solo si no tiene citas. |
| `control_citas_medicas_100_por_ciento_python/citas.py` | `eliminar_cita(cita)`, `contar_citas_paciente(...)` y `contar_citas_medico(...)`. |
| `control_citas_medicas_100_por_ciento_python/almacenamiento.py` | Lectura validada de listas JSON y escritura atómica mediante `guardar_json_atomico(...)`. |
| `control_citas_medicas_100_por_ciento_python/README.md` | Documentación de las nuevas funciones. |

## 7. Pruebas realizadas

Las pruebas funcionales se ejecutaron con archivos temporales, para no alterar los datos reales del proyecto:

1. Crear y eliminar un paciente; verificar que desaparece del listado y del JSON.
2. Crear y eliminar un médico; verificar el cambio persistido.
3. Crear y eliminar una cita; comprobar que desaparece del archivo y de la vista.
4. Intentar eliminar un paciente y un médico con citas asociadas; verificar que ambas operaciones se bloquean y que los registros permanecen.
5. Confirmar que, al eliminar primero la cita, se pueden eliminar después el paciente y el médico.
6. Probar los botones **Eliminar** y **Cancelar** del diálogo de confirmación.
7. Verificar la actualización de las listas y del Dashboard después de las eliminaciones.
8. Comprobar que continúan funcionando el filtrado por estado y el marcado de citas como realizadas.
9. Verificar que un archivo JSON inválido no se sobrescribe durante la eliminación.
10. Ejecutar la comprobación de sintaxis y el análisis de problemas de los módulos modificados; no se reportaron errores.

## 8. Resultado

La eliminación quedó integrada en la aplicación de escritorio existente, sin incorporar tecnologías web ni cambiar el formato JSON. Todas las acciones solicitan confirmación, las relaciones impiden borrar pacientes o médicos con citas pendientes de eliminar y las vistas se actualizan al completar una operación.
