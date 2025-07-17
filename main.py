import logging

from core.casino import Casino
from core.player import Jugador
from core.data_collector import RoundDataCollector
from agents.agente_basico import AgenteBasico
import os
import datetime

# Configurar el logger para mostrar mensajes de depuración
#logging.basicConfig(level=logging.DEBUG)

# Parametros de simulacion
NUM_RONDAS = 5000
CAPITAL_INICIAL = 90000000

# Configurar agente y su jugador
nombre_agente = "AgenteBasico"
jugador = Jugador(nombre=nombre_agente, capital=CAPITAL_INICIAL)
agente = AgenteBasico(jugador)

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
data_collector = RoundDataCollector(filepath=ruta_archivo)

# 3. Crear el Casino e inyectar el DataCollector
casino = Casino(agentes=[agente], data_collector=data_collector, num_mazos=4, zapato=0.75)

# Simulacion de agente
try:
    # No usamos casino.jugar_partida() para poder mostrar el progreso
    casino.jugar_partida(NUM_RONDAS)

finally:
    # Cerrar el DataCollector para guardar el ultimo lote
    print("Simulación terminada. Guardando datos restantes...")
    data_collector.close()
    print("Datos guardados exitosamente.")