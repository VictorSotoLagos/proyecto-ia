import os
import requests
from dotenv import load_dotenv

load_dotenv()

def armar_peticion(pregunta):
    if not pregunta or not pregunta.strip():
        raise ValueError("La pregunta no puede estar vacía.")
    api_key = os.getenv("ANTHROPIC_API_KEY")
    if not api_key:
        raise RuntimeError("Falta ANTHROPIC_API_KEY en el archivo .env.")
    url = "https://api.anthropic.com/v1/messages"
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
        "anthropic-beta": "server-side-fallback-2026-07-01",
    }
    body = {
        "model": "claude-opus-5-5",
        "max_tokens": 500,
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
    return extraer_texto(datos)

print(obtener_dato_de_prueba("Confirma brevemente que la conexión funciona correctamente."))
