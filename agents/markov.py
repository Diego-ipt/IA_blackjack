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
    Agente que implementa la política de juego óptima basada en MDP
    utilizando programación dinámica con memoización.
    """
    def __init__(self, jugador: Jugador, num_mazos: int = 4):
        super().__init__(jugador)
        self.num_mazos = num_mazos
        
        # Array que contiene las cartas restantes en el mazo
        # [As, 2, 3, 4, 5, 6, 7, 8, 9, 10/J/Q/K]
        self.cartas_restantes = np.array([4 * self.num_mazos] * 9 + [16 * self.num_mazos])
        self.memo = {} # Caché para memoización

    def _get_idx(self, valor_carta: int) -> int:
        """Convierte el valor de una carta a su índice en el array de cartas."""
        if valor_carta == 1 or valor_carta == 11:  # As
            return 0
        elif valor_carta <= 9:
            return valor_carta - 1
        else:  # 10, J, Q, K
            return 9

    def observar_carta(self, carta: Carta):
      """
      Actualiza el contador de cartas basado en la carta observada.
      """
      # El As tiene valor 1 en la clase Carta
      idx = self._get_idx(carta.rango.valor)
      if self.cartas_restantes[idx] > 0:
        self.cartas_restantes[idx] -= 1

    def resetear_conteo(self):
        """
        Resetea las cartas restantes y la caché de memoización para una nueva ronda.
        """
        self.cartas_restantes = np.array([4 * self.num_mazos] * 9 + [16 * self.num_mazos])
        self.memo = {}

    def decidir_apuesta(self, capital_actual: int = None) -> int:
        """
        Decide la apuesta.
        Se usara una apuesta fija del 5% del capital por ahora.
        """
        capital = capital_actual if capital_actual is not None else self.jugador.capital
        apuesta_base = int(capital * 0.05)
        return max(10, apuesta_base)
    
    def _calcular_ev_plantarse(self, valor_jugador: int, carta_dealer: Carta, cartas_restantes: np.ndarray) -> float:
        """
        Calcula el Valor Esperado (EV) de plantarse.
        Simula el turno del dealer para determinar las probabilidades de ganar, perder o empatar.
        """
        # El estado para la simulación del dealer solo necesita su carta inicial y las cartas restantes
        estado_dealer_key = (carta_dealer.valor, tuple(cartas_restantes))
        if estado_dealer_key in self.memo:
            dist_prob_dealer = self.memo[estado_dealer_key]
        else:
            dist_prob_dealer = self._simular_dealer(Mano([carta_dealer]), cartas_restantes.copy())
            self.memo[estado_dealer_key] = dist_prob_dealer

        ev = 0.0
        for valor_final_dealer, prob in dist_prob_dealer.items():
            if valor_jugador > 21: # El jugador ya se pasó
                ev -= prob
            elif valor_final_dealer > 21 or valor_jugador > valor_final_dealer:
                ev += prob # Jugador gana
            elif valor_jugador < valor_final_dealer:
                ev -= prob # Jugador pierde
            # Si son iguales, es un empate (EV = 0), por lo que no se suma ni se resta.
        return ev

    def _simular_dealer(self, mano_dealer: Mano, cartas_restantes: np.ndarray) -> dict:
        """
        Función recursiva para simular todas las posibles manos del dealer y sus probabilidades.
        Devuelve un diccionario {valor_final: probabilidad}.
        """
        valor_actual = mano_dealer.valor_total
        if valor_actual >= 17:
            # El dealer se planta.
            return {valor_actual: 1.0}

        dist_prob_final = {}
        total_cartas = np.sum(cartas_restantes)
        if total_cartas == 0:
             return {valor_actual: 1.0}

        for i, count in enumerate(cartas_restantes):
            if count > 0:
                prob_carta = count / total_cartas
                valor_carta = i + 1
                
                nuevas_cartas_restantes = cartas_restantes.copy()
                nuevas_cartas_restantes[i] -= 1
                
                # Crea la nueva carta (el palo no importa para el valor)
                nueva_carta = Carta(Palo.PICAS, Rango.from_valor(valor_carta))
                
                # Simula recursivamente
                dist_sub_problema = self._simular_dealer(Mano(mano_dealer.cartas + [nueva_carta]), nuevas_cartas_restantes)
                
                for valor_final, prob_sub in dist_sub_problema.items():
                    dist_prob_final[valor_final] = dist_prob_final.get(valor_final, 0) + prob_carta * prob_sub
        
        return dist_prob_final

    def _calcular_ev_pedir(self, mano_jugador: Mano, carta_dealer: Carta, cartas_restantes: np.ndarray) -> float:
        """Calcula el EV de pedir una carta."""
        ev_total = 0.0
        total_cartas = np.sum(cartas_restantes)

        for i, count in enumerate(cartas_restantes):
            if count > 0:
                prob_carta = count / total_cartas
                valor_carta = i + 1

                nuevas_cartas_restantes = cartas_restantes.copy()
                nuevas_cartas_restantes[i] -= 1
                
                nueva_carta = Carta(Palo.PICAS, Rango.from_valor(valor_carta))
                nueva_mano = Mano(mano_jugador.cartas + [nueva_carta])

                # El valor de pedir es el promedio ponderado del valor del siguiente estado
                valor_siguiente_estado = self._get_valor_estado(nueva_mano, carta_dealer, nuevas_cartas_restantes)
                ev_total += prob_carta * valor_siguiente_estado
        
        return ev_total

    def _calcular_ev_doblar(self, mano_jugador: Mano, carta_dealer: Carta, cartas_restantes: np.ndarray) -> float:
        """Calcula el EV de doblar la apuesta."""
        ev_total = 0.0
        total_cartas = np.sum(cartas_restantes)

        for i, count in enumerate(cartas_restantes):
            if count > 0:
                prob_carta = count / total_cartas
                valor_carta = i + 1

                nuevas_cartas_restantes = cartas_restantes.copy()
                nuevas_cartas_restantes[i] -= 1

                nueva_carta = Carta(Palo.PICAS, Rango.from_valor(valor_carta))
                nueva_mano = Mano(mano_jugador.cartas + [nueva_carta])
                
                if nueva_mano.valor_total > 21:
                    ev_total += prob_carta * (-2.0) # Se pasa, pierde el doble
                else:
                    # El valor se calcula plantándose con la nueva mano, pero con recompensa x2
                    ev_plantarse_doblado = self._calcular_ev_plantarse(nueva_mano.valor_total, carta_dealer, nuevas_cartas_restantes) * 2.0
                    ev_total += prob_carta * ev_plantarse_doblado
        
        return ev_total
    
    def _calcular_ev_dividir(self, mano_jugador: Mano, carta_dealer: Carta, cartas_restantes: np.ndarray) -> float:
        """
        Calcula el EV de dividir la mano.
        Aproximación: Se asume que las dos manos se juegan de forma independiente.
        El EV es la suma del valor de cada nueva mano.
        """
        carta_dividida_valor = mano_jugador.cartas[0].valor
        
        # Valor de la primera mano
        mano1 = Mano([Carta(Palo.PICAS, Rango.from_valor(carta_dividida_valor))])
        # Nota: Un cálculo más preciso actualizaría las cartas restantes entre las dos manos.
        # Por simplicidad y rendimiento, aquí usamos el mismo mazo para ambas.
        ev_mano1 = self._get_valor_estado(mano1, carta_dealer, cartas_restantes.copy())
        
        # El EV de dividir es la suma de los EVs de las dos manos resultantes
        return ev_mano1 * 2

    def _get_valor_estado(self, mano_jugador: Mano, carta_dealer: Carta, cartas_restantes: np.ndarray) -> float:
        """
        Función principal de la programación dinámica.
        Devuelve el máximo EV alcanzable desde el estado (mano, dealer, cartas) dado.
        Utiliza memoización para evitar recalcular estados.
        """
        # Crear una clave única para el estado actual
        estado_key = (mano_jugador.valor_total, mano_jugador.es_blanda, len(mano_jugador.cartas), carta_dealer.valor, tuple(cartas_restantes))
        if estado_key in self.memo:
            return self.memo[estado_key]

        # Condición de término: si el jugador se pasa, el valor es -1 (pierde la apuesta)
        if mano_jugador.valor_total > 21:
            return -1.0

        # --- Calcular EV de cada acción posible desde este estado ---
        
        # 1. Plantarse siempre es una opción
        ev_plantarse = self._calcular_ev_plantarse(mano_jugador.valor_total, carta_dealer, cartas_restantes)
        
        # 2. Pedir es una opción si no se ha pasado
        ev_pedir = self._calcular_ev_pedir(mano_jugador, carta_dealer, cartas_restantes)

        # La política óptima es elegir la acción con el EV más alto
        valor_optimo = max(ev_plantarse, ev_pedir)
        
        # Guardar el resultado en la caché antes de devolverlo
        self.memo[estado_key] = valor_optimo
        return valor_optimo

    def decidir_accion(self, mano: Mano, carta_dealer: Carta) -> Accion:
        """
        Decide la acción óptima usando las probabilidades del MDP.
        """
        self.memo = {} # Limpiar caché para cada nueva decisión
        
        # Casos especiales que no requieren cálculo recursivo
        if mano.es_blackjack:
            return Accion.PLANTARSE
        if mano.valor_total > 21:
            return Accion.PLANTARSE # Ya se pasó, única acción es terminar

        acciones_ev = {}

        # 1. Acción PLANTARSE
        acciones_ev[Accion.PLANTARSE] = self._calcular_ev_plantarse(mano.valor_total, carta_dealer, self.cartas_restantes.copy())
        
        # 2. Acción PEDIR
        acciones_ev[Accion.PEDIR] = self._calcular_ev_pedir(mano, carta_dealer, self.cartas_restantes.copy())
        
        # 3. Acción DOBLAR (solo con 2 cartas)
        if len(mano.cartas) == 2:
            acciones_ev[Accion.DOBLAR] = self._calcular_ev_doblar(mano, carta_dealer, self.cartas_restantes.copy())

        # 4. Acción DIVIDIR (solo con 2 cartas del mismo valor)
        if len(mano.cartas) == 2 and mano.cartas[0].rango.valor == mano.cartas[1].rango.valor:
            acciones_ev[Accion.DIVIDIR] = self._calcular_ev_dividir(mano, carta_dealer, self.cartas_restantes.copy())

        # La acción de rendirse tiene un EV fijo de -0.5
        # Solo se permite con las dos primeras cartas.
        # Solo consideramos rendirnos si es mejor que cualquier otra opción.
        if len(mano.cartas) == 2:
            mejor_ev = max(acciones_ev.values())
            if -0.5 > mejor_ev:
                return Accion.RENDIRSE
        
        # Seleccionar la acción con el mayor valor esperado
        accion_optima = max(acciones_ev, key=acciones_ev.get)
        
        return accion_optima