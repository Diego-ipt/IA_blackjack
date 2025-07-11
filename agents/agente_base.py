from abc import ABC, abstractmethod
from ..core.player import Jugador, Mano
from ..core.cartas import Carta
from ..core.acciones import Accion

class Agente(ABC):
    def __init__(self, jugador: Jugador):
        """
        Inicializa el agente con un jugador.
        """

        self.jugador = jugador


    @abstractmethod
    def decidir_apuesta(self) -> int:
        """
        Elige cuanto apostar al inicio de una ronda.
        """

    @abstractmethod
    def decidir_accion(self, mano: Mano, carta_dealer: Carta) -> Accion:
        """
        Decide la jugada a realizar para una mano especifica.
        :param mano: Mano del jugador:
        :param carta_dealer: Carta visible del dealer.
        :return: Accion del Enum Accion.
        """

    def observar_carta(self, carta: Carta):
        """
        Para agentes contadores de cartas, el resto lo puede ignorar.
        """
        pass