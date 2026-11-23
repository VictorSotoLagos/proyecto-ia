import json
from collections import Counter
from dotenv import load_dotenv
from google import genai
from google.genai import types
from prompts.banco import BANCO_DE_PROMPTS  # El prompt evaluar_fachada del Gate 1
from tuning_peft import PROYECTO_GCP, UBICACION, MODELO_BASE  # El modelo barato que se podría ajustar con PEFT

# Evidencia para la pregunta "problema_de_formato_o_tono" del Bloque 30, en el caso principal de la app:
# evaluar fotos de fachadas con el criterio de abandono de la comunidad. Claude no se puede ajustar, así que se
# mide el modelo de Gemini barato, sin ajuste, con 20 respuestas reales sobre la misma foto
ARCHIVO_RESULTADOS = "docs/muestra_evaluacion_fachada.json"
REPETICIONES = 20
PROMPT = BANCO_DE_PROMPTS[3]  # evaluar_fachada

SENALES_PERMITIDAS = {"ventanas tapiadas", "vanos abiertos o vidrios rotos", "malezas", "grafitis",
                      "pintura descascarada", "revoque caído", "techo dañado", "escombros"}
NIVELES_PERMITIDOS = {"ninguna", "débil", "moderada", "fuerte", "muy fuerte"}
# La señal más grave de Almirante Barroso 256: la casa perdió el techo. Opus la vio en 4 de 4 intentos (Gate 1)
SENAL_MAS_GRAVE = "techo dañado"


def revisar_evaluacion(texto: str) -> dict:
    """Revisa una respuesta con los 4 criterios fijos. La respuesta falla si no cumple alguno."""
    try:
        datos = json.loads(texto)
    except json.JSONDecodeError:
        return {"json_con_claves": False, "senales_permitidas": False, "nivel_permitido": False,
                "ve_techo_danado": False, "cumple": False, "evidencia": None}
    json_con_claves = isinstance(datos, dict) and all(clave in datos for clave in PROMPT["claves_esperadas"])
    senales = datos.get("senales", []) if isinstance(datos, dict) else []
    senales_permitidas = isinstance(senales, list) and all(s in SENALES_PERMITIDAS for s in senales)
    evidencia = datos.get("evidencia") if isinstance(datos, dict) else None
    nivel_permitido = evidencia in NIVELES_PERMITIDOS
    ve_techo_danado = isinstance(senales, list) and SENAL_MAS_GRAVE in senales
    return {
        "json_con_claves": json_con_claves,
        "senales_permitidas": senales_permitidas,
        "nivel_permitido": nivel_permitido,
        "ve_techo_danado": ve_techo_danado,
        "cumple": json_con_claves and senales_permitidas and nivel_permitido and ve_techo_danado,
        "evidencia": evidencia,
    }


def tomar_muestra(client: genai.Client, imagen: bytes, repeticiones: int = REPETICIONES) -> list[dict]:
    """Envía la misma foto y la misma pregunta varias veces y revisa cada respuesta."""
    config = types.GenerateContentConfig(
        system_instruction=PROMPT["system_instruction"],
        response_mime_type="application/json",  # Pide JSON, pero no obliga a usar las claves ni los nombres
    )
    resultados = []
    for _ in range(repeticiones):
        respuesta = client.models.generate_content(
            model=MODELO_BASE,
            contents=[types.Part.from_bytes(data=imagen, mime_type="image/png"), PROMPT["ejemplo_usuario"]],
            config=config,
        )
        uso = respuesta.usage_metadata
        revision = revisar_evaluacion(respuesta.text or "")
        revision["respuesta"] = respuesta.text
        revision["tokens_entrada"] = (uso.prompt_token_count or 0) if uso else 0
        revision["tokens_salida"] = ((uso.candidates_token_count or 0) + (uso.thoughts_token_count or 0)) if uso else 0
        resultados.append(revision)
    return resultados


def resumir(resultados: list[dict]) -> dict:
    return {
        "respuestas": len(resultados),
        "fallas": sum(not r["cumple"] for r in resultados),
        "sin_json_con_claves": sum(not r["json_con_claves"] for r in resultados),
        "con_senales_no_permitidas": sum(not r["senales_permitidas"] for r in resultados),
        "con_nivel_no_permitido": sum(not r["nivel_permitido"] for r in resultados),
        "sin_techo_danado": sum(not r["ve_techo_danado"] for r in resultados),
        "niveles_de_evidencia": dict(Counter(r["evidencia"] for r in resultados)),
        "tokens_entrada_por_respuesta": round(sum(r["tokens_entrada"] for r in resultados) / len(resultados)),
        "tokens_salida_por_respuesta": round(sum(r["tokens_salida"] for r in resultados) / len(resultados)),
    }


if __name__ == "__main__":
    load_dotenv()  # GOOGLE_APPLICATION_CREDENTIALS=credenciales.json: la cuenta de servicio
    client = genai.Client(vertexai=True, project=PROYECTO_GCP, location=UBICACION)
    with open(PROMPT["imagen"], "rb") as f:
        imagen = f.read()

    resultados = tomar_muestra(client, imagen)
    resumen = resumir(resultados)

    for i, r in enumerate(resultados, start=1):
        marca = "OK " if r["cumple"] else "FALLA"
        print(f"{i:2} {marca} | claves: {r['json_con_claves']} | señales permitidas: {r['senales_permitidas']} | "
              f"nivel: {r['evidencia']} | ve el techo: {r['ve_techo_danado']}")
    print("\n", resumen)

    with open(ARCHIVO_RESULTADOS, "w", encoding="utf-8") as f:
        json.dump({"modelo": MODELO_BASE, "foto": PROMPT["imagen"], "resumen": resumen, "resultados": resultados},
                  f, indent=2, ensure_ascii=False)
    print("Resultados guardados en", ARCHIVO_RESULTADOS)
