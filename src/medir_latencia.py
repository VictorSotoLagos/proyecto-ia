import time

from consumir_claude import armar_peticion, enviar_peticion, extraer_texto, calcular_costo

def medir_latencia(pregunta, modelo, precio_entrada, precio_salida):
    latencias = []
    costos = []
    for i in range(4):
        url, headers, body = armar_peticion(pregunta)
        body["model"] = modelo  # cambiamos el modelo que se va a medir
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


# Misma pregunta de prueba para los tres modelos
pregunta = "Analiza esta fachada de una casona en Av. Brasil, Santiago: ventanas tapiadas con tablas, grafitis en el portón, pintura descascarada y vegetación creciendo en el techo. ¿Qué señales de posible abandono ves y qué tan fuerte es la evidencia? Responde en máximo 5 líneas."

# Precios en USD por millón de tokens (página de precios de Anthropic, revisada el 2026-10-20)
medir_latencia(pregunta, "claude-haiku-5-5", 0.10, 0.50)
medir_latencia(pregunta, "claude-sonnet-5-5", 2.00, 10.00)
medir_latencia(pregunta, "claude-opus-5-5", 4.00, 20.00)
