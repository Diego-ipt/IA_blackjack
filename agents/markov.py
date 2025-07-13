from .agente_base import Agente
from core.acciones import Accion
from core.player import Jugador, Mano
from core.cartas import Carta, Rango
import numpy as np

"""
MODELO DE DECISIÓN DE MARKOV PARA BLACKJACK 
(SOLO UNA RONDA A LA VEZ)

DEFINICIÓN FORMAL:
==================

Estado (S):
El estado del sistema se define como un vector compuesto S = (S_jugador, S_dealer, cartas_restantes) donde:

S_jugador = (valor_actual_j, num_ases_j, es_blanda_j) representa el estado de la mano del jugador:
  - valor_actual_j ∈ {2, 3, ..., 21}: Valor total actual de la mano del jugador
  - num_ases_j ∈ {0, 1, 2, ..., 4}: Número de ases en la mano del jugador
  - es_blanda_j ∈ {0, 1}: Indicador binario si la mano contiene un as valorado como 11

S_dealer = (carta_visible_d) representa la información observable del dealer:
  - carta_visible_d ∈ {2, 3, ..., 10, 11}: Valor de la carta visible del dealer

cartas_restantes ∈ R^10_+ representa la composición actual del mazo:
  - cartas_restantes = [n_as, n_2, n_3, ..., n_9, n_10] donde n_i ≥ 0
  - Σ cartas_restantes_i = total de cartas restantes en el mazo
  - Se actualiza dinámicamente tras cada extracción de carta

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
    """
    def __init__(self, jugador: Jugador, num_mazos: int = 8):
        super().__init__(jugador)
        self.num_mazos = num_mazos
        
        # Array que contiene el número de cartas que quedan en el mazo
        # [As, 2, 3, 4, 5, 6, 7, 8, 9, 10/J/Q/K]
        self.cartas_restantes = np.array([self.num_mazos * 4] * 9 + [self.num_mazos * 16])  # As, 2-9: 4 por mazo; 10/J/Q/K: 16 por mazo

    def observar_carta(self, carta: Carta):
        """
        Actualiza el array de cartas restantes
        """
        if carta.rango == Rango.AS:
            self.cartas_restantes[0] -= 1
        elif carta.rango.valor >= 2 and carta.rango.valor <= 9:
            self.cartas_restantes[carta.rango.valor - 1] -= 1
        else:  # 10, J, Q, K (todos tienen valor 10)
            self.cartas_restantes[9] -= 1
    
    def resetear_conteo(self):
        """
        Resetea el array de cartas vistas (cuando se baraja el mazo)
        """
        self.cartas_restantes = np.array([self.num_mazos * 4] * 9 + [self.num_mazos * 16])  # As, 2-9: 4 por mazo; 10/J/Q/K: 16 por mazo
        
    def decidir_apuesta(self) -> int:
        """
        Decide la apuesta óptima
        """

    
    def decidir_accion(self, mano: Mano, carta_dealer: Carta) -> Accion:
        """
        Decide la acción óptima usando la política MDP
        """


