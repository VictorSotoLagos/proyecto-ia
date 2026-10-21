import os
import requests
from dotenv import load_dotenv

load_dotenv()

URL_API = "https://api.anthropic.com/v1/messages"
VERSION_API = "2023-06-01"
MODELO = "claude-opus-5-5"
MAX_TOKENS = 1000
# Precios de claude-opus-5-5 en USD por millón de tokens (revisados el 2026-10-19)
PRECIO_ENTRADA = 4.00
PRECIO_SALIDA = 20.00
SYSTEM_INSTRUCTION= "Eres un experto en arquitectura y urbanismo, con un enorme conocimiento del Barrio Brasil y Concha y Toro de Santiago. Responde forma precisa y concisa, en máximo 5 líneas, y con un lenguaje claro y comprensible para cualquier persona."

API_KEY = os.getenv("ANTHROPIC_API_KEY")

def armar_peticion(pregunta):
    if not pregunta or not pregunta.strip():
        raise ValueError("La pregunta no puede estar vacía.")
    if not API_KEY:
        raise RuntimeError("Falta la API Key en el archivo .env.")
    url = URL_API
    headers = {
        "x-api-key": API_KEY,
        "anthropic-version": VERSION_API,
        "content-type": "application/json",
        "anthropic-beta": "server-side-fallback-2026-07-01",
    }
    body = {
        "model": MODELO,
        "max_tokens": MAX_TOKENS,
        "system": SYSTEM_INSTRUCTION,
        "messages": [
            {"role": "user", "content": pregunta}
        ],
        "fallbacks": "default",
    }
    return url, headers, body

def enviar_peticion(url, headers, body):
    try:
        respuesta = requests.post(url, headers=headers, json=body, timeout=60)
    except requests.exceptions.RequestException:
        raise RuntimeError("No se pudo conectar con el servicio. Intenta de nuevo en unos segundos.")
    try:
        return respuesta.json()
    except requests.exceptions.JSONDecodeError:
        raise RuntimeError("La respuesta del servicio no llegó en el formato esperado.")

def extraer_texto(datos):
    # Si Anthropic devuelve un error (por ejemplo, API key inválida), muestra su mensaje
    if "error" in datos:
        raise RuntimeError("La API respondió con un error: " + datos["error"]["message"])
    # Claude devuelve varios bloques; buscamos el que es de tipo "text"
    try:
        for bloque in datos["content"]:
            if bloque["type"] == "text":
                return bloque["text"]
    except KeyError:
        raise RuntimeError("La respuesta no trae el campo 'content' esperado.")
    raise RuntimeError("La respuesta no trae ningún bloque de texto.")

def obtener_dato_de_prueba(pregunta):
    url, headers, body = armar_peticion(pregunta)
    datos = enviar_peticion(url, headers, body)
    # Primero se extrae el texto: si la API devolvió un error, se detiene aquí con su mensaje
    texto = extraer_texto(datos)
    costo = calcular_costo(datos, precio_entrada=PRECIO_ENTRADA, precio_salida=PRECIO_SALIDA)
    return texto, costo

#def calcular_costo(datos: dict, precio_entrada: float, precio_salida: float) -> float:
def calcular_costo(datos, precio_entrada, precio_salida):
    uso = datos["usage"]
    tokens_de_entrada = uso["input_tokens"]
    tokens_de_salida = uso["output_tokens"]  # ya incluye el razonamiento
    # Los precios son por millón de tokens
    costo_total = (tokens_de_entrada * precio_entrada + tokens_de_salida * precio_salida) / 1_000_000
    return costo_total


texto, costo = obtener_dato_de_prueba("Cuentame lo que sabes de la arquitectura de Barrio Brasil y Concha y Toro de Santiago")
print(texto)
print(f"Costo estimado: ${costo:.6f} USD")

