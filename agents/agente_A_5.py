import random
from .agente_base import Agente
from core.acciones import Accion
from core.player import Jugador, Mano
from core.cartas import Carta

class AgenteAleatorio_5(Agente):
    def __init__(self, jugador):
        """Inicializa el agente aleatorio con un jugador."""
        super().__init__(jugador)

    def decidir_apuesta(self) -> int:
        """
        Realiza una apuesta estándar del 5% del capital del jugador.
        """

        return int(5)

    def decidir_accion(self, mano: Mano, carta_dealer: Carta):
        """
        Decide aleatoriamente qué hacer en el turno estándar.
        """
        # Del enum Accion (Pedir, Plantarse, Doblar, Dividir, Rendirse)
        opciones = list(Accion)
        return random.choice(opciones)
