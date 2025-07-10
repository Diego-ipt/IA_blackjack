import pytest
from core.cartas import Carta, Palo, Rango, Mazo

# Tests para la clase Carta, Palo, Rango y Mazo
# Hechos por copilot (GPT-4.1)

def test_carta_str_repr():
    carta = Carta(Palo.PICAS, Rango.AS)
    assert str(carta) == "A de ♠"
    assert repr(carta) == f"Carta({Palo.PICAS}, {Rango.AS})"

def test_carta_valor():
    carta = Carta(Palo.DIAMANTES, Rango.JOTA)
    assert carta.valor == 10
    carta_as = Carta(Palo.TREBOLES, Rango.AS)
    assert carta_as.valor == 11

def test_mazo_creacion_basica():
    mazo = Mazo()
    assert len(mazo.cartas) == 52
    assert isinstance(mazo.cartas[0], Carta)

def test_mazo_varios_mazos():
    mazo = Mazo(num_mazos=3)
    assert len(mazo.cartas) == 52 * 3

def test_mazo_barajar_cambia_orden():
    mazo = Mazo()
    cartas_antes = mazo.cartas.copy()
    mazo.barajar()
    cartas_despues = mazo.cartas
    assert set(cartas_antes) == set(cartas_despues)
    # Es muy improbable que el orden sea igual tras barajar
    assert cartas_antes != cartas_despues

def test_mazo_repartir():
    mazo = Mazo()
    cantidad_inicial = len(mazo.cartas)
    carta = mazo.repartir()
    assert isinstance(carta, Carta)
    assert len(mazo.cartas) == cantidad_inicial - 1

def test_mazo_repartir_vacio():
    mazo = Mazo()
    mazo.cartas.clear()
    with pytest.raises(IndexError):
        mazo.repartir()

def test_mazo_necesita_barajar():
    mazo = Mazo(zapato=0.5)
    # Forzamos el mazo a estar justo en el límite
    mazo.limite_barajado = len(mazo.cartas) - 1
    assert not mazo.necesita_barajar()
    mazo.cartas.pop()
    assert mazo.necesita_barajar()

def test_mazo_parametros_invalidos():
    with pytest.raises(ValueError):
        Mazo(num_mazos=0)
    with pytest.raises(ValueError):
        Mazo(zapato=0)
    with pytest.raises(ValueError):
        Mazo(zapato=1.5)

def test_rango_simbolo_valor():
    assert Rango.DOS.simbolo == "2"
    assert Rango.DOS.valor == 2
    assert Rango.KAISER.simbolo == "K"
    assert Rango.KAISER.valor == 10
    assert Rango.AS.simbolo == "A"
    assert Rango.AS.valor == 11

def test_palo_enum():
    assert Palo.PICAS.value == "♠"
    assert Palo.CORAZONES.value == "♥"
    assert Palo.DIAMANTES.value == "♦"
    assert Palo.TREBOLES.value == "♣"
