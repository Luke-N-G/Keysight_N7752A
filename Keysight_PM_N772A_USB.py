# -*- coding: utf-8 -*-
"""
Created on Thu Oct  2 14:38:50 2025

@author: d/dt Lucas
"""

import pyvisa
import numpy as np
import time
import datetime
import matplotlib.pyplot as plt

# -------------------------
# Configuración instrumento
# -------------------------
gateway_ip = "10.73.97.39"
gpib_address = 20
vendor = 'agilent'
visa_address = 'USB0::0x0957::0x3718::MY49A01208::INSTR'

# Printeamos todos los recursos
rm = pyvisa.ResourceManager()
print("Instrumentos disponibles:", rm.list_resources())

try:
    # Abrir conexión
    N7752A = rm.open_resource(visa_address)
    print("Conexión establecida.")
    
    # Limpiamos cache
    N7752A.clear()
    print("IDN:", N7752A.query("*IDN?"))

    # -------------------------
    # Configuración Power Meter
    # -------------------------
    PM_SENSOR = 5   # Num. de sensor
    CHAN = 1        # Canal de sensor
    AUTO_RANGE = 1  # Rango (1 automatico, 0 manual)
    UNIT = 1        # Unidad de medida (1 W)
    ATIME = 0.1     # Tiempo de integración
    CONTINUOUS = 0  # Medición continua (1) o trigger manual (0)

    # Escribimos la configuración al instrumento
    N7752A.write(f'SENS{PM_SENSOR}:CHAN{CHAN}:POW:RANGE:AUTO {AUTO_RANGE}')
    N7752A.write(f'SENS{PM_SENSOR}:CHAN{CHAN}:POW:UNIT {UNIT}')
    N7752A.write(f'SENS{PM_SENSOR}:CHAN{CHAN}:POW:ATIME {ATIME}')
    N7752A.write(f'INIT{CHAN}:CHAN{CHAN}:CONT {CONTINUOUS}')

    # -------------------
    # Preparar guardado
    # -------------------
    intervalo  = 0.1  # Segundos entre muestras (no cuenta el tiempo de integración)
    batch_size = 10   # Cantidad de muestras que se guardan de a bloques

    # Armado de archivo de guardado
    fecha_hora = datetime.datetime.now().strftime("%Y%m%d_%H%M")
    nombre_archivo = f"{fecha_hora}_burbuja.txt"
    file = open(nombre_archivo, "w")
    file.write("tiempo_s\thora\tpotencia_mW\n")

    # -------------------
    # Preparar gráfico
    # -------------------
    plot_update = 1  # Cada cuantas muestras se actualiza el plot
    plt.style.use('ggplot')
    plt.ion()
    fig, ax = plt.subplots()
    tiempos = []
    potencias = []
    line, = ax.plot([], [], '-o', markersize=2)
    ax.set_xlabel("Tiempo [s]")
    ax.set_ylabel("Potencia [mW]")
    

    start_time = time.time()
    running = True
    count = 0

    # -------------------
    # Loop de medición
    # -------------------
    print("Presiona Ctrl-C para detener el programa.")
    while running:
        try:
            # Trigger y lectura
            N7752A.write('INIT1:CHAN1:IMM')
            pwr_mW = float(N7752A.query(f'READ{PM_SENSOR}:CHAN1:POW?')) * 1e3  # Watts -> mW

            # Guardar tiempo y potencia
            t = time.time() - start_time
            hora = datetime.datetime.now().strftime("%H:%M:%S")
            tiempos.append(t)
            potencias.append(pwr_mW)

            # Escribir en archivo
            file.write(f"{t:.2f}\t{hora}\t{pwr_mW:.6f}\n")

            print(f"{hora} - {pwr_mW:.6f} mW")

            # Actualizar gráfico cada 'plot_update' mediciones
            if count % plot_update == 0:
                line.set_xdata(tiempos)
                line.set_ydata(potencias)
                ax.relim()
                ax.autoscale_view()
                fig.canvas.draw_idle()
                fig.canvas.flush_events()
                
            count += 1
            time.sleep(intervalo)

        except KeyboardInterrupt:
            print("\nDetenido por el usuario.")
            running = False
        except Exception as e:
            print("Error:", e)

except Exception as e:
    print("Error:", e)
finally:
    file.close()
    N7752A.close()
    rm.close()
    print("Conexión cerrada.")