from random import shuffle
from player import Jugador, Mano


class Agente:
    def __init__(self, Jugador):
        """Inicializa el agente con un jugador."""
        self.jugador = Jugador
        self.veces_plantado = 0  # Contador de veces que el jugador se ha plantado en la ronda
        self.termino = False  # Indica si ya ha terminado todas las manos
        self.banca_rota = False  # Indica si la banca está rota

    def apostar(self):
        """
        Método elige cuanto apostar.
        Este método debe ser implementado por las subclases.
        """
        raise NotImplementedError("Este método debe ser implementado por una subclase.")
    
    def decidir_accion_primer_turno(self):
        """
        Método que decide la acción a tomar en el primer turno.
        Este método debe ser implementado por las subclases.
        solo se permite: split y doblar.
        devuelve una jugada por mano.
        """
        raise NotImplementedError("Este método debe ser implementado por una subclase.")

    def decidir_accion(self):
        """
        Método que decide la acción a tomar en el turno estándar.
        Este método debe ser implementado por las subclases.
        solo se permite: terminar_mano, stand, pedir_carta y surrender
        jugadas contiene [tipo_jugada, mano]
        """
        raise NotImplementedError("Este método debe ser implementado por una subclase.")	