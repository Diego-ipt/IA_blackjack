import pandas as pd
import os

from .cartas import Carta
from .player import Mano
from .acciones import Accion
from agents.agente_base import Agente

class DataCollector:
    def __init__(self, filepath: str, chunk_size: int = 10000):
        """
        Inicializa recolector de datos para escribir por lotes(chunks) en un archivo CSV.
        :param filepath: Ruta del archivo CSV donde se guardarán los datos.
        :param chunk_size: Número de registros a acumular antes de escribir en el archivo.
        """
        # Diccionarios: Clave: "id(mano)", Valor: dict (registro de datos)
        self.filepath = filepath
        self.chunk_size = chunk_size
        self._header_written = False

        os.makedirs(os.path.dirname(self.filepath), exist_ok=True)

        self.registros = []

    def registrar_decision(self, agente: Agente, mano: Mano, carta_dealer: Carta, accion: Accion):
        registro = {
            "mano_id": id(mano),
            "mano_valor": mano.valor_total,
            "mano_es_blanda": mano.es_blanda,
            "mano_apuesta": mano.apuesta,
            "mano_num_cartas": len(mano.cartas),
            "mano_es_par_divisible": len(mano.cartas) == 2 and (mano.cartas[0].valor == mano.cartas[1].valor),
            "agente_nombre": agente.jugador.nombre,
            "agente_capital_inicial": agente.jugador.capital + mano.apuesta,
            "dealer_valor_carta": carta_dealer.valor,
            "accion_tomada": accion.name,
            "ganancia_neta": None # Se llena despues
        }

        self.registros.append(registro)

    def registrar_resultado(self, mano:Mano, ganancia: float):
        mano_id = id(mano)

        for registro in self.registros:
            if registro.get("mano_id") == mano_id and registro["ganancia_neta"] is None:
                registro["ganancia_neta"] = ganancia

    def check_and_flush(self):
        if len(self.registros) >= self.chunk_size:
            self._flush_to_disk()

    def _flush_to_disk(self):
        """
        Escribe los registros acumulados en el archivo CSV y limpia la lista de registros.
        """
        if not self.registros:
            return

        # Eliminamos los registros que no tienen ganancia_neta (incompletos)
        registros_completos = [r for r in self.registros if r.get("ganancia_neta") is not None]
        for r in registros_completos:
            if "mano_id" in r:
                del r["mano_id"]

        # Si no hay registros completos, no hacemos nada
        if not registros_completos:
            self.registros = []
            return

        df = pd.DataFrame(registros_completos)

        # Normalizamos la recompensa para facilitar el entrenamiento de modelos
        # Evitamos división por cero
        if 'ganancia_neta' in df.columns and 'mano_apuesta' in df.columns:
            df['recompensa_normalizada'] = df.apply(
                lambda row: row['ganancia_neta'] / row['mano_apuesta'] if row['mano_apuesta'] > 0 else 0,
                axis=1
            )

        # Escribimos el DataFrame al archivo CSV
        # Usamos mode='a' para agregar al final del archivo
        # y header=not self._header_written para escribir el encabezado solo una vez
        df.to_csv(
            self.filepath,
            mode='a',
            header=not self._header_written,
            index=False
        )
        self._header_written = True
        self.registros = []


    def close(self):
        """
        Cierra el recolector.
        """
        self._flush_to_disk()

class RoundDataCollector:
    """
    Recolecta y almacena datos agregados al final de cada ronda para cada agente.
    Está optimizado para el análisis de rendimiento a lo largo del tiempo.
    """
    def __init__(self, filepath: str, chunk_size: int = 1000):
        self.filepath = filepath
        self.chunk_size = chunk_size
        self.registros = []
        self._header_written = os.path.exists(self.filepath)

        # Crear directorio si no existe
        os.makedirs(os.path.dirname(self.filepath), exist_ok=True)

    def registrar_resultado_ronda(self, agente: Agente, ronda_num: int, capital_inicial: int, capital_final: int, apuesta_total: int, cartas_restantes_mazo: int):
        """
        Registra el resumen completo de la ronda para un agente.
        Esta funcion se llama UNA VEZ por agente al final de cada ronda.
        """
        ganancia_neta = capital_final - capital_inicial

        if ganancia_neta > 0:
            resultado = 1
        elif ganancia_neta < 0:
            resultado = -1
        else:
            resultado = 0

        registro = {
            "ronda_num": ronda_num,
            "agente_nombre": agente.jugador.nombre,
            "capital_inicial_ronda": capital_inicial,
            "capital_final_ronda": capital_final,
            "ganancia_neta_ronda": ganancia_neta,
            "apuesta_total_ronda": apuesta_total,
            "resultado_ronda": resultado,
            "cartas_restantes_mazo": cartas_restantes_mazo
        }
        self.registros.append(registro)

        # Escribir en disco si alcanzamos el tamaño del chunk
        if len(self.registros) >= self.chunk_size:
            self._flush_to_disk()

    def _flush_to_disk(self):
        """Escribe los registros acumulados en el archivo CSV y limpia la lista."""
        if not self.registros:
            return

        df = pd.DataFrame(self.registros)
        df.to_csv(
            self.filepath,
            mode='a',
            header=not self._header_written,
            index=False
        )
        self._header_written = True
        self.registros = [] # Limpiar para el siguiente chunk

    def close(self):
        """Asegura que todos los registros restantes se escriban en el disco."""
        self._flush_to_disk()