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

def analyze_comparison_performance(df):
    """Analiza el rendimiento de ambos agentes Markov en comparación"""
    print("="*60)
    print("COMPARACIÓN DE AGENTES MARKOV")
    print("="*60)
    
    total_rounds = len(df)
    
    # Análisis para Markov Normal
    normal_wins = len(df[df['normal_result'] == 1])
    normal_losses = len(df[df['normal_result'] == -1])
    normal_ties = len(df[df['normal_result'] == 0])
    
    # Análisis para Markov Arriesgado
    arriesgado_wins = len(df[df['arriesgado_result'] == 1])
    arriesgado_losses = len(df[df['arriesgado_result'] == -1])
    arriesgado_ties = len(df[df['arriesgado_result'] == 0])
    
    print(f"Total de rondas: {total_rounds}")
    print(f"\nMarkov Normal:")
    print(f"  Victorias: {normal_wins} ({normal_wins/total_rounds*100:.2f}%)")
    print(f"  Derrotas: {normal_losses} ({normal_losses/total_rounds*100:.2f}%)")
    print(f"  Empates: {normal_ties} ({normal_ties/total_rounds*100:.2f}%)")
    if normal_losses > 0:
        print(f"  Ratio V/D: {normal_wins/normal_losses:.2f}")
    
    print(f"\nMarkov Arriesgado:")
    print(f"  Victorias: {arriesgado_wins} ({arriesgado_wins/total_rounds*100:.2f}%)")
    print(f"  Derrotas: {arriesgado_losses} ({arriesgado_losses/total_rounds*100:.2f}%)")
    print(f"  Empates: {arriesgado_ties} ({arriesgado_ties/total_rounds*100:.2f}%)")
    if arriesgado_losses > 0:
        print(f"  Ratio V/D: {arriesgado_wins/arriesgado_losses:.2f}")
    
    # Comparación directa
    print(f"\nComparación:")
    normal_winrate = normal_wins / total_rounds
    arriesgado_winrate = arriesgado_wins / total_rounds
    
    diff = (normal_winrate - arriesgado_winrate) * 100
    if abs(diff) < 0.1:
        print(f"  Rendimiento similar ({abs(diff):.2f}% diferencia)")
    elif normal_winrate > arriesgado_winrate:
        print(f"  ✓ Normal supera a Arriesgado por {diff:.2f}%")
    else:
        print(f"  ✓ Arriesgado supera a Normal por {-diff:.2f}%")

def analyze_comparison_decision_times(df):
    """Analiza los tiempos de decisión de ambos agentes"""
    print("\n" + "="*60)
    print("ANÁLISIS DE TIEMPOS DE DECISIÓN - COMPARACIÓN")
    print("="*60)
    
    # Filtrar rondas con decisiones
    df_normal = df[df['normal_decisions'] > 0]
    df_arriesgado = df[df['arriesgado_decisions'] > 0]
    
    if len(df_normal) > 0:
        df_normal['avg_time'] = df_normal['normal_decision_time_ms'] / df_normal['normal_decisions']
        print(f"\nMarkov Normal:")
        print(f"  Rondas con decisiones: {len(df_normal)}")
        print(f"  Tiempo promedio por decisión: {df_normal['avg_time'].mean():.2f} ms")
        print(f"  Tiempo total: {df_normal['normal_decision_time_ms'].sum()} ms")
        print(f"  Decisiones totales: {df_normal['normal_decisions'].sum()}")
    
    if len(df_arriesgado) > 0:
        df_arriesgado['avg_time'] = df_arriesgado['arriesgado_decision_time_ms'] / df_arriesgado['arriesgado_decisions']
        print(f"\nMarkov Arriesgado:")
        print(f"  Rondas con decisiones: {len(df_arriesgado)}")
        print(f"  Tiempo promedio por decisión: {df_arriesgado['avg_time'].mean():.2f} ms")
        print(f"  Tiempo total: {df_arriesgado['arriesgado_decision_time_ms'].sum()} ms")
        print(f"  Decisiones totales: {df_arriesgado['arriesgado_decisions'].sum()}")
    
    # Comparación de eficiencia
    if len(df_normal) > 0 and len(df_arriesgado) > 0:
        normal_avg = df_normal['avg_time'].mean()
        arriesgado_avg = df_arriesgado['avg_time'].mean()
        print(f"\nComparación de eficiencia:")
        if normal_avg < arriesgado_avg:
            print(f"  ✓ Normal es {arriesgado_avg/normal_avg:.2f}x más rápido")
        else:
            print(f"  ✓ Arriesgado es {normal_avg/arriesgado_avg:.2f}x más rápido")

def create_comparison_visualizations(df):
    """Crea visualizaciones comparativas"""
    print("\n" + "="*60)
    print("GENERANDO VISUALIZACIONES COMPARATIVAS")
    print("="*60)
    
    plt.style.use('seaborn-v0_8')
    fig, axes = plt.subplots(2, 3, figsize=(18, 12))
    
    # 1. Ganancia acumulada comparativa
    df['normal_cumulative'] = df['normal_result'].cumsum()
    df['arriesgado_cumulative'] = df['arriesgado_result'].cumsum()
    
    axes[0, 0].plot(df['round'], df['normal_cumulative'], label='Normal', alpha=0.8)
    axes[0, 0].plot(df['round'], df['arriesgado_cumulative'], label='Arriesgado', alpha=0.8)
    axes[0, 0].set_title('Ganancia Acumulada - Comparación')
    axes[0, 0].set_xlabel('Ronda')
    axes[0, 0].set_ylabel('Ganancia Acumulada')
    axes[0, 0].legend()
    axes[0, 0].grid(True)
    
    # 2. Distribución de resultados
    results_data = []
    for agent in ['Normal', 'Arriesgado']:
        col = f'{agent.lower()}_result'
        for result in [-1, 0, 1]:
            count = len(df[df[col] == result])
            results_data.append({'Agente': agent, 'Resultado': result, 'Cantidad': count})
    
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
    df_normal_time = df[df['normal_decisions'] > 0]
    df_arriesgado_time = df[df['arriesgado_decisions'] > 0]
    
    if len(df_normal_time) > 0 and len(df_arriesgado_time) > 0:
        df_normal_time['avg_time'] = df_normal_time['normal_decision_time_ms'] / df_normal_time['normal_decisions']
        df_arriesgado_time['avg_time'] = df_arriesgado_time['arriesgado_decision_time_ms'] / df_arriesgado_time['arriesgado_decisions']
        
        axes[0, 2].hist(df_normal_time['avg_time'], bins=30, alpha=0.7, label='Normal')
        axes[0, 2].hist(df_arriesgado_time['avg_time'], bins=30, alpha=0.7, label='Arriesgado')
        axes[0, 2].set_title('Distribución de Tiempos de Decisión')
        axes[0, 2].set_xlabel('Tiempo promedio (ms)')
        axes[0, 2].set_ylabel('Frecuencia')
        axes[0, 2].legend()
    
    # 4. Rolling win rate comparativo
    window = 50
    df['normal_rolling'] = df['normal_result'].rolling(window=window).mean()
    df['arriesgado_rolling'] = df['arriesgado_result'].rolling(window=window).mean()
    
    axes[1, 0].plot(df['round'], df['normal_rolling'], label='Normal', alpha=0.8)
    axes[1, 0].plot(df['round'], df['arriesgado_rolling'], label='Arriesgado', alpha=0.8)
    axes[1, 0].set_title(f'Tasa de Victoria Promedio (ventana {window})')
    axes[1, 0].set_xlabel('Ronda')
    axes[1, 0].set_ylabel('Tasa de Victoria')
    axes[1, 0].axhline(y=0, color='r', linestyle='--', alpha=0.5)
    axes[1, 0].legend()
    
    # 5. Rendimiento por cartas restantes
    df['cards_bin'] = pd.cut(df['cards_remaining'], 
                            bins=[0, 50, 100, 150, 200, 250],
                            labels=['0-50', '51-100', '101-150', '151-200', '201+'])
    
    normal_by_cards = df.groupby('cards_bin', observed=True)['normal_result'].mean()
    arriesgado_by_cards = df.groupby('cards_bin', observed=True)['arriesgado_result'].mean()
    
    x_pos = np.arange(len(normal_by_cards))
    width = 0.35
    
    axes[1, 1].bar(x_pos - width/2, normal_by_cards, width, label='Normal', alpha=0.8)
    axes[1, 1].bar(x_pos + width/2, arriesgado_by_cards, width, label='Arriesgado', alpha=0.8)
    axes[1, 1].set_title('Rendimiento por Cartas Restantes')
    axes[1, 1].set_xlabel('Cartas Restantes')
    axes[1, 1].set_ylabel('Resultado Promedio')
    axes[1, 1].set_xticks(x_pos)
    axes[1, 1].set_xticklabels(normal_by_cards.index)
    axes[1, 1].legend()
    axes[1, 1].axhline(y=0, color='r', linestyle='--', alpha=0.5)
    
    # 6. Scatter plot: Normal vs Arriesgado por ronda
    colors = ['red' if n < a else 'blue' if n > a else 'gray' 
             for n, a in zip(df['normal_result'], df['arriesgado_result'])]
    axes[1, 2].scatter(df['normal_result'], df['arriesgado_result'], 
                      c=colors, alpha=0.6, s=20)
    axes[1, 2].set_title('Normal vs Arriesgado por Ronda')
    axes[1, 2].set_xlabel('Resultado Normal')
    axes[1, 2].set_ylabel('Resultado Arriesgado')
    axes[1, 2].plot([-1, 1], [-1, 1], 'k--', alpha=0.5)
    
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
            analyze_comparison_decision_times(df)
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
