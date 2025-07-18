# IA Blackjack

## Resumen

Este proyecto implementa y compara agentes inteligentes para jugar Blackjack usando técnicas de Markov, Policy Gradient, Random Forest y Aprendizaje por Refuerzo. El objetivo es analizar el desempeño de diferentes estrategias automáticas en miles de rondas simuladas, generando reportes y visualizaciones para comparar resultados.

## Análisis y visualización de resultados

Después de ejecutar el test principal (`tests/test_all.py`), puedes analizar los resultados y generar gráficos comparativos usando el script:

```bash
python data_viewer/markov_resumen.py
```

Este script realiza:

- Resúmenes de rendimiento por agente (victorias, derrotas, empates, rachas).
- Análisis de tiempos de decisión y complejidad.
- Comparación de desempeño entre agentes.
- Visualizaciones automáticas (gráficos de ganancia acumulada, distribución de resultados, tiempos de decisión, rolling win rate, rendimiento por cartas restantes, cambio de capital acumulado).
- Guarda los gráficos en archivos PNG para revisión posterior.

## Requisitos

Antes de ejecutar el proyecto, instala las siguientes librerías de Python:

```bash
pip install numpy pandas logging matplotlib seaborn tqdm scikit-learn gymnasium stable-baselines3 joblib
```

### Detalle de librerías

- **numpy**: Operaciones numéricas y manejo de arrays.
- **pandas**: Manipulación de datos y archivos CSV.
- **logging**: Logging estándar de Python (incluido en la biblioteca estándar).
- **random**: Generación de números aleatorios (incluido en la biblioteca estándar).
- **collections**: Estructuras de datos avanzadas (incluido en la biblioteca estándar).
- **typing**: Tipado estático (incluido en la biblioteca estándar).
- **matplotlib**: Visualización de gráficos.
- **pathlib**: Manejo de rutas (incluido en la biblioteca estándar).
- **seaborn**: Visualización estadística.
- **glob**: Búsqueda de archivos (incluido en la biblioteca estándar).
- **tqdm**: Barras de progreso.
- **datetime**: Manejo de fechas y horas (incluido en la biblioteca estándar).
- **os**: Operaciones del sistema (incluido en la biblioteca estándar).
- **sklearn**: Algoritmos de machine learning (`scikit-learn`).
- **json**: Manejo de datos JSON (incluido en la biblioteca estándar).
- **gymnasium**: Entorno de simulación para RL.
- **stable-baselines3**: Algoritmos de Aprendizaje por Refuerzo.
- **joblib**: Serialización eficiente de modelos y datos.

Las librerías marcadas como "incluido en la biblioteca estándar" no requieren instalación adicional.

Si usas entornos virtuales, activa tu entorno antes de instalar.

## Estructura del proyecto

- `core/`: Lógica principal del juego y utilidades.
- `agents/`: Implementaciones de agentes inteligentes.
- `policy/`: Algoritmos de Policy Gradient.
- `RL_gym/`: Scripts para entrenamiento con RL.
- `tests/`: Pruebas unitarias.

## Ejecución

### Test principal

El test más importante para comparar el desempeño de todos los agentes es:

```bash
python tests/test_all.py
```

Este script ejecuta miles de rondas, compara todos los agentes y guarda los resultados en un archivo CSV.

### Otros tests

Para correr los tests unitarios:

```bash
pytest tests/
```

Para entrenar el agente con RL:

```bash
python RL_gym/M_RL_gym.py
```

## Notas

- Algunas librerías pueden requerir versiones específicas de Python (recomendado Python 3.10+).
- Si tienes problemas con `stable-baselines3`, revisa la documentación oficial: https://stable-baselines3.readthedocs.io/