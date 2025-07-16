import joblib
from agents.agente_randomForest import AgenteRandomForest
from core.player import Jugador
from core.casino import Casino
from core.data_collector import DataCollector 

import logging

# logging.basicConfig(
#     level=logging.INFO,
#     format="%(name)s - %(message)s"
# )

def evaluar_agente_rf():
    
    # Parámetros
    n_rondas = 10
    capital_inicial = 10_000

    # Crear jugador y agente
    jugador_rf = Jugador(nombre="AgenteRandomForest", capital=capital_inicial)
    
    modelo_path = "resultados/randomForestClass6/rf_action_clf.joblib"
    encoder_path = "resultados/randomForestClass6/label_encoder.joblib"
    agente_rf = AgenteRandomForest(jugador_rf, modelo_path, encoder_path)

    # Crear DataCollector SIN escritura
    collector = DataCollector(filepath="tests/randomforest.csv", guardar_en_archivo=False)  
    casino = Casino(agentes=[agente_rf], data_collector=collector)

    # Simulación
    print(f"→ Simulando {n_rondas} rondas...\n")

    casino.jugar_partida(num_rondas=n_rondas)
    print(f"tamaño registros: {len(collector.registros)} " )

    # Acceder a registros completos
    registros = [
        r for r in collector.registros
        if r.get("ganancia_neta") is not None
    ]

    wins   = sum(r["ganancia_neta"] > 0 for r in registros)
    losses = sum(r["ganancia_neta"] < 0 for r in registros)
    draws  = sum(r["ganancia_neta"] == 0 for r in registros)

    win_pct  = wins / len(registros) * 100
    loss_pct = losses / len(registros) * 100
    draw_pct = draws / len(registros) * 100
    saldo_final = jugador_rf.capital

    print("=== Resultados ===")
    print(f"🏆 Victorias   : {wins} ({win_pct:.2f} %)")
    print(f"💀 Derrotas    : {losses} ({loss_pct:.2f} %)")
    print(f"🤝 Empates     : {draws} ({draw_pct:.2f} %)")
    print(f"💰 Capital final: ${saldo_final:,.0f} (Inicio: ${capital_inicial})")
    print(f"📈 Ganancia neta: ${saldo_final - capital_inicial:,.0f}")



if __name__ == "__main__":
    evaluar_agente_rf()