import os
import requests
from dotenv import load_dotenv

load_dotenv()

def obtener_dato_de_prueba(pregunta):
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
    respuesta = requests.post(url, headers=headers, json=body)
    datos = respuesta.json()
    for bloque in datos["content"]:
        if bloque["type"] == "text":
            return bloque["text"]

print(obtener_dato_de_prueba("Confirma en una frase corta que esta conexión funciona"))