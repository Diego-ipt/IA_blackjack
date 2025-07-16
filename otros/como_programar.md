Les dejo este resumen hecho por una IA para que vean como es el flujo del codigo
y las funciones y clases importantes xD

### Resumen Ejecutivo para Desarrolladores de Agentes

**Bienvenido al Simulador de Blackjack.** Has sido contratado para construir el próximo agente ganador. Esta guía te explicará todo lo que necesitas saber para empezar.

**La Arquitectura en 30 Segundos:**

Nuestro sistema sigue una filosofía de **Separación de Responsabilidades**:

1.  **El `Agente` (Tu Código):** Eres el **cerebro**. Tu única misión es tomar decisiones. No te preocupas por las reglas del juego, el capital o cómo se mueven las cartas. Solo observas un estado y devuelves una acción.
2.  **El `Jugador`:** Es el **cuerpo** de tu agente. Posee el capital y las manos. Tu agente está vinculado a un jugador para poder consultar su estado (`self.jugador.capital`).
3.  **El `Casino`:** Es el **árbitro y director de orquesta**. Él se encarga de todo lo demás: barajar, repartir, validar tus decisiones, pagar las ganancias y ejecutar el juego. Si tu agente intenta una acción ilegal (ej. dividir una mano de 7 y 8), el Casino la ignorará y la tratará como un `PLANTARSE`.

**Tu Tarea:** Crear una nueva clase en la carpeta `blackjack_sim/agents/` que herede de `Agente` e implemente su propia lógica en dos métodos clave: `decidir_apuesta()` y `decidir_accion()`.

---

### Guía Paso a Paso para Construir un Nuevo Agente

#### Paso 1: Crea tu Archivo de Agente

1.  Ve a la carpeta `blackjack_sim/agents/`.
2.  Crea un nuevo archivo, por ejemplo, `agente_estrategia_basica.py`.
3.  Añade la estructura básica de la clase:

```python
# blackjack_sim/agents/agente_estrategia_basica.py
import random

# Importaciones necesarias
from .agente_base import Agente
from ..core.acciones import Accion
from ..core.player import Jugador, Mano
from ..core.cartas import Carta

class AgenteEstrategiaBasica(Agente):
    def __init__(self, jugador: Jugador):
        # Llama al constructor de la clase base. Es obligatorio.
        super().__init__(jugador)
        # Aquí puedes inicializar cualquier estado que tu agente necesite
        # (ej. cargar un modelo de ML, inicializar una tabla Q, etc.)

    def decidir_apuesta(self) -> int:
        # TODO: Implementa tu lógica de apuesta aquí.
        # Por ahora, podemos usar una apuesta fija.
        return 10 # Apuesta fija de 10 unidades

    def decidir_accion(self, mano: Mano, carta_dealer: Carta) -> Accion:
        # TODO: Implementa tu lógica de decisión principal aquí.
        # Por ahora, devolvemos una acción aleatoria.
        return random.choice(list(Accion))
```

#### Paso 2: Implementa tu Lógica de Decisión (`decidir_accion`)

Este es el corazón de tu agente. Recibes dos objetos: `mano` y `carta_dealer`. Aquí tienes cómo acceder a la información que necesitas para tomar una decisión inteligente.

**El "Estado del Juego" a tu disposición:**

*   **Tu Mano Actual (`mano`):**
    *   `mano.valor_total`: El valor total y óptimo de tu mano (ej. 17).
    *   `mano.es_blackjack`: `True` si es un Blackjack natural.
    *   `mano.es_blanda`: `True` si tienes un As que cuenta como 11 (ej. A,6).
    *   `mano.cartas`: La lista de objetos `Carta` en tu mano.
        *   `len(mano.cartas)`: Para saber cuántas cartas tienes.
        *   `mano.cartas[0].valor == mano.cartas[1].valor`: Para comprobar si puedes dividir.

*   **La Carta del Dealer (`carta_dealer`):**
    *   `carta_dealer.valor`: El valor de la carta visible del dealer (ej. 10).
    *   `carta_dealer.rango`: El rango de la carta (ej. `Rango.AS`).

**Ejemplo de Lógica para un Agente de Estrategia Básica:**

```python
# Dentro de decidir_accion

# Valor de mi mano y la del dealer
mi_valor = mano.valor_total
valor_dealer = carta_dealer.valor

# Regla simple: si mi valor es 17 o más, me planto.
if mi_valor >= 17:
    return Accion.PLANTARSE

# Regla simple: si el dealer muestra un 6 o menos y yo tengo 12 o más, me planto.
if valor_dealer <= 6 and mi_valor >= 12:
    return Accion.PLANTARSE

# En cualquier otro caso, pido carta.
return Accion.PEDIR
```

#### Paso 3 (Opcional): Implementa Lógica de Apuesta (`decidir_apuesta`)

Si tu agente usa una estrategia de apuesta variable (como el conteo de cartas), implementarás la lógica aquí.

*   **Información Disponible:**
    *   `self.jugador.capital`: El capital total que tienes disponible.
    *   Cualquier estado interno que tu agente mantenga (ej. `self.conteo_actual`).

**Ejemplo:**

```python
# Dentro de decidir_apuesta

# Apuesta el 2% de mi capital, con un mínimo de 5
apuesta = int(self.jugador.capital * 0.02)
return max(5, apuesta)
```

#### Paso 4 (Para Contadores de Cartas): Usa `observar_carta`

Si tu agente necesita contar cartas, debes sobreescribir el método `observar_carta`. El `Casino` llamará a este método para **cada carta visible** que aparezca en la mesa.

**Ejemplo de un Contador Simple (Sistema Hi-Lo):**

```python
# En tu clase de agente
def __init__(self, jugador: Jugador):
    super().__init__(jugador)
    self.conteo = 0

def observar_carta(self, carta: Carta):
    if carta.valor >= 10: # Cartas altas
        self.conteo -= 1
    elif carta.valor <= 6: # Cartas bajas
        self.conteo += 1
    # Las cartas 7, 8, 9 no cambian el conteo.
    
    # Ahora puedes usar self.conteo en decidir_apuesta para variar tu apuesta.
```

#### Paso 5: Prueba tu Agente

1.  Ve a `main.py` (o a un archivo de test).
2.  Importa tu nuevo agente: `from blackjack_sim.agents.agente_estrategia_basica import AgenteEstrategiaBasica`.
3.  Crea una instancia de tu agente y pásala al `Casino`.
4.  Ejecuta la simulación y observa los logs para ver cómo se comporta tu agente.

¡Y eso es todo! Siguiendo estos pasos, puedes integrar cualquier tipo de lógica, desde una simple tabla de decisiones hasta una red neuronal compleja, en nuestro simulador de forma limpia y modular.