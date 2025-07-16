import numpy as np
from .agente_base import Agente
from core.acciones import Accion
from core.player import Jugador, Mano
from core.cartas import Carta, Rango, Palo

class AgenteMarkov_RL(Agente):
    """
    Agente MDP con una arquitectura de caché optimizada por bucket y una ESTRUCTURA DE RECOMPENSAS
    GRANULAR Y PARAMETRIZADA, diseñada para ser controlada por un agente de RL externo.

    Este agente actúa como el "jugador interno". Un meta-agente (como PPO en el entorno Gym)
    aprenderá cuál es el mejor conjunto de recompensas para este agente, con el objetivo de
    maximizar el rendimiento financiero a largo plazo.
    """
    def __init__(self, jugador: Jugador, num_mazos: int = 4, precision_agrupacion= 20):
        super().__init__(jugador)
        self.num_mazos = num_mazos
        self.precision_agrupacion = precision_agrupacion
        
        self.recompensas = {
            'win_score': 1.0,
            'win_dealer_bust': 1.0,
            'tie': 0.0,
            'loss_score': -1.0,
            'player_bust': -1.0
        }

        self.memo_probabilidades = {}
        self.memo_ev = {}
        self.resetear_conteo()

    def set_recompensas(self, recompensa_dict: dict):
        self.recompensas.update(recompensa_dict)

    def _get_idx(self, valor_carta: int) -> int:
        if valor_carta == 11: return 0
        return valor_carta - 1 if valor_carta < 10 else 9

    def observar_carta(self, carta: Carta):
        idx = self._get_idx(carta.valor)
        if self.cartas_restantes[idx] > 0:
            self.cartas_restantes[idx] -= 1

    def resetear_conteo(self):
        self.cartas_restantes = np.array([4 * self.num_mazos] * 9 + [16 * self.num_mazos])
        self.memo_ev.clear()
        self.memo_probabilidades.clear()
            
    def decidir_apuesta(self, capital_actual: int = None) -> int:
        return 5

    def _crear_clave_agrupada(self) -> tuple:
        total_restantes = np.sum(self.cartas_restantes)
        if total_restantes == 0: return (0, 0, 0, 0)
        num_ases = self.cartas_restantes[0]
        num_bajas = np.sum(self.cartas_restantes[1:6])
        num_medias = np.sum(self.cartas_restantes[6:9])
        num_altas = self.cartas_restantes[9]
        p = self.precision_agrupacion
        return (
            int((num_ases / total_restantes) * p),
            int((num_bajas / total_restantes) * p),
            int((num_medias / total_restantes) * p),
            int((num_altas / total_restantes) * p)
        )
    
    def _get_outcome_distribution(self) -> dict:
        clave_agrupada = self._crear_clave_agrupada()
        if clave_agrupada in self.memo_probabilidades:
            return self.memo_probabilidades[clave_agrupada]

        total_cartas = np.sum(self.cartas_restantes)
        if total_cartas == 0: return {}

        distribucion = { (11 if i==0 else i+1): c/total_cartas for i, c in enumerate(self.cartas_restantes) if c > 0 }
        
        self.memo_probabilidades[clave_agrupada] = distribucion
        return distribucion

    def _calcular_dealer_recursivo(self, valor_actual: int, es_blanda: bool, cartas_restantes: np.ndarray, memo: dict) -> dict:
        clave_memo = (valor_actual, es_blanda, tuple(cartas_restantes))
        if clave_memo in memo:
            return memo[clave_memo]

        if valor_actual > 21: return {'dealer_bust': 1.0}
        if valor_actual >= 17: return {valor_actual: 1.0}

        total_cartas = np.sum(cartas_restantes)
        if total_cartas == 0: return {valor_actual: 1.0}

        # --- CORRECCIÓN AQUÍ ---
        # Inicializar como un diccionario vacío para aceptar cualquier clave de resultado.
        dist_agregada = {}

        for idx, count in enumerate(cartas_restantes):
            if count > 0:
                prob = count / total_cartas
                nuevas_cartas = cartas_restantes.copy(); nuevas_cartas[idx] -= 1
                valor_carta = 11 if idx == 0 else idx + 1
                
                nuevo_valor, nueva_es_blanda = valor_actual + valor_carta, es_blanda or (valor_carta == 11)
                if nuevo_valor > 21 and nueva_es_blanda:
                    nuevo_valor -= 10; nueva_es_blanda = False

                dist_recursiva = self._calcular_dealer_recursivo(nuevo_valor, nueva_es_blanda, nuevas_cartas, memo)
                
                # --- CORRECCIÓN AQUÍ ---
                # Usar .get() para añadir de forma segura a la distribución.
                for res, p in dist_recursiva.items():
                    dist_agregada[res] = dist_agregada.get(res, 0.0) + p * prob
        
        memo[clave_memo] = dist_agregada
        return dist_agregada

    def _simular_dealer(self, carta_dealer_visible: Carta) -> dict:
        clave_cache = (self._crear_clave_agrupada(), carta_dealer_visible.valor)
        if clave_cache in self.memo_probabilidades:
            return self.memo_probabilidades[clave_cache]

        memo_sim = {}
        cartas_sim = self.cartas_restantes.copy()
        
        # Manejar el caso de que la carta del dealer no esté en el conteo (improbable)
        idx_visible = self._get_idx(carta_dealer_visible.valor)
        if cartas_sim[idx_visible] > 0:
            cartas_sim[idx_visible] -= 1
        
        total_ocultas = np.sum(cartas_sim)
        if total_ocultas == 0: return {carta_dealer_visible.valor: 1.0}

        # --- CORRECCIÓN AQUÍ ---
        # Inicializar como un diccionario vacío.
        dist_final = {}

        for idx, count in enumerate(cartas_sim):
            if count > 0:
                prob_oculta = count / total_ocultas
                valor_oculta = 11 if idx == 0 else idx + 1
                
                mazo_post = cartas_sim.copy(); mazo_post[idx] -= 1
                
                valor_ini, blanda_ini = carta_dealer_visible.valor + valor_oculta, carta_dealer_visible.rango == Rango.AS or (valor_oculta == 11)
                if valor_ini > 21 and blanda_ini:
                    valor_ini -= 10; blanda_ini = False
                
                dist_parcial = {21: 1.0} if valor_ini == 21 else self._calcular_dealer_recursivo(valor_ini, blanda_ini, mazo_post, memo_sim)
                
                # --- CORRECCIÓN AQUÍ ---
                # Usar .get() para añadir de forma segura.
                for res, p in dist_parcial.items():
                    dist_final[res] = dist_final.get(res, 0.0) + p * prob_oculta
        
        self.memo_probabilidades[clave_cache] = dist_final
        return dist_final

    def _comparar_distribuciones(self, dist_jugador: dict, dist_dealer: dict) -> dict:
        outcomes = {'win_score': 0.0, 'win_dealer_bust': 0.0, 'tie': 0.0, 'loss_score': 0.0, 'player_bust': 0.0}
        
        outcomes['player_bust'] = dist_jugador.get('player_bust', 0.0)
        prob_dealer_se_pasa = dist_dealer.get('dealer_bust', 0.0)
        
        for score_j, prob_j in dist_jugador.items():
            if score_j == 'player_bust': continue
            outcomes['win_dealer_bust'] += prob_j * prob_dealer_se_pasa
            for score_d, prob_d in dist_dealer.items():
                if score_d == 'dealer_bust': continue
                if score_j > score_d: outcomes['win_score'] += prob_j * prob_d
                elif score_j < score_d: outcomes['loss_score'] += prob_j * prob_d
                else: outcomes['tie'] += prob_j * prob_d
        return outcomes

    def _calcular_ev(self, dist_resultados: dict, apuesta_multiplicador: int = 1) -> float:
        """Calcula el valor esperado a partir de una distribución de resultados y las recompensas."""
        ev = 0.0
        for resultado, prob in dist_resultados.items():
            ev += prob * self.recompensas.get(resultado, 0.0) * apuesta_multiplicador
        return ev

    def _calcular_dis_plantarse(self, mano_jugador: Mano, dist_dealer: dict) -> dict:
        if mano_jugador.valor_total > 21:
            return {'player_bust': 1.0}
        dist_jugador = {mano_jugador.valor_total: 1.0}
        return self._comparar_distribuciones(dist_jugador, dist_dealer)

    def _calcular_dis_pedir(self, mano: Mano, dist_dealer: dict, cartas_restantes: np.ndarray) -> dict:
        dist_final_pedir = {'win_score': 0.0, 'win_dealer_bust': 0.0, 'tie': 0.0, 'loss_score': 0.0, 'player_bust': 0.0}
        dist_siguiente_carta = self._get_outcome_distribution()

        for valor_carta, prob in dist_siguiente_carta.items():
            if prob < 0.005: continue

            mano_simulada = Mano(mano.cartas + [Carta(Palo.PICAS, Rango.from_valor(valor_carta))])
            
            if mano_simulada.valor_total > 21:
                dist_final_pedir['player_bust'] += prob
            else:
                dist_plantarse_despues = self._calcular_dis_plantarse(mano_simulada, dist_dealer)
                for outcome, p_outcome in dist_plantarse_despues.items():
                    dist_final_pedir[outcome] += prob * p_outcome
        return dist_final_pedir

    def _calcular_dis_dividir(self, mano: Mano, dist_dealer: dict) -> dict:
        dist_final_dividir = {'win_score': 0.0, 'win_dealer_bust': 0.0, 'tie': 0.0, 'loss_score': 0.0, 'player_bust': 0.0}
        dist_siguiente_carta = self._get_outcome_distribution()

        for valor_carta, prob in dist_siguiente_carta.items():
            if prob < 0.005: continue
            
            mano_post_split = Mano([mano.cartas[0], Carta(Palo.DIAMANTES, Rango.from_valor(valor_carta))])
            
            dist_resultado_mano = self._calcular_dis_plantarse(mano_post_split, dist_dealer)

            for outcome, p_outcome in dist_resultado_mano.items():
                dist_final_dividir[outcome] += prob * p_outcome
        return dist_final_dividir

    def decidir_accion(self, mano: Mano, carta_dealer: Carta) -> Accion:
        if mano.valor_total >= 21:
            return Accion.PLANTARSE

        dist_dealer = self._simular_dealer(carta_dealer)
        acciones_posibles = {}

        dist_plantarse = self._calcular_dis_plantarse(mano, dist_dealer)
        acciones_posibles[Accion.PLANTARSE] = self._calcular_ev(dist_plantarse)

        dist_pedir = self._calcular_dis_pedir(mano, dist_dealer, self.cartas_restantes)
        acciones_posibles[Accion.PEDIR] = self._calcular_ev(dist_pedir)
        
        if len(mano.cartas) == 2:
            acciones_posibles[Accion.DOBLAR] = self._calcular_ev(dist_pedir, apuesta_multiplicador=2)
            acciones_posibles[Accion.RENDIRSE] = -0.5

            if mano.cartas[0].valor == mano.cartas[1].valor:
                dist_dividir = self._calcular_dis_dividir(mano, dist_dealer)
                acciones_posibles[Accion.DIVIDIR] = self._calcular_ev(dist_dividir) * 2
        
        mejor_accion = max(acciones_posibles, key=acciones_posibles.get)
        
        return mejor_accion