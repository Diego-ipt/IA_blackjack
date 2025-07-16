import joblib
import numpy as np
import pandas as pd
from core.player import Jugador, Mano
from core.cartas import Carta
from core.acciones import Accion
from .agente_base import Agente 

class AgenteRandomForest(Agente):
    def __init__(self, jugador: Jugador, modelo_path: str, encoder_path: str, min_bet: int = 1, base_bet: int = 5, max_bet_fraction: float = 0.1):
        super().__init__(jugador)
        
        self.conteo = 0
        self.base_bet = base_bet
        self.min_bet = min_bet
        self.max_bet_fraction = max_bet_fraction

        # cargar modelo y label encoder
        self.clf = joblib.load(modelo_path)
        self.encoder = joblib.load(encoder_path)

    def decidir_apuesta(self) -> int:
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

        # === Features base extraídas de la mano ===
        mano_valor             = mano.valor_total
        dealer_valor_carta     = carta_dealer.valor
        conteo_cartas          = getattr(self, "conteo", 0)
        usa_conteo             = int(conteo_cartas != 0)
        mano_es_blanda         = int(mano.es_blanda)
        mano_es_par_divisible  = int(len(mano.cartas) == 2 and (mano.cartas[0].valor == mano.cartas[1].valor))
        mano_num_cartas        = len(mano.cartas)

        # === Features derivadas ===
        mano_vs_dealer       = mano_valor * dealer_valor_carta
        valor_por_carta      = mano_valor / mano_num_cartas
        mano_sobre_dealer    = mano_valor / dealer_valor_carta
        cartas_por_conteo    = mano_num_cartas * conteo_cartas * usa_conteo
        blanda_y_valor       = mano_es_blanda * mano_valor

        # === Construcción del DataFrame de entrada ===
        x = pd.DataFrame([{
            "mano_valor": mano_valor,
            "dealer_valor_carta": dealer_valor_carta,
            "conteo_cartas": conteo_cartas,
            "usa_conteo": usa_conteo,
            "mano_es_blanda": mano_es_blanda,
            "mano_es_par_divisible": mano_es_par_divisible,
            "mano_num_cartas": mano_num_cartas,
            "mano_vs_dealer": mano_vs_dealer,
            "valor_por_carta": valor_por_carta,
            "blanda_y_valor": blanda_y_valor,
            "mano_sobre_dealer": mano_sobre_dealer,
            "cartas_por_conteo": cartas_por_conteo
        }])

        # === Predicción del modelo ===
        pred_clase = self.clf.predict(x)[0]
        accion_str = self.encoder.inverse_transform([pred_clase])[0]
        return Accion[accion_str]
