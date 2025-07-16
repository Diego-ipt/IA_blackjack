import pandas as pd
import os

from .cartas import Carta
from .player import Mano
from .acciones import Accion
from agents.agente_base import Agente

class DataCollector:
    def __init__(self, filepath: str, chunk_size: int = 10000, guardar_en_archivo: bool = True):
        """
        Inicializa recolector de datos para escribir por lotes(chunks) en un archivo CSV.
        :param filepath: Ruta del archivo CSV donde se guardarán los datos.
        :param chunk_size: Número de registros a acumular antes de escribir en el archivo.
        """
        # Diccionarios: Clave: "id(mano)", Valor: dict (registro de datos)
        self.filepath = filepath
        self.chunk_size = chunk_size
        self._header_written = False
        self.guardar_en_archivo = guardar_en_archivo

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
            "ganancia_neta": None, # Se llena despues
            "conteo_cartas": getattr(agente, "conteo", pd.NA)
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
        if not self.guardar_en_archivo:
            return
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
            
        df["conteo_cartas"] = df["conteo_cartas"].astype("Int64")

        # Escribimos el DataFrame al archivo CSV
        # Usamos mode='a' para agregar al final del archivo
        # y header=not self._header_written para escribir el encabezado solo una vez
        df.to_csv(
            self.filepath,
            mode="a",
            header=not self._header_written,
            index=False,
            na_rep="None"
        )
        self._header_written = True
        self.registros = []


    def close(self):
        """
        Cierra el recolector.
        """
        self._flush_to_disk()