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
class AgenteMarkov_arriesgado(Agente):
    """
    Agente MDP con una arquitectura de caché y AGRUPACIÓN DE ESTADOS.
    *** VERSIÓN EXPERIMENTAL CON RECOMPENSAS MODIFICADAS ***
    - Victoria: +2
    - Empate: -1
    - Derrota: -2
    """
    def __init__(self, jugador: Jugador, num_mazos: int = 4, precision_agrupacion: int = 20):
        super().__init__(jugador)
        self.num_mazos = num_mazos
        self.precision_agrupacion = precision_agrupacion
        self.resetear_conteo()

    # ... (funciones _get_idx, observar_carta, resetear_conteo, decidir_apuesta sin cambios) ...
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
    
    # ... (funciones de bucketing _crear_clave_agrupada, _calcular_dealer_recursivo sin cambios) ...
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

    # --- LÓGICA DE SIMULACIÓN Y CÁLCULO DE EV (SIN CAMBIOS EN SU ESTRUCTURA, PERO SÍ EN LAS RECOMPENSAS) ---
    def _simular_dealer(self, mano_dealer: Mano, cartas_restantes: np.ndarray) -> dict:
        clave_agrupada = self._crear_clave_agrupada(cartas_restantes)
        cache_key = (mano_dealer.valor_total, mano_dealer.es_blanda, clave_agrupada)
        if cache_key in self.memo_dealer_dist:
            return self.memo_dealer_dist[cache_key]
        else:
            dist_calculada = self._calcular_dealer_recursivo(mano_dealer, cartas_restantes)
            self.memo_dealer_dist[cache_key] = dist_calculada
            return dist_calculada

    def _get_outcome_probabilities(self, valor_jugador: int, carta_dealer: Carta, cartas_restantes: np.ndarray) -> tuple[float, float, float]:
        if valor_jugador > 21:
            return (0.0, 1.0, 0.0)
        
        clave_agrupada = self._crear_clave_agrupada(cartas_restantes)
        prob_key = (valor_jugador, carta_dealer.valor, clave_agrupada)

        if prob_key in self.memo_outcome_prob:
            return self.memo_outcome_prob[prob_key]

        dist_prob_dealer = self._simular_dealer(Mano([carta_dealer]), cartas_restantes)

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
        prob_victoria, prob_derrota, prob_empate = self._get_outcome_probabilities(valor_jugador, carta_dealer, cartas_restantes)
        # ================================================================= #
        # === CAMBIO: Nueva fórmula de EV para la acción de plantarse. === #
        return (prob_victoria * 2) - (prob_derrota * 2) - prob_empate
        # ================================================================= #

    def _calcular_ev_doblar(self, mano_jugador: Mano, carta_dealer: Carta, cartas_restantes: np.ndarray) -> float:
        ev_total = 0.0
        total_cartas = np.sum(cartas_restantes)
        # ================================================================= #
        # === CAMBIO: La recompensa por pasarse al doblar ahora es -4. === #
        if total_cartas == 0: return -4.0
        # ================================================================= #

        for i, count in enumerate(cartas_restantes):
            if count > 0:
                prob_carta = count / total_cartas
                valor_carta = 11 if i == 0 else (10 if i == 9 else i + 1)
                
                nuevas_cartas_restantes = cartas_restantes.copy()
                nuevas_cartas_restantes[i] -= 1
                
                nueva_mano = Mano(mano_jugador.cartas + [Carta(Palo.PICAS, Rango.from_valor(valor_carta))])
                
                prob_victoria, prob_derrota, prob_empate = self._get_outcome_probabilities(nueva_mano.valor_total, carta_dealer, nuevas_cartas_restantes)
                # ================================================================================== #
                # === CAMBIO: Nueva fórmula de EV para cada resultado posible al doblar la apuesta. === #
                ev_doblado = (prob_victoria * 4) - (prob_derrota * 4) - (prob_empate * 2)
                # ================================================================================== #
                ev_total += prob_carta * ev_doblado
        return ev_total
        
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
        # La lógica de dividir se mantiene: el EV es la suma de los EVs de las dos nuevas manos.
        # El cambio en las recompensas se propagará automáticamente a través de la llamada a _get_valor_estado.
        carta_dividida_valor = mano_jugador.cartas[0].valor
        mano_dividida = Mano([Carta(Palo.PICAS, Rango.from_valor(carta_dividida_valor))])
        ev_mano = self._get_valor_estado(mano_dividida, carta_dealer, cartas_restantes.copy())
        return ev_mano * 2

    def _get_valor_estado(self, mano_jugador: Mano, carta_dealer: Carta, cartas_restantes: np.ndarray) -> float:
        # ================================================================================= #
        # === CAMBIO: La recompensa por pasarse ahora es -2, en línea con una derrota. === #
        if mano_jugador.valor_total > 21:
            return -2.0
        # ================================================================================= #

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
        
        # ========================================================================================== #
        # === CAMBIO: El valor de la rendición ahora se compara con -1 en la nueva escala de EV. === #
        if len(mano.cartas) == 2 and -1.0 > mejor_ev:
            return Accion.RENDIRSE
        # ========================================================================================== #
        
        return max(acciones_ev, key=acciones_ev.get)
    

    
class AgenteMarkov_normal(Agente):
    """
    Agente MDP que utiliza una clave de caché AGRUPADA para una eficiencia drásticamente mejorada.
    En lugar de usar el estado exacto del mazo, agrupa las cartas restantes en porcentajes
    discretizados, permitiendo una reutilización masiva de los cálculos.
    """
    def __init__(self, jugador: Jugador, num_mazos: int = 4, precision_agrupacion: int = 20):
        super().__init__(jugador)
        self.num_mazos = num_mazos
        # La precisión define en cuántos "buckets" se divide cada porcentaje. 
        # 10 = buckets de 10%. 20 = buckets de 5%.
        self.precision_agrupacion = precision_agrupacion
        self.resetear_conteo()

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
        # Por ahora, apuesta fija para centrarnos en la estrategia de juego.
        return int(5)

    # --- NUEVAS FUNCIONES PARA AGRUPACIÓN DE ESTADOS ---

    def _crear_clave_agrupada(self, cartas_restantes: np.ndarray) -> tuple:
        """
        Convierte el vector de cartas restantes en una clave simplificada y de baja dimensionalidad.
        Esta es la clave para resolver el problema de rendimiento.
        """
        total_restantes = np.sum(cartas_restantes)
        if total_restantes == 0:
            return (0, 0, 0, 0) # Estado especial para mazo vacío

        # Agrupar cartas: Ases, Bajas (2-6), Medias (7-9), Altas (10s)
        num_ases = cartas_restantes[0]
        num_bajas = np.sum(cartas_restantes[1:6])
        num_medias = np.sum(cartas_restantes[6:9])
        num_altas = cartas_restantes[9]

        # Calcular porcentajes y discretizarlos ("bucketing")
        p = self.precision_agrupacion
        porc_ases_d = int( (num_ases / total_restantes) * p )
        porc_bajas_d = int( (num_bajas / total_restantes) * p )
        porc_medias_d = int( (num_medias / total_restantes) * p )
        porc_altas_d = int( (num_altas / total_restantes) * p )
        
        return (porc_ases_d, porc_bajas_d, porc_medias_d, porc_altas_d)

    def _calcular_dealer_recursivo(self, mano_dealer: Mano, cartas_restantes: np.ndarray) -> dict:
        """
        La función de cálculo de "fuerza bruta" original. Se llama solo cuando
        un estado agrupado no se encuentra en el caché.
        """
        valor_actual = mano_dealer.valor_total
        
        # OJO: Se usa una clave EXACTA para la recursión interna para garantizar la corrección.
        # El caché aquí es temporal, solo para esta llamada de fuerza bruta.
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
        """
        Función directora: Intenta usar el caché con una clave agrupada. Si falla,
        realiza el cálculo completo y almacena el resultado bajo esa clave agrupada.
        """
        clave_agrupada = self._crear_clave_agrupada(cartas_restantes)
        
        # La clave para el caché principal incluye la mano inicial del dealer
        cache_key = (mano_dealer.valor_total, mano_dealer.es_blanda, clave_agrupada)

        if cache_key in self.memo_dealer_dist:
            return self.memo_dealer_dist[cache_key]
        else:
            dist_calculada = self._calcular_dealer_recursivo(mano_dealer, cartas_restantes)
            self.memo_dealer_dist[cache_key] = dist_calculada
            return dist_calculada

    def _get_outcome_probabilities(self, valor_jugador: int, carta_dealer: Carta, cartas_restantes: np.ndarray) -> tuple[float, float, float]:
        if valor_jugador > 21:
            return (0.0, 1.0, 0.0)
        
        clave_agrupada = self._crear_clave_agrupada(cartas_restantes)
        prob_key = (valor_jugador, carta_dealer.valor, clave_agrupada)

        if prob_key in self.memo_outcome_prob:
            return self.memo_outcome_prob[prob_key]

        dist_prob_dealer = self._simular_dealer(Mano([carta_dealer]), cartas_restantes)

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
                valor_carta = 11 if i == 0 else (10 if i == 9 else i + 1)
                
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
            return -1.0

        # La clave de valor AÚN usa la clave agrupada para eficiencia
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
        if len(mano.cartas) == 2 and -0.5 > mejor_ev:
            return Accion.RENDIRSE
        
        return max(acciones_ev, key=acciones_ev.get)