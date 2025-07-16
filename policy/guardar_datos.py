import pandas as pd

def guardar_historial_csv(historial: dict, filename: str):
    """
    Recibe un diccionario con listas (historial) y guarda un CSV con las columnas correspondientes.
    """
    # Crear DataFrame directamente
    df = pd.DataFrame(historial)
    df.to_csv(filename, index=False)
