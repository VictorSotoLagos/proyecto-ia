import time
from dotenv import load_dotenv
from google import genai
from google.genai import types
from dataset_tuning import examples, validar_dataset, CLAVES_ESPERADAS  # El dataset validado del Bloque 29

# Proyecto de Google Cloud de la miniapp. La cuenta de servicio (credenciales.json) se carga desde el .env
PROYECTO_GCP = "proyecto-ia-515221"

# La profe usó gemini-2.5-flash en us-central1, pero Google lo retiró el 20-10-2026. gemini-3.5-flash-lite está
# vigente y acepta tuning; los modelos Gemini 3 o posteriores se entrenan en la región múltiple "us"
MODELO_BASE = "gemini-3.5-flash-lite"
UBICACION = "us"

# Lo que se entrena es el archivo del bucket, no la lista de Python: por eso se sube después de validarlo
GCS_URI = "gs://proyecto-ia-515221-tuning/ejemplos_tuning.jsonl"
NOMBRE_MODELO_AJUSTADO = "clasificacion-solicitudes"

# Mensajes nuevos, que no están en el dataset, para ver si el modelo ajustado generaliza (uno por categoría)
MENSAJES_DE_PRUEBA = [
    "Quiero que revises la fachada de Compañía 2150, en el Barrio Brasil.",
    "¿Hay propiedades con grafitis y malezas en Concha y Toro?",
    "¿A qué hora abre la feria del barrio?",
]


def lanzar_tuning(client: genai.Client) -> types.TuningJob:
    """Crea el trabajo de PEFT en Google Cloud. Devuelve un trabajo en curso, no el modelo terminado."""
    dataset = types.TuningDataset(gcs_uri=GCS_URI)
    config = types.CreateTuningJobConfig(
        # PEFT: congela el modelo original y entrena solo un módulo pequeño (adapter) que se conecta a él
        tuning_mode=types.TuningMode.TUNING_MODE_PEFT_ADAPTER,
        adapter_size=types.AdapterSize.ADAPTER_SIZE_FOUR,
        epoch_count=5,
        tuned_model_display_name=NOMBRE_MODELO_AJUSTADO,
    )
    return client.tunings.tune(base_model=MODELO_BASE, training_dataset=dataset, config=config)


def esperar_a_que_termine(client: genai.Client, nombre_trabajo: str, intervalo_segundos: int = 30) -> types.TuningJob:
    """Consulta el estado del trabajo cada cierto tiempo, hasta que llega a un estado final."""
    estados_finales = {
        types.JobState.JOB_STATE_SUCCEEDED,
        types.JobState.JOB_STATE_FAILED,
        types.JobState.JOB_STATE_CANCELLED,
        types.JobState.JOB_STATE_PARTIALLY_SUCCEEDED,
    }
    while True:
        trabajo = client.tunings.get(name=nombre_trabajo)
        print(f"Estado actual: {trabajo.state}")
        if trabajo.state in estados_finales:
            return trabajo
        time.sleep(intervalo_segundos)


def probar_modelo_ajustado(client: genai.Client, endpoint: str, mensajes: list[str]) -> list[str]:
    """Envía mensajes nuevos al modelo ajustado y devuelve sus respuestas."""
    # Google recomienda el razonamiento MINIMAL para las tareas ajustadas de Gemini 3: mejora el resultado y baja
    # el costo (en el Bloque 28 vimos que los tokens de razonamiento se cobran como tokens de salida)
    config = types.GenerateContentConfig(
        thinking_config=types.ThinkingConfig(thinking_level=types.ThinkingLevel.MINIMAL)
    )
    respuestas = []
    for mensaje in mensajes:
        respuesta = client.models.generate_content(model=endpoint, contents=mensaje, config=config)
        respuestas.append(respuesta.text)
    return respuestas


if __name__ == "__main__":
    load_dotenv()  # GOOGLE_APPLICATION_CREDENTIALS=credenciales.json: la cuenta de servicio del proyecto

    # Antes de enviar nada a entrenar, el dataset tiene que pasar la validación
    problemas = validar_dataset(examples, claves_esperadas=CLAVES_ESPERADAS)
    if problemas:
        raise SystemExit(f"El dataset tiene {len(problemas)} problemas: corrígelos en dataset_tuning.py antes de entrenar")

    client = genai.Client(vertexai=True, project=PROYECTO_GCP, location=UBICACION)

    try:
        print("¡Empezando el trabajo de tuning con Google!")
        trabajo = lanzar_tuning(client)
        print(f"Trabajo creado con éxito. ID {trabajo.name}")

        resultado_final = esperar_a_que_termine(client, trabajo.name)
        print("\nProceso finalizado con estado:", resultado_final.state)

        if resultado_final.state == types.JobState.JOB_STATE_SUCCEEDED:
            print("Modelo listo para usar:", resultado_final.tuned_model.model)
            print("Endpoint:", resultado_final.tuned_model.endpoint)
            respuestas = probar_modelo_ajustado(client, resultado_final.tuned_model.endpoint, MENSAJES_DE_PRUEBA)
            for mensaje, respuesta in zip(MENSAJES_DE_PRUEBA, respuestas):
                print(f"\n{mensaje}\n-> {respuesta}")
        elif resultado_final.error:
            print("Error del trabajo:", resultado_final.error)

    except Exception as error:
        print("No se pudo completar el trabajo de tuning:", error)
