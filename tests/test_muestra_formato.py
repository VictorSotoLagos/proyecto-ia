import sys
from unittest.mock import MagicMock

from langchain_core.messages import AIMessage

# Las pruebas se ejecutan desde la carpeta raíz del proyecto; se agrega src/ para poder importar el módulo
sys.path.append("src")
from muestra_formato import cumple_formato, es_palabra_exacta, tomar_muestra, resumir, MUESTRA

# Estas pruebas no gastan tokens: el clasificador es un MagicMock


def test_la_muestra_tiene_20_mensajes_etiquetados():
    assert len(MUESTRA) == 20
    assert {esperada for _, esperada in MUESTRA} == {"direccion", "busqueda", "otro"}


def test_los_criterios_de_formato():
    assert cumple_formato("direccion") and es_palabra_exacta("direccion")
    # Con espacios o mayúscula, el enrutador la limpia y la acepta, pero no es la palabra exacta
    assert cumple_formato(" Busqueda\n") and not es_palabra_exacta(" Busqueda\n")
    # Con tilde o con una oración, el mensaje caería sin aviso en la ruta "otro": es una falla de formato
    assert not cumple_formato("Dirección")
    assert not cumple_formato("La categoría es: otro")


def test_tomar_muestra_revisa_cada_respuesta_y_suma_tokens():
    cadena_falsa = MagicMock()
    cadena_falsa.invoke.side_effect = [
        AIMessage(content="direccion", usage_metadata={"input_tokens": 100, "output_tokens": 10, "total_tokens": 110}),
        AIMessage(content="Dirección", usage_metadata={"input_tokens": 100, "output_tokens": 10, "total_tokens": 110}),
    ]

    resultados = tomar_muestra(cadena_falsa, [("Revisa Maturana 600.", "direccion"), ("Revisa Cueto 10.", "direccion")])
    resumen = resumir(resultados)

    assert [r["cumple_formato"] for r in resultados] == [True, False]
    assert resumen["fallas_de_formato"] == 1
    assert resumen["categorias_incorrectas"] == 1
    assert resumen["tokens_entrada"] == 200
