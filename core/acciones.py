from enum import Enum, auto

class Accion(Enum):
    """
    Enum que representa las acciones que un jugador puede realizar en el juego de Blackjack.
    """
    PEDIR = auto() # Pedir una carta
    PLANTARSE = auto() # No pedir más cartas
    DOBLAR = auto() # Doblar la apuesta y pedir una sola carta
    DIVIDIR = auto() # Abrir una mano (split), solo si las dos primeras cartas son del mismo rango
    RENDIRSE = auto() # Rendirse, perder la mitad de la apuesta
