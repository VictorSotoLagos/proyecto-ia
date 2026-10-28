import sys

# Las pruebas se ejecutan desde la carpeta raíz del proyecto; se agrega src/ para poder importar el módulo
sys.path.append("src")
from pipeline_texto import procesar_texto


# ---------- procesar_texto: limpieza y tokenización ----------
# No hace falta ningún mock: procesar_texto no usa la red ni depende de nada externo

def test_procesar_texto_normaliza_mayusculas_y_puntuacion():
    resultado = procesar_texto("El Cielo, es AZUL!")

    assert resultado == ["el", "cielo", "es", "azul"]

def test_procesar_texto_solo_puntuacion_devuelve_lista_vacia():
    # Un texto que queda vacío después de limpiarlo devuelve una lista vacía, no un error
    resultado = procesar_texto("¡¡¡...!!!")

    assert resultado == []
