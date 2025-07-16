# blackjack_sim/agents/agente_hilo.py

import logging
from abc import ABC
from core.player import Jugador, Mano
from core.cartas import Carta
from core.acciones import Accion
from .agente_base import Agente

class AgenteHiLo(Agente, ABC):
    """
    Agente que implementa conteo de cartas Hi-Lo y una estrategia básica
    adaptativa. Apuesta más fuerte cuando el conteo es alto.
    """

    def __init__(self, jugador: Jugador,
                 base_bet: int = 5,
                 min_bet: int = 1,
                 max_bet_fraction: float = 0.1):
        """
        :param jugador: instancia de Jugador
        :param base_bet: apuesta base cuando el conteo <= 1
        :param min_bet: apuesta mínima
        :param max_bet_fraction: fracción del capital para apuesta máxima
        """
        super().__init__(jugador)
        self.conteo = 0
        self.base_bet = base_bet
        self.min_bet = min_bet
        self.max_bet_fraction = max_bet_fraction
        self.logger = logging.getLogger(self.__class__.__name__)

    def resetear_conteo(self):
        self.conteo = 0

    def observar_carta(self, carta: Carta):
        val = carta.valor
        if 2 <= val <= 6:
            self.conteo += 1
        elif val >= 10 or carta.rango.name == 'AS':
            self.conteo -= 1

    def decidir_apuesta(self) -> int:
        """
        Apuesta adaptativa según conteo:
        - Si conteo <= 1: apuesta `base_bet`
        - Si conteo > 1: multiplica base_bet * conteo
        - Se respeta capital disponible y mínimos
        """
        cap = self.jugador.capital
        if cap < self.min_bet:
            return 0

        # apuesta máxima como fracción del capital
        max_bet = max(self.min_bet, int(cap * self.max_bet_fraction))

        # Decide apuesta según conteo
        if self.conteo <= 1:
            bet = self.base_bet
        else:
            bet = self.base_bet * self.conteo

        # Clampeo entre min_bet y max_bet
        bet = max(self.min_bet, min(bet, max_bet))


        return bet
    
    
    def decidir_accion(self, mano: Mano, carta_dealer: Carta) -> Accion:
        mi_valor      = mano.valor_total
        dealer_val    = carta_dealer.valor
        duro          = not mano.es_blanda
        num_cartas    = len(mano.cartas)
        par_divisible = num_cartas == 2 and (mano.cartas[0].valor == mano.cartas[1].valor)

        # 1) Desviaciones Hi-Lo (Illustrious 18 completas)

        # Plantarse con 16 vs 10 si conteo >= 0
        if duro and mi_valor == 16 and dealer_val == 10 and self.conteo >= 0:
            return Accion.PLANTARSE

        # Plantarse con 15 vs 10 si conteo >= +4
        if duro and mi_valor == 15 and dealer_val == 10 and self.conteo >= 4:
            return Accion.PLANTARSE

        # Doblar con 10 vs 10 si conteo >= +4
        if duro and mi_valor == 10 and dealer_val == 10 and self.conteo >= 4:
            return Accion.DOBLAR

        # Plantarse con 12 vs 3 si conteo >= +2
        if duro and mi_valor == 12 and dealer_val == 3 and self.conteo >= 2:
            return Accion.PLANTARSE

        # Plantarse con 12 vs 2 si conteo >= +3
        if duro and mi_valor == 12 and dealer_val == 2 and self.conteo >= 3:
            return Accion.PLANTARSE

        # Doblar con 11 vs As si conteo >= +1
        if duro and mi_valor == 11 and dealer_val == 11 and self.conteo >= 1:
            return Accion.DOBLAR

        # Doblar con 9 vs 2 si conteo >= +1
        if duro and mi_valor == 9 and dealer_val == 2 and self.conteo >= 1:
            return Accion.DOBLAR

        # Doblar con 10 vs As si conteo >= +4
        if duro and mi_valor == 10 and dealer_val == 11 and self.conteo >= 4:
            return Accion.DOBLAR

        # Doblar con 9 vs 7 si conteo >= +3
        if duro and mi_valor == 9 and dealer_val == 7 and self.conteo >= 3:
            return Accion.DOBLAR

        # Plantarse con 16 vs 9 si conteo >= +5
        if duro and mi_valor == 16 and dealer_val == 9 and self.conteo >= 5:
            return Accion.PLANTARSE

        # Plantarse con 13 vs 2 si conteo >= -1
        if duro and mi_valor == 13 and dealer_val == 2 and self.conteo >= -1:
            return Accion.PLANTARSE

        # Plantarse con 12 vs 4 si conteo >= 0
        if duro and mi_valor == 12 and dealer_val == 4 and self.conteo >= 0:
            return Accion.PLANTARSE

        # Plantarse con 12 vs 5 si conteo >= -2
        if duro and mi_valor == 12 and dealer_val == 5 and self.conteo >= -2:
            return Accion.PLANTARSE

        # Plantarse con 12 vs 6 si conteo >= -1
        if duro and mi_valor == 12 and dealer_val == 6 and self.conteo >= -1:
            return Accion.PLANTARSE

        # Plantarse con 13 vs 3 si conteo >= -2
        if duro and mi_valor == 13 and dealer_val == 3 and self.conteo >= -2:
            return Accion.PLANTARSE

        # Plantarse con 14 vs 10 si conteo >= +3
        if duro and mi_valor == 14 and dealer_val == 10 and self.conteo >= 3:
            return Accion.PLANTARSE

        # Plantarse con 15 vs 9 si conteo >= +2
        if duro and mi_valor == 15 and dealer_val == 9 and self.conteo >= 2:
            return Accion.PLANTARSE

        # Plantarse con 15 vs As si conteo >= +1
        if duro and mi_valor == 15 and dealer_val == 11 and self.conteo >= 1:
            return Accion.PLANTARSE


        # 2) Splits básicos
        if par_divisible:
            v = mano.cartas[0].valor
            # siempre dividir A-A y 8-8
            if v in (1, 8):
                return Accion.DIVIDIR
            # 9-9 vs dealer 2–6,8–9
            if v == 9 and (2 <= dealer_val <= 6 or 8 <= dealer_val <= 9):
                return Accion.DIVIDIR
            # 7-7 vs dealer 2–7
            if v == 7 and dealer_val <= 7:
                return Accion.DIVIDIR
            # 6-6 vs dealer 2–6
            if v == 6 and dealer_val <= 6:
                return Accion.DIVIDIR
            # 2-2 y 3-3 vs dealer 2–7
            if v in (2, 3) and dealer_val <= 7:
                return Accion.DIVIDIR
            # 5-5 se tratan como valor 10 (doblar)
            if v == 5:
                # caerá en la regla de doblar abajo
                pass

        # 3) Doblar (hard totals)
        if num_cartas == 2 and duro:
            if mi_valor == 11:
                return Accion.DOBLAR
            if mi_valor == 10 and dealer_val <= 9:
                return Accion.DOBLAR
            if mi_valor == 9 and 3 <= dealer_val <= 6:
                return Accion.DOBLAR

        # 4) Rendirse standard (no Hi-Lo)
        if duro and num_cartas == 2:
            if mi_valor == 15 and dealer_val == 10:
                return Accion.RENDIRSE
            if mi_valor == 16 and 9 <= dealer_val <= 11:
                return Accion.RENDIRSE

        # 5) Estrategia básica hard
        if duro:
            if mi_valor >= 17:
                return Accion.PLANTARSE
            if 12 <= mi_valor <= 16 and 2 <= dealer_val <= 6:
                return Accion.PLANTARSE
            
                # 5.5) Estrategia básica: doblar con manos blandas si aplica
        if mano.es_blanda and num_cartas == 2:
            if mi_valor == 18 and 2 <= dealer_val <= 6:
                return Accion.DOBLAR
            if mi_valor == 17 and 3 <= dealer_val <= 6:
                return Accion.DOBLAR
            if mi_valor == 16 and 4 <= dealer_val <= 6:
                return Accion.DOBLAR
            if mi_valor == 15 and 4 <= dealer_val <= 6:
                return Accion.DOBLAR
            if mi_valor == 14 and 5 <= dealer_val <= 6:
                return Accion.DOBLAR
            if mi_valor == 13 and 5 <= dealer_val <= 6:
                return Accion.DOBLAR

        # 6) Estrategia básica soft
        if mano.es_blanda:
            # Soft 19+ siempre plantarse
            if mi_valor >= 19:
                return Accion.PLANTARSE
            # Soft 18 vs dealer 2–8 → plantarse, excepto si ya doblaste antes
            if mi_valor == 18 and dealer_val <= 8:
                return Accion.PLANTARSE
            # Soft 17 o menos → pedir
            if mi_valor <= 17:
                return Accion.PEDIR

        # 7) Caso por defecto: pedir
        return Accion.PEDIR

