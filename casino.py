from random import shuffle
from player import Jugador, Mano
from agente_base import Agente

class Casino:
    def __init__(self, agentes, dealer_nombre="Dealer", max_stands=3, min_apuesta=5000):
        """Inicializa el juego con una lista de jugadores y un dealer."""
        self.agentes = agentes
        self.max_stands = max_stands
        # un jugador no puede plantarse mas de "max_stands" veces
        self.dealer = Jugador(dealer_nombre) # Dealer
        self.baraja = []  # Baraja de cartas
        self.min_apuesta = min_apuesta  # Apuesta mínima para cada jugador

    def reset_baraja(self):
        """Crea y mezcla una baraja estándar de Blackjack."""
        baraja = ['A', '2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K'] * 4
        shuffle(baraja)
        self.baraja = baraja

    def repartir_cartas(self):
        """
        Reparte dos cartas al dealer y luego a cada jugador.
        Cada jugador recibe dos cartas y el dealer recibe una carta visible y una oculta.
        También establece la apuesta inicial de cada jugador.
        """
        # Reparte dos cartas al dealer
        self.dealer.apostar(0, Mano([self.baraja.pop(), self.baraja.pop()]))
        # Reparte dos cartas a cada jugador
        for agente in self.agentes:
            if agente.banca_rota:
                print(f"{agente.jugador.nombre} no puede jugar, la banca está rota.")
                agente.termino = True
                self.fin_ronda_per_mano -= 1
            else:
                # Establece la apuesta inicial del jugador
                apuesta = agente.apostar()
                if apuesta > self.min_apuesta:
                    agente.jugador.apostar(apuesta, Mano([self.baraja.pop(), self.baraja.pop()]))
                else:
                    print(f"{agente.jugador.nombre} no tiene suficiente capital para apostar. Apuesta mínima: {self.min_apuesta}")
                    agente.termino = True  # Marca al jugador como que no puede jugar
                    self.fin_ronda_per_mano -= 1

    def first_turn(self, agente):
        """
        Gestiona el primer turno de los agentes.
        solo se permite: split y doblar
        """
        jugada=agente.decidir_accion_primer_turno()
        if jugada == 'split':
            if agente.jugador.split(agente.jugador.manos[0]):
                carta = self.baraja.pop()
                agente.jugador.pedir_carta(agente.jugador.manos[0], carta)
                carta = self.baraja.pop()
                agente.jugador.pedir_carta(agente.jugador.manos[1], carta)
        elif jugada == 'doblar':
            carta = self.baraja.pop()
            if agente.jugador.doblar(agente.jugador.manos[0], carta):
                agente.termino = True  # Marca al jugador que ya termino de jugar
            else:                
                print(f"{agente.jugador.nombre} no puede doblar, no tiene capital suficiente.")
                self.baraja.append(carta)  # Devuelve la carta a la baraja
        elif jugada == 'nada':
            pass
        else:
            print(f"Acción no válida: {jugada}")


    def turno_jugador(self, agente):
        """
        Gestiona los turnos estandar de un agente
        solo se permite: terminar_mano, stand, pedir_carta y surrender
        jugadas contiene [tipo_jugada, mano]
        """
        jugadas = agente.decidir_accion()
        for jugada in jugadas:
            tipo_jugada, mano = jugada
            if tipo_jugada == 'terminar_mano':
                agente.jugador.terminar_mano(mano)
            elif tipo_jugada == 'stand':
                if agente.veces_plantado >= self.max_stands:
                    print(f"{agente.jugador.nombre} ha alcanzado el máximo de plantadas.")
                    agente.jugador.terminar_mano(mano)
                else:
                    agente.veces_plantado += 1
            elif tipo_jugada == 'pedir_carta':
                carta = self.baraja.pop()
                agente.jugador.pedir_carta(mano, carta)
            elif tipo_jugada == 'surrender':
                agente.jugador.surrender(mano)

        # Check if all hands of the agent are finished
        if not agente.jugador.manos or all(m.bajada for m in agente.jugador.manos):
            agente.termino = True

    def turno_dealer(self):
        """Gestiona el turno del dealer."""
        while self.dealer.manos[0].valor_total() < 17:
            self.dealer.manos[0].agregar_carta(self.baraja.pop())

    def determinar_ganadores(self):
        """
        Determina los ganadores de la ronda y les entrega las ganancias.
        solo se necesita revisar si la mano gana al dealer.
        """
        if self.dealer.manos[0].valor_total() > 21:
            print(f"El dealer ha perdido con la mano {self.dealer.manos[0].cartas}.")
            for agente in self.agentes:
                for mano in agente.jugador.manos:
                    if mano.valor_total() <= 21:
                        print(f"{agente.jugador.nombre} ha ganado con la mano {mano.cartas}.")
                        agente.jugador.capital += mano.apuesta * 2
                    else: #empate
                        print(f"{agente.jugador.nombre} ha empatado con la mano {mano.cartas}.")
                        agente.jugador.capital += mano.apuesta
        else:
            for agente in self.agentes:
                for mano in agente.jugador.manos:
                    if mano.valor_total() > self.dealer.manos[0].valor_total():
                        print(f"{agente.jugador.nombre} ha ganado con la mano {mano.cartas}.")
                        agente.jugador.capital += mano.apuesta * 2
                    elif mano.valor_total() == self.dealer.manos[0].valor_total():
                        print(f"{agente.jugador.nombre} ha empatado con la mano {mano.cartas}.")
                        agente.jugador.capital += mano.apuesta
                    else:
                        print(f"{agente.jugador.nombre} ha perdido con la mano {mano.cartas}.")


    def store_data_per_round(self):
        """Guarda los datos de la ronda en un archivo CSV."""
        pass

    def store_data_per_game(self):
        """Guarda los datos del juego en un archivo CSV."""
        pass

    def jugar_ronda(self):
        """Juega una ronda completa de Blackjack."""
        print("Iniciando una nueva ronda...")
        self.reset_baraja()
        self.repartir_cartas()
        for agente in self.agentes:
            self.first_turn(agente)

        while True:
            for agente in self.agentes:
                if not agente.termino:
                    self.turno_jugador(agente)
            # Ensure the loop exits if all agents are done
            if all(agente.termino for agente in self.agentes):
                break

        self.turno_dealer()
        self.determinar_ganadores()

        # Reinicia las variables para la próxima ronda
        for agente in self.agentes:
            agente.veces_plantado = 0
            agente.termino = False
            agente.jugador.reset_manos()
        self.dealer.reset_manos()

        print("Ronda finalizada.")
