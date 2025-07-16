#!/usr/bin/env python3
"""
generate_dataset.py

Simula rondas de Blackjack con varios agentes y vuelca los datos a CSV.
Aquí usamos un capital grande (1 000 000) y un chunk_size pequeño
para testear rápidamente los volcados sin quedarnos sin fondos.
"""

import logging
from core.player import Jugador
from core.data_collector import DataCollector
from core.casino import Casino
from agents.agente_HiLo import AgenteHiLo
from agents.agente_aleatorio import AgenteAleatorio
from agents.markov import AgenteMarkov_arriesgado, AgenteMarkov_normal

def main():
    # Configurar logging para ver el progreso
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s: %(message)s"
    )

    # DataCollector con chunk_size pequeño para volcar cada 50 registros
    dc = DataCollector(
        filepath="./blackjack_dataset.csv",
        chunk_size=1_000
        
    )

    # Inicializamos cada agente con capital de 1_000_000
    agentes = []
    for cls in (
        AgenteHiLo,
        AgenteAleatorio,
        AgenteMarkov_normal,
        AgenteMarkov_arriesgado
    ):
        jugador = Jugador(nombre=cls.__name__, capital=1_000_000)
        agente = cls(jugador)
        agentes.append(agente)

    # Creamos el casino con 6 barajas y penetración al 75%
    casino = Casino(
        agentes=agentes,
        num_mazos=6,
        zapato=0.75,
        data_collector=dc
    )

    # Número de rondas: puedes ajustar según tu prueba
    n_rondas = 20_000
    logging.info(f"Iniciando simulación de {n_rondas} rondas")
    casino.jugar_partida(n_rondas)

    logging.info("Simulación completada. Archivo: 'blackjack_dataset.csv'")

if __name__ == "__main__":
    main()
