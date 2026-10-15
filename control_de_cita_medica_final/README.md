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

## Almacenamiento
Los pacientes, médicos y citas siguen almacenándose en los archivos JSON existentes de la carpeta `archivos/`. No se necesita migrar esos datos.

## Nota sobre recuperación de contraseña
La opción «Olvidé mi contraseña» muestra un aviso informativo. La recuperación real por correo requiere configurar un servicio de correo o un procedimiento administrativo seguro; no se simula un envío de correo.
