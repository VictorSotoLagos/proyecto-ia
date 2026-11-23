import sys
import json
from unittest.mock import MagicMock

# Las pruebas se ejecutan desde la carpeta raíz del proyecto; se agrega src/ para poder importar el módulo
sys.path.append("src")
from muestra_evaluacion_fachada import revisar_evaluacion, tomar_muestra, resumir

# Estas pruebas no se conectan a Google Cloud ni gastan: el cliente es un MagicMock

EVALUACION_COMPLETA = json.dumps({
    "fachada_visible": True, "senales": ["techo dañado", "escombros"], "pisos": 1,
    "evidencia": "muy fuerte", "descripcion": "La casa perdió el techo.",
}, ensure_ascii=False)


def test_una_evaluacion_completa_cumple_los_cuatro_criterios():
    revision = revisar_evaluacion(EVALUACION_COMPLETA)

    assert revision["cumple"]
    assert revision["evidencia"] == "muy fuerte"


def test_falla_si_no_ve_el_techo_o_inventa_una_senal():
    sin_techo = revisar_evaluacion(EVALUACION_COMPLETA.replace("techo dañado", "malezas"))
    senal_inventada = revisar_evaluacion(EVALUACION_COMPLETA.replace("escombros", "abandono total"))

    assert not sin_techo["cumple"] and not sin_techo["ve_techo_danado"]
    assert not senal_inventada["cumple"] and not senal_inventada["senales_permitidas"]


def test_falla_si_no_es_json():
    revision = revisar_evaluacion("La casa está en muy mal estado.")

    assert not revision["cumple"] and not revision["json_con_claves"]


def test_tomar_muestra_revisa_cada_respuesta():
    client_falso = MagicMock()
    client_falso.models.generate_content.return_value.text = EVALUACION_COMPLETA
    client_falso.models.generate_content.return_value.usage_metadata.prompt_token_count = 1000
    client_falso.models.generate_content.return_value.usage_metadata.candidates_token_count = 80
    client_falso.models.generate_content.return_value.usage_metadata.thoughts_token_count = 20

    resultados = tomar_muestra(client_falso, b"foto", repeticiones=3)
    resumen = resumir(resultados)

    assert client_falso.models.generate_content.call_count == 3
    assert resumen["fallas"] == 0
    assert resumen["tokens_salida_por_respuesta"] == 100
