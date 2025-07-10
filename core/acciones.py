from enum import Enum, auto

class Accion(Enum):
    """
    Enum que representa las acciones que un jugador puede realizar en el juego de Blackjack.
    Cada acción corresponde a una jugada específica que el jugador puede tomar durante su turno.
    Apostar no es una acción de juego, sino una acción previa al juego.
    """
    PEDIR = auto() # Pedir una carta
    PLANTARSE = auto() # No pedir más cartas
    DOBLAR = auto() # Doblar la apuesta y pedir una sola carta
    ABRIR = auto() # Abrir una mano (split), solo si las dos primeras cartas son del mismo rango
    RENDIRSE = auto() # Rendirse, perder la mitad de la apuesta
