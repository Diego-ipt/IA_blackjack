from casino import Casino
from player import Jugador
from agentes_basicos import AgenteAleatorio

def main():
    capital_inicial = 10000000000
    # Crear jugadores
    jugador1 = Jugador("Jugador 1", capital=capital_inicial)
    jugador2 = Jugador("Jugador 2", capital=capital_inicial)
    jugador3 = Jugador("Jugador 3", capital=capital_inicial)

    # Crear agentes para los jugadores
    agente1 = AgenteAleatorio(jugador1)
    agente2 = AgenteAleatorio(jugador2)
    agente3 = AgenteAleatorio(jugador3)

    # Crear el casino con los agentes
    casino = Casino(agentes=[agente1, agente2, agente3], dealer_nombre="Dealer", max_stands=3, min_apuesta=5000)

    # Jugar una ronda
    print("Iniciando Blackjack...")
    for i in range(50):
        casino.jugar_ronda()

    # Mostrar el capital final de los jugadores y cuánto ganaron o perdieron
    print("\nResultados finales:")
    for agente in casino.agentes:
        capital_final = agente.jugador.capital
        ganancia_perdida = capital_final - capital_inicial
        print(f"{agente.jugador.nombre}: Capital final = {capital_final}, Ganancia/Pérdida = {ganancia_perdida}")

if __name__ == "__main__":
    main()