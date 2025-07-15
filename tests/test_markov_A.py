import time
import csv
import datetime
import os
from core.player import Jugador
from core.casino import Casino
from agents.markov import AgenteMarkov_arriesgado, AgenteMarkov_normal
from agents.markov_RL import AgenteMarkov_RL
from agents.agente_A_5 import AgenteAleatorio_5

# ========== CONFIGURACIÓN ==========
NUM_RONDAS = 10000
DINERO_INICIAL = 100000
# ===================================

def test_agente_markov_vs_aleatorios():
    print(f"Iniciando test de agentes Markov con {NUM_RONDAS} rondas...")
    
    # Inicialización de agentes
    jugador_markov_normal = Jugador("Markov_Normal", DINERO_INICIAL)
    agente_markov_normal = AgenteMarkov_normal(jugador_markov_normal, num_mazos=4)
    
    jugador_markov_arriesgado = Jugador("Markov_Arriesgado", DINERO_INICIAL)
    agente_markov_arriesgado = AgenteMarkov_arriesgado(jugador_markov_arriesgado, num_mazos=4)
    
    jugador_aleatorio1 = Jugador("Aleatorio1", DINERO_INICIAL)
    agente_aleatorio1 = AgenteAleatorio_5(jugador_aleatorio1)
    
    jugador_aleatorio2 = Jugador("Aleatorio2", DINERO_INICIAL)
    agente_aleatorio2 = AgenteAleatorio_5(jugador_aleatorio2)
    
    agentes = [agente_markov_normal, agente_markov_arriesgado, agente_aleatorio1, agente_aleatorio2]
    
    # Create unique filename with timestamp
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_filename = f"test_markov_comparison_{timestamp}.csv"
    
    print(f"Agentes creados: {[a.jugador.nombre for a in agentes]}")
    
    fieldnames = [
        'round', 'cards_remaining', 
        'normal_decision_time_ms', 'normal_decisions', 'normal_result',
        'arriesgado_decision_time_ms', 'arriesgado_decisions', 'arriesgado_result'
    ]
    csv_data = []
    
    # Contadores para ambos agentes
    normal_wins = normal_losses = normal_ties = 0
    arriesgado_wins = arriesgado_losses = arriesgado_ties = 0

    # Timing para ambos agentes
    normal_decision_times = []
    arriesgado_decision_times = []

    # Wrap decision methods for timing
    original_normal_decidir = agente_markov_normal.decidir_accion
    original_arriesgado_decidir = agente_markov_arriesgado.decidir_accion

    def timed_normal_decidir(mano, carta_dealer):
        start_time = time.time()
        result = original_normal_decidir(mano, carta_dealer)
        decision_time = time.time() - start_time
        normal_decision_times.append(decision_time)
        return result

    def timed_arriesgado_decidir(mano, carta_dealer):
        start_time = time.time()
        result = original_arriesgado_decidir(mano, carta_dealer)
        decision_time = time.time() - start_time
        arriesgado_decision_times.append(decision_time)
        return result

    agente_markov_normal.decidir_accion = timed_normal_decidir
    agente_markov_arriesgado.decidir_accion = timed_arriesgado_decidir

    casino = Casino(agentes, num_mazos=4, zapato=0.75)
    original_jugar_ronda = casino._jugar_ronda
    round_number = 0

    def tracked_jugar_ronda():
        nonlocal round_number, normal_wins, normal_losses, normal_ties
        nonlocal arriesgado_wins, arriesgado_losses, arriesgado_ties
        
        round_number += 1
        
        # Capitals antes de la ronda
        normal_start_capital = agente_markov_normal.jugador.capital
        arriesgado_start_capital = agente_markov_arriesgado.jugador.capital
        cards_remaining = sum(agente_markov_normal.cartas_restantes)
        
        # Clear decision times
        normal_decision_times.clear()
        arriesgado_decision_times.clear()
        
        if round_number % 100 == 0:
            print(f"Ejecutando ronda {round_number}...")
        
        original_jugar_ronda()
        
        # Capitals después de la ronda
        normal_final_capital = agente_markov_normal.jugador.capital
        arriesgado_final_capital = agente_markov_arriesgado.jugador.capital
        
        normal_capital_change = normal_final_capital - normal_start_capital
        arriesgado_capital_change = arriesgado_final_capital - arriesgado_start_capital

        # Calcular resultados para agente normal
        if normal_capital_change > 0:
            normal_result = 1
            normal_wins += 1
        elif normal_capital_change < 0:
            normal_result = -1
            normal_losses += 1
        else:
            normal_result = 0
            normal_ties += 1

        # Calcular resultados para agente arriesgado
        if arriesgado_capital_change > 0:
            arriesgado_result = 1
            arriesgado_wins += 1
        elif arriesgado_capital_change < 0:
            arriesgado_result = -1
            arriesgado_losses += 1
        else:
            arriesgado_result = 0
            arriesgado_ties += 1

        round_data = {
            'round': round_number,
            'cards_remaining': cards_remaining,
            'normal_decision_time_ms': int(sum(normal_decision_times) * 1000) if normal_decision_times else 0,
            'normal_decisions': len(normal_decision_times),
            'normal_result': normal_result,
            'arriesgado_decision_time_ms': int(sum(arriesgado_decision_times) * 1000) if arriesgado_decision_times else 0,
            'arriesgado_decisions': len(arriesgado_decision_times),
            'arriesgado_result': arriesgado_result
        }
        csv_data.append(round_data)
        
        if round_number % 100 == 0:
            print(f"Ronda {round_number} completada.")
            print(f"  Normal: Capital={normal_final_capital}")
            print(f"  Arriesgado: Capital={arriesgado_final_capital}")

    def tracked_jugar_partida(num_rondas: int):
        """Versión modificada que termina cuando no hay jugadores con dinero"""
        print(f"Iniciando partida de {num_rondas} rondas")
        for i in range(num_rondas):
            print(f"Ronda {i + 1} / {num_rondas}")
            
            # Verificar si algún agente puede apostar
            agentes_con_dinero = []
            for agente in agentes:
                apuesta_minima = agente.decidir_apuesta()
                if agente.jugador.capital >= apuesta_minima and apuesta_minima > 0:
                    agentes_con_dinero.append(agente)
            
            # Si ningún agente puede apostar, terminar la partida
            if not agentes_con_dinero:
                print(f"Partida terminada en ronda {i + 1}: Ningún jugador puede apostar")
                break
                
            tracked_jugar_ronda()
            for agente in agentes:
                print(f"'{agente.jugador.nombre}': Capital = {agente.jugador.capital}")
        print("Partida terminada")

    casino._jugar_ronda = tracked_jugar_ronda
    casino.jugar_partida = tracked_jugar_partida

    print(f"Iniciando simulación de {NUM_RONDAS} rondas...")
    casino.jugar_partida(NUM_RONDAS)

    # Save CSV with error handling
    try:
        with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(csv_data)
        print(f"Data saved to {csv_filename}")
    except PermissionError as e:
        print(f"Error saving CSV file: {e}")
        # Try alternative location
        alt_filename = os.path.join(os.path.expanduser("~"), "Desktop", csv_filename)
        try:
            with open(alt_filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(csv_data)
            print(f"Data saved to alternative location: {alt_filename}")
        except Exception as e2:
            print(f"Failed to save to alternative location: {e2}")

    # Resultados finales para ambos agentes
    total_rounds = round_number
    if total_rounds > 0:
        print(f"\n" + "="*60)
        print("RESULTADOS FINALES - COMPARACIÓN DE AGENTES MARKOV")
        print("="*60)
        
        print(f"\nAgente Markov Normal:")
        print(f"  Victorias: {normal_wins}/{total_rounds} ({normal_wins/total_rounds*100:.2f}%)")
        print(f"  Derrotas: {normal_losses}/{total_rounds} ({normal_losses/total_rounds*100:.2f}%)")
        print(f"  Empates: {normal_ties}/{total_rounds} ({normal_ties/total_rounds*100:.2f}%)")
        
        print(f"\nAgente Markov Arriesgado:")
        print(f"  Victorias: {arriesgado_wins}/{total_rounds} ({arriesgado_wins/total_rounds*100:.2f}%)")
        print(f"  Derrotas: {arriesgado_losses}/{total_rounds} ({arriesgado_losses/total_rounds*100:.2f}%)")
        print(f"  Empates: {arriesgado_ties}/{total_rounds} ({arriesgado_ties/total_rounds*100:.2f}%)")
        
        print(f"\nComparación de rendimiento:")
        normal_winrate = normal_wins / total_rounds if total_rounds > 0 else 0
        arriesgado_winrate = arriesgado_wins / total_rounds if total_rounds > 0 else 0
        
        if normal_winrate > arriesgado_winrate:
            print(f"  ✓ Markov Normal tiene mejor tasa de victoria (+{(normal_winrate - arriesgado_winrate)*100:.2f}%)")
        elif arriesgado_winrate > normal_winrate:
            print(f"  ✓ Markov Arriesgado tiene mejor tasa de victoria (+{(arriesgado_winrate - normal_winrate)*100:.2f}%)")
        else:
            print(f"  = Ambos agentes tienen la misma tasa de victoria")

    for agente in agentes:
        assert agente.jugador.capital >= 0, f"Capital negativo para {agente.jugador.nombre}: {agente.jugador.capital}"
        print(f"Capital final {agente.jugador.nombre}: {agente.jugador.capital}")

if __name__ == "__main__":
    test_agente_markov_vs_aleatorios()
