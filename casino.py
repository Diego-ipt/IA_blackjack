from random import shuffle
from player import Jugador, Mano

class Casino:
    def __init__(self, jugadores, dealer_nombre="Dealer", max_stands=3):
        """Inicializa el juego con una lista de jugadores y un dealer."""
        self.jugadores = jugadores
        self.stand_counter = [0] * len(jugadores)  # Contador de manos plantadas por jugador
        self.bajadas = [0] * len(jugadores)  # Contador jugadores bajados
        self.max_stands = max_stands
        # un jugador no puede plantarse mas de "max_stands" veces
        self.dealer = Jugador(dealer_nombre)
        self.baraja = []  # Baraja de cartas
        self.fin_ronda = False  # Indica si el juego ha terminado

    def reset_baraja(self):
        """Crea y mezcla una baraja estándar de Blackjack."""
        baraja = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K'] * 4
        shuffle(baraja)
        self.baraja = baraja

    def repartir_cartas(self):
        """
        Reparte dos cartas a cada jugador y al dealer
        También establece la apuesta inicial de cada jugador.
        """


    def first_turn(self, jugador, jugada=None):
        """
        Gestiona el primer turno de los jugadores.
        solo se permite: split y doblar
        """


    def turno_jugador(self, jugador, jugadas):
        """
        Gestiona los turnos estandar de un jugador
        solo se permite: terminar_mano, stand, pedir_carta y surrender
        jugadas contiene [tipo_jugada, mano]
        """
        for jugada in jugadas:
            tipo_jugada, mano = jugada


    def turno_dealer(self):
        """Gestiona el turno del dealer."""
        while self.dealer.manos[0].valor_total() < 17:
            self.dealer.manos[0].agregar_carta(self.baraja.pop())

    def determinar_ganadores(self):
        """Determina los ganadores de la ronda y les entrega las ganancias."""


    def jugar_ronda(self):
        """Juega una ronda completa de Blackjack."""
        self.reset_baraja()
        self.repartir_cartas()
        for jugador in self.jugadores:
            self.first_turn(jugador)
        while self.fin_ronda==False:
            for jugador in self.jugadores:
                self.turno_jugador(jugador)
        self.turno_dealer()
        self.determinar_ganadores()
        # Reinicia las manos para la próxima ronda
        for jugador in self.jugadores:
            jugador.reset_manos()
        self.dealer.reset_manos()
