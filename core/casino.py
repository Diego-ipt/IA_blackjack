from random import shuffle

from .acciones import Accion
from .player import Jugador, Mano
from .cartas import Mazo, Carta
from agents.agente_base import Agente


class Casino:
    def __init__(self, agentes: list[Agente], num_mazos: int = 4, zapato: float = 0.75):
        self.agentes = agentes
        self.num_mazos = num_mazos
        self.zapato = zapato
        self.dealer = Jugador(nombre="Dealer", capital=10000)
        self.mazo = Mazo(num_mazos=num_mazos, zapato=zapato)

    def _notificar_observadores(self, carta: Carta):
        for agente in self.agentes:
                # Solo los que tienen implementado observar haran algo
                agente.observar_carta(carta)

    def _jugar_ronda(self):

        #1. Fase de Preparacion

        # Barajar el mazo si es necesario (Crearlo de nuevo)
        if self.mazo.necesita_barajar():
            self.mazo = Mazo(num_mazos=self.num_mazos, zapato=self.zapato)

        for agente in self.agentes:
            agente.jugador.reset_manos()
        self.dealer.reset_manos()

        #2. Fase de Apuestas

        # Los agentes que si tienen para apostar se agregan a la lista
        agentes_activos = []
        for agente in self.agentes:
            apuesta = agente.decidir_apuesta()
            if agente.jugador.apostar(apuesta):
                agentes_activos.append(agente)

        #3. Fase de Reparto

        # Crear mano del dealer
        self.dealer.manos.append(Mano([]))
        self.carta_oculta_dealer = None

        # Repartir primera carta a todos
        for agente in agentes_activos:
            carta = self.mazo.repartir()
            agente.jugador.pedir_carta(agente.jugador.manos[0], carta)
            # Notificar para agentes que cuentan cartas
            self._notificar_observadores(carta)

        carta_visible_dealer = self.mazo.repartir()
        self.dealer.pedir_carta(self.dealer.manos[0], carta_visible_dealer)
        self._notificar_observadores(carta_visible_dealer)

        # Repartir segunda carta a todos
        for agente in agentes_activos:
            carta = self.mazo.repartir()
            agente.jugador.pedir_carta(agente.jugador.manos[0], carta)
            # Notificar para agentes que cuentan cartas
            self._notificar_observadores(carta)

        # Repartimos la carta al dealer que no se muestra
        self.carta_oculta_dealer = self.mazo.repartir()

        # 4. Fase de Jugadores

        for agente in agentes_activos:
            indice_mano_actual = 0
            while indice_mano_actual < len(agente.jugador.manos):

                mano_actual = agente.jugador.manos[indice_mano_actual]

                # Ciclo de juego para mano actual
                while not mano_actual.turno_terminado:
                    # Revisar carta del dealer
                    carta_visible_dealer = self.dealer.manos[0].cartas[0]

                    # Pedir decision al agente
                    accion = agente.decidir_accion(mano_actual, carta_visible_dealer)

                    # El casino valida el movimiento

                    if accion == Accion.PLANTARSE:
                        mano_actual.turno_terminado = True

                    elif accion == Accion.PEDIR:
                        carta_nueva = self.mazo.repartir()
                        agente.jugador.pedir_carta(mano_actual, carta_nueva)
                        self._notificar_observadores(carta_nueva)
                        # Si se pasa de 21 se termina, logica en Mano.agregar_carta

                    elif accion == Accion.DOBLAR:
                        if len(mano_actual.cartas) == 2:
                            if agente.jugador.doblar_apuesta(mano_actual):
                                # Si se pudo, repartir y terminar turno
                                carta_nueva = self.mazo.repartir()
                                agente.jugador.pedir_carta(mano_actual, carta_nueva)
                                self._notificar_observadores(carta_nueva)
                                mano_actual.turno_terminado = True
                            else:
                                # No le alcanzaba capital, se planta
                                print("No se pudo doblar, plantando")
                                mano_actual.turno_terminado = True
                        else:
                            print("No se puede doblar con mas de 2 cartas, plantando")
                            mano_actual.turno_terminado = True

                    elif accion == Accion.DIVIDIR:
                        # Validar si hay 2 cartas
                        if len(mano_actual.cartas) == 2:
                            if agente.jugador.dividir_mano(mano_actual):
                                # Si fue exitoso, repartir una carta nueva a cada mano

                                # Carta mano original
                                carta1 = self.mazo.repartir()
                                agente.jugador.pedir_carta(mano_actual, carta1)
                                self._notificar_observadores(carta1)

                                # Carta mano nueva (ultima en la lista)
                                mano_nueva = agente.jugador.manos[-1]
                                carta2 = self.mazo.repartir()
                                agente.jugador.pedir_carta(mano_nueva, carta2)
                                self._notificar_observadores(carta2)

                                # Aca sigue el bucle whie, no termina el turno
                                # Se jugara la primera mano y luego la mano nueva
                                # se jugara cuando llegue a su indice
                            else:
                                print("No se pudo dividir, plantando")
                                mano_actual.turno_terminado = True
                        else:
                            print("No se puede dividir con mas de 2 cartas, plantando")

                    elif accion == Accion.RENDIRSE:
                        agente.jugador.rendirse(mano_actual)
                        break

                indice_mano_actual += 1

        # 5. Fase de Dealer
        # Agregamos la carta oculta a la mano del dealer
        self.dealer.pedir_carta(self.dealer.manos[0], self.carta_oculta_dealer)
        self._notificar_observadores(self.carta_oculta_dealer)

        # El dealer pide mientras tenga menos que 17
        # Se planta con un 17 blando (A,6), valor_total maneja esto
        while self.dealer.manos[0].valor_total < 17:
            carta_nueva_dealer = self.mazo.repartir()
            self.dealer.pedir_carta(self.dealer.manos[0], carta_nueva_dealer)
            self._notificar_observadores(carta_nueva_dealer)


        # 6. Fase de pagos

        valor_final_dealer = self.dealer.manos[0].valor_total
        dealer_se_paso = valor_final_dealer > 21
        dealer_tiene_bj = self.dealer.manos[0].es_blackjack

        for agente in agentes_activos:
            for mano in agente.jugador.manos:

                if mano.es_blackjack:
                    if not dealer_tiene_bj:
                        # Jugador gana 3:2
                        ganancia = int(mano.apuesta * 1.5)
                        agente.jugador.capital += mano.apuesta + ganancia
                        print(f"{agente.jugador.nombre} gana con {mano.cartas} (blackjack)")
                    else:
                        # Empate, ambos tienen bj
                        agente.jugador.capital += mano.apuesta
                        print(f"{agente.jugador.nombre} empata con {mano.cartas}")
                    continue

                valor_mano_jugador = mano.valor_total
                jugador_se_paso = valor_mano_jugador > 21

                if jugador_se_paso:
                    # Si se paso de 21
                    print(f"{agente.jugador.nombre} pierde con {mano.cartas} (se paso)")
                    pass

                elif dealer_se_paso:
                    # Jugador gana, dealer se paso
                    # Pago es 1:1, (si jugador pago 10, recupera apuesta y gana (recibe 20))
                    agente.jugador.capital += mano.apuesta * 2
                    print(f"{agente.jugador.nombre} gana con {mano.cartas} (dealer se paso)")

                elif valor_mano_jugador > valor_final_dealer:
                    # Si no se paso de 21, y tiene mayor valor que el dealer
                    agente.jugador.capital += mano.apuesta * 2
                    print(f"{agente.jugador.nombre} gana con {mano.cartas}")

                elif valor_mano_jugador == valor_final_dealer:
                    # Empate, el jugador recupera apuesta
                    agente.jugador.capital += mano.apuesta
                    print(f"{agente.jugador.nombre} empata con {mano.cartas}")


                else:
                    # valor mano jugador < valor mano dealer
                    print(f"{agente.jugador.nombre} pierde con {mano.cartas}")
                    pass



    def jugar_partida(self, num_rondas:int):
        """
        Punto de entrada para iniciar la simulacion
        """
        print(f"Iniciando partida de {num_rondas} rondas")
        for i in range(num_rondas):
            print(f"Ronda {i + 1} / {num_rondas}")
            self._jugar_ronda()
            for agente in self.agentes:
                print(f"{agente.jugador.nombre}: Capital = {agente.jugador.capital}")
        print("Partida terminada")

