import logging
from .acciones import Accion
from .player import Jugador, Mano
from .cartas import Mazo, Carta
from agents.agente_base import Agente


class Casino:
    def __init__(self, agentes: list[Agente], num_mazos: int = 4, zapato: float = 0.75, mazo: Mazo = None):
        self.agentes = agentes
        self.num_mazos = num_mazos
        self.zapato = zapato
        self.dealer = Jugador(nombre="Dealer", capital=10000)

        if mazo is not None:
            self.mazo = mazo
        else:
            self.mazo = Mazo(num_mazos=num_mazos, zapato=zapato)
        self.logger = logging.getLogger(self.__class__.__name__)

    def _notificar_observadores(self, carta: Carta):
        for agente in self.agentes:
                # Solo los que tienen implementado observar haran algo
                agente.observar_carta(carta)
    
    def _resetear_conteo_agentes(self):
        """
        Notifica a los agentes que se ha barajado el mazo
        """
        for agente in self.agentes:
            if hasattr(agente, 'resetear_conteo'):
                agente.resetear_conteo()

    def _jugar_ronda(self):
        self.logger.info("--- INICIO DE RONDA ---")
        #1. Fase de Preparacion
        self.logger.info("Fase de preparación: Barajando y reseteando manos.")

        # Barajar el mazo si es necesario (Crearlo de nuevo)
        if self.mazo.necesita_barajar():
            self.mazo = Mazo(num_mazos=self.num_mazos, zapato=self.zapato)
            # Notificar a los agentes que se ha barajado
            self._resetear_conteo_agentes()
            self.logger.info("Mazo barajado - Conteos reseteados")

        for agente in self.agentes:
            agente.jugador.reset_manos()
        self.dealer.reset_manos()

        #2. Fase de Apuestas
        self.logger.info("Fase de apuestas: Jugadores deciden sus apuestas.")
        # Los agentes que si tienen para apostar se agregan a la lista
        agentes_activos = []
        for agente in self.agentes:
            apuesta = agente.decidir_apuesta()
            if agente.jugador.apostar(apuesta):
                agentes_activos.append(agente)
                self.logger.info(f"Jugador '{agente.jugador.nombre}' apuesta ${apuesta}. Capital restante: ${agente.jugador.capital}")
            else:
                self.logger.info(f"Jugador '{agente.jugador.nombre}' no puede apostar ${apuesta}. Capital: ${agente.jugador.capital}")

        #3. Fase de Reparto
        self.logger.info("Fase de reparto: Repartiendo cartas iniciales.")

        # Crear mano del dealer
        self.dealer.manos.append(Mano([]))
        self.carta_oculta_dealer = None

        # Repartir primera carta a todos
        for agente in agentes_activos:
            carta = self.mazo.repartir()
            agente.jugador.pedir_carta(agente.jugador.manos[0], carta)
            self.logger.info(f"Manos repartidas: '{agente.jugador.nombre}' tiene {agente.jugador.manos[0]}. Capital: ${agente.jugador.capital}")
            self._notificar_observadores(carta)

        carta_visible_dealer = self.mazo.repartir()
        self.dealer.pedir_carta(self.dealer.manos[0], carta_visible_dealer)
        self.logger.info(f"Dealer muestra: {self.dealer.manos[0]}.")
        self._notificar_observadores(carta_visible_dealer)

        # Repartir segunda carta a todos
        for agente in agentes_activos:
            carta = self.mazo.repartir()
            agente.jugador.pedir_carta(agente.jugador.manos[0], carta)
            self.logger.info(f"Manos repartidas: '{agente.jugador.nombre}' tiene {agente.jugador.manos[0]}. Capital: ${agente.jugador.capital}")
            self._notificar_observadores(carta)

        # Repartimos la carta al dealer que no se muestra
        self.carta_oculta_dealer = self.mazo.repartir()
        self.logger.info(f"Dealer recibe carta oculta.")

        # 4. Fase de Jugadores
        self.logger.info("Fase de jugadores: Cada jugador toma decisiones.")
        for agente in agentes_activos:
            self.logger.info(f"Turno de '{agente.jugador.nombre}'. Capital: ${agente.jugador.capital}. Manos: {agente.jugador.manos}")
            indice_mano_actual = 0
            while indice_mano_actual < len(agente.jugador.manos):
                mano_actual = agente.jugador.manos[indice_mano_actual]
                self.logger.info(f"-> Jugando mano {indice_mano_actual+1}/{len(agente.jugador.manos)}: {mano_actual}")
                # Ciclo de juego para mano actual
                while not mano_actual.turno_terminado:
                    # Revisar carta del dealer
                    carta_visible_dealer = self.dealer.manos[0].cartas[0]

                    # Pedir decision al agente
                    accion = agente.decidir_accion(mano_actual, carta_visible_dealer)
                    self.logger.info(f"   '{agente.jugador.nombre}' decide: {accion.name}.")
                    # El casino valida el movimiento

                    if accion == Accion.PLANTARSE:
                        self.logger.info(f"   '{agente.jugador.nombre}' se planta con {mano_actual}.")
                        mano_actual.turno_terminado = True

                    elif accion == Accion.PEDIR:
                        carta_nueva = self.mazo.repartir()
                        agente.jugador.pedir_carta(mano_actual, carta_nueva)
                        self.logger.info(f"   '{agente.jugador.nombre}' pide y recibe {carta_nueva}. Nueva mano: {mano_actual}.")
                        self._notificar_observadores(carta_nueva)
                        # Si se pasa de 21 se termina, logica en Mano.agregar_carta
                        if mano_actual.valor_total > 21:
                            self.logger.info(f"   '{agente.jugador.nombre}' se pasa con {mano_actual}.")

                    elif accion == Accion.DOBLAR:
                        if len(mano_actual.cartas) == 2:
                            apuesta_vieja = mano_actual.apuesta
                            if agente.jugador.doblar_apuesta(mano_actual):
                                # Si se pudo, repartir y terminar turno
                                carta_nueva = self.mazo.repartir()
                                agente.jugador.pedir_carta(mano_actual, carta_nueva)
                                self.logger.info(f"   '{agente.jugador.nombre}' dobla y recibe {carta_nueva}. Su apuesta sube de ${apuesta_vieja} a ${mano_actual.apuesta} Nueva mano: {mano_actual}.")
                                self._notificar_observadores(carta_nueva)
                                if mano_actual.valor_total > 21:
                                    self.logger.info(f"   '{agente.jugador.nombre}' se pasa con {mano_actual}.")
                                mano_actual.turno_terminado = True

                            else:
                                self.logger.info(f"   Acción ilegal: {accion.name}. Tratado como PLANTARSE.")
                                mano_actual.turno_terminado = True
                        else:
                            self.logger.info(f"   Acción ilegal: {accion.name}. Tratado como PLANTARSE.")
                            mano_actual.turno_terminado = True

                    elif accion == Accion.DIVIDIR:
                        # Validar si hay 2 cartas
                        if len(mano_actual.cartas) == 2:
                            if agente.jugador.dividir_mano(mano_actual):
                                # Si fue exitoso, repartir una carta nueva a cada mano

                                # Carta mano original
                                carta1 = self.mazo.repartir()
                                agente.jugador.pedir_carta(mano_actual, carta1)
                                self.logger.info(f"   '{agente.jugador.nombre}' divide y recibe {carta1} en mano original. Mano: {mano_actual}.")
                                self._notificar_observadores(carta1)

                                # Carta mano nueva (ultima en la lista)
                                mano_nueva = agente.jugador.manos[-1]
                                carta2 = self.mazo.repartir()
                                agente.jugador.pedir_carta(mano_nueva, carta2)
                                self.logger.info(f"   '{agente.jugador.nombre}' recibe {carta2} en mano nueva. Mano: {mano_nueva}.")
                                self._notificar_observadores(carta2)

                                # Aca sigue el bucle whie, no termina el turno
                                # Se jugara la primera mano y luego la mano nueva
                                # se jugara cuando llegue a su indice
                            else:
                                self.logger.info(f"   Acción ilegal: {accion.name}. Tratado como PLANTARSE.")
                                mano_actual.turno_terminado = True
                        else:
                            self.logger.info(f"   Acción ilegal: {accion.name}. Tratado como PLANTARSE.")
                            mano_actual.turno_terminado = True

                    elif accion == Accion.RENDIRSE:
                        if len(mano_actual.cartas) != 2:
                            self.logger.info(f"   Acción ilegal: {accion.name}. Tratado como PLANTARSE.")
                            mano_actual.turno_terminado = True
                        else:
                            agente.jugador.rendirse(mano_actual)
                            self.logger.info(f"   '{agente.jugador.nombre}' se rinde con {mano_actual}. Recupera ${int(mano_actual.apuesta / 2)}. Mano terminada.")
                            mano_actual.turno_terminado = True

                self.logger.info(f"   Fin de mano {indice_mano_actual+1}: {mano_actual}. Capital: ${agente.jugador.capital}")
                indice_mano_actual += 1

        # 5. Fase de Dealer
        self.logger.info("Fase del dealer: Revelando carta oculta y jugando turno.")
        # Agregamos la carta oculta a la mano del dealer
        self.dealer.pedir_carta(self.dealer.manos[0], self.carta_oculta_dealer)
        self.logger.info(f"Turno del Dealer. Revela: {self.carta_oculta_dealer}. Mano completa: {self.dealer.manos[0]}")
        self._notificar_observadores(self.carta_oculta_dealer)

        # El dealer pide mientras tenga menos que 17
        # Se planta con un 17 blando (A,6), valor_total maneja esto
        while self.dealer.manos[0].valor_total < 17:
            carta_nueva_dealer = self.mazo.repartir()
            self.dealer.pedir_carta(self.dealer.manos[0], carta_nueva_dealer)
            self.logger.info(f"Dealer pide y recibe {carta_nueva_dealer}. Nueva mano: {self.dealer.manos[0]}.")
            self._notificar_observadores(carta_nueva_dealer)

        if self.dealer.manos[0].valor_total > 21:
            self.logger.info(f"Dealer se pasa con {self.dealer.manos[0]}.")
        else:
            self.logger.info(f"Dealer se planta con {self.dealer.manos[0]}.")

        # 6. Fase de pagos
        self.logger.info("Fase de pagos: Calculando resultados y pagos.")
        valor_final_dealer = self.dealer.manos[0].valor_total
        dealer_se_paso = valor_final_dealer > 21
        dealer_tiene_bj = self.dealer.manos[0].valor_total == 21

        for agente in agentes_activos:
            for mano in agente.jugador.manos:
                self.logger.info(f"Revisando mano de '{agente.jugador.nombre}': {mano}. Capital antes: ${agente.jugador.capital_pre_turno}")

                if mano.es_blackjack:
                    if not dealer_tiene_bj:
                        # Jugador gana 3:2
                        ganancia = int(mano.apuesta * 1.5)
                        agente.jugador.capital += mano.apuesta + ganancia
                        self.logger.info(f"'{agente.jugador.nombre}' gana ${ganancia} con {mano} (Blackjack paga 3:2). Capital actual: ${agente.jugador.capital}")
                    else:
                        # Empate, ambos tienen bj
                        agente.jugador.capital += mano.apuesta
                        self.logger.info(f"'{agente.jugador.nombre}' empata con {mano}. Capital actual: ${agente.jugador.capital}")
                    continue

                valor_mano_jugador = mano.valor_total
                jugador_se_paso = valor_mano_jugador > 21

                if jugador_se_paso:
                    # Si se paso de 21
                    self.logger.info(f"'{agente.jugador.nombre}' pierde ${mano.apuesta} con {mano}. Capital actual: ${agente.jugador.capital}")
                elif dealer_se_paso:
                    # Jugador gana, dealer se paso
                    # Pago es 1:1, (si jugador pago 10, recupera apuesta y gana (recibe 20))
                    agente.jugador.capital += mano.apuesta * 2
                    self.logger.info(f"'{agente.jugador.nombre}' gana ${mano.apuesta} con {mano}. Capital actual: ${agente.jugador.capital}")
                elif valor_mano_jugador > valor_final_dealer:
                    # Si no se paso de 21, y tiene mayor valor que el dealer
                    agente.jugador.capital += mano.apuesta * 2
                    self.logger.info(f"'{agente.jugador.nombre}' gana ${mano.apuesta} con {mano}. Capital actual: ${agente.jugador.capital}")
                elif valor_mano_jugador == valor_final_dealer:
                    # Empate, el jugador recupera apuesta
                    agente.jugador.capital += mano.apuesta
                    self.logger.info(f"'{agente.jugador.nombre}' empata con {mano}. Capital actual: ${agente.jugador.capital}")
                else:
                    # valor mano jugador < valor mano dealer
                    self.logger.info(f"'{agente.jugador.nombre}' pierde ${mano.apuesta} con {mano}. Capital actual: ${agente.jugador.capital}")

        self.logger.info("--- FIN DE RONDA ---\n")


    def jugar_partida(self, num_rondas:int):
        """
        Punto de entrada para iniciar la simulacion
        """
        print(f"Iniciando partida de {num_rondas} rondas")
        for i in range(num_rondas):
            print(f"Ronda {i + 1} / {num_rondas}")
            self._jugar_ronda()
            for agente in self.agentes:
                print(f"'{agente.jugador.nombre}': Capital = {agente.jugador.capital}")
        print("Partida terminada")
