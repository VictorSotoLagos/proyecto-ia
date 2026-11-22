import os
import json
from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from langchain_core.output_parsers import StrOutputParser
from enrutamiento_solicitudes import plantilla_clasificacion  # El clasificador que usa la app desde el Bloque 19
from dataset_tuning import ejemplos_raw  # Los 15 mensajes etiquetados del Bloque 29

# Evidencia para la pregunta "problema_de_formato_o_tono" del Bloque 30: se toman 20 respuestas reales del
# clasificador actual y se revisan con una lista fija de criterios
ARCHIVO_RESULTADOS = "docs/muestra_formato_clasificacion.json"
MODELO = "claude-opus-5-5"
CATEGORIAS = ("direccion", "busqueda", "otro")
# Tarifas de Claude Opus 5.5 en USD por millón de tokens (las mismas de registro_rag.py)
TARIFA_ENTRADA_X1M = 4.0
TARIFA_SALIDA_X1M = 20.0

# 20 mensajes con su categoría correcta, etiquetada antes de correr la muestra:
# los 15 del dataset del Bloque 29 y 5 nuevos
MUESTRA = [(texto, salida["categoria"]) for texto, salida in ejemplos_raw] + [
    ("Quiero que revises la fachada de Compañía 2150, en el Barrio Brasil.", "direccion"),
    ("¿Hay propiedades con grafitis y malezas en Concha y Toro?", "busqueda"),
    ("¿A qué hora abre la feria del barrio?", "otro"),
    ("¿Puedes evaluar la fachada de Cueto 345?", "direccion"),
    ("Hola, buenas tardes.", "otro"),
]


def cumple_formato(respuesta: str) -> bool:
    """Criterio 1: después de la limpieza que hace el enrutador (strip y lower), es una de las 3 categorías."""
    return respuesta.strip().lower() in CATEGORIAS


def es_palabra_exacta(respuesta: str) -> bool:
    """Criterio 2: la respuesta ya es exactamente una de las 3 categorías, sin necesidad de limpiarla."""
    return respuesta in CATEGORIAS


def tomar_muestra(cadena, muestra: list[tuple[str, str]]) -> list[dict]:
    """Envía cada mensaje al clasificador y revisa su respuesta con los criterios fijos."""
    resultados = []
    for mensaje, esperada in muestra:
        respuesta_modelo = cadena.invoke({"mensaje": mensaje})
        texto = StrOutputParser().invoke(respuesta_modelo)  # Deja solo el texto, sin el razonamiento
        tokens = respuesta_modelo.usage_metadata or {}
        resultados.append({
            "mensaje": mensaje,
            "esperada": esperada,
            "respuesta_cruda": texto,
            "cumple_formato": cumple_formato(texto),
            "palabra_exacta": es_palabra_exacta(texto),
            "correcta": texto.strip().lower() == esperada,  # Criterio 3: no es de formato, pero sirve
            "tokens_entrada": tokens.get("input_tokens", 0),
            "tokens_salida": tokens.get("output_tokens", 0),
        })
    return resultados


def resumir(resultados: list[dict]) -> dict:
    tokens_entrada = sum(r["tokens_entrada"] for r in resultados)
    tokens_salida = sum(r["tokens_salida"] for r in resultados)
    return {
        "respuestas": len(resultados),
        "fallas_de_formato": sum(not r["cumple_formato"] for r in resultados),
        "no_exactas_antes_de_limpiar": sum(not r["palabra_exacta"] for r in resultados),
        "categorias_incorrectas": sum(not r["correcta"] for r in resultados),
        "tokens_entrada": tokens_entrada,
        "tokens_salida": tokens_salida,
        "costo_usd": round((tokens_entrada * TARIFA_ENTRADA_X1M + tokens_salida * TARIFA_SALIDA_X1M) / 1_000_000, 6),
    }


if __name__ == "__main__":
    load_dotenv()
    # El mismo modelo y la misma plantilla que usa el enrutador en enrutamiento_solicitudes.py
    modelo = ChatAnthropic(model=MODELO, anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"))
    cadena = plantilla_clasificacion | modelo

    resultados = tomar_muestra(cadena, MUESTRA)
    resumen = resumir(resultados)

    for r in resultados:
        marca = "OK " if r["cumple_formato"] else "FALLA"
        print(f"{marca} | esperada: {r['esperada']:9} | respuesta: {r['respuesta_cruda']!r} | {r['mensaje']}")
    print("\n", resumen)

    with open(ARCHIVO_RESULTADOS, "w", encoding="utf-8") as f:
        json.dump({"modelo": MODELO, "resumen": resumen, "resultados": resultados}, f, indent=2, ensure_ascii=False)
    print("Resultados guardados en", ARCHIVO_RESULTADOS)
