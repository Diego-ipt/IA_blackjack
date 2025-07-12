import random
from .agente_base import Agente
from core.acciones import Accion
from core.player import Jugador, Mano
from core.cartas import Carta

class AgenteAleatorio(Agente):
    def __init__(self, jugador):
        """Inicializa el agente aleatorio con un jugador."""
        super().__init__(jugador)

    def decidir_apuesta(self) -> int:
        """
        Realiza una apuesta aleatoria dentro del capital disponible del jugador.
        """

        # Dolares, para no tener tantos ceros en el numero
        apuesta_min = 5
        if self.jugador.capital < apuesta_min:
            return 0

        # Limite de apuesta es el 10% del capital del jugador
        apuesta_max = int(self.jugador.capital * 0.1)

        if apuesta_max < apuesta_min:
            return apuesta_min

        apuesta = random.randint(apuesta_min, apuesta_max)  # Apuesta entre 5000 y el 10% del capital
        return apuesta

    def decidir_accion(self, mano: Mano, carta_dealer: Carta):
        """
        Decide aleatoriamente qué hacer en el turno estándar.
        """
        # Del enum Accion (Pedir, Plantarse, Doblar, Dividir, Rendirse)
        opciones = list(Accion)
        return random.choice(opciones)
