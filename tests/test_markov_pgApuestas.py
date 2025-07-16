import time
import csv
import datetime
import os
from core.player import Jugador
from core.casino import Casino
from agents.markov import AgenteMarkov_arriesgado, AgenteMarkov_normal
from agents.agente_A_5 import AgenteAleatorio_5
from agents.markov_umbral import AgenteMarkov_prob_estable_por_umbral
from agents.markovPoliticaApuestas import AgenteMarkov_PoliticaApuestas


# ========== CONFIGURACIÓN ==========
NUM_RONDAS = 100
DINERO_INICIAL = 400

def test_agentes_markov_comparacion():
    print(f"Iniciando test de agentes Markov con {NUM_RONDAS} rondas...")

    # Inicialización de agentes
    jugador_markov_normal = Jugador("Markov_Normal", DINERO_INICIAL)
    agente_markov_normal = AgenteMarkov_normal(jugador_markov_normal, num_mazos=4)

    jugador_markov_arriesgado = Jugador("Markov_Arriesgado", DINERO_INICIAL)
    agente_markov_arriesgado = AgenteMarkov_arriesgado(jugador_markov_arriesgado, num_mazos=4)

    jugador_markov_umbral = Jugador("Markov_Umbral", DINERO_INICIAL)
    agente_markov_umbral = AgenteMarkov_prob_estable_por_umbral(jugador_markov_umbral, num_mazos=4)
    recompensas = {
        'victoria': 1.0,
        'derrota': -1.0,
        'empate': -0.25
    }
    agente_markov_umbral.set_recompensas(recompensas)

    jugador_aleatorio1 = Jugador("Aleatorio1", DINERO_INICIAL)
    agente_aleatorio1 = AgenteAleatorio_5(jugador_aleatorio1)

    jugador_aleatorio2 = Jugador("Aleatorio2", DINERO_INICIAL)
    agente_aleatorio2 = AgenteAleatorio_5(jugador_aleatorio2)


    jugador_markov_pg = Jugador("Markov_PG", DINERO_INICIAL)
    agente_markov_pg = AgenteMarkov_PoliticaApuestas(jugador_markov_pg)

    agentes = [
        agente_markov_normal,
        agente_markov_arriesgado,
        agente_markov_umbral,
        agente_markov_pg,
        agente_aleatorio1,
        agente_aleatorio2
    ]

    fieldnames = [
        'round', 'cards_remaining',
        'normal_decision_time_ms', 'normal_decisions', 'normal_result', 'normal_capital_change',
        'arriesgado_decision_time_ms', 'arriesgado_decisions', 'arriesgado_result', 'arriesgado_capital_change',
        'umbral_decision_time_ms', 'umbral_decisions', 'umbral_result', 'umbral_capital_change',
        'pg_decision_time_ms', 'pg_decisions', 'pg_result', 'pg_capital_change'

    ]

    csv_data = []

    print(f"Agentes creados: {[a.jugador.nombre for a in agentes]}")
    print("NOTA: Todos los agentes Markov apuestan $5 por ronda, excepto el agente con política que decide su apuesta.")

    # Inicialización de contadores y tiempos
    resultados = {a.jugador.nombre: {'wins':0,'losses':0,'ties':0} for a in agentes}
    tiempos_decision = {a.jugador.nombre: [] for a in agentes}

    # Guardar métodos originales y envolver para medir tiempo decisión
    original_decidir = {}
    for agente in agentes:
        original_decidir[agente.jugador.nombre] = agente.decidir_accion
        def make_timed_decidir(nombre):
            def timed(mano, carta_dealer):
                start = time.time()
                res = original_decidir[nombre](mano, carta_dealer)
                tiempos_decision[nombre].append(time.time() - start)
                return res
            return timed
        agente.decidir_accion = make_timed_decidir(agente.jugador.nombre)

    casino = Casino(agentes, num_mazos=4, zapato=0.75)
    round_number = 0

    def tracked_jugar_ronda():
        nonlocal round_number
        round_number += 1

        # Guardar capital inicial para cada agente
        capital_inicial = {a.jugador.nombre: a.jugador.capital for a in agentes}
        cards_remaining = sum(agentes[0].cartas_restantes) if hasattr(agentes[0], "cartas_restantes") else -1

        # Limpiar tiempos decisión para la ronda actual
        for nombre in tiempos_decision:
            tiempos_decision[nombre].clear()

        casino._jugar_ronda_original()

        # Resultados y cambios de capital por agente
        datos_ronda = {'round': round_number, 'cards_remaining': cards_remaining}

        for agente in agentes:
            capital_final = agente.jugador.capital
            delta = capital_final - capital_inicial[agente.jugador.nombre]
            if delta > 0:
                resultado = 1
                resultados[agente.jugador.nombre]['wins'] += 1
            elif delta < 0:
                resultado = -1
                resultados[agente.jugador.nombre]['losses'] += 1
            else:
                resultado = 0
                resultados[agente.jugador.nombre]['ties'] += 1

            datos_ronda[f"{agente.jugador.nombre.lower()}_decision_time_ms"] = int(sum(tiempos_decision[agente.jugador.nombre]) * 1000) if tiempos_decision[agente.jugador.nombre] else 0
            datos_ronda[f"{agente.jugador.nombre.lower()}_decisions"] = len(tiempos_decision[agente.jugador.nombre])
            datos_ronda[f"{agente.jugador.nombre.lower()}_result"] = resultado
            datos_ronda[f"{agente.jugador.nombre.lower()}_capital_change"] = delta

        csv_data.append(datos_ronda)

        if round_number % 10 == 0:
            print(f"Ronda {round_number} completada.")
            for agente in agentes:
                cap = agente.jugador.capital
                print(f"  {agente.jugador.nombre}: Capital={cap}")

    casino._jugar_ronda_original = casino._jugar_ronda
    casino._jugar_ronda = tracked_jugar_ronda

    def tracked_jugar_partida(num_rondas):
        print(f"Iniciando partida de {num_rondas} rondas")
        for _ in range(num_rondas):
            agentes_con_dinero = [a for a in agentes if a.decidir_apuesta() > 0 and a.jugador.capital >= a.decidir_apuesta()]
            if not agentes_con_dinero:
                print("Partida terminada: Ningún jugador puede apostar.")
                break
            casino._jugar_ronda()
        print("Partida finalizada")

    casino.jugar_partida = tracked_jugar_partida

    casino.jugar_partida(NUM_RONDAS)

    # Guardar CSV
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_filename = f"test_markov_comparison_pg_{timestamp}.csv"
    try:
        with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(csv_data)
        print(f"Datos guardados en {csv_filename}")
    except Exception as e:
        print(f"Error al guardar CSV: {e}")

    # Resultados finales
    print("\nRESULTADOS FINALES")
    total_rounds = round_number
    if total_rounds > 0:
        for agente in agentes:
            res = resultados[agente.jugador.nombre]
            print(f"\n{agente.jugador.nombre}:")
            print(f"  Victorias: {res['wins']}/{total_rounds} ({res['wins']/total_rounds*100:.2f}%)")
            print(f"  Derrotas: {res['losses']}/{total_rounds} ({res['losses']/total_rounds*100:.2f}%)")
            print(f"  Empates: {res['ties']}/{total_rounds} ({res['ties']/total_rounds*100:.2f}%)")
            print(f"  Capital final: {agente.jugador.capital}")

if __name__ == "__main__":
    test_agentes_markov_comparacion()
