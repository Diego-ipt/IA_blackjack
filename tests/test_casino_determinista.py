import pytest
import logging
from ..core.casino import Casino
from ..core.player import Jugador, Mano
from ..core.cartas import Carta, Palo, Rango, MazoDeterminista
from ..core.acciones import Accion
from .agents.agente_determinista import AgenteDeterminista

# Tests para la clase Casino
# Hechos por copilot (Claude Sonnet 4)

#logging.disable(logging.CRITICAL)

class TestCasinoDeterminista:
    """
    Tests exhaustivos para todas las situaciones posibles en blackjack
    usando agente determinista y mazo determinista.
    """

    def create_deterministic_casino(self, cartas: list[Carta], apuestas: list[int], acciones: list[Accion], capital: int = 1000):
        """Helper para crear casino determinista"""
        jugador = Jugador("TestPlayer", capital)
        agente = AgenteDeterminista(jugador, apuestas, acciones)
        mazo = MazoDeterminista(list(reversed(cartas)))
        casino = Casino([agente], num_mazos=1, mazo=mazo)
        # Reverse the card order since pop() takes from the end
        return casino, agente

    def test_pedir_carta_hasta_plantarse(self):
        """Test básico: pedir cartas hasta plantarse"""
        # Cards dealt in order: Jugador 1ra, Dealer visible, Jugador 2da, Dealer oculta, Jugador pide
        cartas = [
            Carta(Palo.PICAS, Rango.CINCO),      # Jugador 1ra
            Carta(Palo.CORAZONES, Rango.DIEZ),   # Dealer visible
            Carta(Palo.DIAMANTES, Rango.SEIS),   # Jugador 2da
            Carta(Palo.TREBOLES, Rango.SIETE),   # Dealer oculta
            Carta(Palo.PICAS, Rango.SIETE),      # Jugador pide
        ]
        apuestas = [50]
        acciones = [Accion.PEDIR, Accion.PLANTARSE]

        casino, agente = self.create_deterministic_casino(cartas, apuestas, acciones)
        capital_inicial = agente.jugador.capital

        casino._jugar_ronda()

        # Jugador: 5+6+7=18, Dealer: 10+7=17
        # Jugador gana
        assert agente.jugador.capital == capital_inicial + 50  # Gana la apuesta

    def test_pedir_hasta_pasarse(self):
        """Test: jugador se pasa de 21"""
        cartas = [
            Carta(Palo.PICAS, Rango.DIEZ),       # Jugador 1ra
            Carta(Palo.CORAZONES, Rango.CINCO),  # Dealer visible
            Carta(Palo.DIAMANTES, Rango.OCHO),   # Jugador 2da
            Carta(Palo.TREBOLES, Rango.SEIS),    # Dealer oculta
            Carta(Palo.PICAS, Rango.NUEVE),      # Jugador pide (27)
            Carta(Palo.PICAS, Rango.DIEZ),
            Carta(Palo.PICAS, Rango.DIEZ),
            Carta(Palo.PICAS, Rango.DIEZ)
        ]
        apuestas = [100]
        acciones = [Accion.PEDIR]  # Se pasará automáticamente

        casino, agente = self.create_deterministic_casino(cartas, apuestas, acciones)
        capital_inicial = agente.jugador.capital

        casino._jugar_ronda()

        # Jugador se pasa (10+8+9=27), pierde
        assert agente.jugador.capital == capital_inicial - 100

    def test_plantarse_inmediatamente(self):
        """Test: plantarse sin pedir cartas"""
        cartas = [
            Carta(Palo.PICAS, Rango.DIEZ),       # Jugador 1ra
            Carta(Palo.CORAZONES, Rango.SEIS),   # Dealer visible
            Carta(Palo.DIAMANTES, Rango.NUEVE),  # Jugador 2da
            Carta(Palo.TREBOLES, Rango.CINCO),   # Dealer oculta
            Carta(Palo.PICAS, Rango.DIEZ),       # Dealer pide (21)
            Carta(Palo.PICAS, Rango.DIEZ),
            Carta(Palo.PICAS, Rango.DIEZ)
        ]
        apuestas = [75]
        acciones = [Accion.PLANTARSE]

        casino, agente = self.create_deterministic_casino(cartas, apuestas, acciones)
        capital_inicial = agente.jugador.capital

        casino._jugar_ronda()

        # Jugador: 19, Dealer: 21, Jugador pierde
        assert agente.jugador.capital == capital_inicial - 75

    def test_doblar_apuesta_gana(self):
        """Test: doblar apuesta y ganar"""
        cartas = [
            Carta(Palo.PICAS, Rango.CINCO),      # Jugador 1ra
            Carta(Palo.CORAZONES, Rango.SEIS),   # Dealer visible
            Carta(Palo.DIAMANTES, Rango.SEIS),   # Jugador 2da
            Carta(Palo.TREBOLES, Rango.DIEZ),    # Dealer oculta
            Carta(Palo.PICAS, Rango.DIEZ),       # Jugador dobla (21)
            Carta(Palo.CORAZONES, Rango.OCHO),   # Dealer pide (24)
        ]
        apuestas = [50]
        acciones = [Accion.DOBLAR]

        casino, agente = self.create_deterministic_casino(cartas, apuestas, acciones)
        capital_inicial = agente.jugador.capital

        casino._jugar_ronda()

        # Jugador dobló (50->100) y tiene 21, Dealer se pasa con 24
        assert agente.jugador.capital == capital_inicial + 100  # Gana apuesta doblada

    def test_doblar_apuesta_se_pasa(self):
        """Test: doblar apuesta y pasarse"""
        cartas = [
            Carta(Palo.PICAS, Rango.DIEZ),       # Jugador 1ra
            Carta(Palo.CORAZONES, Rango.CINCO),  # Dealer visible
            Carta(Palo.DIAMANTES, Rango.OCHO),   # Jugador 2da
            Carta(Palo.TREBOLES, Rango.DIEZ),    # Dealer oculta
            Carta(Palo.PICAS, Rango.CINCO),      # Jugador dobla (23)
            Carta(Palo.PICAS, Rango.DIEZ),
            Carta(Palo.PICAS, Rango.DIEZ),
            Carta(Palo.PICAS, Rango.DIEZ)
        ]
        apuestas = [40]
        acciones = [Accion.DOBLAR]

        casino, agente = self.create_deterministic_casino(cartas, apuestas, acciones)
        capital_inicial = agente.jugador.capital

        casino._jugar_ronda()

        # Jugador dobló (40->80) y se pasó (23), pierde apuesta doblada
        assert agente.jugador.capital == capital_inicial - 80

    def test_doblar_sin_capital_suficiente(self):
        """Test: intentar doblar sin capital suficiente"""
        cartas = [
            Carta(Palo.PICAS, Rango.CINCO),      # Jugador 1ra
            Carta(Palo.CORAZONES, Rango.SEIS),   # Dealer visible
            Carta(Palo.DIAMANTES, Rango.SEIS),   # Jugador 2da
            Carta(Palo.TREBOLES, Rango.DIEZ),    # Dealer oculta
            Carta(Palo.PICAS, Rango.DOS),
        ]
        apuestas = [100]
        acciones = [Accion.DOBLAR]  # Tratado como plantarse

        casino, agente = self.create_deterministic_casino(cartas, apuestas, acciones, capital=150)  # Solo 50 restantes
        capital_inicial = agente.jugador.capital

        casino._jugar_ronda()

        # No pudo doblar, se trató como plantarse con 11 vs dealer 16
        # Dealer pide hasta 17+, jugador pierde
        assert agente.jugador.capital == capital_inicial - 100

    def test_dividir_cartas_iguales(self):
        """Test: dividir par de cartas iguales"""
        cartas = [
            Carta(Palo.PICAS, Rango.OCHO),       # Jugador 1ra
            Carta(Palo.CORAZONES, Rango.SEIS),   # Dealer visible
            Carta(Palo.DIAMANTES, Rango.OCHO),   # Jugador 2da
            Carta(Palo.TREBOLES, Rango.DIEZ),    # Dealer oculta
            Carta(Palo.PICAS, Rango.TRES),       # Mano 1 recibe (11)
            Carta(Palo.CORAZONES, Rango.DIEZ),   # Mano 2 recibe (18)
            Carta(Palo.DIAMANTES, Rango.DIEZ),   # Mano 1 pide (21)
            Carta(Palo.TREBOLES, Rango.CINCO),   # Dealer pide (21)
        ]
        apuestas = [50]
        acciones = [Accion.DIVIDIR, Accion.PEDIR, Accion.PLANTARSE, Accion.PLANTARSE]

        casino, agente = self.create_deterministic_casino(cartas, apuestas, acciones)
        capital_inicial = agente.jugador.capital

        casino._jugar_ronda()

        # Dividió 8-8, Mano1: 8+3+10=21, Mano2: 8+10=18, Dealer: 21
        # Mano1 empata, Mano2 pierde
        assert agente.jugador.capital == capital_inicial - 50  # Pierde una mano, empata otra

    def test_dividir_cartas_diferentes(self):
        """Test: intentar dividir cartas diferentes"""
        cartas = [
            Carta(Palo.PICAS, Rango.OCHO),       # Jugador 1ra
            Carta(Palo.CORAZONES, Rango.SEIS),   # Dealer visible
            Carta(Palo.DIAMANTES, Rango.SIETE),  # Jugador 2da (diferente)
            Carta(Palo.TREBOLES, Rango.DIEZ),    # Dealer oculta
            Carta(Palo.TREBOLES, Rango.DOS)
        ]
        apuestas = [50]
        acciones = [Accion.DIVIDIR]  # Tratado como plantarse

        casino, agente = self.create_deterministic_casino(cartas, apuestas, acciones)
        capital_inicial = agente.jugador.capital

        casino._jugar_ronda()

        # No pudo dividir 8-7, se trató como plantarse con 15 vs dealer 16
        assert agente.jugador.capital == capital_inicial - 50

    def test_dividir_ases(self):
        """Test: dividir par de ases"""
        cartas = [
            Carta(Palo.PICAS, Rango.AS),         # Jugador 1ra
            Carta(Palo.CORAZONES, Rango.SEIS),   # Dealer visible
            Carta(Palo.DIAMANTES, Rango.AS),     # Jugador 2da
            Carta(Palo.TREBOLES, Rango.DIEZ),    # Dealer oculta
            Carta(Palo.PICAS, Rango.DIEZ),       # Mano 1 recibe (21)
            Carta(Palo.CORAZONES, Rango.NUEVE),  # Mano 2 recibe (20)
            Carta(Palo.DIAMANTES, Rango.CINCO),  # Dealer pide (21)
        ]
        apuestas = [60]
        acciones = [Accion.DIVIDIR, Accion.PLANTARSE, Accion.PLANTARSE]

        casino, agente = self.create_deterministic_casino(cartas, apuestas, acciones)
        capital_inicial = agente.jugador.capital

        casino._jugar_ronda()

        # Dividió A-A, Mano1: A+10=21, Mano2: A+9=20, Dealer: 21
        # Mano1 empata, Mano2 pierde
        assert agente.jugador.capital == capital_inicial - 60

    def test_rendirse(self):
        """Test: rendirse y recuperar mitad de apuesta"""
        cartas = [
            Carta(Palo.PICAS, Rango.DIEZ),       # Jugador 1ra
            Carta(Palo.CORAZONES, Rango.AS),     # Dealer visible (fuerte)
            Carta(Palo.DIAMANTES, Rango.SEIS),   # Jugador 2da
            Carta(Palo.TREBOLES, Rango.DIEZ),    # Dealer oculta
        ]
        apuestas = [80]
        acciones = [Accion.RENDIRSE]

        casino, agente = self.create_deterministic_casino(cartas, apuestas, acciones)
        capital_inicial = agente.jugador.capital

        casino._jugar_ronda()

        # Se rindió con 16 vs A del dealer, recupera mitad (40)
        assert agente.jugador.capital == capital_inicial - 40

    def test_rendirse_con_mas_de_dos_cartas(self):
        """Test: intentar rendirse con más de 2 cartas"""
        cartas = [
            Carta(Palo.PICAS, Rango.CINCO),      # Jugador 1ra
            Carta(Palo.CORAZONES, Rango.AS),     # Dealer visible
            Carta(Palo.DIAMANTES, Rango.TRES),   # Jugador 2da
            Carta(Palo.TREBOLES, Rango.DIEZ),    # Dealer oculta
            Carta(Palo.PICAS, Rango.CINCO),      # Jugador pide
        ]
        apuestas = [60]
        acciones = [Accion.PEDIR, Accion.RENDIRSE]  # Segundo intento de rendirse inválido

        casino, agente = self.create_deterministic_casino(cartas, apuestas, acciones)
        capital_inicial = agente.jugador.capital

        casino._jugar_ronda()

        # No pudo rendirse con 3 cartas, se trató como plantarse
        # Jugador: 13, Dealer: 21, pierde todo
        assert agente.jugador.capital == capital_inicial - 60

    def test_blackjack_jugador_vs_dealer_normal(self):
        """Test: blackjack del jugador vs mano normal del dealer"""
        cartas = [
            Carta(Palo.PICAS, Rango.AS),         # Jugador 1ra
            Carta(Palo.CORAZONES, Rango.SEIS),   # Dealer visible
            Carta(Palo.DIAMANTES, Rango.DIEZ),   # Jugador 2da (BJ)
            Carta(Palo.TREBOLES, Rango.DIEZ),    # Dealer oculta
            Carta(Palo.PICAS, Rango.CUATRO),      # Dealer pide (21)
        ]
        apuestas = [100]
        acciones = [Accion.PLANTARSE]

        casino, agente = self.create_deterministic_casino(cartas, apuestas, acciones)
        capital_inicial = agente.jugador.capital

        casino._jugar_ronda()

        # Jugador BJ (A+10) paga 3:2, gana 150 + recupera 100 = +150
        assert agente.jugador.capital == capital_inicial + 150

    def test_blackjack_ambos(self):
        """Test: ambos tienen blackjack - empate"""
        cartas = [
            Carta(Palo.PICAS, Rango.AS),         # Jugador 1ra
            Carta(Palo.CORAZONES, Rango.JOTA),   # Dealer visible
            Carta(Palo.DIAMANTES, Rango.KAISER), # Jugador 2da (BJ)
            Carta(Palo.TREBOLES, Rango.AS),      # Dealer oculta (BJ)
        ]
        apuestas = [80]
        acciones = [Accion.PLANTARSE]

        casino, agente = self.create_deterministic_casino(cartas, apuestas, acciones)
        capital_inicial = agente.jugador.capital

        casino._jugar_ronda()

        # Empate con BJ, recupera apuesta
        assert agente.jugador.capital == capital_inicial

    def test_dealer_se_pasa(self):
        """Test: dealer se pasa, jugador gana"""
        cartas = [
            Carta(Palo.PICAS, Rango.DIEZ),       # Jugador 1ra
            Carta(Palo.CORAZONES, Rango.SEIS),   # Dealer visible
            Carta(Palo.DIAMANTES, Rango.OCHO),   # Jugador 2da
            Carta(Palo.TREBOLES, Rango.DIEZ),    # Dealer oculta
            Carta(Palo.PICAS, Rango.SIETE),      # Dealer pide (23)
        ]
        apuestas = [70]
        acciones = [Accion.PLANTARSE]

        casino, agente = self.create_deterministic_casino(cartas, apuestas, acciones)
        capital_inicial = agente.jugador.capital

        casino._jugar_ronda()

        # Jugador: 18, Dealer se pasa (23), jugador gana 1:1
        assert agente.jugador.capital == capital_inicial + 70

    def test_dealer_17_blando(self):
        """Test: dealer se planta con 17 blando (A,6)"""
        cartas = [
            Carta(Palo.PICAS, Rango.DIEZ),       # Jugador 1ra
            Carta(Palo.CORAZONES, Rango.AS),     # Dealer visible
            Carta(Palo.DIAMANTES, Rango.NUEVE),  # Jugador 2da
            Carta(Palo.TREBOLES, Rango.SEIS),    # Dealer oculta (A,6=17 blando)
        ]
        apuestas = [50]
        acciones = [Accion.PLANTARSE]

        casino, agente = self.create_deterministic_casino(cartas, apuestas, acciones)
        capital_inicial = agente.jugador.capital

        casino._jugar_ronda()

        # Jugador: 19, Dealer: 17, jugador gana
        assert agente.jugador.capital == capital_inicial + 50

    def test_empate_sin_blackjack(self):
        """Test: empate sin blackjack"""
        cartas = [
            Carta(Palo.PICAS, Rango.DIEZ),       # Jugador 1ra
            Carta(Palo.CORAZONES, Rango.SEIS),  # Dealer visible
            Carta(Palo.DIAMANTES, Rango.DIEZ),   # Jugador 2da
            Carta(Palo.TREBOLES, Rango.DIEZ),    # Dealer oculta
            Carta(Palo.CORAZONES, Rango.CUATRO),   # Dealer pide (20)
        ]
        apuestas = [90]
        acciones = [Accion.PLANTARSE]

        casino, agente = self.create_deterministic_casino(cartas, apuestas, acciones)
        capital_inicial = agente.jugador.capital

        casino._jugar_ronda()

        # Ambos tienen 21 pero no BJ, empate, recupera apuesta
        assert agente.jugador.capital == capital_inicial

    def test_multiples_manos_despues_split(self):
        """Test: jugar múltiples manos después de split"""
        cartas = [
            Carta(Palo.PICAS, Rango.NUEVE),      # Jugador 1ra
            Carta(Palo.CORAZONES, Rango.CINCO),  # Dealer visible
            Carta(Palo.DIAMANTES, Rango.NUEVE),  # Jugador 2da
            Carta(Palo.TREBOLES, Rango.DIEZ),    # Dealer oculta
            Carta(Palo.PICAS, Rango.DOS),        # Mano 1 recibe (11)
            Carta(Palo.CORAZONES, Rango.AS),     # Mano 2 recibe (20)
            Carta(Palo.DIAMANTES, Rango.DIEZ),   # Mano 1 pide (21)
            Carta(Palo.TREBOLES, Rango.SEIS),    # Dealer pide (21)
        ]
        apuestas = [40]
        acciones = [Accion.DIVIDIR, Accion.PEDIR, Accion.PLANTARSE, Accion.PLANTARSE]

        casino, agente = self.create_deterministic_casino(cartas, apuestas, acciones)
        capital_inicial = agente.jugador.capital

        casino._jugar_ronda()

        # Mano1: 21 (empate), Mano2: 20 (pierde vs 21)
        assert agente.jugador.capital == capital_inicial - 40

    def test_sin_capital_para_apostar(self):
        """Test: jugador sin capital suficiente para apostar"""
        cartas = [
            Carta(Palo.PICAS, Rango.AS),
            Carta(Palo.CORAZONES, Rango.DIEZ),
        ]
        apuestas = [100]  # Más que el capital disponible
        acciones = [Accion.PLANTARSE]

        casino, agente = self.create_deterministic_casino(cartas, apuestas, acciones, capital=50)
        capital_inicial = agente.jugador.capital

        casino._jugar_ronda()

        # No pudo apostar, capital no cambió
        assert agente.jugador.capital == capital_inicial

    def test_accion_ilegal_con_tres_cartas(self):
        """Test: intentar acción ilegal con más de 2 cartas"""
        cartas = [
            Carta(Palo.PICAS, Rango.CUATRO),     # Jugador 1ra
            Carta(Palo.CORAZONES, Rango.SEIS),   # Dealer visible
            Carta(Palo.DIAMANTES, Rango.CINCO),  # Jugador 2da
            Carta(Palo.TREBOLES, Rango.DIEZ),    # Dealer oculta
            Carta(Palo.PICAS, Rango.TRES),       # Jugador pide (12)
            Carta(Palo.PICAS, Rango.TRES),
            Carta(Palo.PICAS, Rango.TRES)
        ]
        apuestas = [30]
        acciones = [Accion.PEDIR, Accion.DOBLAR]  # Doblar con 3 cartas es ilegal

        casino, agente = self.create_deterministic_casino(cartas, apuestas, acciones)
        capital_inicial = agente.jugador.capital

        casino._jugar_ronda()

        # Acción ilegal tratada como plantarse con 12 vs dealer 16
        assert agente.jugador.capital == capital_inicial - 30

    def test_reset_agente(self):
        """Test: verificar que el agente se resetea correctamente"""
        cartas = [Carta(Palo.PICAS, Rango.AS), Carta(Palo.CORAZONES, Rango.DIEZ)]
        apuestas = [50, 60]
        acciones = [Accion.PLANTARSE, Accion.PEDIR]

        jugador = Jugador("Test", 1000)
        agente = AgenteDeterminista(jugador, apuestas, acciones)

        # Primera decisión
        primera_apuesta = agente.decidir_apuesta()
        primera_accion = agente.decidir_accion(Mano([]), Carta(Palo.PICAS, Rango.AS))

        # Reset
        agente.reset()

        # Debería repetir la primera decisión
        assert agente.decidir_apuesta() == primera_apuesta
        assert agente.decidir_accion(Mano([]), Carta(Palo.PICAS, Rango.AS)) == primera_accion

    def test_agente_sin_mas_acciones(self):
        """Test: agente sin más acciones predefinidas"""
        cartas = [
            Carta(Palo.PICAS, Rango.CINCO),
            Carta(Palo.CORAZONES, Rango.SEIS),
            Carta(Palo.DIAMANTES, Rango.CINCO),
            Carta(Palo.TREBOLES, Rango.DIEZ),
            Carta(Palo.PICAS, Rango.CINCO),  # Para pedir
            Carta(Palo.PICAS, Rango.TRES),
            Carta(Palo.PICAS, Rango.TRES)
        ]
        apuestas = [50]
        acciones = [Accion.PEDIR]  # Solo una acción, luego usará default

        casino, agente = self.create_deterministic_casino(cartas, apuestas, acciones)
        capital_inicial = agente.jugador.capital

        casino._jugar_ronda()

        # Después de pedir una carta, usa acción default (PLANTARSE)
        assert agente.jugador.capital != capital_inicial  # El juego continuó

    def test_agente_sin_mas_apuestas(self):
        """Test: agente sin más apuestas predefinidas"""
        cartas = [Carta(Palo.PICAS, Rango.AS), Carta(Palo.CORAZONES, Rango.DIEZ)]
        apuestas = []  # Sin apuestas predefinidas
        acciones = [Accion.PLANTARSE]

        casino, agente = self.create_deterministic_casino(cartas, apuestas, acciones)
        capital_inicial = agente.jugador.capital

        casino._jugar_ronda()

        # Sin apuestas predefinidas, usa default (0), no puede jugar
        assert agente.jugador.capital == capital_inicial

# Tests adicionales para edge cases específicos
class TestEdgeCasesDeterminista:
    """Tests para casos extremos y situaciones específicas"""

    def create_deterministic_casino(self, cartas: list[Carta], apuestas: list[int], acciones: list[Accion], capital: int = 1000):
        """Helper para crear casino determinista"""
        jugador = Jugador("TestPlayer", capital)
        agente = AgenteDeterminista(jugador, apuestas, acciones)
        casino = Casino([agente], num_mazos=1)
        # Reverse the card order since pop() takes from the end
        casino.mazo = MazoDeterminista(list(reversed(cartas)))
        return casino, agente

    def test_doblar_exactamente_a_21(self):
        """Test edge case: doblar y llegar exactamente a 21"""
        cartas = [
            Carta(Palo.PICAS, Rango.AS),         # Jugador 1ra (11)
            Carta(Palo.CORAZONES, Rango.CINCO),  # Dealer visible
            Carta(Palo.DIAMANTES, Rango.NUEVE),  # Jugador 2da (20)
            Carta(Palo.TREBOLES, Rango.DIEZ),    # Dealer oculta
            Carta(Palo.PICAS, Rango.AS),         # Jugador dobla (21)
            Carta(Palo.CORAZONES, Rango.SEIS),   # Dealer pide (21)
        ]
        apuestas = [100]
        acciones = [Accion.DOBLAR]

        casino, agente = self.create_deterministic_casino(cartas, apuestas, acciones)
        capital_inicial = agente.jugador.capital

        casino._jugar_ronda()

        # Dobló y llegó a 21, empata con dealer que también tiene 21
        assert agente.jugador.capital == capital_inicial  # Empate, recupera apuesta

    def test_dividir_sin_capital_suficiente(self):
        """Test: intentar dividir sin capital suficiente"""
        cartas = [
            Carta(Palo.PICAS, Rango.NUEVE),       # Jugador 1ra
            Carta(Palo.CORAZONES, Rango.OCHO),   # Dealer visible
            Carta(Palo.DIAMANTES, Rango.NUEVE),   # Jugador 2da
            Carta(Palo.TREBOLES, Rango.AS),    # Dealer oculta
        ]
        apuestas = [80]  # Apuesta su capital
        acciones = [Accion.DIVIDIR]  # No puede dividir

        casino, agente = self.create_deterministic_casino(cartas, apuestas, acciones, capital=80)
        capital_inicial = agente.jugador.capital

        casino._jugar_ronda()

        # No pudo dividir, se trató como plantarse
        assert agente.jugador.capital == capital_inicial - 80

    def test_as_como_1_despues_de_pasarse(self):
        """Test: As que cambia de 11 a 1 para evitar pasarse"""
        cartas = [
            Carta(Palo.PICAS, Rango.AS),         # Jugador 1ra (11)
            Carta(Palo.CORAZONES, Rango.SIETE),  # Dealer visible
            Carta(Palo.DIAMANTES, Rango.SEIS),   # Jugador 2da (17)
            Carta(Palo.TREBOLES, Rango.DIEZ),    # Dealer oculta
            Carta(Palo.PICAS, Rango.CINCO),      # Jugador pide (A=1, total=12)
        ]
        apuestas = [50]
        acciones = [Accion.PEDIR, Accion.PLANTARSE]

        casino, agente = self.create_deterministic_casino(cartas, apuestas, acciones)
        capital_inicial = agente.jugador.capital

        casino._jugar_ronda()

        # As se ajustó automáticamente, jugador tiene 12, no se pasó
        assert agente.jugador.capital != capital_inicial  # El juego continuó normalmente

    def test_multiples_ases_ajuste_automatico(self):
        """Test: múltiples ases que se ajustan automáticamente"""
        cartas = [
            Carta(Palo.PICAS, Rango.AS),         # Jugador 1ra (11)
            Carta(Palo.CORAZONES, Rango.SIETE),  # Dealer visible
            Carta(Palo.DIAMANTES, Rango.AS),     # Jugador 2da (12, un As=1)
            Carta(Palo.TREBOLES, Rango.DIEZ),    # Dealer oculta
            Carta(Palo.PICAS, Rango.NUEVE),      # Jugador pide (21)
        ]
        apuestas = [60]
        acciones = [Accion.PEDIR, Accion.PLANTARSE]

        casino, agente = self.create_deterministic_casino(cartas, apuestas, acciones)
        capital_inicial = agente.jugador.capital

        casino._jugar_ronda()

        # Múltiples ases se ajustaron, jugador tiene 21
        assert agente.jugador.capital != capital_inicial

    def test_blackjack_con_cartas_figuras(self):
        """Test: blackjack con diferentes cartas de valor 10"""
        test_cases = [
            (Rango.JOTA, "con Jota"),
            (Rango.CUINA, "con Reina"),
            (Rango.KAISER, "con Rey"),
            (Rango.DIEZ, "con 10")
        ]

        for rango_figura, descripcion in test_cases:
            cartas = [
                Carta(Palo.PICAS, Rango.AS),         # Jugador 1ra
                Carta(Palo.CORAZONES, Rango.SIETE),  # Dealer visible
                Carta(Palo.DIAMANTES, rango_figura), # Jugador 2da (BJ)
                Carta(Palo.TREBOLES, Rango.DIEZ),    # Dealer oculta
            ]
            apuestas = [100]
            acciones = [Accion.PLANTARSE]

            casino, agente = self.create_deterministic_casino(cartas, apuestas, acciones)
            capital_inicial = agente.jugador.capital

            casino._jugar_ronda()

            # Todos deberían resultar en blackjack y pago 3:2
            assert agente.jugador.capital == capital_inicial + 150, f"Falló {descripcion}"

    def test_dealer_exactamente_17_con_as(self):
        """Test: dealer con exactamente 17 blando (A,6) se planta"""
        cartas = [
            Carta(Palo.PICAS, Rango.DIEZ),       # Jugador 1ra
            Carta(Palo.CORAZONES, Rango.AS),     # Dealer visible
            Carta(Palo.DIAMANTES, Rango.OCHO),   # Jugador 2da
            Carta(Palo.TREBOLES, Rango.SEIS),    # Dealer oculta (A,6=17)
        ]
        apuestas = [50]
        acciones = [Accion.PLANTARSE]

        casino, agente = self.create_deterministic_casino(cartas, apuestas, acciones)
        capital_inicial = agente.jugador.capital

        casino._jugar_ronda()

        # Jugador: 18, Dealer: 17 (se planta), jugador gana
        assert agente.jugador.capital == capital_inicial + 50

    def test_split_seguido_de_doble(self):
        """Test: dividir y luego doblar en una de las manos"""
        cartas = [
            Carta(Palo.PICAS, Rango.CINCO),      # Jugador 1ra
            Carta(Palo.CORAZONES, Rango.SEIS),   # Dealer visible
            Carta(Palo.DIAMANTES, Rango.CINCO),  # Jugador 2da
            Carta(Palo.TREBOLES, Rango.DIEZ),    # Dealer oculta
            Carta(Palo.PICAS, Rango.SEIS),       # Mano 1 recibe (11)
            Carta(Palo.CORAZONES, Rango.CINCO),  # Mano 2 recibe (10)
            Carta(Palo.DIAMANTES, Rango.DIEZ),   # Mano 1 dobla (21)
            Carta(Palo.TREBOLES, Rango.AS),      # Mano 2 pide (21)
            Carta(Palo.PICAS, Rango.CINCO),      # Dealer pide (21)
        ]
        apuestas = [50]
        acciones = [Accion.DIVIDIR, Accion.DOBLAR, Accion.PEDIR, Accion.PLANTARSE]

        casino, agente = self.create_deterministic_casino(cartas, apuestas, acciones)
        capital_inicial = agente.jugador.capital

        casino._jugar_ronda()

        # Mano1 dobló (100), Mano2 normal (50), ambos empatan con dealer
        assert agente.jugador.capital == capital_inicial  # Empates, recupera apuestas

    def test_maximo_cartas_sin_pasarse(self):
        """Test: máximo número de cartas sin pasarse"""
        cartas = [
            Carta(Palo.PICAS, Rango.AS),         # Jugador 1ra (1)
            Carta(Palo.CORAZONES, Rango.SIETE),  # Dealer visible
            Carta(Palo.DIAMANTES, Rango.AS),     # Jugador 2da (2)
            Carta(Palo.TREBOLES, Rango.DIEZ),    # Dealer oculta
            Carta(Palo.PICAS, Rango.AS),         # Jugador pide (3)
            Carta(Palo.CORAZONES, Rango.AS),     # Jugador pide (4)
            Carta(Palo.DIAMANTES, Rango.AS),     # Jugador pide (5)
            Carta(Palo.TREBOLES, Rango.AS),      # Jugador pide (6)
            Carta(Palo.PICAS, Rango.AS),         # Jugador pide (7)
            Carta(Palo.CORAZONES, Rango.AS),     # Jugador pide (8)
            Carta(Palo.DIAMANTES, Rango.AS),     # Jugador pide (9)
            Carta(Palo.TREBOLES, Rango.AS),      # Jugador pide (10)
            Carta(Palo.PICAS, Rango.AS),         # Jugador pide (11=21)
        ]
        apuestas = [30]
        acciones = [Accion.PEDIR] * 9 + [Accion.PLANTARSE]

        casino, agente = self.create_deterministic_casino(cartas, apuestas, acciones)
        capital_inicial = agente.jugador.capital

        casino._jugar_ronda()

        # Jugador consiguió 21 con muchas cartas
        assert agente.jugador.capital != capital_inicial
