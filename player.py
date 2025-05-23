#https://www.pokerstars.com/es-419/casino/how-to-play/blackjack/rules/?&no_redirect=1

"""
cartas posibles:
    - A (1 o 11)
    - 2-10 (su valor nominal)
    - J, Q, K (10 puntos cada uno)
"""

def valor_carta(carta):
    """Devuelve el valor de una carta en el juego de Blackjack."""
    if carta in ['J', 'Q', 'K']:
        return 10
    elif carta == 'A':
        return 11  # El valor del As puede ajustarse más tarde si es necesario.
    else:
        return int(carta)

class Mano:
    """Clase que representa la mano de un jugador en el juego de Blackjack."""
    def __init__(self, cartas):
        # Inicializa la mano con una lista de cartas y una apuesta.
        self.cartas = cartas
        self.total = sum(valor_carta(carta) for carta in cartas)
        self.ases = cartas.count('A')  # Cuenta cuántos Ases hay en la mano.
        # Ajusta el valor del As si el total supera 21. (tocaron dos Ases)
        if self.total > 21 and 'A' in cartas:
            self.ases -= 1
            self.total -= 10
        self.apuesta = 0  # Inicializa la apuesta en 0 (no apostada)
        self.bajada = False  # Indica si la mano ya termino

    def agregar_carta(self, carta):
        """si se pasa, se marca la mano como bajada."""
        self.cartas.append(carta)
        if carta == 'A':
            self.ases += 1
        self.total += valor_carta(carta)
        # Ajusta el valor del As si el total supera 21.
        if self.total > 21:
            if self.ases > 0:
                self.ases -= 1
                self.total -= 10
            else:
                self.bajada=True
                return False  # La mano ha perdido, no se puede seguir jugando.
        return True # La mano sigue vigente.

    def valor_total(self):
        """Devuelve el valor total de la mano."""
        return self.total



class Jugador:
    def __init__(self, nombre, capital=0):
        # Inicializa el jugador
        self.nombre = nombre
        self.capital = capital
        self.manos = []

    def apostar(self, cantidad, mano):
        """Permite al jugador realizar una apuesta."""
        if cantidad > self.capital:
            return False  # No tiene suficiente capital para apostar.
        mano.apuesta = cantidad
        self.manos.append(mano)
        self.capital -= cantidad

    def pedir_carta(self, mano, carta):
        """Permite al jugador pedir una carta adicional."""
        if mano in self.manos: 
            return mano.agregar_carta(carta) # La mano ha perdido, no se puede seguir jugando.

            
    def terminar_mano(self, mano):
        """marca la mano como terminada."""
        if mano in self.manos:
            mano.bajada = True  # Marca la mano como terminada.

    def split(self, mano):
        """Permite al jugador dividir su mano si tiene dos cartas del mismo valor."""
        if len(mano.cartas) == 2 and valor_carta(mano.cartas[0]) == valor_carta(mano.cartas[1]) and self.capital >= mano.apuesta:
            nueva_mano = Mano([mano.cartas.pop()])
            self.capital -= mano.apuesta
            nueva_mano.apuesta = mano.apuesta
            self.manos.append(nueva_mano)
            return True  # Se ha realizado el split.
        return False  # No se puede realizar el split.
            

    def doblar(self, mano, carta):
        """Permite al jugador doblar su apuesta y recibir una carta adicional."""
        if self.capital < mano.apuesta or len(mano.cartas) != 2:
            return False  # No puede doblar si no tiene suficiente capital o si ya tiene más de 2 cartas.
        self.capital -= mano.apuesta
        mano.apuesta *= 2
        self.pedir_carta(mano, carta)  # Pide una carta adicional.
        self.terminar_mano(mano)  # Termina la mano después de doblar.
        return True


    def surrender(self, mano):
        """Permite al jugador rendirse y recuperar la mitad de su apuesta."""
        if mano in self.manos:
            self.capital += mano.apuesta // 2  # Asegura que sea un entero
            self.manos.remove(mano)
            return True
        return False  # La mano no existe, no se puede rendir.

    def reset_manos(self):
        """Reinicia la mano del jugador para una nueva ronda."""
        self.manos = []