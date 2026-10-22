import json
import time
from prompts.banco import BANCO_DE_PROMPTS
from consumir_claude import MODELO, armar_peticion, enviar_peticion, extraer_texto, parsear_respuesta_json, leer_imagen_base64

registro = {}

try:

    for prompt in BANCO_DE_PROMPTS:
        exitos = 0
        intentos = 3
        # Solo "evaluar_fachada" trae foto; los demás prompts son solo texto
        imagen_b64 = None
        if "imagen" in prompt:
            imagen_b64 = leer_imagen_base64(prompt["imagen"])
        for intento in range(intentos):
            url, headers, body = armar_peticion(
                MODELO,
                prompt["ejemplo_usuario"],
                prompt["system_instruction"],
                prompt["response_schema"],
                imagen_b64
            )
            respuesta = enviar_peticion(url, headers, body)
            texto = extraer_texto(respuesta)
            try:
                datos = parsear_respuesta_json(texto, prompt["claves_esperadas"])
                exitos += 1
                print(f"{prompt['nombre']} - intento {intento + 1}: respuesta válida")
            except ValueError as error:
                print(f" intento {intento + 1} falló: {error}")
            time.sleep(1)
        print(f"{prompt['nombre']}: {exitos}/{intentos} respuestas válidas")
        registro[prompt["nombre"]] = {"exitos": exitos, "intentos": intentos}
    # Cuando termine de recorrer los prompts, guarda los resultados en registro_resultados.json
    with open("src/prompts/registro_resultados.json", "w", encoding="utf-8") as archivo:
        json.dump(registro, archivo, indent=2, ensure_ascii=False)

except (ValueError, RuntimeError) as error:
    print("No se pudo completar la operación:", error)
