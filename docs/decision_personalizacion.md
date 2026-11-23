# Decision de personalizacion

## 1. El problema
Los vecinos van a buscar viviendas por señales de abandono (por ejemplo, "casas de un piso con ventanas tapiadas en Barrio Brasil"), y esas señales salen de evaluar fotos de Google Street View. El modelo no sabe qué casas del barrio ya están evaluadas, con qué señales ni qué anotaron los vecinos, porque ese inventario crece con cada foto evaluada; además, es una demo con presupuesto propio, y evaluar cada foto con Claude Opus 5.5 cuesta US$0,0149 (docs/decision-arquitectura.md).

## 2. Resultado del metodo de decision
- RAG: 5 puntos
- PEFT: 1 puntos
- Fine-tuning completo: 0 puntos

Hay un ganador claro: RAG. Las respuestas del método y la evidencia de cada una están en `src/decision.py`:

| Pregunta | Respuesta | Evidencia |
|---|---|---|
| `informacion_cambia_seguido` | True | Los datos de propiedades que consulta el agente (`src/agente_comunidad.py`) cambiaron en 3 commits en noviembre de 2026 (12, 13 y 14). El inventario crece con cada foto evaluada y con cada nota de un vecino. |
| `problema_de_formato_o_tono` | False | En una muestra de 20 evaluaciones de la foto de Almirante Barroso 256 con `gemini-3.5-flash-lite` sin ajuste (`src/muestra_evaluacion_fachada.py`), 0 fallaron los 4 criterios fijos: JSON con las 5 claves, solo señales permitidas, nivel de evidencia permitido y ver el techo dañado, la señal más grave. Las 20 calificaron la evidencia como "muy fuerte", igual que Opus en el Gate 1. El umbral es 3 de 20. |
| `dataset_grande_y_de_calidad` | False | Hay 1 evaluación de fachada etiquetada, la de Almirante Barroso 256. El umbral es 200. |
| `presupuesto_limitado_o_iterar_rapido` | True | Es una demo con presupuesto propio: alcanza para muestras y para entrenamientos de PEFT de centavos (cerca de US$0,01 cada uno, `docs/registro_tuning.md`), pero no para un fine-tuning completo. Uso este criterio en vez del umbral de 2 intentos, porque el límite real de la demo es el costo de cada técnica. |
| `necesita_multiples_variantes` | False | Hay un solo evaluador de fachadas para los 2 barrios. |

## 3. Tecnica elegida y por que
**Elijo RAG.** Lo que le falta al modelo es información que cambia: qué casas están evaluadas, con qué señales y qué anotaron los vecinos. Sin ese inventario, el modelo responde de memoria y se equivoca; en el Bloque 29, por ejemplo, ubicó Concha y Toro en Puente Alto (`docs/registro_tuning.md`).

- **PEFT no hace falta todavía.** El modelo barato ya aplica el criterio de la comunidad sin ajuste, en 20 de 20 respuestas. Por eso, con el presupuesto de una demo, la evaluación de las fotos puede pasar de Opus a `gemini-3.5-flash-lite` usando solo el prompt.
- **Revisé la respuesta más dudosa**, la del formato. La muestra usó una sola foto, de una casa en ruina evidente. Si con fotos de casas en estados intermedios fallaran 3 o más de 20, `problema_de_formato_o_tono` pasaría a True. Con eso, el método daría RAG 5, PEFT 3 y fine-tuning completo 1: RAG seguiría ganando y PEFT entraría como complemento. RAG serviría para saber qué casas hay, y PEFT para que el modelo barato aplique el criterio igual en cada foto.
- **Descarto el fine-tuning completo**, porque no hay presupuesto para reentrenar el modelo entero ni 200 ejemplos para hacerlo.
- **El clasificador de mensajes no necesita personalización.** Con el prompt actual acertó el formato y la categoría en 20 de 20 respuestas (`docs/muestra_formato_clasificacion.json`).

## 4. Que necesitarias para ejecutarla
**Para RAG**, que es la técnica elegida:
- **Corpus:** hoy hay 1 ficha indexable, la de Almirante Barroso 256. Para la demo propongo cubrir las 64 fachadas del Barrio Concha y Toro, la cifra del programa de recuperación de fachadas del Gobierno de Santiago (julio de 2026), más Almirante Barroso 256. Faltan 64 fichas de 65.
- **Fotos y evaluación:** cada ficha necesita su foto de Street View evaluada. Con Opus, las 64 evaluaciones costarían unos US$0,95 (64 × US$0,0149) y tardarían unos 9 minutos (8,6 segundos cada una). Con `gemini-3.5-flash-lite`, cada evaluación usó 1.371 tokens de entrada y 159 de salida.
- **Notas de los vecinos:** van como documentos adicionales del corpus, cada una con su fecha.
- **Indexación:** se reutiliza lo de la Unidad 2.5 (`src/indexar_corpus.py`: Chroma con embeddings de Gemini). Cada ficha cabe en un chunk, y su barrio, pisos y nivel de evidencia van como metadatos.

**Para PEFT, solo si se cumple la condición de la sección 3:**
- **Ejemplos:** hay 1 evaluación etiquetada. Faltan 199 para llegar a 200, unas 16,6 horas a 5 minutos por ejemplo, la tasa de la lección. Cada ejemplo necesita además su foto en el bucket de Google Cloud.
- **Primer paso:** antes de etiquetar, tomar una muestra de 20 fotos variadas para saber si hace falta.
