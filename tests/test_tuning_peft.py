import sys
from unittest.mock import MagicMock

from google.genai import types

# Las pruebas se ejecutan desde la carpeta raíz del proyecto; se agrega src/ para poder importar el módulo
sys.path.append("src")
from tuning_peft import lanzar_tuning, esperar_a_que_termine, probar_modelo_ajustado, MODELO_BASE, GCS_URI

# Estas pruebas no se conectan a Google Cloud ni gastan: el cliente es un MagicMock


def test_lanzar_tuning_pide_peft_con_el_dataset_del_bucket():
    client_falso = MagicMock()

    lanzar_tuning(client_falso)

    argumentos = client_falso.tunings.tune.call_args.kwargs
    assert argumentos["base_model"] == MODELO_BASE
    assert argumentos["training_dataset"].gcs_uri == GCS_URI
    assert argumentos["config"].tuning_mode == types.TuningMode.TUNING_MODE_PEFT_ADAPTER
    assert argumentos["config"].adapter_size == types.AdapterSize.ADAPTER_SIZE_FOUR


def test_esperar_a_que_termine_consulta_hasta_llegar_a_un_estado_final():
    client_falso = MagicMock()
    # side_effect entrega una respuesta distinta en cada llamada: primero "en curso", después "terminado"
    client_falso.tunings.get.side_effect = [
        types.TuningJob(name="trabajo-1", state=types.JobState.JOB_STATE_RUNNING),
        types.TuningJob(name="trabajo-1", state=types.JobState.JOB_STATE_SUCCEEDED),
    ]

    trabajo = esperar_a_que_termine(client_falso, "trabajo-1", intervalo_segundos=0)

    assert trabajo.state == types.JobState.JOB_STATE_SUCCEEDED
    assert client_falso.tunings.get.call_count == 2


def test_probar_modelo_ajustado_usa_el_endpoint_y_razonamiento_minimo():
    client_falso = MagicMock()
    client_falso.models.generate_content.return_value.text = '{"categoria": "otro", "barrio": "no indicado"}'

    respuestas = probar_modelo_ajustado(client_falso, "projects/1/locations/us/endpoints/2", ["Hola"])

    assert respuestas == ['{"categoria": "otro", "barrio": "no indicado"}']
    argumentos = client_falso.models.generate_content.call_args.kwargs
    assert argumentos["model"] == "projects/1/locations/us/endpoints/2"
    assert argumentos["config"].thinking_config.thinking_level == types.ThinkingLevel.MINIMAL
