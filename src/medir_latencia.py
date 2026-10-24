import time

from consumir_claude import armar_peticion, enviar_peticion, extraer_texto, calcular_costo, leer_imagen_base64

def medir_latencia(pregunta, system_instruction, imagen_b64, modelo, precio_entrada, precio_salida):
    latencias = []
    costos = []
    for i in range(4):
        # armar_peticion envía la foto y la pregunta juntas (sin esquema JSON: aquí se compara texto libre)
        url, headers, body = armar_peticion(modelo, pregunta, system_instruction, imagen_b64=imagen_b64)
        inicio = time.perf_counter()
        respuesta_json = enviar_peticion(url, headers, body)
        fin = time.perf_counter()
        texto = extraer_texto(respuesta_json)  # si la API respondió con un error, se detiene aquí
        costo = calcular_costo(respuesta_json, precio_entrada, precio_salida)
        latencias.append(fin - inicio)
        costos.append(costo)
        print(f"{modelo} - Intento {i + 1}")
        print(f"Latencia: {latencias[-1]:.2f} segundos")
        print(f"Costo: ${costo:.6f} USD")
        print(f"Respuesta: {texto}")
        print()

    latencia_promedio = sum(latencias) / len(latencias)
    costo_promedio = sum(costos) / len(costos)
    print(f"{modelo} - Latencia promedio: {latencia_promedio:.2f} segundos")
    print(f"{modelo} - Costo promedio: ${costo_promedio:.6f} USD")
    print()
    return latencia_promedio, costo_promedio


# Foto real de Google Street View (mayo 2024) de la propiedad de calle Almirante Barroso 256
# (correr este archivo desde la carpeta raíz del proyecto)
imagen_b64 = leer_imagen_base64("docs/fachada-almirante-barroso-256.png")

# Misma pregunta y misma foto para los tres modelos
pregunta = "Analiza esta foto de Google Street View de la fachada de la propiedad de calle Almirante Barroso 256, Barrio Brasil, Santiago. ¿Qué señales de posible abandono ves (por ejemplo: ventanas tapiadas, malezas, grafitis, pintura descascarada) y qué tan fuerte es la evidencia? Responde en máximo 5 líneas."

# Misma instrucción de sistema que usaba armar_peticion antes de recibirla como parámetro
system_instruction = "Eres un experto en arquitectura y urbanismo, con un enorme conocimiento del Barrio Brasil y Concha y Toro de Santiago. Responde forma precisa y concisa, en máximo 5 líneas, y con un lenguaje claro y comprensible para cualquier persona."

# Precios en USD por millón de tokens (página de precios de Anthropic, revisada el 2026-10-20)
try:
    medir_latencia(pregunta, system_instruction, imagen_b64, "claude-haiku-5-5", 0.10, 0.50)
    medir_latencia(pregunta, system_instruction, imagen_b64, "claude-sonnet-5-5", 2.00, 10.00)
    medir_latencia(pregunta, system_instruction, imagen_b64, "claude-opus-5-5", 4.00, 20.00)
except (ValueError, RuntimeError) as error:
    print("No se pudo completar la operación:", error)
