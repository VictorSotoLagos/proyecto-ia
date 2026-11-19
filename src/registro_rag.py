import os
import time  # Latencia
import json  # Registro en JSON Lines
from contextlib import contextmanager  # Administrador de contexto: ejecuta algo antes y después de un bloque
from datetime import datetime, timezone
from dotenv import load_dotenv
from langchain_anthropic import ChatAnthropic
from indexar_corpus import crear_embeddings, cargar_vectorstore  # Embeddings de Gemini y el índice del Bloque 24
from recuperar_contexto import formatear_contexto  # Contexto numerado y citas del Bloque 26

ARCHIVO_REGISTROS = "docs/registros_latencia_costo.jsonl"

# Claude Opus 5.5, el modelo del proyecto (docs/decision-arquitectura.md). Tarifas en USD por millón de tokens,
# de la página oficial de precios de Anthropic
MODELO = "claude-opus-5-5"
TARIFA_ENTRADA_X1M = 4.0
TARIFA_SALIDA_X1M = 20.0

# Plantilla de la clase: obliga a usar SOLO el contexto recuperado y a citar [1], [2]
PROMPT_TEMPLATE = """Responde la pregunta usando SOLO el contexto de abajo. Cita la \
fuente de cada afirmacion con su numero entre corchetes, como [1]. Si el contexto no \
alcanza para responder, dilo explicitamente en vez de inventar.

Contexto:
{contexto}

Pregunta: {pregunta}

Respuesta:"""


def aprox_tokens(texto: str) -> int:
    # Aproximación de la clase: unos 4 caracteres por token. Solo para comparar tamaños; el costo usa los tokens reales
    return len(texto) // 4


@contextmanager
def medir(tiempos: dict, etapa: str):
    """Cronometra el bloque de código dentro del with y guarda los segundos en tiempos[etapa]."""
    inicio = time.perf_counter()  # 1. Antes del bloque
    yield  # 2. Corre el código que está dentro del with
    tiempos[etapa] = time.perf_counter() - inicio  # 3. Después del bloque


def calcular_costo(tokens_entrada: int, tokens_salida: int,
                   tarifa_entrada_x1M: float = TARIFA_ENTRADA_X1M,
                   tarifa_salida_x1M: float = TARIFA_SALIDA_X1M) -> float:
    """Costo en USD de una llamada, a partir de los tokens reales que devolvió el modelo."""
    costo_entrada = (tokens_entrada / 1_000_000) * tarifa_entrada_x1M
    costo_salida = (tokens_salida / 1_000_000) * tarifa_salida_x1M
    return round(costo_entrada + costo_salida, 6)


def extraer_texto(contenido):
    # Con Claude, la respuesta llega como una lista de bloques: el razonamiento (thinking) y el texto
    if isinstance(contenido, str):
        return contenido
    texto = ""
    for bloque in contenido:
        if bloque.get("type") == "text":
            texto += bloque["text"]
    return texto


def registrar_consulta(vectorstore, modelo, pregunta: str, k: int = 3) -> dict:
    """
    Corre una consulta RAG real de punta a punta (recuperación, prompt con contexto y generación con Claude),
    midiendo el tiempo de cada etapa y los tokens reales de la respuesta.
    """
    tiempos = {}

    # Etapa 1: embedding de la pregunta (Gemini) y búsqueda en Chroma
    with medir(tiempos, "embed_y_busqueda"):
        retriever = vectorstore.as_retriever(search_kwargs={"k": k})
        chunks = retriever.invoke(pregunta)

    # Etapa 2: armado del prompt con los chunks numerados (local)
    with medir(tiempos, "armado_prompt"):
        contexto, citas = formatear_contexto(chunks)
        prompt = PROMPT_TEMPLATE.format(contexto=contexto, pregunta=pregunta)

    # Etapa 3: generación de la respuesta con Claude
    with medir(tiempos, "generacion"):
        respuesta = modelo.invoke(prompt)

    # usage_metadata trae los tokens reales. Con Claude, output_tokens incluye los del razonamiento, que también se cobran
    tokens = dict(respuesta.usage_metadata) if respuesta.usage_metadata else None
    costo_usd = None
    if tokens:
        costo_usd = calcular_costo(tokens.get("input_tokens", 0), tokens.get("output_tokens", 0))

    return {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "pregunta": pregunta,
        "k": k,
        "modelo": MODELO,
        "tiempos_ms": {etapa: round(segundos * 1000, 2) for etapa, segundos in tiempos.items()},
        "tiempo_total_ms": round(sum(tiempos.values()) * 1000, 2),
        "tokens": tokens,
        "costo_estimado_usd": costo_usd,
        # Cuánto creció el texto que recibe el modelo, respecto de la pregunta sola
        "factor_crecimiento": round(len(prompt) / len(pregunta), 1),
        "tokens_aprox_prompt": aprox_tokens(prompt),
        "ids_recuperados": [c.id for c in chunks],
        "citas_disponibles": citas,
        "respuesta_generada": extraer_texto(respuesta.content),
    }


def guardar_registro_jsonl(registro: dict, ruta_archivo: str = ARCHIVO_REGISTROS) -> None:
    """Agrega el registro al final del archivo, en una sola línea (formato JSON Lines)."""
    with open(ruta_archivo, "a", encoding="utf-8") as f:
        f.write(json.dumps(registro, ensure_ascii=False) + "\n")


def leer_registros(ruta_archivo: str = ARCHIVO_REGISTROS) -> None:
    """Imprime lo esencial de cada corrida guardada, como leer_registros.py del curso."""
    with open(ruta_archivo, encoding="utf-8") as f:
        for linea in f:
            r = json.loads(linea)
            tokens_entrada = r["tokens"]["input_tokens"] if r["tokens"] else None
            print(f"k={r['k']} input_tokens={tokens_entrada} generacion={r['tiempos_ms']['generacion']} ms "
                  f"total={r['tiempo_total_ms']} ms costo=US${r['costo_estimado_usd']} {r['pregunta'][:45]}")


if __name__ == "__main__":
    load_dotenv()
    vectorstore = cargar_vectorstore(crear_embeddings())
    modelo = ChatAnthropic(model=MODELO, max_tokens=2000, anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"))

    # 3 preguntas distintas del conjunto de evaluación del Bloque 27 con k=3, y la primera otra vez con k=6
    # para comprobar que más chunks significan más tokens de entrada (más costo)
    corridas = [
        ("¿Qué pasa si la clasificación del mensaje falla?", 3),
        ("¿Cuánto cuesta evaluar una propiedad y cuánto se demora?", 3),
        ("¿Qué acciones del agente necesitan que un coordinador las apruebe?", 3),
        ("¿Qué pasa si la clasificación del mensaje falla?", 6),
    ]

    for pregunta, k in corridas:
        registro = registrar_consulta(vectorstore, modelo, pregunta, k)
        guardar_registro_jsonl(registro)
        print(json.dumps(registro, indent=2, ensure_ascii=False))
        print()

    print(f"--- Resumen de {ARCHIVO_REGISTROS} ---")
    leer_registros()
