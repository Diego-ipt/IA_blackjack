import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from pathlib import Path
import glob

def load_latest_csv():
    """Carga el archivo CSV más reciente de los resultados de comparación de Markov"""
    csv_files = glob.glob("test_markov_comparison_*.csv")
    if not csv_files:
        # Fallback a archivos antiguos
        csv_files = glob.glob("test_markov_results_*.csv")
        if not csv_files:
            raise FileNotFoundError("No se encontraron archivos CSV de resultados")
        
        latest_file = max(csv_files, key=lambda x: Path(x).stat().st_mtime)
        print(f"Cargando archivo antiguo: {latest_file}")
        return pd.read_csv(latest_file), "old"
    
    latest_file = max(csv_files, key=lambda x: Path(x).stat().st_mtime)
    print(f"Cargando archivo de comparación: {latest_file}")
    return pd.read_csv(latest_file), "comparison"

def calculate_streaks(results):
    """Calcula las rachas de victorias y derrotas"""
    if len(results) == 0:
        return 0, 0, 0, 0
    
    win_streaks = []
    loss_streaks = []
    current_win_streak = 0
    current_loss_streak = 0
    
    for result in results:
        if result == 1:  # Victoria
            current_win_streak += 1
            if current_loss_streak > 0:
                loss_streaks.append(current_loss_streak)
                current_loss_streak = 0
        elif result == -1:  # Derrota
            current_loss_streak += 1
            if current_win_streak > 0:
                win_streaks.append(current_win_streak)
                current_win_streak = 0
        else:  # Empate
            if current_win_streak > 0:
                win_streaks.append(current_win_streak)
                current_win_streak = 0
            if current_loss_streak > 0:
                loss_streaks.append(current_loss_streak)
                current_loss_streak = 0
    
    # Agregar rachas finales si existen
    if current_win_streak > 0:
        win_streaks.append(current_win_streak)
    if current_loss_streak > 0:
        loss_streaks.append(current_loss_streak)
    
    max_win_streak = max(win_streaks) if win_streaks else 0
    avg_win_streak = np.mean(win_streaks) if win_streaks else 0
    max_loss_streak = max(loss_streaks) if loss_streaks else 0
    avg_loss_streak = np.mean(loss_streaks) if loss_streaks else 0
    
    return max_win_streak, avg_win_streak, max_loss_streak, avg_loss_streak

def analyze_agent_performance(df, agent_name, prefix):
    """Analiza el rendimiento detallado de un agente específico"""
    print("="*60)
    print(f"RESUMEN DE RENDIMIENTO DEL AGENTE {agent_name.upper()}")
    print("="*60)
    
    total_rounds = len(df)
    wins = len(df[df[f'{prefix}_result'] == 1])
    losses = len(df[df[f'{prefix}_result'] == -1])
    ties = len(df[df[f'{prefix}_result'] == 0])
    
    print(f"Total de rondas jugadas: {total_rounds}")
    print(f"Victorias: {wins} ({wins/total_rounds*100:.2f}%)")
    print(f"Derrotas: {losses} ({losses/total_rounds*100:.2f}%)")
    print(f"Empates: {ties} ({ties/total_rounds*100:.2f}%)")
    if losses > 0:
        print(f"Ratio Victoria/Derrota: {wins/losses:.2f}")
    
    # Calcular rachas
    results = df[f'{prefix}_result'].values
    max_win, avg_win, max_loss, avg_loss = calculate_streaks(results)
    print(f"Racha de victorias más larga: {max_win}")
    print(f"Racha promedio de victorias: {avg_win:.2f}")
    print(f"Racha de derrotas más larga: {max_loss}")
    print(f"Racha promedio de derrotas: {avg_loss:.2f}")

def analyze_agent_decision_times(df, agent_name, prefix):
    """Analiza los tiempos de decisión de un agente específico"""
    print("\n" + "="*60)
    print(f"ANÁLISIS DE TIEMPOS DE DECISIÓN - {agent_name.upper()}")
    print("="*60)
    
    # Filtrar rondas con decisiones
    df_agent = df[df[f'{prefix}_decisions'] > 0].copy()
    
    if len(df_agent) == 0:
        print("No hay datos de decisiones para este agente")
        return
    
    # Calcular tiempo promedio por decisión
    df_agent['avg_time'] = df_agent[f'{prefix}_decision_time_ms'] / df_agent[f'{prefix}_decisions']
    
    total_decisions = df_agent[f'{prefix}_decisions'].sum()
    total_time = df_agent[f'{prefix}_decision_time_ms'].sum()
    avg_time = df_agent['avg_time'].mean()
    min_time = df_agent['avg_time'].min()
    max_time = df_agent['avg_time'].max()
    std_time = df_agent['avg_time'].std()
    
    print(f"Rondas con decisiones: {len(df_agent)}")
    print(f"Total de decisiones tomadas: {total_decisions}")
    print(f"Tiempo total de decisión: {total_time} ms")
    print(f"Tiempo promedio por decisión: {avg_time:.2f} ms")
    print(f"Tiempo más rápido por decisión: {min_time:.2f} ms")
    print(f"Tiempo más lento por decisión: {max_time:.2f} ms")
    print(f"Desviación estándar: {std_time:.2f} ms")
    
    # Percentiles
    print(f"\nPercentiles de tiempo por decisión:")
    percentiles = [50, 75, 90, 95, 99]
    for p in percentiles:
        value = np.percentile(df_agent['avg_time'], p)
        print(f"  P{p}: {value:.2f} ms")

def analyze_agent_by_cards_remaining(df, agent_name, prefix):
    """Analiza el rendimiento de un agente por cartas restantes"""
    print("\n" + "="*60)
    print(f"ANÁLISIS POR CARTAS RESTANTES EN EL MAZO - {agent_name.upper()}")
    print("="*60)
    
    # Crear bins para cartas restantes
    df['cards_bin'] = pd.cut(df['cards_remaining'], 
                            bins=[0, 50, 100, 150, 200, 300],
                            labels=['0-50', '51-100', '101-150', '151-200', '201+'])
    
    # Análisis por bins
    grouped = df.groupby('cards_bin', observed=True)[f'{prefix}_result'].agg(['count', 'mean', 'sum'])
    
    print("Rendimiento por rango de cartas restantes:")
    print("           count   mean  sum  win_rate_%  loss_rate_%  tie_rate_%")
    print("cards_bin")
    
    for bin_name in grouped.index:
        bin_data = df[df['cards_bin'] == bin_name]
        wins = len(bin_data[bin_data[f'{prefix}_result'] == 1])
        losses = len(bin_data[bin_data[f'{prefix}_result'] == -1])
        ties = len(bin_data[bin_data[f'{prefix}_result'] == 0])
        total = len(bin_data)
        
        win_rate = wins / total * 100 if total > 0 else 0
        loss_rate = losses / total * 100 if total > 0 else 0
        tie_rate = ties / total * 100 if total > 0 else 0
        
        print(f"{bin_name:8} {grouped.loc[bin_name, 'count']:8} {grouped.loc[bin_name, 'mean']:7.3f} {grouped.loc[bin_name, 'sum']:4} {win_rate:10.2f} {loss_rate:11.2f} {tie_rate:10.2f}")
    
    # Correlación
    correlation = df['cards_remaining'].corr(df[f'{prefix}_result'])
    print(f"\nCorrelación entre cartas restantes y resultado: {correlation:.4f}")
    
    # Desglose detallado
    print(f"\nDesglose detallado:")
    for bin_name in grouped.index:
        bin_data = df[df['cards_bin'] == bin_name]
        wins = len(bin_data[bin_data[f'{prefix}_result'] == 1])
        losses = len(bin_data[bin_data[f'{prefix}_result'] == -1])
        ties = len(bin_data[bin_data[f'{prefix}_result'] == 0])
        total = len(bin_data)
        print(f"  {bin_name}: {wins}W/{losses}L/{ties}T de {total} rondas")

def analyze_agent_decision_complexity(df, agent_name, prefix):
    """Analiza la complejidad de decisiones de un agente"""
    print("\n" + "="*60)
    print(f"ANÁLISIS DE COMPLEJIDAD DE DECISIONES - {agent_name.upper()}")
    print("="*60)
    
    # Filtrar rondas con decisiones
    df_agent = df[df[f'{prefix}_decisions'] > 0].copy()
    
    if len(df_agent) == 0:
        print("No hay datos de decisiones para este agente")
        return
    
    # Correlación entre número de decisiones y tiempo total
    correlation = df_agent[f'{prefix}_decisions'].corr(df_agent[f'{prefix}_decision_time_ms'])
    print(f"Correlación decisiones vs tiempo total: {correlation:.4f}")
    
    # Rendimiento por número de decisiones
    grouped = df_agent.groupby(f'{prefix}_decisions').agg({
        f'{prefix}_decision_time_ms': ['count', 'mean', 'std'],
        f'{prefix}_result': 'mean'
    })
    
    print(f"\nRendimiento por número de decisiones por ronda:")
    print("                total_decision_time_ms                 result")
    print("                                 count    mean     std   mean")
    print(f"{prefix}_decisions")
    
    for decisions in grouped.index:
        count = grouped.loc[decisions, (f'{prefix}_decision_time_ms', 'count')]
        mean_time = grouped.loc[decisions, (f'{prefix}_decision_time_ms', 'mean')]
        std_time = grouped.loc[decisions, (f'{prefix}_decision_time_ms', 'std')]
        mean_result = grouped.loc[decisions, (f'{prefix}_result', 'mean')]
        
        std_str = f"{std_time:.2f}" if not pd.isna(std_time) else "NaN"
        print(f"{decisions:15} {count:8} {mean_time:8.2f} {std_str:8} {mean_result:6.2f}")

def analyze_comparison_performance(df):
    """Analiza el rendimiento de los tres agentes Markov en comparación"""
    # Detectar qué agentes están presentes en el dataset
    agents = []
    if 'normal_result' in df.columns:
        agents.append(('Markov Normal', 'normal'))
    if 'arriesgado_result' in df.columns:
        agents.append(('Markov Arriesgado', 'arriesgado'))
    if 'rl_result' in df.columns:
        agents.append(('Markov RL (Optimizado)', 'rl'))
    
    # Análisis detallado por agente
    for agent_name, prefix in agents:
        analyze_agent_performance(df, agent_name, prefix)
        analyze_agent_decision_times(df, agent_name, prefix)
        analyze_agent_by_cards_remaining(df, agent_name, prefix)
        analyze_agent_decision_complexity(df, agent_name, prefix)
    
    # Comparación entre agentes
    print("\n" + "="*60)
    print("COMPARACIÓN ENTRE AGENTES MARKOV")
    print("="*60)
    
    total_rounds = len(df)
    comparison_data = []
    
    for agent_name, prefix in agents:
        wins = len(df[df[f'{prefix}_result'] == 1])
        losses = len(df[df[f'{prefix}_result'] == -1])
        ties = len(df[df[f'{prefix}_result'] == 0])
        winrate = wins / total_rounds * 100
        
        # Tiempo promedio de decisión
        df_agent = df[df[f'{prefix}_decisions'] > 0].copy()
        if len(df_agent) > 0:
            df_agent['avg_time'] = df_agent[f'{prefix}_decision_time_ms'] / df_agent[f'{prefix}_decisions']
            avg_decision_time = df_agent['avg_time'].mean()
        else:
            avg_decision_time = 0
        
        comparison_data.append({
            'Agente': agent_name,
            'Victorias': wins,
            'Derrotas': losses,
            'Empates': ties,
            'Tasa_Victoria_%': winrate,
            'Tiempo_Promedio_ms': avg_decision_time
        })
    
    comparison_df = pd.DataFrame(comparison_data)
    print(comparison_df.to_string(index=False))
    
    # Mejor agente por tasa de victoria
    best_agent = comparison_df.loc[comparison_df['Tasa_Victoria_%'].idxmax()]
    print(f"\n✓ Mejor agente por tasa de victoria: {best_agent['Agente']} ({best_agent['Tasa_Victoria_%']:.2f}%)")
    
    # Agente más eficiente (menor tiempo de decisión)
    fastest_agent = comparison_df.loc[comparison_df['Tiempo_Promedio_ms'].idxmin()]
    print(f"✓ Agente más eficiente: {fastest_agent['Agente']} ({fastest_agent['Tiempo_Promedio_ms']:.2f} ms promedio)")

def create_comparison_visualizations(df):
    """Crea visualizaciones comparativas para todos los agentes disponibles"""
    print("\n" + "="*60)
    print("GENERANDO VISUALIZACIONES COMPARATIVAS")
    print("="*60)
    
    # Detectar agentes disponibles
    agents = []
    if 'normal_result' in df.columns:
        agents.append(('Normal', 'normal'))
    if 'arriesgado_result' in df.columns:
        agents.append(('Arriesgado', 'arriesgado'))
    if 'rl_result' in df.columns:
        agents.append(('RL', 'rl'))
    
    plt.style.use('seaborn-v0_8')
    fig, axes = plt.subplots(2, 3, figsize=(18, 12))
    
    # 1. Ganancia acumulada comparativa
    for agent_name, prefix in agents:
        df[f'{prefix}_cumulative'] = df[f'{prefix}_result'].cumsum()
        axes[0, 0].plot(df['round'], df[f'{prefix}_cumulative'], label=agent_name, alpha=0.8)
    
    axes[0, 0].set_title('Ganancia Acumulada - Comparación')
    axes[0, 0].set_xlabel('Ronda')
    axes[0, 0].set_ylabel('Ganancia Acumulada')
    axes[0, 0].legend()
    axes[0, 0].grid(True)
    
    # 2. Distribución de resultados
    results_data = []
    for agent_name, prefix in agents:
        for result in [-1, 0, 1]:
            count = len(df[df[f'{prefix}_result'] == result])
            results_data.append({'Agente': agent_name, 'Resultado': result, 'Cantidad': count})
    
    results_df = pd.DataFrame(results_data)
    result_labels = {-1: 'Derrota', 0: 'Empate', 1: 'Victoria'}
    results_df['Resultado_Label'] = results_df['Resultado'].map(result_labels)
    
    pivot_results = results_df.pivot(index='Resultado_Label', columns='Agente', values='Cantidad')
    pivot_results.plot(kind='bar', ax=axes[0, 1])
    axes[0, 1].set_title('Distribución de Resultados')
    axes[0, 1].set_xlabel('Resultado')
    axes[0, 1].set_ylabel('Cantidad')
    axes[0, 1].tick_params(axis='x', rotation=45)
    
    # 3. Tiempos de decisión comparativos
    for agent_name, prefix in agents:
        df_agent = df[df[f'{prefix}_decisions'] > 0].copy()
        if len(df_agent) > 0:
            df_agent['avg_time'] = df_agent[f'{prefix}_decision_time_ms'] / df_agent[f'{prefix}_decisions']
            axes[0, 2].hist(df_agent['avg_time'], bins=30, alpha=0.7, label=agent_name)
    
    axes[0, 2].set_title('Distribución de Tiempos de Decisión')
    axes[0, 2].set_xlabel('Tiempo promedio (ms)')
    axes[0, 2].set_ylabel('Frecuencia')
    axes[0, 2].legend()
    
    # 4. Rolling win rate comparativo
    window = 50
    for agent_name, prefix in agents:
        df[f'{prefix}_rolling'] = df[f'{prefix}_result'].rolling(window=window).mean()
        axes[1, 0].plot(df['round'], df[f'{prefix}_rolling'], label=agent_name, alpha=0.8)
    
    axes[1, 0].set_title(f'Tasa de Victoria Promedio (ventana {window})')
    axes[1, 0].set_xlabel('Ronda')
    axes[1, 0].set_ylabel('Tasa de Victoria')
    axes[1, 0].axhline(y=0, color='r', linestyle='--', alpha=0.5)
    axes[1, 0].legend()
    
    # 5. Rendimiento por cartas restantes
    df['cards_bin'] = pd.cut(df['cards_remaining'], 
                            bins=[0, 50, 100, 150, 200, 300],
                            labels=['0-50', '51-100', '101-150', '151-200', '201+'])
    
    x_pos = np.arange(len(df['cards_bin'].cat.categories))
    width = 0.8 / len(agents)
    
    for i, (agent_name, prefix) in enumerate(agents):
        by_cards = df.groupby('cards_bin', observed=True)[f'{prefix}_result'].mean()
        axes[1, 1].bar(x_pos + i*width - width*(len(agents)-1)/2, by_cards, width, 
                      label=agent_name, alpha=0.8)
    
    axes[1, 1].set_title('Rendimiento por Cartas Restantes')
    axes[1, 1].set_xlabel('Cartas Restantes')
    axes[1, 1].set_ylabel('Resultado Promedio')
    axes[1, 1].set_xticks(x_pos)
    axes[1, 1].set_xticklabels(df['cards_bin'].cat.categories)
    axes[1, 1].legend()
    axes[1, 1].axhline(y=0, color='r', linestyle='--', alpha=0.5)
    
    # 6. Cambios de capital acumulados
    for agent_name, prefix in agents:
        if f'{prefix}_capital_change' in df.columns:
            df[f'{prefix}_capital_cumulative'] = df[f'{prefix}_capital_change'].cumsum()
            axes[1, 2].plot(df['round'], df[f'{prefix}_capital_cumulative'], 
                           label=f'{agent_name} Capital', alpha=0.8)
    
    axes[1, 2].set_title('Cambio de Capital Acumulado')
    axes[1, 2].set_xlabel('Ronda')
    axes[1, 2].set_ylabel('Cambio de Capital ($)')
    axes[1, 2].legend()
    axes[1, 2].grid(True)
    
    plt.tight_layout()
    
    # Guardar la figura
    timestamp = pd.Timestamp.now().strftime("%Y%m%d_%H%M%S")
    filename = f"markov_comparison_{timestamp}.png"
    plt.savefig(filename, dpi=300, bbox_inches='tight')
    print(f"Gráficos guardados en: {filename}")
    
    plt.show()

# ...existing code for old format analysis...
def analyze_performance(df):
    """Analiza el rendimiento general del agente Markov (formato antiguo)"""
    print("="*60)
    print("RESUMEN DE RENDIMIENTO DEL AGENTE MARKOV")
    print("="*60)
    
    total_rounds = len(df)
    wins = len(df[df['result'] == 1])
    losses = len(df[df['result'] == -1])
    ties = len(df[df['result'] == 0])
    
    print(f"Total de rondas jugadas: {total_rounds}")
    print(f"Victorias: {wins} ({wins/total_rounds*100:.2f}%)")
    print(f"Derrotas: {losses} ({losses/total_rounds*100:.2f}%)")
    print(f"Empates: {ties} ({ties/total_rounds*100:.2f}%)")
    if losses > 0:
        print(f"Ratio Victoria/Derrota: {wins/losses:.2f}")

def main():
    """Función principal"""
    try:
        # Cargar datos
        df, file_type = load_latest_csv()
        
        if file_type == "comparison":
            # Análisis para formato de comparación
            analyze_comparison_performance(df)
            create_comparison_visualizations(df)
        else:
            # Análisis para formato antiguo
            analyze_performance(df)
            # ...existing old format analysis functions...
        
        print("\n" + "="*60)
        print("ANÁLISIS COMPLETADO")
        print("="*60)
        
    except Exception as e:
        print(f"Error durante el análisis: {e}")

if __name__ == "__main__":
    main()
