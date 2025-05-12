import random
from agente_base import Agente

class AgenteAleatorio(Agente):
    def __init__(self, jugador):
        """Inicializa el agente aleatorio con un jugador."""
        super().__init__(jugador)

    def apostar(self):
        """Realiza una apuesta aleatoria dentro del capital disponible del jugador."""
        if self.jugador.capital > 0:
            return random.randint(5000, self.jugador.capital)
        return 0

    def decidir_accion_primer_turno(self, mano):
        """
        Decide aleatoriamente qué hacer en el primer turno.
        Opciones: 'split', 'doblar', o 'nada'.
        """
        opciones = ['split', 'doblar', 'nada']
        return random.choice(opciones)

    def decidir_accion(self, mano):
        """
        Decide aleatoriamente qué hacer en el turno estándar.
        Opciones: 'terminar_mano', 'stand', 'pedir_carta', 'surrender'.
        """
        opciones = ['terminar_mano', 'stand', 'pedir_carta', 'surrender']
        return random.choice(opciones)