# Decision de personalizacion

## 1. El problema
La miniaplicación clasifica cada mensaje de un vecino como direccion, busqueda u otro para elegir su ruta, y la etiqueta tiene que llegar exacta: con tilde o con texto extra, el mensaje cae sin aviso en la ruta equivocada. Hoy la clasificación la hace Claude Opus 5.5 con un prompt, y en una muestra de 20 respuestas reales (docs/muestra_formato_clasificacion.json) 0 fallaron el formato y 0 tuvieron la categoría equivocada.

## 2. Resultado del metodo de decision
- RAG: 0 puntos
- Fine-tuning completo: 0 puntos
- PEFT: 0 puntos

**Empate entre: RAG, Fine-tuning completo, PEFT**

Respuestas del método, con la evidencia de cada una (`src/decision.py`):

| Pregunta | Respuesta | Evidencia |
|---|---|---|
| `informacion_cambia_seguido` | False | Las 3 categorías y las 3 etiquetas de barrio están en `src/prompts/banco.py` desde el 22-10-2026, y el enrutador usa las mismas desde el 04-11-2026: 0 cambios desde entonces. |
| `problema_de_formato_o_tono` | False | En una muestra de 20 respuestas reales del clasificador del enrutador (`src/muestra_formato.py`, 22-11-2026), 0 fallaron el formato. El umbral es 3 de 20. |
| `dataset_grande_y_de_calidad` | False | Hay 15 ejemplos etiquetados (`src/dataset_tuning.py`), y el umbral es 200. |
| `presupuesto_limitado_o_iterar_rapido` | False | El presupuesto alcanza para más de 2 entrenamientos: cada uno costó cerca de US$0,01 y tardó 27 minutos (`docs/registro_tuning.md`). No se necesita ver el efecto en menos de un día. |
| `necesita_multiples_variantes` | False | Hay un solo clasificador para los 2 barrios y las 3 categorías. |

## 3. Tecnica elegida y por que
El método terminó en un empate triple en 0 puntos: ninguna de las cinco preguntas dio una señal a favor de personalizar, así que el puntaje no decide por mí.

**Decisión: no personalizo el modelo por ahora y mantengo el prompt actual.** Hoy el problema no aparece (0 de 20 respuestas fallaron el formato), así que pagar el costo en datos, cómputo y tiempo de cualquiera de las tres técnicas no corregiría nada. Clasificar tampoco es caro: las 20 respuestas de la muestra costaron US$0,019, cerca de US$0,001 cada una.

- **Descarto RAG**, porque al clasificador no le falta información: las categorías son fijas y el barrio sale del propio mensaje, no de un documento que cambie.
- **Descarto el fine-tuning completo**, porque necesita todavía más ejemplos y cómputo que PEFT, y la salida es una sola palabra.
- **PEFT queda como técnica de reserva**, para el día en que la clasificación pase a un modelo más barato que no cumpla el formato. Corrí el método otra vez cambiando solo la respuesta más dudosa: si `problema_de_formato_o_tono` fuera True, PEFT ganaría con 2 puntos, contra 1 del fine-tuning completo y 0 de RAG. Ese caso ya se vio en el Bloque 29: `gemini-3.5-flash-lite`, ajustado con 15 ejemplos, no devolvió el formato en ninguno de 3 mensajes nuevos (`docs/registro_tuning.md`).

## 4. Que necesitarias para ejecutarla
Hoy no hay nada que ejecutar. Para usar PEFT, la técnica de reserva, haría falta lo siguiente:

- **Ejemplos:** tengo 15 ejemplos etiquetados, 5 por categoría. El método pide al menos 200, así que con unos 67 por categoría (201 en total) me faltan 62 de cada una, 186 en total. A 5 minutos por ejemplo, la tasa de la lección, son unas 15,5 horas de etiquetado.
- **Calidad:** antes de entrenar, revisaría 20 ejemplos al azar para confirmar que ninguno tiene etiquetas contradictorias.
- **Cómputo y tiempo:** cada intento de entrenamiento tardó 27 minutos. Los 15 ejemplos actuales suman 474 tokens, unos 32 por ejemplo, así que 201 ejemplos serían unos 6.400 tokens por época. Con 5 épocas son unos 32.000 tokens, cerca de US$0,16 a la tarifa que Google publica para el tuning de Gemini 2.5 (US$5 por millón).
- **Corpus:** no necesito un corpus para indexar, porque no uso RAG.
- **Condición para empezar:** que una muestra de 20 respuestas del modelo que se quiera usar tenga 3 o más fallas de formato, el umbral del método.
