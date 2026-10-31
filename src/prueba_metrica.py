# ARCHIVO TEMPORAL: ejemplo de la lección "Cuando la métrica engaña" (Bloque 15)
# Mide qué proporción de las palabras de la referencia aparece también en la respuesta

from pipeline_texto import procesar_texto

referencia = "El cielo es azul."
respuesta = "el cielo es azul"

tokens_referencia = procesar_texto(referencia)
tokens_respuesta = procesar_texto(respuesta)

# set() quita las palabras repetidas y & deja solo las que están en los dos conjuntos
comunes = set(tokens_referencia) & set(tokens_respuesta)

# Si la referencia quedó vacía (por ejemplo, era solo puntuación), se evita dividir por cero
if tokens_referencia:
    proporcion = len(comunes) / len(set(tokens_referencia))
else:
    proporcion = 0.0

print(f"Coincidencia: {proporcion:.0%}")  # :.0% muestra el número como porcentaje sin decimales
