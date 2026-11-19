import sys
import os
import json
from unittest.mock import MagicMock

from langchain_core.documents import Document
from langchain_core.messages import AIMessage

# Las pruebas se ejecutan desde la carpeta raíz del proyecto; se agrega src/ para poder importar el módulo
sys.path.append("src")
from registro_rag import calcular_costo, medir, registrar_consulta, guardar_registro_jsonl

# Estas pruebas no gastan tokens: el vector store y el modelo son MagicMock


def test_calcular_costo_con_las_tarifas_de_opus():
    # 1.000.000 de tokens de entrada a US$4 y 100.000 de salida a US$20 por millón
    assert calcular_costo(1_000_000, 100_000) == 4.0 + 2.0


def test_medir_guarda_el_tiempo_de_la_etapa():
    tiempos = {}
    with medir(tiempos, "etapa_prueba"):
        sum(range(1000))

    assert "etapa_prueba" in tiempos
    assert tiempos["etapa_prueba"] >= 0


def test_registrar_consulta_arma_el_registro_con_tokens_y_costo():
    vectorstore_falso = MagicMock()
    vectorstore_falso.as_retriever.return_value.invoke.return_value = [
        Document(page_content="Si la clasificación falla, lo atrapa el try/except.", id="errores_2",
                 metadata={"fuente": "docs/registro_orquestacion.md"}),
    ]
    modelo_falso = MagicMock()
    modelo_falso.invoke.return_value = AIMessage(
        content=[{"type": "thinking", "thinking": "", "signature": "x"},
                 {"type": "text", "text": "Lo atrapa el try/except [1]."}],
        usage_metadata={"input_tokens": 200, "output_tokens": 50, "total_tokens": 250},
    )

    registro = registrar_consulta(vectorstore_falso, modelo_falso, "¿Qué pasa si la clasificación falla?", k=3)

    for clave in ["timestamp", "pregunta", "k", "tiempos_ms", "tiempo_total_ms", "tokens"]:
        assert clave in registro  # Las claves que pide el CORE
    assert set(registro["tiempos_ms"]) == {"embed_y_busqueda", "armado_prompt", "generacion"}
    assert registro["tokens"]["input_tokens"] == 200
    assert registro["costo_estimado_usd"] == calcular_costo(200, 50)
    assert registro["respuesta_generada"] == "Lo atrapa el try/except [1]."
    assert registro["citas_disponibles"] == {1: "docs/registro_orquestacion.md"}
    assert registro["ids_recuperados"] == ["errores_2"]


def test_registrar_consulta_sin_datos_de_uso_no_falla():
    vectorstore_falso = MagicMock()
    vectorstore_falso.as_retriever.return_value.invoke.return_value = []
    modelo_falso = MagicMock()
    modelo_falso.invoke.return_value = AIMessage(content="El contexto no alcanza para responder.")

    registro = registrar_consulta(vectorstore_falso, modelo_falso, "pregunta", k=3)

    assert registro["tokens"] is None
    assert registro["costo_estimado_usd"] is None


def test_guardar_registro_jsonl_agrega_una_linea_por_corrida():
    archivo_prueba = "tests/registros_prueba.jsonl"
    guardar_registro_jsonl({"pregunta": "a", "k": 3}, archivo_prueba)
    guardar_registro_jsonl({"pregunta": "b", "k": 6}, archivo_prueba)

    with open(archivo_prueba, encoding="utf-8") as f:
        lineas = f.readlines()
    os.remove(archivo_prueba)

    assert len(lineas) == 2
    assert json.loads(lineas[1])["k"] == 6
