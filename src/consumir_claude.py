import os
import requests
from dotenv import load_dotenv

load_dotenv()

def armar_peticion(pregunta):
    api_key = os.getenv("ANTHROPIC_API_KEY")
    url = "https://api.anthropic.com/v1/messages"
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json",
        "anthropic-beta": "server-side-fallback-2026-07-01",
    }
    body = {
        "model": "claude-opus-5-5",
        "max_tokens": 16000,
        "messages": [
            {"role": "user", "content": pregunta}
        ],
        "fallbacks": "default",
    }
    return url, headers, body

def enviar_peticion(url, headers, body):
    respuesta = requests.post(url, headers=headers, json=body)
    return respuesta.json()

def extraer_texto(datos):
    for bloque in datos["content"]:
        if bloque["type"] == "text":
            return bloque["text"]

def obtener_dato_de_prueba(pregunta):
    url, headers, body = armar_peticion(pregunta)
    datos = enviar_peticion(url, headers, body)
    return extraer_texto(datos)

print(obtener_dato_de_prueba("Confirma en una frase corta que esta conexión funciona"))

