## Registro de la latencia y el costo del flujo RAG (CORE del Bloque 28)

- Fecha: 2026-11-19
- Comando: `python src/registro_rag.py` (embeddings `gemini-embedding-001` para la búsqueda; generación con `claude-opus-5-5`, `max_tokens=2000`)
- Pruebas: `pytest` (`tests/test_registro_rag.py`, con el vector store y el modelo simulados con `MagicMock`; no gasta tokens)
- Registros: [registros_latencia_costo.jsonl](registros_latencia_costo.jsonl), una corrida real por línea

### Qué hace

`registrar_consulta` corre el flujo RAG completo y mide el tiempo de cada etapa con el administrador de contexto `medir` de la clase:

| Etapa | Qué incluye | Dónde corre |
|---|---|---|
| `embed_y_busqueda` | Embedding de la pregunta con Gemini y búsqueda de los k chunks en Chroma | Gemini (red) y Chroma (local) |
| `armado_prompt` | `formatear_contexto` y la plantilla de la clase, que obliga a responder solo con el contexto y a citar [1], [2] | Local |
| `generacion` | La respuesta de Claude Opus 5.5 | API de Claude (red) |

- **Tokens reales:** salen de `respuesta.usage_metadata` (`input_tokens`, `output_tokens`, `total_tokens`), no de la aproximación por caracteres. Con Claude, `output_tokens` incluye los tokens del razonamiento, que también se cobran.
- **Costo:** `calcular_costo` usa las tarifas de Claude Opus 5.5: US$4 por millón de tokens de entrada y US$20 por millón de salida. No incluye el embedding de la pregunta en Gemini, que es mucho más barato.
- **Datos extra de cada registro**, además de las claves que pide la actividad (`timestamp`, `pregunta`, `k`, `tiempos_ms`, `tiempo_total_ms` y `tokens`):
  - el modelo;
  - el costo;
  - el factor de crecimiento del prompt respecto de la pregunta;
  - los ids recuperados;
  - las citas;
  - la respuesta.
- Cada registro se agrega como una línea nueva con `guardar_registro_jsonl`, y `leer_registros` imprime el resumen.

### Resultado

```
k=3 input_tokens=437 generacion=5780.88 ms total=6998.01 ms costo=US$0.011208 ¿Qué pasa si la clasificación del mensaje fal
k=3 input_tokens=598 generacion=1374.24 ms total=2324.55 ms costo=US$0.004112 ¿Cuánto cuesta evaluar una propiedad y cuánto
k=3 input_tokens=468 generacion=6354.94 ms total=6767.01 ms costo=US$0.016072 ¿Qué acciones del agente necesitan que un coo
k=6 input_tokens=736 generacion=3529.26 ms total=3921.96 ms costo=US$0.010324 ¿Qué pasa si la clasificación del mensaje fal
```

| # | k | Búsqueda (ms) | Prompt (ms) | Generación (ms) | Tokens entrada / salida | Costo (USD) | Chunks recuperados |
|---|---|---|---|---|---|---|---|
| 1 | 3 | 1217,1 | 0,03 | 5780,9 | 437 / 473 | 0,011208 | errores_2, errores_1, formas_de_uso_2 |
| 2 | 3 | 950,3 | 0,02 | 1374,2 | 598 / 86 | 0,004112 | modelo_1, formas_de_uso_1, objetivo_1 |
| 3 | 3 | 412,1 | 0,02 | 6354,9 | 468 / 710 | 0,016072 | limites_1, limites_2, agente_1 |
| 4 | 6 | 392,7 | 0,02 | 3529,3 | 736 / 369 | 0,010324 | errores_2, errores_1, formas_de_uso_2, limites_1, objetivo_2, modelo_2 |

### Cómo se probó (los 3 escenarios de la actividad)

1. **Al menos 3 preguntas distintas** del conjunto de evaluación del Bloque 27: `registros_latencia_costo.jsonl` quedó con 4 líneas, cada una un JSON completo con las claves que pide la actividad.
2. **Misma pregunta con k=3 y con k=6:** los tokens de entrada subieron de 437 a 736 (+68%). Con más chunks hay más contexto, y por lo tanto más costo de entrada.
3. **La generación es la etapa más lenta** en las 4 corridas: de 1,4 a 6,4 segundos, contra 0,4 a 1,2 segundos de la búsqueda y unos 0,02 ms del armado del prompt.

### Observaciones

- **El costo lo domina la salida, no la entrada.** Los tokens de entrada se mantuvieron entre 437 y 736, pero los de salida variaron de 86 a 710 según cuánto razonó y escribió Claude. La consulta 3 fue la más cara (US$0,016) por su respuesta más larga, y la 4, con k=6, costó menos que la 1 con k=3, porque su respuesta fue más corta. Con un modelo que razona, subir k encarece la entrada, pero el costo total depende sobre todo de la salida.
- **El prompt crece entre 17 y 36 veces respecto de la pregunta sola** (factor de crecimiento): es el contexto recuperado.
- **Las 4 respuestas citan su fuente con [1], [2]**, y responden con el contenido de los chunks recuperados.
- **La latencia de la búsqueda depende de la red:** bajó de 1,2 s en la primera corrida a 0,95 s en la segunda, y a unos 0,4 s en las dos últimas. Probablemente la primera incluye abrir la conexión con Gemini.
- **Costo de toda la corrida:** unos US$0,042 en Claude, más 4 embeddings de Gemini.
- **Una sola corrida no es una muestra representativa**, como advierte el curso. Para estimar el costo típico del flujo conviene repetir con más preguntas, de distinto largo.
