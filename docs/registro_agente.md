## Registro del agente de la Comunidad Brasil Alameda

- Fecha de la corrida: 2026-11-10
- Comando: `python src/agente_comunidad.py` (modelo `claude-opus-5-5`, con `langchain-classic` 1.0.8; 6 consultas, unas 10 llamadas a la API)
- Pruebas: `pytest` (`tests/test_agente_comunidad.py`: herramientas, aprobación, memoria y traza; ninguna usa la API)
- Traza: `trazas_agente.jsonl`, una línea por consulta. Los límites de autonomía están en [limites_autonomia_agente.md](limites_autonomia_agente.md)

### Qué hace

A diferencia de la chain de enrutamiento del Bloque 19, que sigue un camino fijo, aquí el modelo decide qué herramienta usar, y `AgentExecutor` repite el ciclo razonar → actuar → observar hasta tener una respuesta.

| Herramienta | Cuándo la usa el agente (según su docstring) | Argumentos | Riesgo |
|---|---|---|---|
| `consultar_propiedad` | El vecino da una dirección y pregunta por su estado | `direccion` | Bajo |
| `buscar_propiedades` | El vecino pide encontrar propiedades con ciertas características, sin dar una dirección | `barrio`, `pisos`, `senal`, con `args_schema` (`CriteriosBusqueda`, de `pydantic`) | Bajo |
| `reportar_a_municipalidad` | Solo si el vecino pide explícitamente reportar una propiedad | `direccion`, `motivo`, con `args_schema` (`ArgumentosReporte`) | Alto: pide aprobación humana |

- El registro de propiedades es un diccionario en memoria (`PROPIEDADES`), como `ESTADOS` en la clase. Por ahora tiene una sola propiedad real: Almirante Barroso 256, con la evaluación de su foto del Gate 1 (las 8 señales, 1 piso, evidencia "muy fuerte"). Una búsqueda en noticias (2026-11-10) no encontró direcciones públicas con número de otras propiedades abandonadas del barrio.
- La memoria guarda un historial por vecino (`session_id`) con `RunnableWithMessageHistory`. El prompt tiene `chat_history` antes del mensaje del vecino y `agent_scratchpad` después.
- `return_intermediate_steps=True` permite ver qué herramienta eligió el agente y con qué argumentos.

### Resultado

| # | Sesión | Mensaje | Herramienta elegida (`intermediate_steps`) | Respuesta (resumen) |
|---|---|---|---|---|
| 1 | vecino_1 | ¿En qué estado está la casa de Almirante Barroso 256? | `consultar_propiedad` (`direccion`: "Almirante Barroso 256") | Las 8 señales y evidencia muy fuerte; advierte que la foto es de mayo de 2024 |
| 2 | vecino_1 | ¿Y esa casa tiene grafitis? | ninguna | "Sí", a partir de la respuesta anterior (memoria) |
| 3 | vecino_2 | ¿De qué casa te pregunté recién? | ninguna | "No tengo registro de ninguna pregunta anterior" |
| 4 | vecino_3 | Busca casas de un piso con ventanas tapiadas en Barrio Brasil. | `buscar_propiedades` (`barrio`: "Barrio Brasil", `pisos`: 1, `senal`: "ventanas tapiadas") | Encontró Almirante Barroso 256 |
| 5 | vecino_3 | ¿Cómo me puedo sumar a la Comunidad Brasil Alameda? | `buscar_propiedades`, con los mismos argumentos que en la 4 | Repite el resultado anterior y dice que no tiene información para sumarse |
| 6 | vecino_1 | Quiero reportar a la Municipalidad la casa de Almirante Barroso 256, porque se le cayó el techo. | `reportar_a_municipalidad` | No se envió: nadie respondió la aprobación (ver el documento de límites) |

### Verificación (Bloques 21 y 22)

- **Cada herramienta se dispara con su propia entrada:** la 1 eligió `consultar_propiedad`, la 4 `buscar_propiedades` y la 6 `reportar_a_municipalidad`, cada una con los argumentos correctos.
- **Memoria de dos turnos:** en la 2, "esa casa" se entendió como Almirante Barroso 256 sin repetir la dirección y sin volver a consultar.
- **Dos sesiones no se mezclan:** vecino_2 (3) no supo de qué casa preguntó vecino_1. La prueba `test_dos_sesiones_no_comparten_historial` lo confirma sin usar la API.
- **Sin herramienta cuando no se necesita:** no se cumplió en la 5. Ver Observaciones.

### Observaciones

- **El agente repitió una herramienta que no necesitaba (consulta 5).** La memoria guarda solo el texto de las respuestas, no qué herramientas se usaron. Al leer su respuesta anterior en el historial, el agente creyó que la había dado sin consultar el registro ("En mi mensaje anterior te di ese resultado sin haber consultado el registro"), lo que es falso, porque en la 4 sí consultó. Por eso repitió la búsqueda. El problema no está en el docstring, porque la pregunta no tiene nada que ver con buscar propiedades. Para la próxima corrida, la pregunta general quedó en una sesión nueva (vecino_4), como la plantea el curso. El caso queda como ejemplo de revisión de trazas en el documento de límites.
- **La respuesta final con Claude:** llega como una lista de bloques, con el razonamiento (*thinking*) primero y el texto después. Por eso `extraer_texto` busca el bloque de tipo `"text"`, en vez de leer `["output"][0]["text"]` como en el ejemplo de la clase con Gemini.
- **Sin `verbose=True`:** con Claude imprimiría también los bloques de razonamiento, que son muy largos. Los pasos quedan en `trazas_agente.jsonl`.
- **Advertencia de LangChain:** `InMemoryChatMessageHistory` está marcada como obsoleta desde LangChain 1.6.4 y se eliminará en la 2.0. Se usa igual porque es la que enseña el curso. Además, el historial se pierde al cerrar el programa.
- **Segunda corrida pendiente:** el 2026-11-12, la segunda corrida (con la pregunta general en una sesión nueva y la aprobación del reporte) falló en la primera llamada con el error 401 `invalid x-api-key`. La clave del `.env` no cambió, pero dejó de ser válida. No se gastó nada y no se escribió en la traza. Hay que repetirla con una clave nueva.
