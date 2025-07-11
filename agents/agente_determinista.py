import random
from .agente_base import Agente
from core.acciones import Accion
from core.player import Jugador, Mano
from core.cartas import Carta

class AgenteDeterminista(Agente):
    def __init__(self, jugador, guion_apuestas: list[int], guion_acciones: list[Accion]):
        """
        Agente determinista que sigue un guion predefinido de apuestas y acciones.
        Para realizar testeos y simulaciones de partidas con un comportamiento predecible.
        """
        super().__init__(jugador)
        self.guion_apuestas = guion_apuestas
        self.guion_acciones = guion_acciones
        self.indice_apuesta_actual = 0
        self.indice_accion_actual = 0

    def decidir_apuesta(self) -> int:
        if self.indice_apuesta_actual < len(self.guion_apuestas):
            apuesta = self.guion_apuestas[self.indice_apuesta_actual]
            self.indice_apuesta_actual += 1
            return apuesta
        else:
            return 0

    def decidir_accion(self, mano: Mano, carta_dealer: Carta):

        # Del enum Accion (Pedir, Plantarse, Doblar, Dividir, Rendirse)
        if self.indice_accion_actual < len(self.guion_acciones):
            accion = self.guion_acciones[self.indice_accion_actual]
            self.indice_accion_actual += 1
            return accion
        else:
            return Accion.PLANTARSE

    def reset(self):
        """
        Resetea el agente a su estado inicial, reiniciando los indices de guion.
        """
        self.indice_apuesta_actual = 0
        self.indice_accion_actual = 0

