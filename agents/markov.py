from .agente_base import Agente
from core.acciones import Accion
from core.player import Jugador, Mano
from core.cartas import Carta, Rango, Palo
import numpy as np

"""
MODELO DE DECISIÓN DE MARKOV PARA BLACKJACK 
(SOLO UNA RONDA A LA VEZ)

DEFINICIÓN FORMAL:
==================

Estado (S):
El estado del sistema se define como un vector compuesto S = (S_jugador, S_dealer, probabilidades_cartas) donde:

S_jugador = (valor_actual_j, num_ases_j, es_blanda_j) representa el estado de la mano del jugador:
  - valor_actual_j ∈ {2, 3, ..., 21}: Valor total actual de la mano del jugador
  - num_ases_j ∈ {0, 1, 2, ..., 4}: Número de ases en la mano del jugador
  - es_blanda_j ∈ {0, 1}: Indicador binario si la mano contiene un as valorado como 11

S_dealer = (carta_visible_d) representa la información observable del dealer:
  - carta_visible_d ∈ {2, 3, ..., 10, 11}: Valor de la carta visible del dealer

probabilidades_cartas ∈ R^10 representa las probabilidades de extracción del mazo:
  - probabilidades_cartas = [p_as, p_2, p_3, ..., p_9, p_10] donde p_i ∈ [0,1]
  - Σ probabilidades_cartas_i = 1 (distribución de probabilidad válida)
  - Se actualiza dinámicamente tras cada extracción de carta usando teorema de Bayes

Acciones (A):
- A = {PLANTARSE, PEDIR, DOBLAR, DIVIDIR, RENDIRSE}
- Cada acción lleva a diferentes nodos de evaluación

Función de Transición (P):
- P(s'|s,a) = Probabilidad de transitar del estado s al estado s' tomando la acción A
- Depende de las cartas restantes en el mazo y la acción elegida

Función de Recompensa (R):
- PLANTARSE: R ∈ {-1, 0, +1} según (derrota, empate, victoria)
- DOBLAR: R ∈ {-2, 0, +2} según (derrota, empate, victoria)  
- RENDIRSE: R = -0.5 (pérdida fija del 50% de la apuesta)
- PEDIR: R = 0 (recompensa diferida hasta acción terminal)
- DIVIDIR: R = suma de recompensas de cada mano dividida
- PASARSE DE 21: R = -1 (pérdida total de la apuesta)

Política Óptima (π*):
- π*(s) = argmax_a Q*(s,a): Política que maximiza el valor Q en cada estado
- Q*(s,a) = R(s,a) + γ Σ_s' P(s'|s,a) V*(s'): Función de valor Q óptima
- V*(s) = max_a Q*(s,a): Función de valor de estado óptima
- γ = 1 (sin descuento temporal, ya que el juego termina en tiempo finito)

Para acciones terminales (PLANTARSE, DOBLAR, RENDIRSE):
  Q*(s,a) = Σ_i P(resultado_i) * R(resultado_i)
  Donde resultado_i ∈ {victoria, empate, derrota}

Para acción PEDIR:
  Q*(s,PEDIR) = Σ_c P(carta_c) * V*(s')
  Donde s' es el nuevo estado después de recibir carta c

Para acción DIVIDIR:
  Q*(s,DIVIDIR) = V*(s1') + V*(s2')
  Donde s1' y s2' son los estados de cada mano dividida

La política óptima π*(s) selecciona la acción que maximiza Q*(s,a) para cada estado s.

ESTRUCTURA DE NODOS:
===================

Nodo Raíz (Estado Inicial):
├── PLANTARSE → Nodo Terminal: Probabilidades {P(victoria), P(empate), P(derrota)}
├── DOBLAR → Nodo Terminal: Probabilidades {P(victoria), P(empate), P(derrota)} 
├── DIVIDIR → Dos Nodos Raíz (una por cada mano dividida)
├── RENDIRSE → Nodo Terminal: Recompensa fija -0.5
└── PEDIR → Nuevo Nodo de Maximización (estado s')
    ├── PASARSE DE 21 → Nodo Terminal {Recompensa fija -1}
    └── SIGUE EN JUEGO → Nuevo Nodo de Maximización (estado s'')    
        ├── PEDIR → Nuevo Nodo de Maximización (estado s''') y asi sucesivamente
        ├── PLANTARSE → Nodo Terminal: Probabilidades {P(victoria), P(empate), P(derrota)}
        └── PASARSE DE 21 → Nodo Terminal {Recompensa fija -1}

Cálculo de Probabilidades:
- P(victoria) = P(dealer_se_pasa AND valor_jugador <= 21) + P(dealer_valor < valor_jugador AND dealer_valor <= 21 AND valor_jugador <= 21)
- P(empate) = P(dealer_valor == valor_jugador AND dealer_valor <= 21 AND valor_jugador <= 21)
- P(derrota) = P(dealer_valor > valor_jugador AND dealer_valor <= 21 AND valor_jugador <= 21) + P(jugador_se_pasa)

Las probabilidades se calculan usando las cartas restantes en el mazo y simulando
el comportamiento determinista del dealer (pedir hasta 17+).
"""

class AgenteMarkov(Agente):
    """
    Agente MDP con una arquitectura de caché de 3 niveles para máxima eficiencia.
    1. memo_dealer_dist: Almacena la distribución de la mano final del dealer.
    2. memo_outcome_prob: Almacena las probabilidades de resultado (win/loss/tie).
    3. memo_valor_estado: Almacena el valor de los estados de decisión para la recursión de DP.
    Los cachés persisten entre decisiones y solo se resetean al barajar el mazo.
    """
    def __init__(self, jugador: Jugador, num_mazos: int = 4):
        super().__init__(jugador)
        self.num_mazos = num_mazos
        self.resetear_conteo() # Inicializa todo

    def _get_idx(self, valor_carta: int) -> int:
        if valor_carta == 11: return 0
        return valor_carta - 1 if valor_carta < 10 else 9

    def observar_carta(self, carta: Carta):
        idx = self._get_idx(carta.valor)
        if self.cartas_restantes[idx] > 0:
            self.cartas_restantes[idx] -= 1

    def resetear_conteo(self):
        """Resetea todos los cachés y las cartas. Se llama solo al barajar."""
        self.cartas_restantes = np.array([4 * self.num_mazos] * 9 + [16 * self.num_mazos])
        self.memo_valor_estado = {}
        self.memo_outcome_prob = {}
        self.memo_dealer_dist = {}
            
    def decidir_apuesta(self, capital_actual: int = None) -> int:
        capital = capital_actual if capital_actual is not None else self.jugador.capital
        apuesta_base = int(capital * 0.05)
        return max(10, apuesta_base) if capital > 10 else 0

    def _simular_dealer(self, mano_dealer: Mano, cartas_restantes: np.ndarray) -> dict:
        """
        Calcula y memoiza la distribución de probabilidad de la mano final del dealer.
        Este es el "subcomponente" fundamental y más reutilizable.
        """
        valor_actual = mano_dealer.valor_total
        key = (valor_actual, mano_dealer.es_blanda, tuple(cartas_restantes))
        
        if key in self.memo_dealer_dist:
            return self.memo_dealer_dist[key]

        if valor_actual >= 17:
            return {valor_actual: 1.0}

        dist_prob_final = {}
        total_cartas = np.sum(cartas_restantes)
        if total_cartas == 0:
             return {valor_actual: 1.0}

        for i, count in enumerate(cartas_restantes):
            if count > 0:
                # ... (lógica de recursión, sin cambios) ...
                prob_carta = count / total_cartas
                valor_carta = 11 if i == 0 else i + 1
                nuevas_cartas_restantes = cartas_restantes.copy()
                nuevas_cartas_restantes[i] -= 1
                nueva_carta = Carta(Palo.PICAS, Rango.from_valor(valor_carta))
                sub_dist = self._simular_dealer(Mano(mano_dealer.cartas + [nueva_carta]), nuevas_cartas_restantes)
                for v_final, p_sub in sub_dist.items():
                    dist_prob_final[v_final] = dist_prob_final.get(v_final, 0) + prob_carta * p_sub
        
        self.memo_dealer_dist[key] = dist_prob_final
        return dist_prob_final

    def _get_outcome_probabilities(self, valor_jugador: int, carta_dealer: Carta, cartas_restantes: np.ndarray) -> tuple[float, float, float]:
        """
        Usa la distribución del dealer (del caché profundo) para calcular y memoizar
        las probabilidades de resultado (victoria, derrota, empate).
        """
        if valor_jugador > 21:
            return (0.0, 1.0, 0.0)

        prob_key = (valor_jugador, carta_dealer.valor, tuple(cartas_restantes))
        if prob_key in self.memo_outcome_prob:
            return self.memo_outcome_prob[prob_key]

        # 1. Obtener el subcomponente: la distribución del dealer (esto estará fuertemente cacheado)
        dist_prob_dealer = self._simular_dealer(Mano([carta_dealer]), cartas_restantes)

        # 2. Calcular las probabilidades finales usando la distribución del dealer
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

    def _calcular_ev_plantarse(self, valor_jugador: int, carta_dealer: Carta, cartas_restantes: np.ndarray) -> float:
        prob_victoria, prob_derrota, _ = self._get_outcome_probabilities(valor_jugador, carta_dealer, cartas_restantes)
        return prob_victoria - prob_derrota

    def _calcular_ev_doblar(self, mano_jugador: Mano, carta_dealer: Carta, cartas_restantes: np.ndarray) -> float:
        ev_total = 0.0
        total_cartas = np.sum(cartas_restantes)
        if total_cartas == 0: return -2.0

        for i, count in enumerate(cartas_restantes):
            if count > 0:
                prob_carta = count / total_cartas
                valor_carta = 11 if i == 0 else i + 1
                
                nuevas_cartas_restantes = cartas_restantes.copy()
                nuevas_cartas_restantes[i] -= 1
                
                nueva_mano = Mano(mano_jugador.cartas + [Carta(Palo.PICAS, Rango.from_valor(valor_carta))])
                
                prob_victoria, prob_derrota, _ = self._get_outcome_probabilities(nueva_mano.valor_total, carta_dealer, nuevas_cartas_restantes)
                ev_doblado = (prob_victoria * 2) - (prob_derrota * 2)
                ev_total += prob_carta * ev_doblado
        return ev_total
        
    def _calcular_ev_pedir(self, mano_jugador: Mano, carta_dealer: Carta, cartas_restantes: np.ndarray) -> float:
        ev_total = 0.0
        total_cartas = np.sum(cartas_restantes)

        for i, count in enumerate(cartas_restantes):
            if count > 0:
                prob_carta = count / total_cartas
                valor_carta = 11 if i == 0 else i + 1
                
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
            return -1.0

        estado_key = (mano_jugador.valor_total, mano_jugador.es_blanda, len(mano_jugador.cartas), carta_dealer.valor, tuple(cartas_restantes))
        if estado_key in self.memo_valor_estado:
            return self.memo_valor_estado[estado_key]

        ev_plantarse = self._calcular_ev_plantarse(mano_jugador.valor_total, carta_dealer, cartas_restantes)
        ev_pedir = self._calcular_ev_pedir(mano_jugador, carta_dealer, cartas_restantes)

        valor_optimo = max(ev_plantarse, ev_pedir)
        self.memo_valor_estado[estado_key] = valor_optimo
        return valor_optimo

    def decidir_accion(self, mano: Mano, carta_dealer: Carta) -> Accion:
        """
        Decide la acción óptima. YA NO LIMPIA LOS CACHÉS.
        Los cachés ahora persisten durante todo el zapato.
        """
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
        if len(mano.cartas) == 2 and -0.5 > mejor_ev:
            return Accion.RENDIRSE
        
        return max(acciones_ev, key=acciones_ev.get)