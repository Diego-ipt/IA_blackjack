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
from agents.markov_h import AgenteHibrido_Markov_HiLo # Asume que esta clase existe

# --------------------------------------------------------------------------- #
# 1. Definición del Entorno de Gym Simplificado
# --------------------------------------------------------------------------- #

class BlackjackSimplifiedHybridEnv(gym.Env):
    """
    Un entorno de Gymnasium para optimizar los 4 parámetros clave del agente híbrido:
    recompensa de victoria, empate, derrota y el factor de riesgo.
    """
    def __init__(self, num_rondas_simulacion=1000, capital_inicial=5000):
        super(BlackjackSimplifiedHybridEnv, self).__init__()
        
        self.num_rondas_simulacion = num_rondas_simulacion
        self.capital_inicial = capital_inicial

        # ================================================================= #
        # === CAMBIO: Espacio de acciones ahora tiene 4 dimensiones === #
        # [R_victoria, R_empate, R_derrota, factor_riesgo]
        # ================================================================= #
        low_bounds = np.array([0.0, -5.0, -5.0, 0.0], dtype=np.float32)
        high_bounds = np.array([5.0, 0.0, 0.0, 0.5], dtype=np.float32)
        self.action_space = gym.spaces.Box(low=low_bounds, high=high_bounds, dtype=np.float32)
        
        self.observation_space = gym.spaces.Box(low=0, high=1, shape=(1,), dtype=np.float32)
        
        self.jugador_hibrido = Jugador("Hibrido", self.capital_inicial)
        self.agente_hibrido = AgenteHibrido_Markov_HiLo(self.jugador_hibrido, num_mazos=4)

    def step(self, action):
        # 1. La 'acción' es el vector de 4 parámetros
        recompensas_simplificadas = {
            'victoria': float(action[0]),
            'empate':   float(action[1]),
            'derrota':  float(action[2])
        }
        factor_riesgo_aprendido = float(action[3])
        
        # 2. Configurar el agente con los nuevos parámetros
        self.agente_hibrido.set_recompensas(recompensas_simplificadas)
        self.agente_hibrido.set_factor_riesgo(factor_riesgo_aprendido)
        
        # 3. Ejecutar la simulación
        self.agente_hibrido.jugador.capital = self.capital_inicial
        casino = Casino([self.agente_hibrido], num_mazos=4)
        casino.jugar_partida(self.num_rondas_simulacion) 
        
        # 4. La recompensa es el cambio neto en el capital
        capital_final = self.agente_hibrido.jugador.capital
        reward = capital_final - self.capital_inicial
        
        print(f"Probando Parámetros -> Resultado Capital Neto: {reward}")

        terminated = True
        truncated = False
        
        return np.array([0], dtype=np.float32), reward, terminated, truncated, {}

    def reset(self, seed=None, options=None):
        super().reset(seed=seed)
        return np.array([0], dtype=np.float32), {}

    def close(self):
        print("Entorno cerrado.")

# --------------------------------------------------------------------------- #
# 1.5. Callback para Guardar Mejores Parámetros Simplificados
# --------------------------------------------------------------------------- #

class BestSimplifiedParamsCallback(BaseCallback):
    """Callback para guardar el mejor conjunto de 4 parámetros encontrado."""
    def __init__(self, env, save_freq=20, verbose=0):
        super(BestSimplifiedParamsCallback, self).__init__(verbose)
        self.env = env
        self.save_freq = save_freq
        self.best_reward = float('-inf')
        self.best_action = None
        self.episode_count = 0
        self.filename = "mejores_parametros_simplificados.json"
        self.historial = []
        
    def _on_step(self) -> bool:
        self.episode_count += 1
        if len(self.locals.get('rewards', [])) > 0:
            current_reward = self.locals['rewards'][-1]
            if current_reward > self.best_reward:
                self.best_reward = current_reward
                if len(self.locals.get('actions', [])) > 0:
                    self.best_action = self.locals['actions'][-1]
                if self.verbose > 0:
                    print(f"\n🎯 Nueva mejor recompensa encontrada: {self.best_reward}")
        
        if self.episode_count % self.save_freq == 0:
            self._save_best_params()
            
        return True
    
    def _save_best_params(self):
        if self.best_action is not None:
            raw_action = self.best_action
            action_space = self.env.action_space
            clipped_action = np.clip(raw_action, action_space.low, action_space.high)
            
            parametros_actuales = {
                'recompensa_victoria': float(clipped_action[0]),
                'recompensa_empate': float(clipped_action[1]),
                'recompensa_derrota': float(clipped_action[2]),
                'factor_riesgo_escala': float(clipped_action[3])
            }
            
            timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
            checkpoint = {
                'episodio': self.episode_count,
                'mejor_recompensa': float(self.best_reward),
                'parametros_optimos': parametros_actuales,
                'timestamp': timestamp
            }
            self.historial.append(checkpoint)
            
            data_to_save = {
                'ultimo_checkpoint': checkpoint,
                'historial_completo': self.historial
            }
            
            try:
                with open(self.filename, 'w', encoding='utf-8') as f:
                    json.dump(data_to_save, f, indent=4)
                print(f"💾 Actualizado: {self.filename} (Episodio {self.episode_count}, Recompensa: {self.best_reward})")
            except Exception as e:
                print(f"❌ Error al guardar archivo: {e}")

# --------------------------------------------------------------------------- #
# 2. Función Principal para Entrenar
# --------------------------------------------------------------------------- #

def entrenar_parametros_simplificados():
    # --------------------------------------------------------------------------- #
    # 1. Parámetros de Entrenamiento
    # --------------------------------------------------------------------------- #
    
    # Número total de simulaciones a ejecutar durante todo el entrenamiento.
    # Cada simulación es un "paso de tiempo" para el modelo de RL.
    TOTAL_TIMESTEPS = 5000 
    
    # Número de rondas de Blackjack a jugar en CADA simulación.
    # Un número más alto da una mejor estimación del rendimiento de un conjunto de parámetros.
    RONDAS_POR_EPISODIO = 1000
    
    # Frecuencia con la que el callback guardará el mejor resultado encontrado.
    # SAVE_FREQ = 1 significa que guardará después de cada episodio si hay una mejora.
    SAVE_FREQ = 20
    
    # Número de pasos (episodios) que PPO recolecta antes de actualizar su política.
    # Un valor bajo (ej. 5-20) permite actualizaciones rápidas, bueno para pruebas.
    # Un valor más alto (ej. 128, 256) es más estable para entrenamientos largos.
    N_STEPS_PER_UPDATE = 100

    # --------------------------------------------------------------------------- #
    # 2. Creación del Entorno y Componentes de RL
    # --------------------------------------------------------------------------- #

    print("Creando entorno de RL simplificado para optimizar parámetros...")
    env = BlackjackSimplifiedHybridEnv(num_rondas_simulacion=RONDAS_POR_EPISODIO)
    
    # Crear el callback que se encargará de guardar los mejores parámetros
    callback = BestSimplifiedParamsCallback(env, save_freq=SAVE_FREQ, verbose=1)
    
    # Crear el modelo PPO. 'verbose=1' mostrará el progreso del entrenamiento.
    model = PPO("MlpPolicy", env, verbose=1, ent_coef=0.01, n_steps=N_STEPS_PER_UPDATE)

    # --------------------------------------------------------------------------- #
    # 3. Entrenamiento
    # --------------------------------------------------------------------------- #

    print(f"\nIniciando entrenamiento por {TOTAL_TIMESTEPS} timesteps (simulaciones)...")
    print(f"El modelo se actualizará cada {N_STEPS_PER_UPDATE} simulaciones.")
    
    model.learn(total_timesteps=TOTAL_TIMESTEPS, callback=callback)
    
    print("\nEntrenamiento completado.")

    # --------------------------------------------------------------------------- #
    # 4. Resultados Finales
    # --------------------------------------------------------------------------- #

    print("\nCalculando los parámetros óptimos finales encontrados por el modelo...")
    obs, _ = env.reset()
    mejor_vector_parametros, _ = model.predict(obs, deterministic=True)
    
    # Desempaquetar el vector de acciones en un diccionario legible
    parametros_optimos = {
        'recompensa_victoria': float(mejor_vector_parametros[0]),
        'recompensa_empate': float(mejor_vector_parametros[1]),
        'recompensa_derrota': float(mejor_vector_parametros[2]),
        'factor_riesgo_escala': float(mejor_vector_parametros[3])
    }

    print("\n=============================================")
    print("  Parámetros Óptimos Simplificados Aprendidos")
    print("=============================================")
    for key, value in parametros_optimos.items():
        print(f"  {key:<25}: {value:.4f}")
    print("=============================================")

    # Guardar el resultado final en un archivo JSON único
    timestamp = datetime.datetime.now().strftime("%Y%m%d_%H%M%S")
    filename = f"parametros_simplificados_optimos_{timestamp}.json"
    
    try:
        with open(filename, 'w', encoding='utf-8') as f:
            json.dump(parametros_optimos, f, indent=4)
        print(f"\n✅ Resultados finales guardados exitosamente en: {filename}")
    except Exception as e:
        print(f"\n❌ Error al guardar el archivo final: {e}")

if __name__ == '__main__':
    entrenar_parametros_simplificados()