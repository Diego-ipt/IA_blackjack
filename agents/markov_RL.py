import numpy as np
from .agente_base import Agente
from core.acciones import Accion
from core.player import Jugador, Mano
from core.cartas import Carta, Rango, Palo

class AgenteMarkov_RL(Agente):
    """
    Agente MDP con una arquitectura de caché optimizada y una ESTRUCTURA DE RECOMPENSAS
    GRANULAR Y PARAMETRIZADA, diseñada para ser controlada por un agente de RL.
    """
    def __init__(self, jugador: Jugador, num_mazos: int = 4, precision_agrupacion: int = 20):
        super().__init__(jugador)
        self.num_mazos = num_mazos
        self.precision_agrupacion = precision_agrupacion
        
        # Recompensas por defecto, ahora con 5 componentes.
        self.recompensas = {
            'win_score': 1.0,      # Victoria por más puntos
            'win_dealer_bust': 1.0,# Victoria porque el dealer se pasó
            'tie': 0.0,            # Empate
            'loss_score': -1.0,    # Derrota por menos puntos
            'player_bust': -1.0    # Derrota porque el jugador se pasó
        }
        
        self.resetear_conteo()

    def set_recompensas(self, recompensa_dict: dict):
        """Método para que un agente externo configure las recompensas."""
        self.recompensas.update(recompensa_dict)
        # Limpiar cachés ya que la política óptima cambiará
        self.memo_valor_estado.clear()
        self.memo_outcome_prob.clear()

    def _get_idx(self, valor_carta: int) -> int:
        if valor_carta == 11: return 0
        return valor_carta - 1 if valor_carta < 10 else 9

    def observar_carta(self, carta: Carta):
        idx = self._get_idx(carta.valor)
        if self.cartas_restantes[idx] > 0:
            self.cartas_restantes[idx] -= 1

    def resetear_conteo(self):
        self.cartas_restantes = np.array([4 * self.num_mazos] * 9 + [16 * self.num_mazos])
        self.memo_valor_estado = {}
        self.memo_outcome_prob = {}
        self.memo_dealer_dist = {}
            
    def decidir_apuesta(self, capital_actual: int = None) -> int:
        return int(5)
    
    def _crear_clave_agrupada(self, cartas_restantes: np.ndarray) -> tuple:
        total_restantes = np.sum(cartas_restantes)
        if total_restantes == 0:
            return (0, 0, 0, 0)
        num_ases = cartas_restantes[0]
        num_bajas = np.sum(cartas_restantes[1:6])
        num_medias = np.sum(cartas_restantes[6:9])
        num_altas = cartas_restantes[9]
        p = self.precision_agrupacion
        porc_ases_d = int( (num_ases / total_restantes) * p )
        porc_bajas_d = int( (num_bajas / total_restantes) * p )
        porc_medias_d = int( (num_medias / total_restantes) * p )
        porc_altas_d = int( (num_altas / total_restantes) * p )
        return (porc_ases_d, porc_bajas_d, porc_medias_d, porc_altas_d)

    def _calcular_dealer_recursivo(self, mano_dealer: Mano, cartas_restantes: np.ndarray) -> dict:
        valor_actual = mano_dealer.valor_total
        key_recursiva = (valor_actual, mano_dealer.es_blanda, tuple(cartas_restantes))
        temp_cache = {}
        if key_recursiva in temp_cache:
            return temp_cache[key_recursiva]
        if valor_actual >= 17:
            return {valor_actual: 1.0}
        dist_prob_final = {}
        total_cartas = np.sum(cartas_restantes)
        if total_cartas == 0:
             return {valor_actual: 1.0}
        for i, count in enumerate(cartas_restantes):
            if count > 0:
                prob_carta = count / total_cartas
                valor_carta = 11 if i == 0 else (10 if i == 9 else i + 1)
                nuevas_cartas_restantes = cartas_restantes.copy()
                nuevas_cartas_restantes[i] -= 1
                nueva_carta = Carta(Palo.PICAS, Rango.from_valor(valor_carta))
                sub_dist = self._calcular_dealer_recursivo(Mano(mano_dealer.cartas + [nueva_carta]), nuevas_cartas_restantes)
                for v_final, p_sub in sub_dist.items():
                    dist_prob_final[v_final] = dist_prob_final.get(v_final, 0) + prob_carta * p_sub
        temp_cache[key_recursiva] = dist_prob_final
        return dist_prob_final

    def _simular_dealer(self, mano_dealer: Mano, cartas_restantes: np.ndarray) -> dict:
        clave_agrupada = self._crear_clave_agrupada(cartas_restantes)
        cache_key = (mano_dealer.valor_total, mano_dealer.es_blanda, clave_agrupada)
        if cache_key in self.memo_dealer_dist:
            return self.memo_dealer_dist[cache_key]
        else:
            dist_calculada = self._calcular_dealer_recursivo(mano_dealer, cartas_restantes)
            self.memo_dealer_dist[cache_key] = dist_calculada
            return dist_calculada
    
    def _get_outcome_distribution(self, valor_jugador: int, carta_dealer: Carta, cartas_restantes: np.ndarray) -> dict:
        clave_agrupada = self._crear_clave_agrupada(cartas_restantes)
        prob_key = (valor_jugador, carta_dealer.valor, clave_agrupada)

        if prob_key in self.memo_outcome_prob:
            return self.memo_outcome_prob[prob_key]

        if valor_jugador > 21:
            return {'win_score': 0, 'win_dealer_bust': 0, 'tie': 0, 'loss_score': 0, 'player_bust': 1.0}

        dist_prob_dealer = self._simular_dealer(Mano([carta_dealer]), cartas_restantes)
        
        dist = {'win_score': 0, 'win_dealer_bust': 0, 'tie': 0, 'loss_score': 0, 'player_bust': 0}

        for valor_final_dealer, prob in dist_prob_dealer.items():
            if valor_final_dealer > 21:
                dist['win_dealer_bust'] += prob
            elif valor_jugador > valor_final_dealer:
                dist['win_score'] += prob
            elif valor_jugador < valor_final_dealer:
                dist['loss_score'] += prob
            else:
                dist['tie'] += prob
        
        self.memo_outcome_prob[prob_key] = dist
        return dist

    def _calcular_ev_plantarse(self, valor_jugador: int, carta_dealer: Carta, cartas_restantes: np.ndarray) -> float:
        dist = self._get_outcome_distribution(valor_jugador, carta_dealer, cartas_restantes)
        ev = sum(dist[key] * self.recompensas[key] for key in dist)
        return ev

    def _calcular_ev_doblar(self, mano_jugador: Mano, carta_dealer: Carta, cartas_restantes: np.ndarray) -> float:
        ev_total = 0.0
        total_cartas = np.sum(cartas_restantes)
        if total_cartas == 0: return self.recompensas['loss_score'] * 2

        for i, count in enumerate(cartas_restantes):
            if count > 0:
                prob_carta = count / total_cartas
                valor_carta = 11 if i == 0 else (10 if i == 9 else i + 1)
                nuevas_cartas_restantes = cartas_restantes.copy()
                nuevas_cartas_restantes[i] -= 1
                nueva_mano = Mano(mano_jugador.cartas + [Carta(Palo.PICAS, Rango.from_valor(valor_carta))])
                dist = self._get_outcome_distribution(nueva_mano.valor_total, carta_dealer, nuevas_cartas_restantes)
                ev_doblado = sum(dist[key] * self.recompensas[key] * 2 for key in dist)
                ev_total += prob_carta * ev_doblado
        return ev_total

    # ========================================================================= #
    # === ESTAS DOS FUNCIONES FALTABAN. LAS AÑADIMOS DE NUEVO. === #
    # ========================================================================= #
    def _calcular_ev_pedir(self, mano_jugador: Mano, carta_dealer: Carta, cartas_restantes: np.ndarray) -> float:
        ev_total = 0.0
        total_cartas = np.sum(cartas_restantes)
        if total_cartas == 0:
            return self._calcular_ev_plantarse(mano_jugador.valor_total, carta_dealer, cartas_restantes)
        
        for i, count in enumerate(cartas_restantes):
            if count > 0:
                prob_carta = count / total_cartas
                valor_carta = 11 if i == 0 else (10 if i == 9 else i + 1)
                nuevas_cartas_restantes = cartas_restantes.copy()
                nuevas_cartas_restantes[i] -= 1
                nueva_mano = Mano(mano_jugador.cartas + [Carta(Palo.PICAS, Rango.from_valor(valor_carta))])
                valor_siguiente_estado = self._get_valor_estado(nueva_mano, carta_dealer, nuevas_cartas_restantes)
                ev_total += prob_carta * valor_siguiente_estado
        
        return ev_total
        
    def _calcular_ev_dividir(self, mano_jugador: Mano, carta_dealer: Carta, cartas_restantes: np.ndarray) -> float:
        carta_dividida_valor = mano_jugador.cartas[0].valor
        mano_dividida = Mano([Carta(Palo.PICAS, Rango.from_valor(carta_dividida_valor))])
        ev_mano = self._get_valor_estado(mano_dividida, carta_dealer, cartas_restantes.copy())
        return ev_mano * 2

    def _get_valor_estado(self, mano_jugador: Mano, carta_dealer: Carta, cartas_restantes: np.ndarray) -> float:
        if mano_jugador.valor_total > 21:
            return self.recompensas['player_bust']

        clave_agrupada = self._crear_clave_agrupada(cartas_restantes)
        estado_key = (mano_jugador.valor_total, mano_jugador.es_blanda, len(mano_jugador.cartas), carta_dealer.valor, clave_agrupada)
        if estado_key in self.memo_valor_estado:
            return self.memo_valor_estado[estado_key]
        
        ev_plantarse = self._calcular_ev_plantarse(mano_jugador.valor_total, carta_dealer, cartas_restantes)
        ev_pedir = self._calcular_ev_pedir(mano_jugador, carta_dealer, cartas_restantes)

        valor_optimo = max(ev_plantarse, ev_pedir)
        self.memo_valor_estado[estado_key] = valor_optimo
        return valor_optimo

    def decidir_accion(self, mano: Mano, carta_dealer: Carta) -> Accion:
        if mano.es_blackjack or mano.valor_total > 21:
            return Accion.PLANTARSE
        
        acciones_ev = {}
        acciones_ev[Accion.PLANTARSE] = self._calcular_ev_plantarse(mano.valor_total, carta_dealer, self.cartas_restantes.copy())
        acciones_ev[Accion.PEDIR] = self._calcular_ev_pedir(mano, carta_dealer, self.cartas_restantes.copy())
        
        if len(mano.cartas) == 2:
            acciones_ev[Accion.DOBLAR] = self._calcular_ev_doblar(mano, carta_dealer, self.cartas_restantes.copy())
            if mano.cartas[0].rango == mano.cartas[1].rango:
                acciones_ev[Accion.DIVIDIR] = self._calcular_ev_dividir(mano, carta_dealer, self.cartas_restantes.copy())
        
        mejor_ev = max(acciones_ev.values())

        # El valor de la rendición es la mitad de la recompensa por derrota (ya que se pierde media apuesta)
        # Asumiendo que la recompensa por derrota es negativa, su mitad es un número mayor (más cercano a cero).
        ev_rendirse = self.recompensas.get('loss_score', -1.0) / 2.0
        if len(mano.cartas) == 2 and ev_rendirse > mejor_ev:
            return Accion.RENDIRSE
            
        return max(acciones_ev, key=acciones_ev.get)