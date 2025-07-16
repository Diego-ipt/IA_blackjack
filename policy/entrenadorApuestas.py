import numpy as np
from tqdm import tqdm
from datetime import datetime
import os
from collections import deque
import pandas as pd

from agents.markovPoliticaApuestas import AgenteMarkov_PoliticaApuestas
from core.casino import Casino
from core.player import Jugador
from guardar_datos import guardar_historial_csv  # Importa la función para guardar CSV


class EntrenadorApuestas:
    """
    Entrenador especializado para la política de apuestas de AgenteMarkov_PoliticaApuestas.
    Incluye evaluación antes y después del entrenamiento y persistencia de pesos.
    """

    def __init__(self, capital_inicial=10000, num_episodios=10, rondas_por_episodio=5):
        self.capital_inicial = capital_inicial
        self.num_episodios = num_episodios
        self.rondas_por_episodio = rondas_por_episodio

        # Inicializar agente y casino
        self.jugador = Jugador("Markov_PG_Train", capital_inicial)
        self.agente = AgenteMarkov_PoliticaApuestas(self.jugador, num_mazos=4)
        self.casino = Casino([self.agente], num_mazos=4)

        # Historial de entrenamiento
        self.historial = {
            'episodio': [],
            'capital': [],
            'apuesta_promedio': [],
            'entropia': [],
            'timestamp': datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        }

    def ejecutar_entrenamiento(self):
        """Loop principal de entrenamiento con evaluación previa y posterior"""
        print(f" Evaluando agente antes del entrenamiento...")
        self.evaluar_agente(nombre="pre_entrenamiento")

        print(f" Iniciando entrenamiento ({self.num_episodios} episodios)")
        for episodio in tqdm(range(self.num_episodios), desc="Entrenando política de apuestas"):
            self._resetear_episodio()
            self.casino.jugar_partida(self.rondas_por_episodio)
            self.agente.pg_apuestas.entrenar()
            self._registrar_metricas(episodio)

        print(f"\n Entrenamiento finalizado. Evaluando agente...")
        self.evaluar_agente(nombre="post_entrenamiento")

        self._guardar_resultados_csv()
        self._guardar_pesos()
        self._mostrar_resumen()
        self._mostrar_resultados_finales()

    def _resetear_episodio(self):
        """Prepara el agente y el casino para un nuevo episodio"""
        self.jugador.capital = self.capital_inicial
        self.agente.resetear_conteo(reset_completo=True)

        # Mantener entropía constante para conservar exploración
        self.agente.pg_apuestas.entropia_peso = 0.01

    def _registrar_metricas(self, episodio):
        """Captura métricas importantes del episodio"""
        self.historial['episodio'].append(episodio)
        self.historial['capital'].append(self.jugador.capital)
        apuesta_promedio = 0
        manos_con_apuesta = [mano.apuesta for mano in self.jugador.manos if hasattr(mano, 'apuesta')]
        if manos_con_apuesta:
            apuesta_promedio = np.mean(manos_con_apuesta)
        self.historial['apuesta_promedio'].append(apuesta_promedio)
        self.historial['entropia'].append(self.agente.pg_apuestas.entropia_peso)

    def _guardar_resultados_csv(self):
        """Guarda el progreso del entrenamiento en un archivo CSV usando pandas"""
        filename = f"entrenamiento_apuestas_{datetime.now().strftime('%Y%m%d_%H%M%S')}.csv"
        guardar_historial_csv(self.historial, filename)
        print(f"\n💾 Resultados del entrenamiento guardados en '{filename}'")



    def _guardar_pesos(self):
        """Guarda los pesos en una carpeta 'pesos_guardados' en el directorio raíz del proyecto."""
        raiz_proyecto = os.path.abspath(os.path.join(os.path.dirname(__file__), '..'))

        # Ruta completa a la carpeta de pesos dentro del proyecto
        carpeta_pesos = os.path.join(raiz_proyecto, 'pesos_guardados')
        os.makedirs(carpeta_pesos, exist_ok=True)  # Crea la carpeta si no existe

        # Nombre del archivo
        pesos_file = os.path.join(carpeta_pesos,f"pesos_aprendidos_{datetime.now().strftime('%Y%m%d_%H%M%S')}.json")

        # Guardar pesos usando el método de la política
        self.agente.pg_apuestas.guardar_pesos(pesos_file)
        print(f"📦 Pesos guardados en: {pesos_file}")

    def evaluar_agente(self, rondas=5, nombre="evaluacion"):
        """Ejecuta una simulación completa sin entrenamiento"""
        self.jugador.capital = self.capital_inicial
        self.agente.pg_apuestas.capital_actual = self.capital_inicial
        self.casino.jugar_partida(rondas)
        capital_final = self.jugador.capital
        roi = (capital_final - self.capital_inicial) / self.capital_inicial * 100
        print(f"🧪 Evaluación {nombre}: Capital final = ${capital_final:,.2f} (ROI: {roi:.2f}%)")

    def _mostrar_resumen(self):
        """Muestra un resumen estadístico del entrenamiento"""
        capitales = np.array(self.historial['capital'])
        roi = (capitales[-1] - self.capital_inicial) / self.capital_inicial * 100

        print("\n Resumen Final del Entrenamiento:")
        print(f"- Capital inicial: ${self.capital_inicial:,.2f}")
        print(f"- Capital final: ${capitales[-1]:,.2f} (ROI: {roi:.2f}%)")
        print(f"- Máximo alcanzado: ${max(capitales):,.2f}")
        print(f"- Apuesta promedio: ${np.mean(self.historial['apuesta_promedio']):,.2f}")
        print(f"- Entropía final: {self.historial['entropia'][-1]:.6f}")

    def _mostrar_resultados_finales(self):
        print("\n Resultados acumulados:")
        print(f"- Rondas ganadas: {self.agente.contador_resultados['ganadas']}")
        print(f"- Rondas perdidas: {self.agente.contador_resultados['perdidas']}")
        print(f"- Rondas empatadas: {self.agente.contador_resultados['empatadas']}")
        total = sum(self.agente.contador_resultados.values())
        if total > 0:
            print(f"- Porcentaje de victorias: {self.agente.contador_resultados['ganadas'] / total * 100:.2f}%")


# Ejecutar si se llama directamente
if __name__ == '__main__':
    entrenador = EntrenadorApuestas(
        capital_inicial=10000,
        num_episodios=10,
        rondas_por_episodio=5
    )
    entrenador.ejecutar_entrenamiento()
