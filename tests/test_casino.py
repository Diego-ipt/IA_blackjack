import pytest
from core.casino import Casino
from core.player import Jugador
from agents.agente_aleatorio import AgenteAleatorio

def test_simulacion_blackjack_varios_jugadores():
    # Crear varios jugadores con capital inicial
    jugadores = [Jugador(f"Jugador{i+1}", 100) for i in range(3)]
    agentes = [AgenteAleatorio(jugador) for jugador in jugadores]
    casino = Casino(agentes, num_mazos=2, zapato=0.7)
    # Simular 5 rondas
    casino.jugar_partida(num_rondas=5)
    # Verificar que el capital de los jugadores cambió
    for jugador in jugadores:
        assert jugador.capital != 100

def test_simulacion_blackjack_jugador_sin_capital():
    jugador = Jugador("SinDinero", 0)
    agente = AgenteAleatorio(jugador)
    casino = Casino([agente], num_mazos=1, zapato=0.7)
    casino.jugar_partida(num_rondas=3)
    # El jugador no puede apostar, su capital sigue en 0
    assert jugador.capital == 0

def test_simulacion_blackjack_un_jugador():
    jugador = Jugador("Solo", 50)
    agente = AgenteAleatorio(jugador)
    casino = Casino([agente], num_mazos=1, zapato=0.7)
    casino.jugar_partida(num_rondas=3)
    # El capital puede variar
    assert jugador.capital >= 0
