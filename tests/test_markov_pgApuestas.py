import time
import csv
import datetime
from core.player import Jugador
from core.casino import Casino
from agents.markov import AgenteMarkov_arriesgado, AgenteMarkov_normal
from agents.agente_A_5 import AgenteAleatorio_5
from agents.markov_umbral import AgenteMarkov_prob_estable_por_umbral
from agents.markovPoliticaApuestas import AgenteMarkov_PoliticaApuestas

# ========== CONFIGURACIÓN ==========
NUM_RONDAS = 100
DINERO_INICIAL = 1000


def test_agentes_markov_comparacion():
    print(f"\n{'=' * 50}\nIniciando test de agentes Markov con {NUM_RONDAS} rondas\n{'=' * 50}")

    # Inicialización de agentes
    agentes = [
        ("Markov_Normal", AgenteMarkov_normal(Jugador("Markov_Normal", DINERO_INICIAL), num_mazos=4)),
        ("Markov_Arriesgado", AgenteMarkov_arriesgado(Jugador("Markov_Arriesgado", DINERO_INICIAL), num_mazos=4)),
        ("Markov_Umbral", AgenteMarkov_prob_estable_por_umbral(Jugador("Markov_Umbral", DINERO_INICIAL), num_mazos=4)),
        ("Markov_PG", AgenteMarkov_PoliticaApuestas(Jugador("Markov_PG", DINERO_INICIAL), num_mazos=4)),
        ("Aleatorio1", AgenteAleatorio_5(Jugador("Aleatorio1", DINERO_INICIAL))),
        ("Aleatorio2", AgenteAleatorio_5(Jugador("Aleatorio2", DINERO_INICIAL)))
    ]

    # Configurar recompensas para el agente de umbral
    agentes[2][1].set_recompensas({'victoria': 1.0, 'derrota': -1.0, 'empate': -0.25})

    # Preparar estructura de datos
    fieldnames = ['ronda', 'cartas_restantes'] + \
                 [f"{nombre}_capital" for nombre, _ in agentes] + \
                 [f"{nombre}_apuesta" for nombre, _ in agentes] + \
                 [f"{nombre}_decision_ms" for nombre, _ in agentes] + \
                 [f"{nombre}_resultado" for nombre, _ in agentes]

    resultados = {nombre: {'ganadas': 0, 'perdidas': 0, 'empatadas': 0} for nombre, _ in agentes}
    historial = []

    # Casino configurado
    casino = Casino([agente for _, agente in agentes], num_mazos=4, zapato=0.75)

    print("\nAgentes participantes:")
    for nombre, agente in agentes:
        print(f"- {nombre}: {agente.__class__.__name__}")

    # Función para registrar resultados
    def registrar_ronda(ronda):
        datos_ronda = {
            'ronda': ronda,
            'cartas_restantes': sum(agentes[0][1].cartas_restantes) if hasattr(agentes[0][1],
                                                                               'cartas_restantes') else -1
        }

        for nombre, agente in agentes:
            capital = agente.jugador.capital
            apuesta = agente.decidir_apuesta() if hasattr(agente,
                                                          'decidir_apuesta') else 5  # Default $5 para otros agentes
            resultado = "activo" if capital > 0 else "eliminado"

            datos_ronda.update({
                f"{nombre}_capital": capital,
                f"{nombre}_apuesta": apuesta,
                f"{nombre}_decision_ms": 0,
                f"{nombre}_resultado": resultado
            })

        return datos_ronda

    # Bucle principal de juego
    for ronda in range(1, NUM_RONDAS + 1):
        datos_ronda = registrar_ronda(ronda)

        # Jugar ronda y medir tiempos
        for nombre, agente in agentes:
            if agente.jugador.capital <= 0:
                continue

            inicio = time.time()
            try:
                casino._jugar_ronda()  # Jugar una ronda completa
            except Exception as e:
                print(f"Error en ronda {ronda} con {nombre}: {str(e)}")
                continue
            finally:
                datos_ronda[f"{nombre}_decision_ms"] = int((time.time() - inicio) * 1000)

        # Actualizar resultados
        for nombre, agente in agentes:
            if agente.jugador.capital > datos_ronda[f"{nombre}_capital"]:
                resultados[nombre]['ganadas'] += 1
            elif agente.jugador.capital < datos_ronda[f"{nombre}_capital"]:
                resultados[nombre]['perdidas'] += 1
            else:
                resultados[nombre]['empatadas'] += 1

        historial.append(datos_ronda)

        if ronda % 10 == 0 or ronda == NUM_RONDAS:
            print(f"\nRonda {ronda} - Resumen:")
            for nombre, agente in agentes:
                print(
                    f"{nombre}: ${agente.jugador.capital} (G:{resultados[nombre]['ganadas']} P:{resultados[nombre]['perdidas']} E:{resultados[nombre]['empatadas']})")

    # Guardar resultados en CSV
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    csv_filename = f"resultados_markov_{timestamp}.csv"

    try:
        with open(csv_filename, 'w', newline='', encoding='utf-8') as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(historial)
        print(f"\nDatos guardados en {csv_filename}")
    except Exception as e:
        print(f"\nError al guardar CSV: {e}")

    # Resultados finales
    print("\n" + "=" * 50)
    print("RESULTADOS FINALES".center(50))
    print("=" * 50)

    for nombre, agente in agentes:
        res = resultados[nombre]
        total = sum(res.values())
        print(f"\n{nombre}:")
        print(f"  Capital final: ${agente.jugador.capital}")
        print(f"  Rendimiento: {(agente.jugador.capital - DINERO_INICIAL) / DINERO_INICIAL * 100:.2f}%")
        print(f"  Victorias: {res['ganadas']} ({res['ganadas'] / total * 100:.1f}%)")
        print(f"  Derrotas: {res['perdidas']} ({res['perdidas'] / total * 100:.1f}%)")
        print(f"  Empates: {res['empatadas']} ({res['empatadas'] / total * 100:.1f}%)")


if __name__ == "__main__":
    test_agentes_markov_comparacion()