import random
from .agente_base import Agente
from core.acciones import Accion
from core.player import Jugador, Mano
from core.cartas import Carta

class AgenteBasico(Agente):
    """
    Agente que implementa únicamente la estrategia básica de blackjack,
    sin contar cartas. La apuesta es siempre la apuesta base
    (respetando mínimo y fracción máxima del capital).
    """

    def __init__(self,
                 jugador: Jugador,
                 base_bet: int = 5,
                 min_bet: int = 1,
                 max_bet_fraction: float = 0.1):
        """
        :param jugador: instancia de Jugador
        :param base_bet: apuesta que realizará siempre si el capital lo permite
        :param min_bet: apuesta mínima
        :param max_bet_fraction: fracción del capital para apuesta máxima
        """
        super().__init__(jugador)
        self.base_bet = base_bet
        self.min_bet = min_bet
        self.max_bet_fraction = max_bet_fraction

    def decidir_apuesta(self) -> int:
        """
        Siempre apuesta base_bet, clamp entre min_bet y max_bet (según fracción del capital).
        """
        cap = self.jugador.capital
        if cap < self.min_bet:
            return 0

        max_bet = max(self.min_bet, int(cap * self.max_bet_fraction))
        bet = self.base_bet
        # Clamp
        bet = max(self.min_bet, min(bet, max_bet))
        return bet

    def decidir_accion(self, mano: Mano, carta_dealer: Carta) -> Accion:
        """
        Estrategia básica completa (splits, doblar, rendirse, hard y soft totals).
        """
        mi_valor      = mano.valor_total
        dealer_val    = carta_dealer.valor
        duro          = not mano.es_blanda
        num_cartas    = len(mano.cartas)
        par_divisible = num_cartas == 2 and (mano.cartas[0].valor == mano.cartas[1].valor)

        # 1) Splits básicos
        if par_divisible:
            v = mano.cartas[0].valor
            if v in (1, 8):
                return Accion.DIVIDIR
            if v == 9 and (2 <= dealer_val <= 6 or 8 <= dealer_val <= 9):
                return Accion.DIVIDIR
            if v == 7 and dealer_val <= 7:
                return Accion.DIVIDIR
            if v == 6 and dealer_val <= 6:
                return Accion.DIVIDIR
            if v in (2, 3) and dealer_val <= 7:
                return Accion.DIVIDIR
            # 5-5 se tratan como 10 → caerán en doblar

        # 2) Doblar (hard totals)
        if num_cartas == 2 and duro:
            if mi_valor == 11:
                return Accion.DOBLAR
            if mi_valor == 10 and dealer_val <= 9:
                return Accion.DOBLAR
            if mi_valor == 9 and 3 <= dealer_val <= 6:
                return Accion.DOBLAR

        # 3) Rendirse (opcional según reglas)
        if duro and num_cartas == 2:
            if mi_valor == 15 and dealer_val == 10:
                return Accion.RENDIRSE
            if mi_valor == 16 and 9 <= dealer_val <= 11:
                return Accion.RENDIRSE

        # 4) Estrategia básica hard
        if duro:
            if mi_valor >= 17:
                return Accion.PLANTARSE
            if 12 <= mi_valor <= 16 and 2 <= dealer_val <= 6:
                return Accion.PLANTARSE

        # 5) Doblar con manos blandas (soft doubles)
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
            if mi_valor >= 19:
                return Accion.PLANTARSE
            if mi_valor == 18 and dealer_val <= 8:
                return Accion.PLANTARSE
            if mi_valor <= 17:
                return Accion.PEDIR

        # 7) Caso por defecto
        return Accion.PEDIR
