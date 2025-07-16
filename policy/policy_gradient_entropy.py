import numpy as np
from collections import deque


class RedNeuronal:
    def __init__(self, tam_entrada, capas_ocultas, tam_salida):
        # Crea una lista con los tamaños de todas las capas de la red:
        # Entrada + capas ocultas + salida
        tamanos_capas = [tam_entrada] + capas_ocultas + [tam_salida]

        # Inicializa listas vacías donde se guardarán los pesos y los sesgos
        self.pesos = []
        self.sesgos = []

        # Para cada par de capas consecutivas, inicializa pesos y sesgos
        for i in range(len(tamanos_capas) - 1):
            # Escala de inicialización
            # Es una forma de normalización basada en el número de entradas y salidas de cada capa
            escala = np.sqrt(2.0 / (tamanos_capas[i] + tamanos_capas[i + 1]))

            # Inicializa la matriz de pesos con valores aleatorios siguiendo una distribución normal
            # y la escala para mantener activaciones razonables
            # La matriz tendrá forma (neurona_actual, neurona_siguiente)
            self.pesos.append(np.random.randn(tamanos_capas[i], tamanos_capas[i + 1]) * escala)

            # Inicializa el vector de sesgos con ceros (uno por cada neurona de la siguiente capa)
            self.sesgos.append(np.zeros(tamanos_capas[i + 1]))

    def forward(self, X):
        # Vector 1D se reestructura como matriz 2D
        # Para que sea compatible con los productos matriciales
        if X.ndim == 1:
            X = X.reshape(1, -1)

        # Inicializa la activación como la entrada original
        activacion = X

        # Guarda todas las activaciones
        activaciones = [X]

        # Lista para guardar los valores z
        zs = []

        # Recorre todas las capas, menos la última que es la de salida y aplica ReLU
        for i in range(len(self.pesos) - 1):
            # z = W*x + b
            z = np.dot(activacion, self.pesos[i]) + self.sesgos[i]
            zs.append(z)  # Se guarda el valor de z

            # Aplica la función de activación ReLU: f(z) = max(0,z)
            activacion = np.maximum(0, z)  # ReLU
            activaciones.append(activacion)  # Guarda la activación

        # SALIDA CONTINUA:
        # Última capa - usamos sigmoide para acotar entre 0 y 1
        z = np.dot(activacion, self.pesos[-1]) + self.sesgos[-1]
        zs.append(z)
        salida = 1 / (1 + np.exp(-z))  # Función sigmoide para salida continua
        activaciones.append(salida)

        # Devuelve la salida final, todas las activaciones y los valores z
        # para usar en backpropagation
        return salida, activaciones, zs

    # Se utiliza en backpropagation
    # 1 si x > 0
    # 0 si x <= 0
    def derivada_relu(self, x):
        return np.where(x > 0, 1, 0)

    # función para calcular la derivada de la sigmoide
    def derivada_sigmoide(self, x):
        return x * (1 - x)

    def backtracking(self, X, y, tasa_aprendizaje, grad_entropia=None):
        if X.ndim == 1:
            X = X.reshape(1, -1)

        tam_batch = X.shape[0]  # Número de muestras en el batch

        salida, activaciones, zs = self.forward(X)  # forward pass: calcula salida, activaciones y valores de z

        # SALIDA CONTINUA:
        # pérdida MSE (error cuadrático medio) para regresión
        error = salida - y
        perdida = np.mean(error ** 2)

        # Calcula el error en la capa de salida usando derivada de sigmoide
        delta = error * self.derivada_sigmoide(salida)

        # Añade gradiente de entropía si se proporciona
        if grad_entropia is not None:
            delta += grad_entropia / tam_batch  # Normaliza por tamaño del batch

        # Recorre las capas en orden inverso, de salida a entrada
        for i in range(len(self.pesos) - 1, -1, -1):
            # Gradiente de los pesos
            grad_pesos = np.dot(activaciones[i].T, delta) / tam_batch

            # gradiente sesgos
            grad_sesgos = np.sum(delta, axis=0) / tam_batch

            # Actualiza pesos y sesgos restando el gradiente multiplicado por tasa de aprendizaje
            self.pesos[i] -= tasa_aprendizaje * grad_pesos
            self.sesgos[i] -= tasa_aprendizaje * grad_sesgos

            # Si no es la primera capa entonces se propaga delta hacia atrás multiplicando
            # por la derivada ReLu
            if i > 0:
                delta = np.dot(delta, self.pesos[i].T) * self.derivada_relu(zs[i - 1])

        # Se devuelve el valor de la pérdida para monitorear el entrenamiento
        return perdida


class ApuestaConPolicyGradient:
    def __init__(self, capital_inicial, rango_apuesta=[0.01, 0.1],
                 tasa_aprendizaje=0.01, descuento=0.99, entropia_peso=0.01, decaimiento_entropia=0.995):
        """
        Inicializa el agente para gestión de apuestas con porcentajes aleatorios en un rango
        y regularización de entropía para controlar la exploración.

        Usa política gaussiana para acciones continuas.
        """
        self.capital_actual = capital_inicial
        self.capital_inicial = capital_inicial
        self.rango_apuesta = rango_apuesta
        self.tasa_aprendizaje = tasa_aprendizaje
        self.descuento = descuento
        self.entropia_peso = entropia_peso
        self.decaimiento_entropia = decaimiento_entropia
        self.entropia_min = 0.001

        # Red neuronal con salida continua (1 neurona) para predecir el porcentaje de apuesta
        # La salida será un valor entre 0 y 1 que luego se escala al rango deseado
        self.red_politica = RedNeuronal(tam_entrada=4, capas_ocultas=[16], tam_salida=1)

        # Buffers para entrenamiento
        self.estados = deque(maxlen=10000)  # Almacena los estados observados
        self.porcentajes_apostados = deque(
            maxlen=10000)  # Almacena los porcentajes de apuesta usados (valores continuos)
        self.recompensas = deque(maxlen=10000)  # Almacena las recompensas obtenidas

        # Historial de desempeño
        self.historial_recompensas = deque(maxlen=100)  # Recompensas acumuladas por episodio
        self.num_episodios = 0  # Contador de episodios completados
        self.pasos_episodio = 0  # Contador de pasos dentro del episodio actual

    def obtener_estado(self):
        capital_norm = self.capital_actual / self.capital_inicial  # Capital normalizado
        progreso = self.pasos_episodio / 100  # Progreso del episodio normalizado

        # Calcula tendencia y volatilidad de las últimas 10 recompensas
        ultimas_recompensas = np.array(list(self.recompensas)[-10:]) if len(self.recompensas) >= 10 else np.zeros(10)

        tendencia = np.mean(ultimas_recompensas) / (self.capital_inicial + 1e-8)  # Normalizada por capital inicial
        volatilidad = np.std(ultimas_recompensas) / (self.capital_inicial + 1e-8)  # Normalizada por capital inicial

        return np.array([capital_norm, progreso, tendencia, volatilidad])

    def elegir_apuesta(self, estado):
        """
        Selecciona un porcentaje de apuesta dentro del rango configurado,
        con exploración controlada por la entropía.

        Usa una política gaussiana con media predicha por la red
        y desviación estándar controlada por entropia_peso.
        """
        # La red predice la media de la distribución (entre 0 y 1)
        media = self.red_politica.forward(estado.reshape(1, -1))[0][0][0]

        # La desviación estándar para exploración es controlada por entropia_peso
        std = self.entropia_peso

        # Muestra de la distribución normal
        muestra = np.random.normal(media, std)

        # Escala al rango deseado y aplica clipping(se limitan valores)
        porcentaje = self.rango_apuesta[0] + (self.rango_apuesta[1] - self.rango_apuesta[0]) * muestra
        return np.clip(porcentaje, self.rango_apuesta[0], self.rango_apuesta[1])

    def guardar_experiencia(self, estado, porcentaje_apuesta, resultado_apuesta):
        """
        Guarda la experiencia (estado, acción, recompensa) para entrenamiento posterior.
        """
        # Calcula el monto apostado y la ganancia
        monto_apostado = self.capital_actual * porcentaje_apuesta
        ganancia = monto_apostado * resultado_apuesta

        # Actualiza el capital
        self.capital_actual += ganancia

        # Almacena la experiencia
        self.estados.append(estado)
        self.porcentajes_apostados.append(porcentaje_apuesta)
        self.recompensas.append(ganancia)
        self.pasos_episodio += 1

    def calcular_recompensas_descuento(self):
        recompensas = np.array(self.recompensas, dtype=np.float32)
        recompensas_descuento = np.zeros_like(recompensas)
        acumulado = 0

        # Calcula recompensas descontadas desde el final hacia el inicio
        for i in reversed(range(len(recompensas))):
            acumulado = acumulado * self.descuento + recompensas[i]
            recompensas_descuento[i] = acumulado / (self.capital_inicial + 1e-8)  # Normaliza por capital inicial

        return recompensas_descuento

    def calcular_gradiente_entropia(self, porcentaje_base):
        """
        Calcula el gradiente de la entropía para una distribución gaussiana.
        """
        return self.entropia_peso * (1.0 - 2.0 * porcentaje_base)  # Fomenta valores intermedios

    def entrenar(self):
        """
        Entrena la política usando policy Gradient con regularización de entropía.
        """
        if not self.estados or not self.recompensas:
            print("No hay suficientes datos para entrenar la política.")
            return None

        # Prepara los datos de entrenamiento
        estados = np.vstack(self.estados)
        porcentajes_apostados = np.array(self.porcentajes_apostados).reshape(-1, 1)

        # Normaliza los porcentajes al rango [0,1] para el entrenamiento
        porcentajes_normalizados = (porcentajes_apostados - self.rango_apuesta[0]) / (
                self.rango_apuesta[1] - self.rango_apuesta[0])

        # Calcula recompensas descontadas y normalizadas
        recompensas = self.calcular_recompensas_descuento()
        recompensas = (recompensas - np.mean(recompensas)) / (np.std(recompensas) + 1e-8)

        # Obtiene solo el primer valor retornado por forward() (porcentaje_base)
        porcentaje_base = self.red_politica.forward(estados)[0]
        gradiente_entropia = self.calcular_gradiente_entropia(porcentaje_base)

        # Entrena la red neuronal
        perdida = self.red_politica.backtracking(
            estados,
            porcentajes_normalizados * recompensas[:, np.newaxis],  # Ajuste basado en recompensas
            self.tasa_aprendizaje,
            gradiente_entropia  # Regularización por entropía
        )

        # Reduce progresivamente la entropía
        self.entropia_peso = max(self.entropia_min, self.entropia_peso * self.decaimiento_entropia)

        # Limpia buffers y registra
        self.historial_recompensas.append(sum(self.recompensas))
        self.num_episodios += 1
        self.pasos_episodio = 0
        self.estados.clear()
        self.porcentajes_apostados.clear()
        self.recompensas.clear()

        print(f"Política entrenada - Pérdida: {perdida:.4f}, Capital: {self.capital_actual:.2f}")

        return perdida

    def promedio_recompensa(self):
        if len(self.historial_recompensas) == 0:
            return 0
        return sum(self.historial_recompensas) / len(self.historial_recompensas)

    def obtener_capital(self):
        return self.capital_actual


    #Guardar pesos para poder utilizar más adelantes

    def guardar_pesos(self, filename):
        """
        Guarda los pesos y sesgos de la red neuronal en un archivo .npz de manera segura.

        """
        try:
            # Convertir cada capa a arrays numpy y guardar individualmente
            pesos_dict = {}
            sesgos_dict = {}

            for i, (peso, sesgo) in enumerate(zip(self.red_politica.pesos, self.red_politica.sesgos)):
                pesos_dict[f'pesos_{i}'] = peso
                sesgos_dict[f'sesgos_{i}'] = sesgo

            # Guardar en un solo archivo comprimido
            np.savez_compressed(
                filename,
                num_capas=len(self.red_politica.pesos),
                **pesos_dict,
                **sesgos_dict
            )
            print(f"Pesos guardados correctamente en {filename}.npz")
        except Exception as e:
            print(f"Error al guardar pesos: {str(e)}")
            raise

    def cargar_pesos(self, filename):
        """
        Carga los pesos y sesgos desde un archivo .npz de manera segura con validación mejorada

        """
        try:
            # Cargar archivo
            datos = np.load(filename, allow_pickle=True)

            # Obtener número de capas
            if 'num_capas' not in datos:
                raise ValueError("El archivo no contiene el número de capas")

            num_capas = int(datos['num_capas'])
            nuevos_pesos = []
            nuevos_sesgos = []

            # Cargar cada capa
            for i in range(num_capas):
                peso_key = f'pesos_{i}'
                sesgo_key = f'sesgos_{i}'

                if peso_key not in datos:
                    raise ValueError(f"No se encontraron pesos para la capa {i}")
                if sesgo_key not in datos:
                    raise ValueError(f"No se encontraron sesgos para la capa {i}")

                nuevos_pesos.append(datos[peso_key])
                nuevos_sesgos.append(datos[sesgo_key])

            # Validación de dimensiones
            if len(nuevos_pesos) != len(nuevos_sesgos):
                raise ValueError("Número de capas de pesos y sesgos no coincide")

            # Verificar consistencia interna de las dimensiones cargadas
            for i in range(1, num_capas):
                if nuevos_pesos[i].shape[0] != nuevos_pesos[i - 1].shape[1]:
                    raise ValueError(f"Dimensión incompatible entre capa {i - 1} y {i}")
                if nuevos_pesos[i].shape[1] != nuevos_sesgos[i].shape[0]:
                    raise ValueError(f"Dimensión incompatible en capa {i}")

            # Si todo está bien, reemplazar los pesos
            self.red_politica.pesos = nuevos_pesos
            self.red_politica.sesgos = nuevos_sesgos

            print(f" Pesos cargados correctamente desde {filename}")
            return True

        except Exception as e:
            print(f" Error al cargar pesos: {str(e)}")
            return False