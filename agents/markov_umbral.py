import numpy as np
from .agente_base import Agente
from core.acciones import Accion
from core.player import Jugador, Mano
from core.cartas import Carta, Rango, Palo

class AgenteMarkov_prob_estable_por_umbral(Agente):
    """
    Agente MDP con una estrategia de probabilidad estable actualizada por umbrales.

    Este agente opera con una distribución de probabilidad fija. Esta distribución
    solo se recalcula y actualiza para todas las decisiones futuras en el momento
    exacto en que el conteo de cualquier subconjunto de cartas (por ejemplo, Ases)
    cae a la mitad de su cantidad inicial.

    Este enfoque minimiza los cálculos en cada turno, pero permite que el agente
    se adapte a cambios significativos y predefinidos en la composición del mazo.
    """
    def __init__(self, jugador: Jugador, num_mazos: int = 4):
        super().__init__(jugador)
        self.num_mazos = num_mazos
        self.resetear_conteo()

    def _get_idx(self, valor_carta: int) -> int:
        if valor_carta == 11: return 0  # As
        return valor_carta - 1 if valor_carta < 10 else 9

    def _actualizar_probabilidades(self):
        """
        Recalcula la distribución de probabilidad actual basándose en el
        conteo de cartas restantes. Esta función es el núcleo de la estrategia
        y solo se llama cuando se cruza un umbral.
        """
        total_cartas = np.sum(self.cartas_restantes)
        if total_cartas > 0:
            self.prob_dist_actual = self.cartas_restantes / total_cartas
        else:
            self.prob_dist_actual = np.zeros_like(self.cartas_restantes)
        # Opcional: Descomentar para ver cuándo ocurren las actualizaciones
        # print(f"--- PROBABILIDADES ACTUALIZADAS. Total cartas: {total_cartas} ---")

    def observar_carta(self, carta: Carta):
        """
        Reduce el conteo de la carta observada y comprueba si se ha alcanzado
        un umbral (50% o cero) para recalcular las probabilidades.
        """
        idx = self._get_idx(carta.valor)
        
        # Solo procesar si todavía quedan cartas de este tipo
        if self.cartas_restantes[idx] > 0:
            self.cartas_restantes[idx] -= 1
            
            # Definir los umbrales para esta carta
            umbral_mitad = self.cartas_iniciales[idx] / 2
            umbral_cero = 0
            
            # ================================================================= #
            # === CAMBIO: Se activa la actualización si se alcanza la mitad O si se llega a cero === #
            if (self.cartas_restantes[idx] == umbral_mitad or 
                self.cartas_restantes[idx] == umbral_cero):
                self._actualizar_probabilidades()
            # ================================================================= #

    def resetear_conteo(self):
        """Resetea los contadores de cartas, las cachés y la probabilidad actual."""
        self.cartas_iniciales = np.array([4 * self.num_mazos] * 9 + [16 * self.num_mazos], dtype=float)
        self.cartas_restantes = self.cartas_iniciales

        # Establecer la distribución de probabilidad inicial
        self._actualizar_probabilidades()
        
        self.memo_valor_estado = {}
        self.memo_outcome_prob = {}
        self.memo_dealer_dist = {}
            
    def decidir_apuesta(self, capital_actual: int = None) -> int:
        return 5  # Apuesta fija

    def _calcular_dealer_recursivo(self, mano_dealer: Mano, prob_dist: np.ndarray) -> dict:
        """Calcula la distribución de resultados del dealer usando la dist. de probabilidad dada."""
        valor_actual = mano_dealer.valor_total
        
        # ================================================================================= #
        # === CAMBIO: La clave de la caché AHORA incluye la distribución de probabilidad. === #
        key_recursiva = (valor_actual, mano_dealer.es_blanda, tuple(prob_dist))
        # ================================================================================= #
        
        # El nombre del caché debe ser único para esta función para evitar colisiones
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
        
        # ================================================================================= #
        # === CAMBIO: La clave de la caché AHORA incluye la distribución de probabilidad. === #
        prob_key = (valor_jugador, carta_dealer.valor, tuple(prob_dist))
        # ================================================================================= #

        if prob_key in self.memo_outcome_prob:
            return self.memo_outcome_prob[prob_key]

        # No es necesario limpiar el caché del dealer aquí si la clave ya incluye la prob_dist
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
            return -1.0

        # ================================================================================= #
        # === CAMBIO: La clave de la caché AHORA incluye la distribución de probabilidad. === #
        estado_key = (mano_jugador.valor_total, mano_jugador.es_blanda, len(mano_jugador.cartas), carta_dealer.valor, tuple(prob_dist))
        # ================================================================================= #
        
        if estado_key in self.memo_valor_estado:
            return self.memo_valor_estado[estado_key]

        ev_plantarse = self._calcular_ev_plantarse(mano_jugador.valor_total, carta_dealer, prob_dist)
        ev_pedir = self._calcular_ev_pedir(mano_jugador, carta_dealer, prob_dist)

        valor_optimo = max(ev_plantarse, ev_pedir)
        self.memo_valor_estado[estado_key] = valor_optimo
        return valor_optimo

    def _calcular_ev_plantarse(self, valor_jugador: int, carta_dealer: Carta, prob_dist: np.ndarray) -> float:
        prob_victoria, prob_derrota, _ = self._get_outcome_probabilities(valor_jugador, carta_dealer, prob_dist)
        return prob_victoria - prob_derrota

    def _calcular_ev_doblar(self, mano_jugador: Mano, carta_dealer: Carta, prob_dist: np.ndarray) -> float:
        ev_total = 0.0
        if np.sum(prob_dist) == 0: return -2.0

        for i, prob_carta in enumerate(prob_dist):
            if prob_carta > 0:
                valor_carta = 11 if i == 0 else (10 if i == 9 else i + 1)
                nueva_mano = Mano(mano_jugador.cartas + [Carta(Palo.PICAS, Rango.from_valor(valor_carta))])
                prob_victoria, prob_derrota, _ = self._get_outcome_probabilities(nueva_mano.valor_total, carta_dealer, prob_dist)
                ev_doblado = (prob_victoria * 2) - (prob_derrota * 2)
                ev_total += prob_carta * ev_doblado
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
        carta_dividida_valor = mano_jugador.cartas.valor
        mano_dividida = Mano([Carta(Palo.PICAS, Rango.from_valor(carta_dividida_valor))])
        ev_mano = self._get_valor_estado(mano_dividida, carta_dealer, prob_dist)
        return ev_mano * 2

  
    def decidir_accion(self, mano: Mano, carta_dealer: Carta) -> Accion:
        if mano.es_blackjack or mano.valor_total > 21:
            return Accion.PLANTARSE

        prob_dist = self.prob_dist_actual
        
        acciones_ev = {}
        acciones_ev[Accion.PLANTARSE] = self._calcular_ev_plantarse(mano.valor_total, carta_dealer, prob_dist)
        acciones_ev[Accion.PEDIR] = self._calcular_ev_pedir(mano, carta_dealer, prob_dist)
        
        # Solo considerar doblar o dividir si el jugador tiene dos cartas
        if len(mano.cartas) == 2:
            acciones_ev[Accion.DOBLAR] = self._calcular_ev_doblar(mano, carta_dealer, prob_dist)
            
            if mano.cartas[0].valor == mano.cartas[1].valor:
                acciones_ev[Accion.DIVIDIR] = self._calcular_ev_dividir(mano, carta_dealer, prob_dist)
                
        mejor_ev = max(acciones_ev.values())
        
        # La opción de rendirse solo está disponible en la primera jugada
        if len(mano.cartas) == 2 and -0.5 > mejor_ev:
            return Accion.RENDIRSE
        
        return max(acciones_ev, key=acciones_ev.get)