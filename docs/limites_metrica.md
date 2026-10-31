# Límites de la métrica de evaluación

## Qué mide

Coincidencia de palabras entre una respuesta generada y una referencia escrita a mano, contando repeticiones, después de pasar ambos textos por `procesar_texto` (precisión, cobertura y F1, calculados en `src/precision.py`).

## Modos de falla conocidos

- **Respuestas correctas con otras palabras puntúan bajo.** "¿Qué es la tasación de una propiedad?" obtuvo F1 = 0.41, aunque la respuesta era correcta y completa: dijo "valoración" y "valor de mercado" donde la referencia dice "estimación" y "valor comercial". Lo mismo con "mantenimiento" en vez de "mantención" (F1 = 0.36 en "¿Qué diferencia hay entre una propiedad desocupada y una propiedad abandonada?").
- **Respuestas más detalladas que la referencia bajan la precisión.** "¿Qué es el Conservador de Bienes Raíces?" obtuvo F1 = 0.42 (precisión 0.32) por agregar datos correctos que la referencia no tiene, como hipotecas y prohibiciones. En "¿Una propiedad abandonada significa que no tiene dueño o que no tiene ocupantes?" la respuesta era correcta y completa, y obtuvo F1 = 0.32.
- **Un F1 alto puede esconder una omisión.** "¿Qué es la Unidad de Fomento (UF)?" obtuvo F1 = 0.83, pero la respuesta no menciona que la UF se usa para fijar precios de propiedades.
- **Con un F1 bajo, la métrica no distingue una omisión real de una paráfrasis.** El peor caso, "¿Qué señales en la fachada indican que una propiedad no recibe mantención?" (F1 = 0.22), sí tenía un problema real: faltaban los rayados. Pero los otros 4 casos de F1 bajo (0.32 a 0.42) eran respuestas correctas.
- **La métrica solo es tan buena como la referencia.** En la tasación y el Conservador de Bienes Raíces, ni la referencia ni la respuesta eran completas. La métrica mide cuánto se parece la respuesta a la referencia, no si la respuesta es buena.
- **No observados en esta muestra, pero conocidos (Bloque 16):** un dato equivocado (una fecha o una cifra) puede obtener un F1 alto si el resto de la oración coincide, y una negación ausente casi no baja el puntaje aunque invierta el significado.

## Muestra revisada

- 2026-10-30: 10 casos revisados a mano (los 5 con menor F1 y los 5 con mayor F1) sobre 26 respuestas de `claude-opus-5-5`, con la rúbrica de corrección factual, completitud y contradicción. Detalle en `docs/revision_manual.json`.
- Resultado: los 10 casos fueron factualmente correctos y ninguno tuvo contradicciones. 2 casos fueron incompletos: el de F1 más bajo (0.22) y uno de F1 alto (0.83).

## Recomendación de uso

Usar el F1 promedio para comparar versiones del prompt o del modelo sobre los mismos 26 casos, no para decidir si una respuesta individual es buena o mala: en esta muestra, un F1 bajo 0.45 casi siempre correspondió a respuestas correctas. Revisar siempre a mano las respuestas que listan señales o requisitos (como las señales de abandono de una fachada), porque las omisiones casi no bajan el puntaje, y las que incluyen fechas, cifras o leyes.
