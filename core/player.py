from .cartas import Carta, Rango, Palo

#https://www.pokerstars.com/es-419/casino/how-to-play/blackjack/rules/?&no_redirect=1
"""
cartas posibles:
    - A (1 o 11)
    - 2-10 (su valor nominal)
    - J, Q, K (10 puntos cada uno)
"""

class Mano:
    def __init__(self, cartas: list[Carta]):
        """Clase que representa la mano de un jugador en el juego de Blackjack."""
        self.cartas = cartas
        self.apuesta = 0  # Inicializa la apuesta en 0 (no apostada)
        self.turno_terminado = False  # Indica si la mano ya termino


    @property
    def valor_total(self) -> int:
        """Devuelve el valor total de la mano."""
        total = sum(carta.valor for carta in self.cartas)
        ases = sum(1 for carta in self.cartas if carta.rango == Rango.AS)

        while total > 21 and ases > 0:
            total -= 10
            ases -= 1

        return total

    @property
    def es_blanda(self):
        """
        Indica si la mano es blanda (contiene un As que cuenta como 11).
        """
        total_con_as = sum(carta.valor for carta in self.cartas)
        hay_ases = any(carta.rango == Rango.AS for carta in self.cartas)

        return total_con_as <= 21 and hay_ases

    @property
    def es_blackjack(self):
        """
        Indica si la mano es un Blackjack (21 con 2 cartas: As + 10, J, Q o K).
        """
        return len(self.cartas) == 2 and self.valor_total == 21

    def agregar_carta(self, carta: Carta):
        """
        Agrega una carta a la mano
        """
        self.cartas.append(carta)

        if self.valor_total > 21:
            self.turno_terminado = True

    def __str__(self):
        cartas_str = ", ".join(str(c) for c in self.cartas)
        if self.es_blanda:
            return f"[{cartas_str}] (Valor = {self.valor_total}, Blanda)"
        return f"[{cartas_str}] (Valor = {self.valor_total})"

    def __repr__(self) -> str:
        cartas_str = ", ".join(str(c) for c in self.cartas)
        return f"Mano(cartas=[{cartas_str}], valor = {self.valor_total})"


class Jugador:
    def __init__(self, nombre: str, capital: int):
        """
        Inicializa el jugador
        :param nombre: Nombre del jugador
        :param capital: Capital inicial del jugador
        """
        self.nombre = nombre
        self.capital = capital
        self.capital_pre_turno = 0
        self.manos = []

    def __str__(self):
        return f"{self.nombre} (Capital: {self.capital})"

    def reset_manos(self):
        """
        Reinicia la mano del jugador para una nueva ronda.
        """
        self.manos = []

    def apostar(self, cantidad: int) -> bool:
        """
        Permite al jugador realizar una apuesta inicial
        :param cantidad: Cantidad a apostar
        :return: True si la apuesta se ha realizado correctamente, False en caso contrario.
        """

        # No tiene suficiente capital para apostar.
        if cantidad <= 0 or cantidad > self.capital:
            return False

        self.capital_pre_turno = self.capital
        self.capital -= cantidad
        mano = Mano([])
        mano.apuesta = cantidad
        self.manos.append(mano)
        return True


    def pedir_carta(self, mano: Mano, carta: Carta):
        """
        Agrega una carta a la mano del jugador.
        """
        if mano in self.manos:
            return mano.agregar_carta(carta)
        return None


    def dividir_mano(self, mano: Mano) -> bool:
        """
        Permite al jugador dividir su mano si tiene dos cartas del mismo valor.
        :param mano: Mano a dividir
        :return: True si se ha realizado el split, False en caso contrario.
        """
        if len(mano.cartas) != 2 and self.capital >= mano.apuesta:
            return False

        if mano.cartas[0].rango.simbolo != mano.cartas[1].rango.simbolo:
            # No se puede dividir si las cartas no son del mismo simbolo (Ojo: simbolo se refiere a letra, no palo).
            return False

        self.capital -= mano.apuesta
        carta_dividida = mano.cartas.pop()
        nueva_mano = Mano([carta_dividida])
        nueva_mano.apuesta = mano.apuesta
        self.manos.append(nueva_mano)
        return True  # Se ha realizado el split.


    def doblar_apuesta(self, mano: Mano):
        """
        Permite al jugador doblar su apuesta.
        El casino se encarga de repartir una carta adicional.
        """
        if self.capital < mano.apuesta:
            # No puede doblar si no tiene suficiente capital o si ya tiene más de 2 cartas.
            print("No alcanza capital")
            return False

        self.capital -= mano.apuesta
        mano.apuesta *= 2
        return True

    def rendirse(self, mano: Mano):
        """
        Permite al jugador rendirse y recuperar la mitad de su apuesta.
        """
        if mano in self.manos:
            # Asegura que sea un entero
            self.capital += mano.apuesta // 2
            self.manos.remove(mano)
            return True
        return False  # La mano no existe, no se puede rendir.

