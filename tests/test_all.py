import time
import csv
import datetime
import os
from core.player import Jugador
from core.casino import Casino
from agents.markov import AgenteMarkov_arriesgado, AgenteMarkov_normal
from agents.agente_A_5 import AgenteAleatorio_5
from agents.markov_umbral import AgenteMarkov_prob_estable_por_umbral
from agents.markov_h import AgenteHibrido_Markov_HiLo
from agents.agente_HiLo import AgenteHiLo
from agents.agente_randomForest import AgenteRandomForest
from agents.markovPoliticaApuestas import AgenteMarkov_PoliticaApuestas

# ========== CONFIGURACIÓN ==========
NUM_RONDAS = 50
DINERO_INICIAL = 900000

def inicializar_tracking_agentes(agentes):
    """Inicializa estructuras de tracking para todos los agentes dinámicamente"""
    tracking = {}
    for agente in agentes:
        nombre = agente.jugador.nombre
        tracking[nombre] = {
            'wins': 0,
            'losses': 0,
            'ties': 0,
            'decision_times': [],
            'agente_ref': agente
        }
    return tracking

def actualizar_resultado_agente(tracking, nombre_agente, capital_change):
    """Actualiza contadores de resultado para un agente específico"""
    if capital_change > 0:
        tracking[nombre_agente]['wins'] += 1
        return 1
    elif capital_change < 0:
        tracking[nombre_agente]['losses'] += 1
        return -1
    else:
        tracking[nombre_agente]['ties'] += 1
        return 0

def crear_wrapper_timing(agente_nombre, tracking):
    """Crea un wrapper para medir tiempos de decisión de un agente específico"""
    agente = tracking[agente_nombre]['agente_ref']
    original_decidir = agente.decidir_accion
    
    def timed_decidir(mano, carta_dealer):
        start_time = time.time()
        result = original_decidir(mano, carta_dealer)
        decision_time = time.time() - start_time
        tracking[agente_nombre]['decision_times'].append(decision_time)
        return result
    
    return timed_decidir

def generar_fieldnames_csv(agentes):
    """Genera los nombres de columnas del CSV dinámicamente basado en los agentes"""
    fieldnames = ['round', 'cards_remaining']
    for agente in agentes:
        nombre = agente.jugador.nombre.lower().replace(' ', '_')
        fieldnames.extend([
            f'{nombre}_decision_time_ms',
            f'{nombre}_decisions',
            f'{nombre}_result',
            f'{nombre}_capital_change'
        ])
    return fieldnames

def test_all():
    print(f"Iniciando test de agentes Markov con {NUM_RONDAS} rondas...")
    
    # Inicialización de agentes
    jugador_markov_normal = Jugador("Markov_Normal", DINERO_INICIAL)
    agente_markov_normal = AgenteMarkov_normal(jugador_markov_normal, num_mazos=4)
    
    jugador_markov_arriesgado = Jugador("Markov_Arriesgado", DINERO_INICIAL)
    agente_markov_arriesgado = AgenteMarkov_arriesgado(jugador_markov_arriesgado, num_mazos=4)
    
    jugador_markov_umbral = Jugador("Markov_Umbral", DINERO_INICIAL)
    agente_markov_umbral = AgenteMarkov_prob_estable_por_umbral(jugador_markov_umbral, num_mazos=4)
    
    recompensas = {
        'victoria': 0.49809807538986206,  
        'derrota': -0.38012391328811646,
        'empate': 0.0  
    }
    agente_markov_umbral.set_recompensas(recompensas)

    jugador_markov_hibrido = Jugador("Markov_Hibrido", DINERO_INICIAL)
    agente_markov_hibrido = AgenteHibrido_Markov_HiLo(jugador_markov_hibrido, num_mazos=4)

    recompensas_hibrido = {
        'victoria': 0.49809807538986206,  
        'derrota': -0.38012391328811646,
        'empate': 0.0    
    }
    agente_markov_hibrido.set_recompensas(recompensas_hibrido)
    agente_markov_hibrido.set_factor_riesgo(0.01)

    jugador_hilo = Jugador("HiLo", DINERO_INICIAL)
    agente_hilo = AgenteHiLo(jugador_hilo, base_bet=5, min_bet=1, max_bet_fraction=0.1)

    jugador_aleatorio1 = Jugador("Aleatorio1", DINERO_INICIAL)
    agente_aleatorio1 = AgenteAleatorio_5(jugador_aleatorio1)
    
    jugador_aleatorio2 = Jugador("Aleatorio2", DINERO_INICIAL)
    agente_aleatorio2 = AgenteAleatorio_5(jugador_aleatorio2)
    
    jugador_random_forest = Jugador("RandomForest", DINERO_INICIAL)
    modelo_path = "resultados/randomForestClass6/rf_action_clf.joblib"
    encoder_path = "resultados/randomForestClass6/label_encoder.joblib"
    agente_random_forest = AgenteRandomForest(jugador_random_forest, modelo_path, encoder_path)

    jugador_markov_politica = Jugador("Markov_Politica", DINERO_INICIAL)
    agente_markov_politica = AgenteMarkov_PoliticaApuestas(jugador_markov_politica, num_mazos=4)
    
    agentes = [agente_markov_normal, agente_markov_arriesgado, agente_markov_umbral, 
               agente_markov_hibrido, agente_hilo, agente_aleatorio1, agente_aleatorio2,
               agente_random_forest, agente_markov_politica]
    
    # Inicializar tracking dinámico
    tracking_agentes = inicializar_tracking_agentes(agentes)
    
    # Create unique filename with timestamp
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_filename = f"test_markov_comparison_{timestamp}.csv"
    
    print(f"Agentes creados: {[a.jugador.nombre for a in agentes]}")
    
    fieldnames = generar_fieldnames_csv(agentes)
    csv_data = []
    
    print("NOTA: Agentes Markov apuestan $5 por ronda, HiLo usa apuesta adaptativa")

    # Configurar wrappers de timing para todos los agentes
    for agente in agentes:
        nombre = agente.jugador.nombre
        agente.decidir_accion = crear_wrapper_timing(nombre, tracking_agentes)

    casino = Casino(agentes, num_mazos=4, zapato=0.75)
    original_jugar_ronda = casino._jugar_ronda
    round_number = 0

    def tracked_jugar_ronda():
        nonlocal round_number
        round_number += 1
        
        # Capitals antes de la ronda
        capitals_inicio = {}
        for agente in agentes:
            nombre = agente.jugador.nombre
            capitals_inicio[nombre] = agente.jugador.capital
            tracking_agentes[nombre]['decision_times'].clear()
        
        cards_remaining = sum(agente_markov_normal.cartas_restantes)
        
        if round_number % 100 == 0:
            print(f"Ejecutando ronda {round_number}...")
        
        original_jugar_ronda()
        
        # Procesar resultados de todos los agentes
        round_data = {
            'round': round_number,
            'cards_remaining': cards_remaining
        }
        
        for agente in agentes:
            nombre = agente.jugador.nombre
            nombre_csv = nombre.lower().replace(' ', '_')
            
            capital_final = agente.jugador.capital
            capital_change = capital_final - capitals_inicio[nombre]
            
            resultado = actualizar_resultado_agente(tracking_agentes, nombre, capital_change)
            
            decision_times = tracking_agentes[nombre]['decision_times']
            round_data.update({
                f'{nombre_csv}_decision_time_ms': int(sum(decision_times) * 1000) if decision_times else 0,
                f'{nombre_csv}_decisions': len(decision_times),
                f'{nombre_csv}_result': resultado,
                f'{nombre_csv}_capital_change': capital_change
            })
        
        csv_data.append(round_data)
        
        if round_number % 100 == 0:
            print(f"Ronda {round_number} completada.")
            for agente in agentes:
                nombre = agente.jugador.nombre
                capital_change = agente.jugador.capital - capitals_inicio[nombre]
                print(f"  {nombre}: Capital={agente.jugador.capital} (Δ{capital_change:+d})")

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
        alt_filename = os.path.join(os.path.expanduser("~"), "Desktop", csv_filename)
        try:
            with open(alt_filename, 'w', newline='', encoding='utf-8') as csvfile:
                writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
                writer.writeheader()
                writer.writerows(csv_data)
            print(f"Data saved to alternative location: {alt_filename}")
        except Exception as e2:
            print(f"Failed to save to alternative location: {e2}")

    # Resultados finales para todos los agentes
    total_rounds = round_number
    if total_rounds > 0:
        print(f"\n" + "="*60)
        print("RESULTADOS FINALES - COMPARACIÓN DE AGENTES")
        print("="*60)
        
        for agente in agentes:
            nombre = agente.jugador.nombre
            stats = tracking_agentes[nombre]
            wins = stats['wins']
            losses = stats['losses']
            ties = stats['ties']
            
            print(f"\n{nombre}:")
            print(f"  Victorias: {wins}/{total_rounds} ({wins/total_rounds*100:.2f}%)")
            print(f"  Derrotas: {losses}/{total_rounds} ({losses/total_rounds*100:.2f}%)")
            print(f"  Empates: {ties}/{total_rounds} ({ties/total_rounds*100:.2f}%)")
        
    for agente in agentes:
        assert agente.jugador.capital >= 0, f"Capital negativo para {agente.jugador.nombre}: {agente.jugador.capital}"
        print(f"Capital final {agente.jugador.nombre}: {agente.jugador.capital}")

if __name__ == "__main__":
    test_all()
