import sys
from unittest.mock import MagicMock

from langchain_core.messages import AIMessage

# Las pruebas se ejecutan desde la carpeta raíz del proyecto; se agrega src/ para poder importar el módulo
sys.path.append("src")
from cadena_ficha import construir_cadena


# ---------- construir_cadena: ficha de la propiedad en 3 pasos ----------
# El modelo es un MagicMock: no se hace ninguna petición real a la API

def test_cadena_conecta_los_tres_pasos():
    modelo_falso = MagicMock()
    # side_effect con una lista: una respuesta distinta en cada llamada, en orden
    modelo_falso.side_effect = [
        AIMessage(content="Casa de un piso con ventanas tapiadas y pasto en la entrada"),
        AIMessage(content="ventanas tapiadas\nmalezas"),
        AIMessage(content="Conclusión: En posible abandono"),
    ]

    cadena = construir_cadena(modelo_falso)
    resultado = cadena.invoke({"reporte": "reporte de prueba"})

    assert modelo_falso.call_count == 3
    # La cadena devuelve el texto del último paso: la conclusión
    assert resultado == "Conclusión: En posible abandono"
