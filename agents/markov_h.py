import numpy as np
from .agente_base import Agente
from core.acciones import Accion
from core.player import Jugador, Mano
from core.cartas import Carta, Rango, Palo

"""
El factor_riesgo_escala: Este es tu nuevo "dial de agresividad".
factor_riesgo_escala = 0: El agente ignora el Hi-Lo y es un Markov puro.
factor_riesgo_escala = 0.05 (defecto): El Hi-Lo da un pequeño "empujón". En la mayoría de los casos, la decisión del Markov prevalecerá, pero cuando los EV de dos acciones sean muy cercanos, el Hi-Lo actuará como desempate.
factor_riesgo_escala = 0.2: El Hi-Lo tiene una influencia muy fuerte y puede hacer que el agente tome decisiones que contradicen el cálculo de EV puro.
"""

class AgenteHibrido_Markov_HiLo(Agente):
    """
    Agente Híbrido que combina un modelo MDP con un conteo Hi-Lo como factor de riesgo.

    1. Calcula el Valor Esperado (EV) de cada acción usando un modelo de Markov
       con probabilidades actualizadas por umbrales.
    2. Mantiene un conteo de cartas Hi-Lo paralelo.
    3. Usa el "Conteo Verdadero" del Hi-Lo para aplicar un "empujón" o "penalización"
       al EV de cada acción, ajustando la decisión final basada en el riesgo situacional.
    """
    def __init__(self, jugador: Jugador, num_mazos: int = 4, recompensas: dict = None, factor_riesgo_escala: float = 0.05):
        """
        Inicializa el agente híbrido.

        Args:
            jugador (Jugador): El objeto jugador que este agente controlará.
            num_mazos (int): El número de mazos en el zapato.
            recompensas (dict, optional): Diccionario para personalizar las recompensas.
            factor_riesgo_escala (float, optional): Controla la influencia del conteo Hi-Lo.
                Un valor más alto hace que el agente sea más sensible al conteo.
        """
        super().__init__(jugador)
        self.num_mazos = num_mazos
        
        self.recompensas = {'victoria': 1.0, 'derrota': -1.0, 'empate': 0.0}
        if recompensas is not None:
            self.recompensas.update(recompensas)
        
        # Nuevo parámetro para la influencia del Hi-Lo
        self.factor_riesgo_escala = factor_riesgo_escala

        self.resetear_conteo()
    
    def set_recompensas(self, nuevas_recompensas: dict):
        self.recompensas.update(nuevas_recompensas)
        
    def set_factor_riesgo(self, nuevo_factor: float):
        """
        Permite actualizar el factor de riesgo que determina la influencia
        del conteo Hi-Lo en las decisiones del agente.

        Args:
            nuevo_factor (float): El nuevo valor para la escala del factor de riesgo.
        """
        self.factor_riesgo_escala = nuevo_factor

    def _get_idx(self, valor_carta: int) -> int:
        if valor_carta == 11: return 0
        return valor_carta - 1 if valor_carta < 10 else 9

    def _actualizar_probabilidades(self):
        total_cartas = np.sum(self.cartas_restantes)
        if total_cartas > 0:
            self.prob_dist_actual = self.cartas_restantes / total_cartas
        else:
            self.prob_dist_actual = np.zeros_like(self.cartas_restantes)

    def observar_carta(self, carta: Carta):
        # --- Lógica del Modelo de Markov ---
        idx = self._get_idx(carta.valor)
        if self.cartas_restantes[idx] > 0:
            self.cartas_restantes[idx] -= 1
            umbral_mitad = self.cartas_iniciales[idx] / 2
            umbral_cero = 0
            if (self.cartas_restantes[idx] == umbral_mitad or 
                self.cartas_restantes[idx] == umbral_cero):
                self._actualizar_probabilidades()
        
        # ================================================================= #
        # === NUEVO: Lógica de conteo Hi-Lo en paralelo === #
        # ================================================================= #
        if carta.valor >= 2 and carta.valor <= 6:
            self.conteo_hilo += 1
        elif carta.valor >= 10: # 10, J, Q, K, As
            self.conteo_hilo -= 1

    def resetear_conteo(self):
        # --- Reseteo para el Modelo de Markov ---
        self.cartas_iniciales = np.array([4 * self.num_mazos] * 9 + [16 * self.num_mazos], dtype=float)
        self.cartas_restantes = self.cartas_iniciales.copy()
        self._actualizar_probabilidades()
        self.memo_valor_estado = {}
        self.memo_outcome_prob = {}
        self.memo_dealer_dist = {}
        
        # ================================================================= #
        # === NUEVO: Reseteo para el conteo Hi-Lo === #
        # ================================================================= #
        self.conteo_hilo = 0
            
    def decidir_apuesta(self, capital_actual: int = None) -> int:
        # (Aquí se podría implementar una apuesta variable basada en el Hi-Lo,
        # pero por ahora lo mantenemos fijo para centrarnos en la estrategia de juego)
        return 5

    # --- Todos los métodos de cálculo de EV (_calcular_ev_*, _get_valor_estado, etc.) ---
    # --- permanecen SIN CAMBIOS. Calculan el EV "puro". ---
    # (Se omite el código de los métodos de cálculo por brevedad, es idéntico al anterior)
    def _calcular_dealer_recursivo(self, mano_dealer: Mano, prob_dist: np.ndarray) -> dict:
        valor_actual = mano_dealer.valor_total
        key_recursiva = (valor_actual, mano_dealer.es_blanda, tuple(prob_dist))
        if key_recursiva in self.memo_dealer_dist:
            return self.memo_dealer_dist[key_recursiva]
        if valor_actual >= 17:
            return {valor_actual: 1.0}
        dist_prob_final = {}
        if np.sum(prob_dist) == 0:
             return {valor_actual: 1.0}
        for i, prob_carta in enumerate(prob_dist):
            if prob_carta > 0:
                valor_carta = 11 if i == 0 else (10 if i == 9 else i + 1)
                nueva_carta = Carta(Palo.PICAS, Rango.from_valor(valor_carta))
                sub_dist = self._calcular_dealer_recursivo(Mano(mano_dealer.cartas + [nueva_carta]), prob_dist)
                for v_final, p_sub in sub_dist.items():
                    dist_prob_final[v_final] = dist_prob_final.get(v_final, 0) + prob_carta * p_sub
        self.memo_dealer_dist[key_recursiva] = dist_prob_final
        return dist_prob_final

    def _get_outcome_probabilities(self, valor_jugador: int, carta_dealer: Carta, prob_dist: np.ndarray) -> tuple[float, float, float]:
        if valor_jugador > 21:
            return (0.0, 1.0, 0.0)
        prob_key = (valor_jugador, carta_dealer.valor, tuple(prob_dist))
        if prob_key in self.memo_outcome_prob:
            return self.memo_outcome_prob[prob_key]
        dist_prob_dealer = self._calcular_dealer_recursivo(Mano([carta_dealer]), prob_dist)
        prob_victoria, prob_derrota, prob_empate = 0.0, 0.0, 0.0
        for valor_final_dealer, prob in dist_prob_dealer.items():
            if valor_final_dealer > 21 or valor_jugador > valor_final_dealer:
                prob_victoria += prob
            elif valor_jugador < valor_final_dealer:
                prob_derrota += prob
            else:
                prob_empate += prob
        resultado = (prob_victoria, prob_derrota, prob_empate)
        self.memo_outcome_prob[prob_key] = resultado
        return resultado

    def _get_valor_estado(self, mano_jugador: Mano, carta_dealer: Carta, prob_dist: np.ndarray) -> float:
        if mano_jugador.valor_total > 21:
            return self.recompensas['derrota']
        estado_key = (mano_jugador.valor_total, mano_jugador.es_blanda, len(mano_jugador.cartas), carta_dealer.valor, tuple(prob_dist))
        if estado_key in self.memo_valor_estado:
            return self.memo_valor_estado[estado_key]
        ev_plantarse = self._calcular_ev_plantarse(mano_jugador.valor_total, carta_dealer, prob_dist)
        ev_pedir = self._calcular_ev_pedir(mano_jugador, carta_dealer, prob_dist)
        valor_optimo = max(ev_plantarse, ev_pedir)
        self.memo_valor_estado[estado_key] = valor_optimo
        return valor_optimo

    def _calcular_ev_plantarse(self, valor_jugador: int, carta_dealer: Carta, prob_dist: np.ndarray) -> float:
        prob_victoria, prob_derrota, prob_empate = self._get_outcome_probabilities(valor_jugador, carta_dealer, prob_dist)
        return (prob_victoria * self.recompensas['victoria'] + 
                prob_derrota * self.recompensas['derrota'] + 
                prob_empate * self.recompensas['empate'])

    def _calcular_ev_doblar(self, mano_jugador: Mano, carta_dealer: Carta, prob_dist: np.ndarray) -> float:
        ev_total = 0.0
        if np.sum(prob_dist) == 0: return self.recompensas['derrota'] * 2
        for i, prob_carta in enumerate(prob_dist):
            if prob_carta > 0:
                valor_carta = 11 if i == 0 else (10 if i == 9 else i + 1)
                nueva_mano = Mano(mano_jugador.cartas + [Carta(Palo.PICAS, Rango.from_valor(valor_carta))])
                prob_victoria, prob_derrota, prob_empate = self._get_outcome_probabilities(nueva_mano.valor_total, carta_dealer, prob_dist)
                ev_una_carta = (prob_victoria * self.recompensas['victoria'] + 
                                prob_derrota * self.recompensas['derrota'] + 
                                prob_empate * self.recompensas['empate'])
                ev_total += prob_carta * (ev_una_carta * 2)
        return ev_total
        
    def _calcular_ev_pedir(self, mano_jugador: Mano, carta_dealer: Carta, prob_dist: np.ndarray) -> float:
        ev_total = 0.0
        if np.sum(prob_dist) == 0:
            return self._calcular_ev_plantarse(mano_jugador.valor_total, carta_dealer, prob_dist)
        for i, prob_carta in enumerate(prob_dist):
            if prob_carta > 0:
                valor_carta = 11 if i == 0 else (10 if i == 9 else i + 1)
                nueva_mano = Mano(mano_jugador.cartas + [Carta(Palo.PICAS, Rango.from_valor(valor_carta))])
                valor_siguiente_estado = self._get_valor_estado(nueva_mano, carta_dealer, prob_dist)
                ev_total += prob_carta * valor_siguiente_estado
        return ev_total
        
    def _calcular_ev_dividir(self, mano_jugador: Mano, carta_dealer: Carta, prob_dist: np.ndarray) -> float:
        carta_dividida_valor = mano_jugador.cartas[0].valor
        mano_dividida = Mano([Carta(Palo.PICAS, Rango.from_valor(carta_dividida_valor))])
        ev_mano = self._get_valor_estado(mano_dividida, carta_dealer, prob_dist)
        return ev_mano * 2

    def decidir_accion(self, mano: Mano, carta_dealer: Carta) -> Accion:
        if mano.es_blackjack or mano.valor_total > 21:
            return Accion.PLANTARSE

        self.memo_valor_estado.clear()
        self.memo_outcome_prob.clear()
        self.memo_dealer_dist.clear()
        
        prob_dist = self.prob_dist_actual
        
        # 1. Calcular los EV puros basados en el modelo de Markov
        acciones_ev = {}
        acciones_ev[Accion.PLANTARSE] = self._calcular_ev_plantarse(mano.valor_total, carta_dealer, prob_dist)
        acciones_ev[Accion.PEDIR] = self._calcular_ev_pedir(mano, carta_dealer, prob_dist)
        
        if len(mano.cartas) == 2:
            acciones_ev[Accion.DOBLAR] = self._calcular_ev_doblar(mano, carta_dealer, prob_dist)
            if mano.cartas[0].valor == mano.cartas[1].valor:
                acciones_ev[Accion.DIVIDIR] = self._calcular_ev_dividir(mano, carta_dealer, prob_dist)
        
        # ================================================================= #
        # === NUEVO: Aplicar el factor de riesgo basado en Hi-Lo === #
        # ================================================================= #
        
        # 2. Calcular el Conteo Verdadero
        mazos_restantes = np.sum(self.cartas_restantes) / 52.0
        if mazos_restantes < 0.5: # Si queda menos de medio mazo, la volatilidad es muy alta
            mazos_restantes = 0.5
        
        conteo_verdadero = self.conteo_hilo / mazos_restantes

        # 3. Aplicar el "empujón" del Hi-Lo si el conteo es significativo
        if conteo_verdadero >= 1 or conteo_verdadero <= -1:
            ajuste = conteo_verdadero * self.factor_riesgo_escala
            
            # Conteo alto (+) aumenta el valor de jugadas agresivas/de espera
            # y penaliza pedir (más riesgo de pasarse).
            # Conteo bajo (-) tiene el efecto contrario.
            if Accion.PLANTARSE in acciones_ev:
                acciones_ev[Accion.PLANTARSE] += ajuste
            if Accion.DOBLAR in acciones_ev:
                acciones_ev[Accion.DOBLAR] += ajuste * 1.5 # Doblar es aún más sensible al conteo
            if Accion.DIVIDIR in acciones_ev:
                acciones_ev[Accion.DIVIDIR] += ajuste * 1.5 # Dividir también
            if Accion.PEDIR in acciones_ev:
                acciones_ev[Accion.PEDIR] -= ajuste # Pedir es más arriesgado con conteo alto

        # 4. Tomar la decisión final con los EV ajustados
        mejor_ev = max(acciones_ev.values())
        
        valor_rendirse = self.recompensas['derrota'] / 2.0
        if len(mano.cartas) == 2 and valor_rendirse > mejor_ev:
            return Accion.RENDIRSE
        
        return max(acciones_ev, key=acciones_ev.get)