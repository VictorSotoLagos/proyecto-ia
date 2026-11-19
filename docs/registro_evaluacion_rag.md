## Registro de la evaluación de la recuperación (Bloque 27)

- Fecha: 2026-11-17
- Comando: `python src/evaluacion_recuperacion.py` (retriever real de Chroma sobre `vectorstore/`; 15 llamadas a Gemini por cada k, solo para el embedding de cada pregunta)
- Pruebas: `pytest` (`tests/test_evaluacion_recuperacion.py`: métricas y evaluación con un retriever simulado con `MagicMock`; no gasta tokens)
- Resultados guardados: [resultados_evaluacion.txt](resultados_evaluacion.txt) (k=3) y [resultados_evaluacion_k5.txt](resultados_evaluacion_k5.txt) (k=5)

### Qué hace

- **Conjunto de evaluación:** 15 preguntas sobre el corpus del Bloque 24 (14 chunks), una de ellas sin respuesta en el corpus. Los ids relevantes de cada pregunta se etiquetaron a mano leyendo el texto de cada chunk, **antes** de correr el retriever. Los ids estables del índice (`modelo_1`, `limites_2`…) hacen que las etiquetas se lean fácil.
- **Métricas**, las mismas de la clase:
  - `precision_at_k`: de los k chunks recuperados, qué fracción sirve.
  - `recall_at_k`: de los chunks relevantes, qué fracción se recuperó. Queda en `None` si la pregunta no tiene respuesta en el corpus.
  - `f1_score`: equilibrio entre las dos.
  - `promediar`: ignora los `None`.
- **k en los dos lados:** el mismo k se usa en `as_retriever` y en `evaluar_recuperacion`.
- **Configuración de cada corrida:** se anota en el archivo de resultados (k, `chunk_size` y `chunk_overlap`, leídos de `indexar_corpus.py`). Así se puede comparar con corridas futuras.

### Resultado

| | Precisión promedio | Recall promedio | F1 promedio |
|---|---|---|---|
| k=3 | 0,311 | 0,929 | 0,486 |
| k=5 | 0,200 | 1,000 | 0,350 |

Con k=3, 13 de las 14 preguntas con respuesta recuperaron su chunk relevante (recall 1,00). La única que falló fue "¿Qué modelo de IA evalúa las fachadas y en qué formato entrega el resultado?" (recall 0,00). Con k=5 se recuperaron todas.

### Cómo se probó (los 3 escenarios de la actividad)

1. **Determinista:** dos corridas seguidas, sin cambiar nada, dieron archivos de resultados idénticos (comparados con `diff`) para k=3 y para k=5.
2. **El trade-off de k:** al pasar de k=3 a k=5, el recall subió (0,929 → 1,000) y la precisión bajó (0,311 → 0,200), como se vio en la primera lección del bloque.
3. **Guardado para comparar:** cada corrida queda en su propio archivo, con la fecha y la configuración.

### Observaciones

- **La pregunta que falló:** con k=5, `objetivo_2` quedó en el cuarto lugar (distancia 0,5711). Por delante quedaron:
  - `senales_1` (0,4117), que describe el JSON que devuelve la evaluación y por eso también responde en parte "en qué formato";
  - `formas_de_uso_1` (0,4467);
  - `objetivo_1` (0,5147).

  Hay dos causas probables: la pregunta mezcla dos temas (el modelo y el formato), y `objetivo_2` es el chunk más corto del corpus (105 caracteres), así que tiene poco contenido para parecerse a la pregunta. La etiqueta no se cambió después de ver el resultado, para no maquillar la métrica.
- **La precisión es baja a propósito:** casi todas las preguntas tienen un solo chunk relevante, así que con k=3 la precisión máxima posible es 0,33. Por eso el recall es la métrica que más importa aquí. Como pide el curso, con un solo chunk relevante por pregunta el recall promedio quedó por sobre la precisión promedio.
- **La pregunta sin respuesta** (el horario de la Municipalidad) tiene recall "n/a" y no entra al promedio de recall. Su precisión 0,00 sí entra al promedio de precisión, porque los 3 chunks que trajo no sirven.
- **Una mejora posible para una próxima corrida:** unir el párrafo de `objetivo_2` con el anterior en el corpus, para que no quede un chunk tan corto, y volver a correr la evaluación para comparar con estos archivos.
