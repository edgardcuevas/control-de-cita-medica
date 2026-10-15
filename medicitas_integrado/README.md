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

## Almacenamiento
Los pacientes, médicos y citas siguen almacenándose en los archivos JSON existentes de la carpeta `archivos/`. No se necesita migrar esos datos.

## Nota sobre recuperación de contraseña
La opción «Olvidé mi contraseña» muestra un aviso informativo. La recuperación real por correo requiere configurar un servicio de correo o un procedimiento administrativo seguro; no se simula un envío de correo.
