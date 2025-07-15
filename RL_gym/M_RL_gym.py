import gymnasium as gym
import numpy as np
import json
import datetime
import os
from stable_baselines3 import PPO
from stable_baselines3.common.callbacks import BaseCallback

# Asegúrate de que las importaciones apunten a la ubicación correcta de tus archivos
from core.casino import Casino
from core.player import Jugador
from agents.markov_RL import AgenteMarkov_RL

# --------------------------------------------------------------------------- #
# 1. Definición del Entorno de Aprendizaje por Refuerzo para las Recompensas
# --------------------------------------------------------------------------- #

class BlackjackRewardEnv(gym.Env):
    """
    Un entorno de Gymnasium donde una 'acción' es elegir la estructura de recompensas
    y la 'recompensa' para el meta-agente es el rendimiento financiero del AgenteMarkov.
    """
    def __init__(self, num_rondas_simulacion=1000, capital_inicial=10000):
        super(BlackjackRewardEnv, self).__init__()
        
        self.num_rondas_simulacion = num_rondas_simulacion
        self.capital_inicial = capital_inicial

        # ESPACIO DE ACCIONES: Los 5 valores de recompensa que queremos aprender.
        # [R_win_score, R_win_dealer_bust, R_tie, R_loss_score, R_player_bust]
        # Límites generosos para permitir al agente explorar libremente.
        low_bounds = np.array([-5.0, -5.0, -5.0, -5.0, -5.0], dtype=np.float32)
        high_bounds = np.array([5.0, 5.0, 5.0, 0.0, 0.0], dtype=np.float32)
        self.action_space = gym.spaces.Box(low=low_bounds, high=high_bounds, dtype=np.float32)
        
        # ESPACIO DE OBSERVACIÓN: Simple para este ejemplo, no usamos un estado complejo.
        self.observation_space = gym.spaces.Box(low=0, high=1, shape=(1,), dtype=np.float32)
        
        # Crear una instancia persistente del AgenteMarkov que se reutilizará
        self.jugador_markov = Jugador("Controlado", self.capital_inicial)
        self.agente_controlado = AgenteMarkov_RL(self.jugador_markov, num_mazos=4)

    def step(self, action):
        # 1. La 'acción' del meta-agente es el vector de 5 recompensas
        recompensas_aprendidas = {
            'win_score': float(action[0]),
            'win_dealer_bust': float(action[1]),
            'tie': float(action[2]),
            'loss_score': float(action[3]),
            'player_bust': float(action[4])
        }
        
        # 2. Configurar el AgenteMarkov con las nuevas recompensas
        self.agente_controlado.set_recompensas(recompensas_aprendidas)
        
        # 3. Resetear el capital del jugador y ejecutar una simulación larga
        self.agente_controlado.jugador.capital = self.capital_inicial
        
        # Se asume una versión del casino que no imprime en cada ronda para acelerar el proceso
        casino = Casino([self.agente_controlado], num_mazos=4)
        casino.jugar_partida(self.num_rondas_simulacion) 
        
        # 4. La recompensa para el meta-agente es el cambio neto en el capital
        capital_final = self.agente_controlado.jugador.capital
        reward = capital_final - self.capital_inicial
        
        print(f"Probando Recompensas -> Resultado Capital Neto: {reward}")

        # El episodio del meta-agente termina después de cada simulación
        done = True
        terminated = True
        truncated = False
        
        # Devolvemos una observación placeholder, la recompensa, y que el episodio ha terminado
        return np.array([0], dtype=np.float32), reward, terminated, truncated, {}

    def reset(self, seed=None, options=None):
        # Reinicia el entorno para una nueva prueba de recompensas
        super().reset(seed=seed)
        return np.array([0], dtype=np.float32), {}

    def close(self):
        # Limpieza si es necesario
        print("Entorno cerrado.")

# --------------------------------------------------------------------------- #
# 1.5. Callback para Guardar Mejores Recompensas Periódicamente
# --------------------------------------------------------------------------- #

class BestRewardsCallback(BaseCallback):
    """
    Callback personalizado para guardar las mejores recompensas cada cierto número de episodios
    """
    def __init__(self, env, save_freq=20, verbose=0):
        super(BestRewardsCallback, self).__init__(verbose)
        self.env = env
        self.save_freq = save_freq
        self.best_reward = float('-inf')
        self.best_action = None
        self.episode_count = 0
        self.filename = "mejores_recompensas_progreso.json"
        self.historial = []
        
    def _on_step(self) -> bool:
        # En nuestro entorno, cada step es un episodio completo
        self.episode_count += 1
        
        # Obtener la última recompensa
        if len(self.locals.get('rewards', [])) > 0:
            current_reward = self.locals['rewards'][-1]
            
            # Si encontramos una mejor recompensa, la guardamos
            if current_reward > self.best_reward:
                self.best_reward = current_reward
                # Obtener la acción que generó esta recompensa
                if len(self.locals.get('actions', [])) > 0:
                    self.best_action = self.locals['actions'][-1]
                    
                if self.verbose > 0:
                    print(f"\n🎯 Nueva mejor recompensa encontrada: {self.best_reward}")
        
        # Guardar cada save_freq episodios
        if self.episode_count % self.save_freq == 0:
            self._save_best_rewards()
            
        return True
    
    def _save_best_rewards(self):
        if self.best_action is not None:
            recompensas_actuales = {
                'win_score': float(self.best_action[0]),
                'win_dealer_bust': float(self.best_action[1]),
                'tie': float(self.best_action[2]),
                'loss_score': float(self.best_action[3]),
                'player_bust': float(self.best_action[4])
            }
            
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            
            # Añadir al historial
            checkpoint = {
                'episodio': self.episode_count,
                'mejor_recompensa': float(self.best_reward),
                'recompensas_optimas': recompensas_actuales,
                'timestamp': timestamp
            }
            self.historial.append(checkpoint)
            
            # Guardar todo el historial en el mismo archivo
            data_to_save = {
                'ultimo_checkpoint': checkpoint,
                'historial_completo': self.historial,
                'total_episodios_entrenados': self.episode_count
            }
            
            try:
                with open(self.filename, 'w', encoding='utf-8') as f:
                    json.dump(data_to_save, f, indent=4)
                print(f"💾 Actualizado: {self.filename} (Episodio {self.episode_count}, Recompensa: {self.best_reward})")
            except Exception as e:
                print(f"❌ Error al guardar archivo: {e}")

# --------------------------------------------------------------------------- #
# 2. Función Principal para Entrenar y Guardar los Resultados
# --------------------------------------------------------------------------- #

def entrenar_y_guardar_recompensas():
    # --- Parámetros de Entrenamiento ---
    # Número de episodios de entrenamiento. CADA episodio es una simulación completa.
    # Aumentar para un entrenamiento real. 100 es para una prueba.
    TOTAL_EPISODIOS = 100
    # Número de rondas de Blackjack a simular en CADA episodio.
    RONDAS_POR_EPISODIO = 1000
    # Frecuencia de guardado (cada cuántos episodios guardar)
    SAVE_FREQ = 20

    print("Creando entorno de RL para optimizar recompensas...")
    env = BlackjackRewardEnv(num_rondas_simulacion=RONDAS_POR_EPISODIO)
    
    # Crear el callback para guardar mejores recompensas
    callback = BestRewardsCallback(env, save_freq=SAVE_FREQ, verbose=1)
    
    # Crear el modelo PPO. 'verbose=1' mostrará el progreso del entrenamiento.
    model = PPO("MlpPolicy", env, verbose=1, ent_coef=0.01, n_steps=20)

    print(f"\nIniciando entrenamiento por {TOTAL_EPISODIOS} episodios...")
    print(f"💾 Se guardarán las mejores recompensas cada {SAVE_FREQ} episodios")
    # El total de timesteps es igual al número de episodios ya que cada step=done
    model.learn(total_timesteps=TOTAL_EPISODIOS, callback=callback)
    print("Entrenamiento completado.")

    # --- Predecir y Guardar la Mejor Estructura de Recompensas ---
    
    print("\nCalculando la estructura de recompensas óptima encontrada...")
    obs, _ = env.reset()  # Extract only the observation, ignore info
    mejor_recompensa_vector, _ = model.predict(obs, deterministic=True)
    
    recompensas_optimas = {
        'win_score': float(mejor_recompensa_vector[0]),
        'win_dealer_bust': float(mejor_recompensa_vector[1]),
        'tie': float(mejor_recompensa_vector[2]),
        'loss_score': float(mejor_recompensa_vector[3]),
        'player_bust': float(mejor_recompensa_vector[4])
    }

    # Imprimir el resultado en la consola
    print("\n=============================================")
    print("  Estructura de Recompensas Óptima Aprendida")
    print("=============================================")
    for key, value in recompensas_optimas.items():
        print(f"  {key:<20}: {value:.4f}")
    print("=============================================")

    # Guardar el resultado en un archivo JSON
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"recompensas_optimas_{timestamp}.json"
    
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(recompensas_optimas, f, indent=4)
        print(f"\n✅ Resultados guardados exitosamente en: {filename}")
    except Exception as e:
        print(f"\n❌ Error al guardar el archivo: {e}")

if __name__ == '__main__':
    entrenar_y_guardar_recompensas()