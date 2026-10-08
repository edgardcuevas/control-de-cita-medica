import json

import pacientes
import medicos
import citas

def menu():
    print("\n=== Sistema de Control de Citas Médicas ===")
    print("1. Registrar paciente")
    print("2. Registrar médico")
    print("3. Agendar cita")
    print("4. Ver todas las citas")
    print("5. Marcar una cita como hecha")
    print("6. Salir")

while True:
    menu()
    opcion = input("Seleccione una opción: ")

    try:
        if opcion == "1":
            paciente = pacientes.registrar_paciente()
            pacientes.mostrar_paciente(paciente)

        elif opcion == "2":
            medico = medicos.registrar_medico()
            medicos.mostrar_medico(medico)

        elif opcion == "3":
            cita = citas.agendar_cita()
            if cita:
                citas.mostrar_cita(cita)

        elif opcion == "4":
            citas.mostrar_todas_las_citas()

        elif opcion == "5":
            citas.marcar_cita_como_hecha()

        elif opcion == "6":
            print("Saliendo del sistema...")
            break

        else:
            print("Opción inválida, intente de nuevo.")
    except (OSError, json.JSONDecodeError) as error:
        print(f"No se pudo guardar o leer la información: {error}")
