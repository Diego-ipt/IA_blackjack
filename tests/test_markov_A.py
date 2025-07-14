import pytest
import logging
import csv
import time
from datetime import datetime
from core.casino import Casino
from core.player import Jugador
from agents.agente_aleatorio import AgenteAleatorio
from agents.markov import AgenteMarkov

def test_simulacion_blackjack_un_jugador_markov():
    jugador = Jugador("SoloMarkov", 50)
    agente = AgenteMarkov(jugador, num_mazos=1)
    casino = Casino([agente], num_mazos=1, zapato=0.7)
    casino.jugar_partida(num_rondas=3)
    # El capital puede variar
    assert jugador.capital >= 0

def test_agente_markov_vs_aleatorios():
    """Test con un agente Markov y tres agentes aleatorios con recolección de datos CSV"""
    # Initialize CSV data collection
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_filename = f"markov_performance_{timestamp}.csv"
    
    jugador_markov = Jugador("Markov", 500)
    jugadores_aleatorios = [Jugador(f"Aleatorio{i+1}", 500) for i in range(3)]
    agentes = [AgenteMarkov(jugador_markov, num_mazos=4)]
    agentes += [AgenteAleatorio(jugador) for jugador in jugadores_aleatorios]
    
    # Find the Markov agent for data collection
    agente_markov = agentes[0]
    
    # Prepare CSV file
    csv_data = []
    fieldnames = [
        'round', 'start_capital', 'final_capital', 'capital_change',
        'win_percentage', 'cards_remaining_start', 'avg_decision_time_ms',
        'total_decisions', 'wins', 'losses', 'ties'
    ]
    
    # Monkey patch the Markov agent to collect timing data
    original_decidir_accion = agente_markov.decidir_accion
    decision_times = []
    
    def timed_decidir_accion(mano, carta_dealer):
        start_time = time.time()
        result = original_decidir_accion(mano, carta_dealer)
        decision_time = time.time() - start_time
        decision_times.append(decision_time)
        return result
    
    agente_markov.decidir_accion = timed_decidir_accion
    
    # Monkey patch casino to track results per round
    casino = Casino(agentes, num_mazos=4, zapato=0.75)
    original_jugar_ronda = casino._jugar_ronda
    round_number = 0
    
    def tracked_jugar_ronda():
        nonlocal round_number, decision_times
        round_number += 1
        
        # Track start conditions
        start_capital = agente_markov.jugador.capital
        cards_remaining = sum(agente_markov.cartas_restantes)
        decision_times.clear()
        
        # Track wins/losses for this round
        start_hands_count = 0
        wins = losses = ties = 0
        
        # Call original round method
        original_jugar_ronda()
        
        # Calculate round statistics
        final_capital = agente_markov.jugador.capital
        capital_change = final_capital - start_capital
        
        # Calculate win percentage based on capital change
        # Positive change = win, negative = loss, zero = tie
        if capital_change > 0:
            wins = 1
        elif capital_change < 0:
            losses = 1
        else:
            ties = 1
            
        total_hands = wins + losses + ties
        win_percentage = (wins / total_hands * 100) if total_hands > 0 else 0
        
        # Calculate average decision time
        avg_decision_time = (sum(decision_times) * 1000) if decision_times else 0  # Convert to ms
        
        # Store round data
        round_data = {
            'round': round_number,
            'start_capital': start_capital,
            'final_capital': final_capital,
            'capital_change': capital_change,
            'win_percentage': win_percentage,
            'cards_remaining_start': cards_remaining,
            'avg_decision_time_ms': avg_decision_time,
            'total_decisions': len(decision_times),
            'wins': wins,
            'losses': losses,
            'ties': ties
        }
        csv_data.append(round_data)
    
    casino._jugar_ronda = tracked_jugar_ronda

    # Simular 100 rondas en lugar de 20 para más datos
    casino.jugar_partida(num_rondas=100)
    
    # Write CSV file
    with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(csv_data)
    
    print(f"Data saved to {csv_filename}")

    # Verificar que todos los jugadores mantienen capital válido
    for agente in agentes:
        assert agente.jugador.capital >= 0
        print(f"Capital final {agente.jugador.nombre}: {agente.jugador.capital}")

if __name__ == "__main__":
    print("Running Markov agent tests...")
    
    # Run the basic test
    print("\n=== Test 1: Basic Markov simulation ===")
    test_simulacion_blackjack_un_jugador_markov()
    print("✓ Basic test passed")
    
    # Run only the main test with CSV output (100 rounds)
    print("\n=== Test 2: Markov vs Random agents with CSV output (100 rounds) ===")
    test_agente_markov_vs_aleatorios()
    print("✓ Test completed")
    
    print("\nTest completed successfully!")