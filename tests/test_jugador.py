import pytest
from core.cartas import Carta, Rango, Palo
from core.player import Mano, Jugador

# Tests para la clase Mano y Jugador
# Hechos por copilot (GPT-4.1)

def test_mano_valor_total_sin_as():
    cartas = [Carta(Palo.PICAS, Rango.DIEZ), Carta(Palo.CORAZONES, Rango.CINCO)]
    mano = Mano(cartas)
    assert mano.valor_total == 15

def test_mano_valor_total_con_as():
    cartas = [Carta(Palo.PICAS, Rango.AS), Carta(Palo.CORAZONES, Rango.OCHO)]
    mano = Mano(cartas)
    assert mano.valor_total == 19

def test_mano_valor_total_as_ajustado():
    cartas = [Carta(Palo.PICAS, Rango.AS), Carta(Palo.CORAZONES, Rango.OCHO), Carta(Palo.DIAMANTES, Rango.CINCO)]
    mano = Mano(cartas)
    assert mano.valor_total == 14  # As cuenta como 1

def test_mano_es_blanda():
    mano = Mano([Carta(Palo.PICAS, Rango.AS), Carta(Palo.CORAZONES, Rango.SEIS)])
    print(mano.valor_total)
    assert mano.es_blanda
    mano = Mano([Carta(Palo.PICAS, Rango.DIEZ), Carta(Palo.CORAZONES, Rango.SEIS)])
    print(mano.valor_total)
    assert not mano.es_blanda

def test_mano_agregar_carta_y_turno_terminado():
    mano = Mano([Carta(Palo.PICAS, Rango.DIEZ), Carta(Palo.CORAZONES, Rango.OCHO)])
    mano.agregar_carta(Carta(Palo.DIAMANTES, Rango.CUATRO))
    assert mano.valor_total == 22
    assert mano.turno_terminado

def test_jugador_apostar_y_reset():
    jugador = Jugador("Alice", 100)
    assert jugador.apostar(50)
    assert jugador.capital == 50
    assert len(jugador.manos) == 1
    jugador.reset_manos()
    assert len(jugador.manos) == 0

def test_jugador_apostar_invalido():
    jugador = Jugador("Bob", 10)
    assert not jugador.apostar(0)
    assert not jugador.apostar(20)
    assert jugador.capital == 10

def test_jugador_pedir_carta():
    jugador = Jugador("Carol", 100)
    jugador.apostar(10)
    mano = jugador.manos[0]
    jugador.pedir_carta(mano, Carta(Palo.PICAS, Rango.CINCO))
    assert len(mano.cartas) == 1

def test_jugador_dividir_mano():
    jugador = Jugador("Dan", 100)
    jugador.apostar(10)
    mano = jugador.manos[0]
    mano.cartas = [Carta(Palo.PICAS, Rango.OCHO), Carta(Palo.CORAZONES, Rango.OCHO)]
    assert jugador.dividir_mano(mano)
    assert len(jugador.manos) == 2
    assert jugador.capital == 80

def test_jugador_dividir_mano_invalido():
    jugador = Jugador("Eve", 10)
    jugador.apostar(5)
    mano = jugador.manos[0]
    mano.cartas = [Carta(Palo.PICAS, Rango.OCHO), Carta(Palo.CORAZONES, Rango.NUEVE)]
    assert not jugador.dividir_mano(mano)
    mano.cartas = [Carta(Palo.PICAS, Rango.OCHO)]
    assert not jugador.dividir_mano(mano)

def test_jugador_doblar_apuesta():
    jugador = Jugador("Frank", 100)
    jugador.apostar(20)
    mano = jugador.manos[0]
    assert jugador.doblar_apuesta(mano)
    assert jugador.capital == 60
    assert mano.apuesta == 40

def test_jugador_doblar_apuesta_invalido():
    jugador = Jugador("Grace", 10)
    jugador.apostar(10)
    mano = jugador.manos[0]
    assert not jugador.doblar_apuesta(mano)
    assert jugador.capital == 0
    assert mano.apuesta == 10

def test_jugador_rendirse():
    jugador = Jugador("Heidi", 100)
    jugador.apostar(20)
    mano = jugador.manos[0]
    assert jugador.rendirse(mano)
    assert jugador.capital == 90  # Recupera la mitad de la apuesta
    assert len(jugador.manos) == 0

def test_jugador_rendirse_invalido():
    jugador = Jugador("Ivan", 100)
    mano = Mano([])
    assert not jugador.rendirse(mano)

