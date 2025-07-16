import numpy as np
from collections import deque
import logging
from typing import Tuple, Dict, Deque
from core.acciones import Accion
from core.player import Jugador, Mano
from core.cartas import Carta, Rango, Palo
from .agente_base import Agente
from .policy_gradient_entropy import ApuestaConPolicyGradient


class AgenteMarkov_PoliticaApuestas(Agente):
    def __init__(self, jugador: Jugador, num_mazos: int = 4, config: dict = None):
        super().__init__(jugador)
        self.num_mazos = num_mazos

        # Configuración con valores por defecto
        self.config = {
            'precision_agrupacion': 20,
            'tasa_aprendizaje_pg': 0.01,
            'descuento_pg': 0.99,
            'entropia_peso': 0.01,
            'decaimiento_entropia': 0.995,
            'rango_apuesta': [0.01, 0.1],
            'min_apuesta': 10,
            'max_porcentaje_capital': 0.2
        }
        if config:
            self.config.update(config)

        self.contador_resultados = {
            'ganadas': 0,
            'perdidas': 0,
            'empatadas': 0
        }

        # Inicializa la política de apuestas
        self.pg_apuestas = ApuestaConPolicyGradient(
            capital_inicial=self.jugador.capital,
            rango_apuesta=self.config['rango_apuesta'],
            tasa_aprendizaje=self.config['tasa_aprendizaje_pg'],
            descuento=self.config['descuento_pg'],
            entropia_peso=self.config['entropia_peso'],
            decaimiento_entropia=self.config['decaimiento_entropia']
        )

        # Cargar pesos entrenados al inicializar el agente
        try:
            self.pg_apuestas.cargar_pesos("pesos_guardados/pesos_policy_pg.npz")
        except Exception as e:
            logging.warning(f"No se pudieron cargar los pesos al inicializar el agente: {str(e)}")

        # Configuración de logging
        self.logger = logging.getLogger(__name__)
        self.logger.setLevel(logging.INFO)

        # Inicializar cachés como diccionarios simples
        self.memo_valor_estado = {}
        self.memo_outcome_prob = {}
        self.memo_dealer_dist = {}

        self.resetear_conteo(reset_completo=True)

    def _get_idx(self, valor_carta: int) -> int:
        """Mapea valores de carta a índices (As=0, 2-9=1-8, 10/J/Q/K=9)"""
        return 0 if valor_carta == 11 else (valor_carta - 1 if valor_carta < 10 else 9)

    def observar_carta(self, carta: Carta):
        """Actualiza el conteo de cartas restantes"""
        idx = self._get_idx(carta.valor)
        if self.cartas_restantes[idx] > 0:
            self.cartas_restantes[idx] -= 1

    def resetear_conteo(self, reset_completo: bool = True):
        """Resetea todos los cachés y las cartas. Se llama al barajar."""
        # Reset Markov
        self.cartas_restantes = np.array([4 * self.num_mazos] * 9 + [16 * self.num_mazos])

        # Limpiar cachés
        self.memo_valor_estado.clear()
        self.memo_outcome_prob.clear()
        self.memo_dealer_dist.clear()

        # Reset policy Gradient
        self.pg_apuestas.capital_actual = self.jugador.capital

        if reset_completo:
            # Reset completo (nuevo juego)
            self.pg_apuestas.estados.clear()
            self.pg_apuestas.porcentajes_apostados.clear()
            self.pg_apuestas.recompensas.clear()
        else:
            # Reset parcial (barajada) - conserva experiencias recientes
            if len(self.pg_apuestas.estados) > 1000:
                self.pg_apuestas.estados = deque(list(self.pg_apuestas.estados)[-1000:], maxlen=10000)
                self.pg_apuestas.porcentajes_apostados = deque(list(self.pg_apuestas.porcentajes_apostados)[-1000:],
                                                               maxlen=10000)
                self.pg_apuestas.recompensas = deque(list(self.pg_apuestas.recompensas)[-1000:], maxlen=10000)

        self.pg_apuestas.pasos_episodio = 0
        self.logger.info("Conteo y cachés reiniciados")

    def _calcular_conteo_hi_lo(self) -> float:
        """Calcula el conteo Hi-Lo para ajustar apuestas"""
        conteo = 0
        total_cartas = np.sum(self.cartas_restantes)
        if total_cartas == 0:
            return 0.0

        # Valores Hi-Lo: As y 10/J/Q/K=-1, 2-6=+1, 7-9=0
        for i, count in enumerate(self.cartas_restantes):
            if i == 0 or i == 9:  # Ases y 10/J/Q/K
                conteo -= count
            elif 1 <= i <= 5:  # Cartas 2-6
                conteo += count

        mazos_restantes = total_cartas / 52.0
        return conteo / max(1, mazos_restantes)

    def decidir_apuesta(self, capital_actual: int = None) -> int:
        """Decide el monto a apostar usando política aprendida y conteo de cartas"""
        capital = capital_actual if capital_actual is not None else self.jugador.capital
        if capital < self.config['min_apuesta']:
            return 0

        # Sincronizar capital y obtener porcentaje
        self.pg_apuestas.capital_actual = capital

        # Calcular ventaja basada en conteo de cartas
        conteo = self._calcular_conteo_hi_lo()
        ventaja_estimada = max(0, 0.005 * conteo)

        # Obtener porcentaje base de la red neuronal
        estado = self.pg_apuestas.obtener_estado()
        porcentaje_base = self.pg_apuestas.elegir_apuesta(estado)

        # Ajustar porcentaje según ventaja
        porcentaje_ajustado = np.clip(
            porcentaje_base * (1 + ventaja_estimada),
            self.config['rango_apuesta'][0],
            self.config['rango_apuesta'][1]
        )

        # Calcular apuesta con límites inteligentes
        apuesta = np.clip(
            int(capital * porcentaje_ajustado),
            self.config['min_apuesta'],
            int(capital * self.config['max_porcentaje_capital'])
        )

        self.logger.debug(
            f"Apuesta decidida: {apuesta} (Capital: {capital}, Porcentaje: {porcentaje_ajustado:.2%}, Conteo: {conteo:.2f})")
        return apuesta

    def finalizar_ronda(self, resultado: float, apuesta_actual: int):
        """Registra resultado y entrena la política de apuestas"""
        if apuesta_actual == 0:
            return

        #REGISTRO DE RESULTADO
        if resultado > 0:
            self.contador_resultados['ganadas'] += 1
        elif resultado < 0:
            self.contador_resultados['perdidas'] += 1
        else:
            self.contador_resultados['empatadas'] += 1

        recompensa_normalizada = resultado / (apuesta_actual + 1e-6)
        estado = self.pg_apuestas.obtener_estado()
        porcentaje = apuesta_actual / self.jugador.capital

        self.pg_apuestas.guardar_experiencia(estado, porcentaje, recompensa_normalizada)

        # Normalizar recompensa
        recompensa_normalizada = resultado / (apuesta_actual + 1e-6)

        estado = self.pg_apuestas.obtener_estado()
        porcentaje = apuesta_actual / self.jugador.capital

        self.pg_apuestas.guardar_experiencia(estado, porcentaje, recompensa_normalizada)

        # Entrenar cada 50 rondas o si el resultado fue significativo
        if len(self.pg_apuestas.estados) % 50 == 0 or abs(resultado) > apuesta_actual * 2:
            perdida = self.pg_apuestas.entrenar()
            self.logger.debug(
                f"Entrenamiento PG - Pérdida: {perdida:.4f}, Entropía: {self.pg_apuestas.entropia_peso:.4f}")



    # --- Métodos MDP con caché manual ---
    def _crear_clave_agrupada(self, cartas_restantes: np.ndarray) -> tuple:
        """Crea una clave agrupada para caché basada en porcentajes discretizados"""
        total_restantes = np.sum(cartas_restantes)
        if total_restantes == 0:
            return (0, 0, 0, 0)

        num_ases = cartas_restantes[0]
        num_bajas = np.sum(cartas_restantes[1:6])  # 2-6
        num_medias = np.sum(cartas_restantes[6:9])  # 7-9
        num_altas = cartas_restantes[9]  # 10/J/Q/K

        p = self.config['precision_agrupacion']
        return (
            int((num_ases / total_restantes) * p),
            int((num_bajas / total_restantes) * p),
            int((num_medias / total_restantes) * p),
            int((num_altas / total_restantes) * p)
        )

    def _calcular_dealer_dist_iterativa(self, mano_inicial: Mano, cartas_restantes: np.ndarray) -> dict:
        """Versión iterativa para evitar problemas de recursión"""
        stack = [(mano_inicial, cartas_restantes, 1.0)]
        dist_final = {}

        while stack:
            mano_actual, cartas_actuales, prob_actual = stack.pop()

            if mano_actual.valor_total >= 17:
                dist_final[mano_actual.valor_total] = dist_final.get(mano_actual.valor_total, 0) + prob_actual
                continue

            total_cartas = np.sum(cartas_actuales)
            if total_cartas == 0:
                dist_final[mano_actual.valor_total] = dist_final.get(mano_actual.valor_total, 0) + prob_actual
                continue

            for i, count in enumerate(cartas_actuales):
                if count > 0:
                    valor_carta = 11 if i == 0 else (10 if i == 9 else i + 1)
                    nuevas_cartas = cartas_actuales.copy()
                    nuevas_cartas[i] -= 1
                    nueva_mano = Mano(mano_actual.cartas + [Carta(Palo.PICAS, Rango.from_valor(valor_carta))])
                    stack.append((nueva_mano, nuevas_cartas, prob_actual * (count / total_cartas)))

        return dist_final

    def _simular_dealer(self, mano_dealer: Mano, cartas_restantes: np.ndarray) -> dict:
        """Simula la distribución de probabilidad del dealer usando caché manual"""
        clave_agrupada = self._crear_clave_agrupada(cartas_restantes)
        cache_key = (mano_dealer.valor_total, mano_dealer.es_blanda, clave_agrupada)

        if cache_key in self.memo_dealer_dist:
            return self.memo_dealer_dist[cache_key]

        dist_calculada = self._calcular_dealer_dist_iterativa(mano_dealer, cartas_restantes)
        self.memo_dealer_dist[cache_key] = dist_calculada
        return dist_calculada

    def _get_outcome_probabilities(self, valor_jugador: int, carta_dealer: Carta,
                                   cartas_restantes: np.ndarray) -> tuple:
        """Calcula probabilidades de resultado (ganar, perder, empatar) con caché manual"""
        # Casos especiales primero
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
        """Valor esperado de plantarse"""
        prob_victoria, prob_derrota, _ = self._get_outcome_probabilities(valor_jugador, carta_dealer, cartas_restantes)
        return prob_victoria - prob_derrota

    def _calcular_ev_doblar(self, mano_jugador: Mano, carta_dealer: Carta, cartas_restantes: np.ndarray) -> float:
        """Valor esperado de doblar"""
        ev_total = 0.0
        total_cartas = np.sum(cartas_restantes)
        if total_cartas == 0:
            return -2.0

        for i, count in enumerate(cartas_restantes):
            if count > 0:
                prob_carta = count / total_cartas
                valor_carta = 11 if i == 0 else (10 if i == 9 else i + 1)

                nuevas_cartas_restantes = cartas_restantes.copy()
                nuevas_cartas_restantes[i] -= 1

                nueva_mano = Mano(mano_jugador.cartas + [Carta(Palo.PICAS, Rango.from_valor(valor_carta))])

                prob_victoria, prob_derrota, _ = self._get_outcome_probabilities(
                    nueva_mano.valor_total, carta_dealer, nuevas_cartas_restantes
                )
                ev_doblado = (prob_victoria * 2) - (prob_derrota * 2)
                ev_total += prob_carta * ev_doblado
        return ev_total

    def _calcular_ev_pedir(self, mano_jugador: Mano, carta_dealer: Carta, cartas_restantes: np.ndarray) -> float:
        """Valor esperado de pedir carta"""
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
        """Valor esperado de dividir"""
        if len(mano_jugador.cartas) != 2:
            return -1.0

        carta_dividida_valor = mano_jugador.cartas[0].valor
        mano_dividida = Mano([Carta(Palo.PICAS, Rango.from_valor(carta_dividida_valor))])
        ev_mano = self._get_valor_estado(mano_dividida, carta_dealer, cartas_restantes.copy())
        return ev_mano * 2

    def _get_valor_estado(self, mano_jugador: Mano, carta_dealer: Carta, cartas_restantes: np.ndarray) -> float:
        """Calcula el valor del estado usando MDP con caché manual"""
        if mano_jugador.valor_total > 21:
            return -1.0

        clave_agrupada = self._crear_clave_agrupada(cartas_restantes)
        estado_key = (
            mano_jugador.valor_total,
            mano_jugador.es_blanda,
            len(mano_jugador.cartas),
            carta_dealer.valor,
            clave_agrupada
        )

        if estado_key in self.memo_valor_estado:
            return self.memo_valor_estado[estado_key]

        ev_plantarse = self._calcular_ev_plantarse(mano_jugador.valor_total, carta_dealer, cartas_restantes)
        ev_pedir = self._calcular_ev_pedir(mano_jugador, carta_dealer, cartas_restantes)

        valor_optimo = max(ev_plantarse, ev_pedir)
        self.memo_valor_estado[estado_key] = valor_optimo
        return valor_optimo

    def decidir_accion(self, mano: Mano, carta_dealer: Carta) -> Accion:
        """Toma la decisión óptima basada en el valor esperado de cada acción"""
        if mano.es_blackjack or mano.valor_total > 21:
            return Accion.PLANTARSE

        acciones_ev = {
            Accion.PLANTARSE: self._calcular_ev_plantarse(mano.valor_total, carta_dealer, self.cartas_restantes.copy()),
            Accion.PEDIR: self._calcular_ev_pedir(mano, carta_dealer, self.cartas_restantes.copy())
        }

        # Acciones especiales solo disponibles con 2 cartas
        if len(mano.cartas) == 2:
            acciones_ev[Accion.DOBLAR] = self._calcular_ev_doblar(mano, carta_dealer, self.cartas_restantes.copy())

            if mano.cartas[0].rango == mano.cartas[1].rango:
                acciones_ev[Accion.DIVIDIR] = self._calcular_ev_dividir(mano, carta_dealer,
                                                                        self.cartas_restantes.copy())

            # Considerar rendirse si el EV es muy bajo
            mejor_ev = max(acciones_ev.values())
            if -0.5 > mejor_ev:
                return Accion.RENDIRSE

        return max(acciones_ev, key=acciones_ev.get)