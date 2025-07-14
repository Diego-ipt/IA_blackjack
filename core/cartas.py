import random
from enum import Enum

class Palo(Enum):
    """
    Representa el palo de la carta (Corazon, Diamante, Pica, Trebol)
    """
    PICAS = "♠"
    CORAZONES = "♥"
    DIAMANTES = "♦"
    TREBOLES = "♣"

class Rango(Enum):
    """
    Representa el valor de la carta (2,3,...,J,Q,K,A)
    """
    DOS = ("2", 2)
    TRES = ("3", 3)
    CUATRO = ("4", 4)
    CINCO = ("5", 5)
    SEIS = ("6", 6)
    SIETE = ("7", 7)
    OCHO = ("8", 8)
    NUEVE = ("9", 9)
    DIEZ = ("10", 10)
    JOTA = ("J", 10)
    CUINA = ("Q", 10)
    KAISER = ("K", 10)
    AS = ("A", 11)

    @property
    def simbolo(self) -> str:
        """
        Devuelve el símbolo de la carta.
        """
        return self.value[0]

    @property
    def valor(self) -> int:
        """
        Devuelve el valor de la carta.
        """
        return self.value[1]
    
    @classmethod
    def from_valor(cls, valor: int):
        """
        Devuelve el Rango correspondiente a un valor dado.
        """
        if valor == 1 or valor == 11:
            return cls.AS
        elif valor == 2:
            return cls.DOS
        elif valor == 3:
            return cls.TRES
        elif valor == 4:
            return cls.CUATRO
        elif valor == 5:
            return cls.CINCO
        elif valor == 6:
            return cls.SEIS
        elif valor == 7:
            return cls.SIETE
        elif valor == 8:
            return cls.OCHO
        elif valor == 9:
            return cls.NUEVE
        elif valor == 10:
            return cls.DIEZ
        else:
            raise ValueError(f"Valor inválido: {valor}")

class Carta:

    def __init__(self, palo: Palo, rango: Rango):
        """
        Inicializa una carta con un palo y un rango.
        :param palo: Palo de la carta (Palo)
        :param rango: Rango de la carta (Rango)
        """
        self.palo = palo
        self.rango = rango

    def __str__(self):
        return f"{self.rango.simbolo}{self.palo.value}"

    def __repr__(self):
        return f"Carta({self.palo}, {self.rango})"

    @property
    def valor(self):
        """
        Devuelve el valor de la carta. Abstrae el uso de Enums
        """
        return self.rango.valor

    @property
    def simbolo(self):

        return self.rango.simbolo




class Mazo:

    def __init__(self, num_mazos: int = 1, zapato: float = 0.75):
        """
        Inicializa un mazo de cartas.
        :param num_mazos: Número de mazos a crear (por defecto 1)
        :param zapato: Porcentaje de cartas que se jugaran antes de barajar (por defecto 0.75, entre 0 y 1)

        :raises ValueError: Si el número de mazos es menor que 1 o si el zapato no está entre 0 y 1.
        """

        if num_mazos < 1:
            raise ValueError("El número de mazos debe ser al menos 1.")
        if not (0 < zapato <= 1):
            raise ValueError("El zapato debe ser un valor entre 0 y 1.")

        self.num_mazos = num_mazos
        self.cartas = []

        # Crea un mazo individual de cartas
        mazo_individual = [Carta(palo=palo,rango=rango) for palo in Palo for rango in Rango]

        # Multiplica el mazo individual por el número de mazos
        self.cartas = mazo_individual * self.num_mazos

        """
        En el BJ, el zapato es un porcentaje de cartas que se jugarán antes de volver a barajar.
        Ej: Si el zapato es 0.75, significa que se jugarán el 75% de las cartas antes de barajar.
        Usualmente se coloca una tarjeta roja entre el mazo que indica el limite del zapato.
        El límite de cartas que se deben jugar antes de barajar se establece aleatoriamente entre el 60% y el 100% del total de cartas que no se han jugado.
        Asi evitamos que se acaben las cartas.        
        """
        cartas_totales = len(self.cartas)
        cartas_sin_jugar = int(cartas_totales * (1 - zapato))
        self.limite_barajado = random.randint(int(cartas_sin_jugar * 0.6), cartas_sin_jugar)

        # Baraja el mazo al inicializar
        self.barajar()

    def __len__(self):
        """
        Devuelve el número de cartas en el mazo.
        :return: Número de cartas en el mazo (int)
        """
        return len(self.cartas)

    def barajar(self):
        """
        Baraja el mazo de cartas.
        :return: None
        """
        random.shuffle(self.cartas)

    def repartir(self):
        """
        Reparte una carta del mazo.
        :return: Carta repartida (Carta)
        :raises IndexError: Si no hay cartas en el mazo.
        """
        if len(self.cartas) == 0:
            raise IndexError
        return self.cartas.pop()

    def necesita_barajar(self):
        """
        Comprueba si es necesario barajar el mazo.
        :return: True si es necesario barajar, False en caso contrario.
        """
        return len(self.cartas) <= self.limite_barajado

class MazoDeterminista(Mazo):
    """
    Mazo determinista que reparte cartas de forma predecible.
    Utilizado para pruebas y simulaciones.
    """

    def __init__(self, cartas: list[Carta]):
        super().__init__(num_mazos=1)
        self.cartas = cartas
        self.limite_barajado = 0  # No se baraja, se reparte en orden

