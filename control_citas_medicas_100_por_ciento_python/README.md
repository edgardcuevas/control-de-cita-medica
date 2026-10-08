# Control de Citas Médicas — 100% Python

Esta es la versión nueva del proyecto, construida directamente sobre el sistema que se entregó originalmente y sobre la maqueta visual mostrada.

## Importante

**No contiene HTML, CSS, JavaScript, Flask, React, Vite ni Node.js.**

La interfaz gráfica está hecha con **Tkinter**, que forma parte de Python.

El proyecto conserva el enfoque de:
- `main.py`
- `pacientes.py`
- `medicos.py`
- `citas.py`
- carpeta `archivos/` con JSON

La estructura original del sistema y sus datos se mantuvieron como base. La maqueta de Figma se tradujo a una interfaz de escritorio: barra lateral, dashboard, tarjetas, tablas, formularios y detalle de cita.

## Ejecutar

No necesitas instalar paquetes externos si tienes Python 3 instalado:

```bash
python main.py
```

En Windows también puedes ejecutar:

```text
INICIAR.bat
```

## Funciones

- Dashboard
- Registrar paciente
- Registrar médico
- Agendar cita
- Ver todas las citas
- Filtrar por estado
- Ver detalle de una cita
- Marcar cita como realizada
- Persistencia en JSON

## Tecnologías

- Python
- Tkinter
- ttk
- JSON

No se usa HTML para ninguna pantalla.
