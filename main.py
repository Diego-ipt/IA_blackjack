import logging

from core.casino import Casino
from core.player import Jugador
from core.data_collector import DataCollector
from agents.agente_aleatorio import AgenteAleatorio
import os
import datetime

# Configurar el logger para mostrar mensajes de depuración
#logging.basicConfig(level=logging.DEBUG)

# Parametros de simulacion
NUM_RONDAS = 1000
CAPITAL_INICIAL = 100_000

# Configurar agente y su jugador
nombre_agente = "AgenteAleatorio1"
jugador = Jugador(nombre=nombre_agente, capital=CAPITAL_INICIAL)
agente = AgenteAleatorio(jugador)

#  Configurar la ruta del archivo CSV
timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
nombre_archivo = f"{nombre_agente}_{timestamp}.csv"
# Carpeta por tipo de agente
ruta_carpeta = os.path.join('results', nombre_agente)
ruta_archivo = os.path.join(ruta_carpeta, nombre_archivo)

print(f"Iniciando simulación para '{nombre_agente}'...")
print(f"Los datos se guardaran en: {ruta_archivo}")

# 2. Inicializar el DataCollector con la ruta del archivo
# Escribira en el disco cada 10,000 registros
data_collector = DataCollector(filepath=ruta_archivo, chunk_size=10000)

# 3. Crear el Casino e inyectar el DataCollector
casino = Casino(agentes=[agente], data_collector=data_collector)

# Simulacion de agente
try:
    # No usamos casino.jugar_partida() para poder mostrar el progreso
    for i in range(NUM_RONDAS):
        if (i + 1) % 100 == 0:
            print(f"Progreso: Ronda {i + 1} / {NUM_RONDAS}")
        casino._jugar_ronda()

finally:
    # Cerrar el DataCollector para guardar el ultimo lote
    print("Simulación terminada. Guardando datos restantes...")
    data_collector.close()
    print("Datos guardados exitosamente.")