import sys
from unittest.mock import MagicMock

from langchain_core.runnables import RunnableLambda

# Las pruebas se ejecutan desde la carpeta raíz del proyecto; se agrega src/ para poder importar el módulo
sys.path.append("src")
from enrutamiento_solicitudes import (
    construir_cadena_con_enrutamiento,
    construir_ruta_segura,
    procesar_mensaje_seguro,
)


# Simula un error de red al llamar al modelo
def fallar_a_proposito(x):
    raise ConnectionError("simulado")


# ---------- construir_ruta_segura: los dos respaldos de cada ruta ----------
# Se usa un RunnableLambda real que lanza la excepción, no un MagicMock, como recomienda el curso

def test_ruta_usa_modelo_secundario_ante_fallo_del_principal():
    ruta_rota = RunnableLambda(fallar_a_proposito)
    ruta_secundaria_falsa = RunnableLambda(lambda x: "respuesta del modelo secundario")

    ruta_segura = construir_ruta_segura(ruta_rota, ruta_secundaria_falsa)
    resultado = ruta_segura.invoke({"mensaje": "Revisa la casa de Almirante Barroso 256."})

    assert resultado == "respuesta del modelo secundario"


def test_ruta_usa_respuesta_generica_si_fallan_los_dos_modelos():
    ruta_rota = RunnableLambda(fallar_a_proposito)
    ruta_secundaria_rota = RunnableLambda(fallar_a_proposito)

    ruta_segura = construir_ruta_segura(ruta_rota, ruta_secundaria_rota)
    resultado = ruta_segura.invoke({"mensaje": "Revisa la casa de Almirante Barroso 256."})

    assert "comunidad brasil alameda" in resultado.lower()


# ---------- procesar_mensaje_seguro: el try/except general ----------
# La clasificación falla antes de que RunnableBranch elija una ruta, así que ningún with_fallbacks de las rutas lo cubre

def test_procesar_mensaje_seguro_no_propaga_excepciones():
    clasificacion_falsa = MagicMock()
    clasificacion_falsa.side_effect = ConnectionError("simulado")

    cadena_falsa = construir_cadena_con_enrutamiento(paso_clasificacion=clasificacion_falsa)
    resultado = procesar_mensaje_seguro(cadena_falsa, "mensaje de prueba")

    assert "no pudimos procesar" in resultado.lower()
