import random
from agente_base import Agente

class AgenteAleatorio(Agente):
    def __init__(self, jugador):
        """Inicializa el agente aleatorio con un jugador."""
        super().__init__(jugador)

    def apostar(self):
        """Realiza una apuesta aleatoria dentro del capital disponible del jugador."""
        if self.jugador.capital > 0:
            return random.randint(5000, int(self.jugador.capital/10))  # Apuesta entre 5000 y el 10% del capital
        return 0

    def decidir_accion_primer_turno(self):
        """
        Decide aleatoriamente qué hacer en el primer turno.
        Opciones: 'split', 'doblar', o 'nada'.
        """
        opciones = ['split', 'doblar', 'nada']
        return random.choice(opciones)

    def decidir_accion(self):
        """
        Decide aleatoriamente qué hacer en el turno estándar.
        Opciones: 'terminar_mano', 'stand', 'pedir_carta', 'surrender'.
        """
        
        opciones = ['terminar_mano', 'stand', 'pedir_carta', 'surrender']
        for mano in self.jugador.manos:
            if not mano.bajada:  # Verifica si la mano no ha sido bajada
                jugada = (random.choice(opciones), mano)  # Cambiar a tupla
                print(f"{self.jugador.nombre} ha decidido: {jugada[0]} en la mano {jugada[1].cartas}")
                return [jugada]  # Devuelve una lista de tuplas
        self.termino = True
        return []  # Si no hay manos disponibles, devuelve una lista vacía