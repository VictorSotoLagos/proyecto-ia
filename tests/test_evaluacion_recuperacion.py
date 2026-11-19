import sys
from unittest.mock import MagicMock

from langchain_core.documents import Document

# Las pruebas se ejecutan desde la carpeta raíz del proyecto; se agrega src/ para poder importar el módulo
sys.path.append("src")
from evaluacion_recuperacion import (
    CASOS_EVALUACION,
    precision_at_k,
    recall_at_k,
    f1_score,
    promediar,
    evaluar_recuperacion,
)

# Estas pruebas no consultan Chroma ni gastan tokens: el retriever es un MagicMock


# ---------- Métricas ----------

def test_precision_es_la_fraccion_de_recuperados_que_sirve():
    assert precision_at_k(["errores_1", "modelo_1", "agente_1"], {"errores_1"}) == 1 / 3
    assert precision_at_k([], {"errores_1"}) == 0.0


def test_recall_es_la_fraccion_de_relevantes_recuperada():
    assert recall_at_k(["limites_1", "agente_2"], {"limites_1", "limites_2"}) == 0.5
    assert recall_at_k(["limites_1"], set()) is None  # Pregunta sin respuesta en el corpus


def test_f1_combina_precision_y_recall():
    assert f1_score(0.5, 1.0) == 2 * 0.5 * 1.0 / 1.5
    assert f1_score(0.0, 0.0) == 0.0
    assert f1_score(0.3, None) == 0.0


def test_promediar_ignora_los_none():
    assert promediar([1.0, None, 0.0]) == 0.5
    assert promediar([None]) == 0.0


# ---------- Evaluación completa ----------

def test_evaluar_recuperacion_calcula_metricas_y_promedios():
    retriever_falso = MagicMock()
    retriever_falso.invoke.return_value = [
        Document(page_content="a", id="errores_2"),
        Document(page_content="b", id="errores_1"),
        Document(page_content="c", id="modelo_1"),
    ]
    casos = [
        {"pregunta": "¿Qué pasa si la clasificación falla?", "ids_relevantes": {"errores_2"}},
        {"pregunta": "Pregunta sin respuesta", "ids_relevantes": set()},
    ]

    resultados, precision_promedio, recall_promedio, f1_promedio = evaluar_recuperacion(retriever_falso, casos, k=3)

    assert resultados[0]["precision"] == 1 / 3
    assert resultados[0]["recall"] == 1.0
    assert resultados[1]["recall"] is None and resultados[1]["f1"] is None
    assert precision_promedio == (1 / 3 + 0.0) / 2  # La precisión de la pregunta sin respuesta sí cuenta
    assert recall_promedio == 1.0  # El recall "n/a" no entra al promedio
    assert f1_promedio == resultados[0]["f1"]


def test_evaluar_recuperacion_considera_solo_k_chunks():
    retriever_falso = MagicMock()
    retriever_falso.invoke.return_value = [Document(page_content="x", id=f"chunk_{i}") for i in range(5)]

    resultados, _, _, _ = evaluar_recuperacion(retriever_falso, [{"pregunta": "p", "ids_relevantes": {"chunk_4"}}], k=3)

    assert resultados[0]["ids_recuperados"] == ["chunk_0", "chunk_1", "chunk_2"]
    assert resultados[0]["recall"] == 0.0


# ---------- Conjunto de evaluación ----------

def test_conjunto_tiene_entre_8_y_15_preguntas_con_ids_del_indice():
    ids_del_indice = {"objetivo_1", "objetivo_2", "senales_1", "senales_2", "formas_de_uso_1", "formas_de_uso_2",
                      "modelo_1", "modelo_2", "errores_1", "errores_2", "agente_1", "agente_2",
                      "limites_1", "limites_2"}

    assert 8 <= len(CASOS_EVALUACION) <= 15
    for caso in CASOS_EVALUACION:
        assert caso["ids_relevantes"] <= ids_del_indice  # Ningún id mal escrito
