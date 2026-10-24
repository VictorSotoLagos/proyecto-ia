import os
import json
import re
import base64
import requests
from dotenv import load_dotenv

from prompts.banco import BANCO_DE_PROMPTS

load_dotenv()

URL_API = "https://api.anthropic.com/v1/messages"
VERSION_API = "2023-06-01"
MODELO = "claude-opus-5-5"
MAX_TOKENS = 1000
# Precios de claude-opus-5-5 en USD por millón de tokens (revisados el 2026-10-19)
PRECIO_ENTRADA = 4.00
PRECIO_SALIDA = 20.00

API_KEY = os.getenv("ANTHROPIC_API_KEY")

def leer_imagen_base64(ruta):
    # Las imágenes viajan dentro del JSON como texto en base64
    with open(ruta, "rb") as archivo:
        return base64.standard_b64encode(archivo.read()).decode("utf-8")

def armar_peticion(modelo, pregunta, system_instruction, response_schema=None, imagen_b64=None):
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
        "model": modelo,
        "max_tokens": MAX_TOKENS,
        "system": system_instruction,
        "messages": [
            {"role": "user", "content": pregunta}
        ],
        "fallbacks": "default",
    }

    if response_schema is not None:
        body["output_config"] = {
            "format": {"type": "json_schema", "schema": response_schema}
        }

    if imagen_b64 is not None:
        # Enviamos la foto y la pregunta juntas: el mensaje pasa a ser una lista de dos bloques
        # (la foto de prueba es PNG; si usas una foto JPEG, cambia a "image/jpeg")
        body["messages"][0]["content"] = [
            {"type": "image", "source": {"type": "base64", "media_type": "image/png", "data": imagen_b64}},
            {"type": "text", "text": pregunta},
        ]

    return url, headers, body

def enviar_peticion(url, headers, body):
    try:
        respuesta = requests.post(url, headers=headers, json=body, timeout=60)
    except requests.exceptions.Timeout:
        raise RuntimeError("Se agotó el tiempo de espera. Intenta de nuevo en unos momentos.")
    except requests.exceptions.RequestException:
        raise RuntimeError("No se pudo conectar con el servicio. Intenta de nuevo en unos segundos.")

    # Primero se revisa el código de estado: si la API respondió con un error, se detiene aquí
    if respuesta.status_code in (401, 403):
        raise RuntimeError("La API Key es inválida o no tiene permisos para usar este modelo.")
    if respuesta.status_code >= 500:
        raise RuntimeError("El proveedor no pudo procesar la solicitud. Intenta de nuevo en unos segundos.")
    if respuesta.status_code == 429:
        raise RuntimeError("Se superó el límite de solicitudes. Intenta de nuevo en unos segundos.")

    if respuesta.status_code != 200:
        raise RuntimeError(f"La API respondió con un error: {respuesta.status_code} - {respuesta.text}")

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

def obtener_dato_de_prueba(pregunta, imagen_b64):
    # La instrucción y el esquema salen del banco de prompts, para no escribirlos dos veces.
    # BANCO_DE_PROMPTS[3] es "evaluar_fachada", el cuarto prompt del banco.
    prompt = BANCO_DE_PROMPTS[3]
    system_instruction = prompt["system_instruction"]
    response_schema = prompt["response_schema"]

    url, headers, body = armar_peticion(MODELO, pregunta, system_instruction, response_schema, imagen_b64)
    datos = enviar_peticion(url, headers, body)
    # Primero se extrae el texto: si la API devolvió un error, se detiene aquí con su mensaje
    texto = extraer_texto(datos)
    respuesta = parsear_respuesta_json(texto, prompt["claves_esperadas"])
    costo = calcular_costo(datos, precio_entrada=PRECIO_ENTRADA, precio_salida=PRECIO_SALIDA)
    return respuesta, costo

#def calcular_costo(datos: dict, precio_entrada: float, precio_salida: float) -> float:
def calcular_costo(datos, precio_entrada, precio_salida):
    uso = datos["usage"]
    tokens_de_entrada = uso["input_tokens"]
    tokens_de_salida = uso["output_tokens"]  # ya incluye el razonamiento
    # Los precios son por millón de tokens
    costo_total = (tokens_de_entrada * precio_entrada + tokens_de_salida * precio_salida) / 1_000_000
    return costo_total

def parsear_respuesta_json(texto, claves_requeridas=None):
    texto_limpio = texto.strip()
    # Quita los ```json ... ``` que a veces rodean el JSON
    texto_limpio = re.sub(r"^```(?:json)?\s*", "", texto_limpio)
    texto_limpio = re.sub(r"\s*```$", "", texto_limpio)
    try:
        datos = json.loads(texto_limpio)
    except json.JSONDecodeError:
        raise ValueError("La respuesta del modelo no es JSON válido")
    
    if claves_requeridas:
        for clave in claves_requeridas:
            if clave not in datos:
                raise ValueError(f"Falta la clave '{clave}' en la respuesta")
    return datos


if __name__ == "__main__": # Solo se ejecuta al correr este archivo directamente, NO cuando otro archivo lo importa
    try:
        # Foto real de Google Street View de Almirante Barroso 256 (correr desde la carpeta raíz del proyecto)
        imagen_b64 = leer_imagen_base64("docs/fachada-almirante-barroso-256.png")
        respuesta, costo = obtener_dato_de_prueba("Evalúa la fachada de la propiedad de calle Almirante Barroso 256, Barrio Brasil.", imagen_b64)
        print(respuesta)
        print(f"Costo estimado: ${costo:.6f} USD")
    except (ValueError, RuntimeError) as error:
        print("No se pudo completar la operación:", error)

