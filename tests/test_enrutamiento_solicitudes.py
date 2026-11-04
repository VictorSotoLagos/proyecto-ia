import sys
from unittest.mock import MagicMock

from langchain_core.messages import AIMessage

# Las pruebas se ejecutan desde la carpeta raíz del proyecto; se agrega src/ para poder importar el módulo
sys.path.append("src")
from enrutamiento_solicitudes import (
    construir_cadena_con_enrutamiento,
    construir_paso_clasificacion,
)


# ---------- construir_cadena_con_enrutamiento: una prueba por ruta ----------
# Se mockea paso_clasificacion para forzar la categoría, sin depender de cómo clasifique el modelo real

def test_enrutamiento_va_a_cadena_direccion():
    clasificacion_falsa = MagicMock()
    clasificacion_falsa.return_value = "direccion"
    cadena_direccion_falsa = MagicMock()
    cadena_direccion_falsa.return_value = "respuesta de direccion"

    cadena = construir_cadena_con_enrutamiento(
        paso_clasificacion=clasificacion_falsa,
        cadena_direccion=cadena_direccion_falsa,
    )
    resultado = cadena.invoke({"mensaje": "Revisa la casa de Almirante Barroso 256"})

    assert cadena_direccion_falsa.called
    assert resultado == "respuesta de direccion"


def test_enrutamiento_va_a_cadena_busqueda():
    clasificacion_falsa = MagicMock()
    clasificacion_falsa.return_value = "busqueda"
    cadena_busqueda_falsa = MagicMock()
    cadena_busqueda_falsa.return_value = "respuesta de busqueda"

    cadena = construir_cadena_con_enrutamiento(
        paso_clasificacion=clasificacion_falsa,
        cadena_busqueda=cadena_busqueda_falsa,
    )
    resultado = cadena.invoke({"mensaje": "Dame una casa de un piso con malezas"})

    assert cadena_busqueda_falsa.called
    assert resultado == "respuesta de busqueda"


def test_enrutamiento_usa_default_ante_categoria_desconocida():
    clasificacion_falsa = MagicMock()
    clasificacion_falsa.return_value = "categoria_inventada"
    cadena_otro_falsa = MagicMock()
    cadena_otro_falsa.return_value = "respuesta por defecto"

    cadena = construir_cadena_con_enrutamiento(
        paso_clasificacion=clasificacion_falsa,
        cadena_otro=cadena_otro_falsa,
    )
    resultado = cadena.invoke({"mensaje": "mensaje ambiguo"})

    assert cadena_otro_falsa.called
    assert resultado == "respuesta por defecto"


# ---------- construir_paso_clasificacion: normalización ----------

def test_clasificacion_normaliza_antes_de_comparar():
    modelo_falso = MagicMock()
    # Tiene que ser un AIMessage real: StrOutputParser necesita leer .content de un mensaje de verdad
    modelo_falso.return_value = AIMessage(content=" Direccion \n")

    resultado = construir_paso_clasificacion(modelo_falso).invoke(
        {"mensaje": "Revisa la casa de Almirante Barroso 256"}
    )

    assert resultado == "direccion"
