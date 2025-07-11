import pytest
import logging

if __name__ == "__main__":

    # Configurar el logger para mostrar mensajes de depuración
    logging.basicConfig(level=logging.DEBUG)

    # Ejecutar las pruebas
    pytest.main(["-v", "--tb=short", "tests/"])