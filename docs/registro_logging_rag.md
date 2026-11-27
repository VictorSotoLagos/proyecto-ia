# Registro: logging, consumo y filtro de inyección del flujo RAG (Bloque 31)

Actividad del curso: "Instrumenta tu solución con logging y registro de consumo". Archivo: `src/logging_rag.py`, junto a los demás archivos del proyecto. Pruebas: `tests/test_logging_rag.py`.

## Qué hace

| Paso | Función | Qué deja en el log |
|---|---|---|
| 1. Logging estructurado | `JsonFormatter` y `trace_id_var` | Cada línea es un JSON con `ts`, `level`, `msg` y el `trace_id` de su consulta |
| 2. Registro de consumo | `registrar_consumo(respuesta)` | Evento `consumo_llm` con los tokens de `usage_metadata` y el costo según las tarifas de Opus (Bloque 28) |
| 3. Filtro de inyección | `filtrar_documentos_sospechosos(documentos)` | Evento `documento_descartado_por_inyeccion` con la fuente y la cantidad de patrones |
| 4. Una consulta completa | `procesar_consulta(pregunta, documentos)` | `consulta_recibida`, los descartes y `contexto_filtrado`, todos con el mismo `trace_id` |

## Cambios respecto del ejemplo del curso

- **Documentos reales.** El filtro revisa `page_content` y lee `metadata["fuente"]`, que es la forma de los chunks que devuelve nuestro Chroma (Bloque 24). La actividad usaba una `namedtuple` con `contenido` y `fuente`, que no calza con un `Document`.
- **También se revisa la pregunta.** Si la búsqueda misma trae un patrón (inyección directa), la consulta se bloquea antes de mirar los documentos, como en la clase de Cynthia (`construir_mensajes`). Esto cubre el RNF-04 de la ficha de diseño.
- **Costo en el consumo.** `registrar_consumo` agrega `costo_estimado_usd` con `calcular_costo` del Bloque 28, para poder saber cuánto costó cada llamada con solo leer los logs.
- **Un contador más.** `contexto_filtrado` también dice cuántos documentos se recuperaron (`n_recuperados`).

## Qué se registra y qué no

De la pregunta se guarda solo su largo (`pregunta_len`). De cada documento descartado, solo su fuente y cuántos patrones coincidieron. Ningún log guarda el texto de la pregunta ni de los documentos. Una prueba lo comprueba.

## Corrida del 2026-11-27 (sin API)

`python src/logging_rag.py` usa una respuesta del modelo y dos documentos armados a mano, así que no gasta nada. Los documentos son un chunk del corpus y una ficha de prueba, en la que el texto de un letrero de la fachada trae un intento de inyección.

```
{"ts": "2026-11-27T18:52:00", "level": "INFO", "msg": "consumo registrado", "trace_id": "trace-prueba-001", "evento": "consumo_llm", "input_tokens": 210, "output_tokens": 18, "total_tokens": 228, "costo_estimado_usd": 0.0012}

{"ts": "2026-11-27T18:52:00", "level": "INFO", "msg": "consulta recibida", "trace_id": "trace-faf91e6e", "evento": "consulta_recibida", "pregunta_len": 29}
{"ts": "2026-11-27T18:52:00", "level": "WARNING", "msg": "documento descartado por inyeccion", "trace_id": "trace-faf91e6e", "evento": "documento_descartado_por_inyeccion", "fuente": "ficha_de_prueba_con_inyeccion", "n_patrones": 3}
{"ts": "2026-11-27T18:52:00", "level": "INFO", "msg": "contexto filtrado", "trace_id": "trace-faf91e6e", "evento": "contexto_filtrado", "n_recuperados": 2, "n_limpios": 1, "n_descartados": 1}
documentos que llegan al prompt: 1

{"ts": "2026-11-27T18:52:00", "level": "INFO", "msg": "consulta recibida", "trace_id": "trace-76a097b7", "evento": "consulta_recibida", "pregunta_len": 42}
{"ts": "2026-11-27T18:52:00", "level": "WARNING", "msg": "consulta bloqueada por inyeccion", "trace_id": "trace-76a097b7", "evento": "consulta_bloqueada_por_inyeccion", "n_patrones": 2}
documentos que llegan al prompt: 0
```

Solo con los logs se puede reconstruir cada consulta:

- **`trace-faf91e6e`:** llegó una pregunta de 29 caracteres y se recuperaron 2 documentos. La ficha de prueba se descartó porque coincidió con 3 patrones, y llegó 1 documento al prompt.
- **`trace-76a097b7`:** la pregunta misma traía 2 patrones, así que se bloqueó y no llegó ningún documento.
- **`trace-prueba-001`:** registró 228 tokens, por un costo estimado de US$0,0012.

Los `trace_id` de las consultas cambian en cada corrida.

## Pruebas

`pytest tests/test_logging_rag.py` corre 9 pruebas, y ninguna llama a una API. Con ellas, el proyecto suma 84 pruebas, y todas pasan.

- Las pruebas 1 a 3 de la actividad:
  - el filtro descarta el documento con inyección y deja pasar el limpio;
  - el consumo trae los tokens exactos, y una respuesta sin `usage_metadata` no rompe nada;
  - cada consulta tiene su propio `trace_id`, que no se mezcla con el de otra.
- Una consulta deja sus 3 eventos con el mismo `trace_id`.
- Una pregunta con inyección se bloquea.
- Los logs no guardan textos completos.
- RNF-04 de la ficha: las 6 búsquedas de prueba con los patrones de la clase se detectan, y las 10 búsquedas normales pasan.

La actividad pide probar con la consola los logs que se ven en ella. Para eso, las pruebas cambian la salida del logger por un `io.StringIO`, un "archivo en memoria" que se puede leer, y al terminar la dejan como estaba.

## Límites y lo que falta

- **El filtro es una lista negra.** Solo reconoce las 6 frases de la clase. Un ataque con sinónimos, en otro idioma o con letras separadas pasa. También podría descartar un documento legítimo que hable de seguridad. Es la primera barrera, no la única: falta la delimitación del contexto en el prompt, que se suma al versionar el prompt en el Bloque 32.
- **No está conectado al flujo real.** Conectarlo es el paso opcional 4 de la actividad, y cuesta una llamada a Opus por consulta. Se conecta en el Gate 2, al unir recuperación, filtro, generación y `registrar_consumo` en un solo servicio.
