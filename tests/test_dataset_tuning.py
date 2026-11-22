import sys
import os
import json

from google.genai import types

# Las pruebas se ejecutan desde la carpeta raíz del proyecto; se agrega src/ para poder importar el módulo
sys.path.append("src")
from dataset_tuning import (ejemplos_raw, examples, chequear_balance, validar_dataset, guardar_jsonl,
                            CLAVES_ESPERADAS, ARCHIVO_JSONL)

# Estas pruebas no se conectan a Google Cloud ni gastan tokens


def test_el_dataset_tiene_al_menos_10_ejemplos_de_mas_de_una_categoria():
    assert len(examples) >= 10
    assert len(chequear_balance(ejemplos_raw, "categoria")) > 1


def test_las_categorias_y_los_barrios_estan_balanceados():
    assert chequear_balance(ejemplos_raw, "categoria") == {"direccion": 5, "busqueda": 5, "otro": 5}
    assert chequear_balance(ejemplos_raw, "barrio") == {"Barrio Brasil": 5, "Concha y Toro": 5, "no indicado": 5}


def test_validar_dataset_no_encuentra_problemas():
    assert validar_dataset(examples, CLAVES_ESPERADAS) == []


def test_validar_dataset_detecta_un_duplicado_y_una_clave_faltante():
    # Paso 3 de "Cómo se prueba": romper ejemplos a propósito y confirmar que el validador los encuentra
    rotos = examples + [
        examples[0],  # text_input duplicado
        types.TuningExample(text_input="Revisa Maturana 600.", output='{"categoria": "direccion"}'),  # sin "barrio"
    ]
    problemas = validar_dataset(rotos, CLAVES_ESPERADAS)

    assert "ejemplo 15: text_input duplicado" in problemas
    assert 'ejemplo 16: output no tiene la clave "barrio"' in problemas


def test_validar_dataset_detecta_un_output_con_comillas_simples():
    # El error invisible a simple vista de la lección: comillas simples en vez de dobles no es JSON válido
    roto = [types.TuningExample(text_input="Hola", output="{'categoria': 'otro', 'barrio': 'no indicado'}")]

    assert validar_dataset(roto, CLAVES_ESPERADAS) == ["ejemplo 0: output no es JSON valido"]


def test_guardar_jsonl_escribe_el_formato_de_google_cloud():
    archivo_prueba = "tests/ejemplos_tuning_prueba.jsonl"
    guardar_jsonl(ejemplos_raw[:2], archivo_prueba)

    with open(archivo_prueba, encoding="utf-8") as f:
        lineas = f.readlines()
    os.remove(archivo_prueba)

    assert len(lineas) == 2
    primera = json.loads(lineas[0])
    assert [turno["role"] for turno in primera["contents"]] == ["user", "model"]
    assert json.loads(primera["contents"][1]["parts"][0]["text"]) == ejemplos_raw[0][1]


def test_el_archivo_que_se_sube_al_bucket_coincide_con_el_dataset():
    # Lo que se entrena es docs/ejemplos_tuning.jsonl: tiene que ser el mismo dataset que se validó
    with open(ARCHIVO_JSONL, encoding="utf-8") as f:
        lineas = [json.loads(linea) for linea in f]

    assert len(lineas) == len(ejemplos_raw)
    for linea, (texto, salida) in zip(lineas, ejemplos_raw):
        assert linea["contents"][0]["parts"][0]["text"] == texto
        assert json.loads(linea["contents"][1]["parts"][0]["text"]) == salida
