from .agente_base import Agente
from core.acciones import Accion
from core.player import Jugador, Mano
from core.cartas import Carta, Rango
import numpy as np


class AgenteMarkov(Agente):
    """
    Agente que implementa la política de juego óptima basada en MDP
    """
    def __init__(self, jugador: Jugador, num_mazos: int = 8):
        super().__init__(jugador)
        self.num_mazos = num_mazos
        
        # Array que contiene el número de cartas que han salido
        # [As, 2, 3, 4, 5, 6, 7, 8, 9, 10/J/Q/K]
        self.cartas_vistas = np.zeros(10, dtype=int)
        
    def observar_carta(self, carta: Carta):
        """
        Actualiza el array de cartas vistas
        """
        if carta.rango == Rango.AS:
            self.cartas_vistas[0] += 1
        elif carta.rango.valor >= 2 and carta.rango.valor <= 9:
            self.cartas_vistas[carta.rango.valor - 1] += 1
        else:  # 10, J, Q, K (todos tienen valor 10)
            self.cartas_vistas[9] += 1
    
    def resetear_conteo(self):
        """
        Resetea el array de cartas vistas (cuando se baraja el mazo)
        """
        self.cartas_vistas = np.zeros(10, dtype=int)
        
    def decidir_apuesta(self) -> int:
        """
        Decide la apuesta óptima
        """

    
    def decidir_accion(self, mano: Mano, carta_dealer: Carta) -> Accion:
        """
        Decide la acción óptima usando la política MDP
        """


