import time
import csv
from core.player import Jugador
from core.casino import Casino
from agents.markov import AgenteMarkov
from agents.agente_A_5 import AgenteAleatorio_5

def test_agente_markov_vs_aleatorios():
    print("Iniciando test del agente Markov...")
    
    # Inicialización de agentes
    jugador_markov = Jugador("Markov", 1000)
    agente_markov = AgenteMarkov(jugador_markov, num_mazos=4)
    
    jugador_aleatorio1 = Jugador("Aleatorio1", 1000)
    agente_aleatorio1 = AgenteAleatorio_5(jugador_aleatorio1)
    
    jugador_aleatorio2 = Jugador("Aleatorio2", 1000)
    agente_aleatorio2 = AgenteAleatorio_5(jugador_aleatorio2)
    
    agentes = [agente_markov, agente_aleatorio1, agente_aleatorio2]
    csv_filename = "test_markov_results.csv"
    
    print(f"Agentes creados: {[a.jugador.nombre for a in agentes]}")
    
    fieldnames = [
        'round', 'cards_remaining', 'total_decision_time_ms',
        'total_decisions', 'result'
    ]
    csv_data = []
    total_wins = total_losses = total_ties = 0

    original_decidir_accion = agente_markov.decidir_accion
    decision_times = []

    def timed_decidir_accion(mano, carta_dealer):
        start_time = time.time()
        result = original_decidir_accion(mano, carta_dealer)
        decision_time = time.time() - start_time
        decision_times.append(decision_time)
        return result

    agente_markov.decidir_accion = timed_decidir_accion

    casino = Casino(agentes, num_mazos=4, zapato=0.75)
    original_jugar_ronda = casino._jugar_ronda
    round_number = 0

    def tracked_jugar_ronda():
        nonlocal round_number, decision_times, total_wins, total_losses, total_ties
        round_number += 1
        start_capital = agente_markov.jugador.capital
        cards_remaining = sum(agente_markov.cartas_restantes)
        decision_times.clear()
        
        print(f"Ejecutando ronda {round_number}...")
        original_jugar_ronda()
        
        final_capital = agente_markov.jugador.capital
        capital_change = final_capital - start_capital

        # Resultado: +1 victoria, 0 empate, -1 derrota
        if capital_change > 0:
            result = 1
            total_wins += 1
        elif capital_change < 0:
            result = -1
            total_losses += 1
        else:
            result = 0
            total_ties += 1

        round_data = {
            'round': round_number,
            'cards_remaining': cards_remaining,
            'total_decision_time_ms': int(sum(decision_times) * 1000) if decision_times else 0,
            'total_decisions': len(decision_times),
            'result': result
        }
        csv_data.append(round_data)
        
        if round_number % 10 == 0:
            print(f"Ronda {round_number} completada. Capital Markov: {final_capital}")

    casino._jugar_ronda = tracked_jugar_ronda

    print("Iniciando simulación de 100 rondas...")
    casino.jugar_partida(num_rondas=100)

    with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
        writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
        writer.writeheader()
        writer.writerows(csv_data)

    print(f"Data saved to {csv_filename}")

    total_rounds = total_wins + total_losses + total_ties
    if total_rounds > 0:
        print(f"Victorias: {total_wins/total_rounds*100:.2f}%")
        print(f"Derrotas: {total_losses/total_rounds*100:.2f}%")
        print(f"Empates: {total_ties/total_rounds*100:.2f}%")
    else:
        print("No se completaron rondas")

    for agente in agentes:
        assert agente.jugador.capital >= 0
        print(f"Capital final {agente.jugador.nombre}: {agente.jugador.capital}")

if __name__ == "__main__":
    test_agente_markov_vs_aleatorios()
