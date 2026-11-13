## Registro del agente de la Comunidad Brasil Alameda

- Corridas: una el 2026-11-10 y dos el 2026-11-13
- Comando: `python src/agente_comunidad.py` (modelo `claude-opus-5-5`, con `langchain-classic` 1.0.8; entre 6 y 8 consultas por corrida, de 10 a 14 llamadas a la API cada una)
- Pruebas: `pytest` (`tests/test_agente_comunidad.py`: herramientas, notas, aprobación, memoria y traza; ninguna usa la API)
- Traza: `trazas_agente.jsonl`, una línea por consulta. Los límites de autonomía están en [limites_autonomia_agente.md](limites_autonomia_agente.md)

### Qué hace

A diferencia de la chain de enrutamiento del Bloque 19, que sigue un camino fijo, aquí el modelo decide qué herramienta usar, y `AgentExecutor` repite el ciclo razonar → actuar → observar hasta tener una respuesta.

| Herramienta | Cuándo la usa el agente (según su docstring) | Argumentos | Riesgo |
|---|---|---|---|
| `consultar_propiedad` | El vecino da una dirección y pregunta por su estado | `direccion` | Bajo |
| `buscar_propiedades` | El vecino pide encontrar propiedades con ciertas características, sin dar una dirección | `barrio`, `pisos`, `senal`, con `args_schema` (`CriteriosBusqueda`, de `pydantic`) | Bajo |
| `guardar_nota_vecino` | El vecino pide anotar algo que vio en la fachada de una propiedad | `direccion`, `nota`, con `args_schema` (`ArgumentosNota`) | Medio: escribe en el registro, pero `borrar_nota` la deshace |
| `reportar_a_municipalidad` | Solo si el vecino pide explícitamente reportar una propiedad | `direccion`, `motivo`, con `args_schema` (`ArgumentosReporte`) | Alto: pide aprobación humana |

- El registro de propiedades es un diccionario en memoria (`PROPIEDADES`), como `ESTADOS` en la clase. Por ahora tiene una sola propiedad real: Almirante Barroso 256, con la evaluación de su foto del Gate 1 (las 8 señales, 1 piso, evidencia "muy fuerte"). Una búsqueda en noticias (2026-11-10) no encontró direcciones públicas con número de otras propiedades abandonadas del barrio.
- Cada propiedad tiene una lista de `notas`. `guardar_nota_vecino` agrega una, con su fecha y hora, y `consultar_propiedad` las muestra. `borrar_nota(direccion, numero)` no es una herramienta del agente: la usa un coordinador para deshacer una nota equivocada.
- La memoria guarda un historial por vecino (`session_id`) con `RunnableWithMessageHistory`. El prompt tiene `chat_history` antes del mensaje del vecino y `agent_scratchpad` después.
- `return_intermediate_steps=True` permite ver qué herramienta eligió el agente y con qué argumentos.

### Resultado: corrida 1 (2026-11-10, líneas 1 a 6 de la traza)

| # | Sesión | Mensaje | Herramienta elegida (`intermediate_steps`) | Respuesta (resumen) |
|---|---|---|---|---|
| 1 | vecino_1 | ¿En qué estado está la casa de Almirante Barroso 256? | `consultar_propiedad` (`direccion`: "Almirante Barroso 256") | Las 8 señales y evidencia muy fuerte; advierte que la foto es de mayo de 2024 |
| 2 | vecino_1 | ¿Y esa casa tiene grafitis? | ninguna | "Sí", a partir de la respuesta anterior (memoria) |
| 3 | vecino_2 | ¿De qué casa te pregunté recién? | ninguna | "No tengo registro de ninguna pregunta anterior" |
| 4 | vecino_3 | Busca casas de un piso con ventanas tapiadas en Barrio Brasil. | `buscar_propiedades` (`barrio`: "Barrio Brasil", `pisos`: 1, `senal`: "ventanas tapiadas") | Encontró Almirante Barroso 256 |
| 5 | vecino_3 | ¿Cómo me puedo sumar a la Comunidad Brasil Alameda? | `buscar_propiedades`, con los mismos argumentos que en la 4 | Repite el resultado anterior y dice que no tiene información para sumarse |
| 6 | vecino_1 | Quiero reportar a la Municipalidad la casa de Almirante Barroso 256, porque se le cayó el techo. | `reportar_a_municipalidad` | No se envió: nadie respondió la aprobación (ver el documento de límites) |

### Resultado: corrida 2 (2026-11-13, líneas 7 a 12 de la traza)

Mismos mensajes, con un cambio: la pregunta general pasó a una sesión nueva (vecino_4), como la plantea el curso. La aprobación del reporte se respondió con "s" por la entrada estándar (`printf 's\n' | python src/agente_comunidad.py`), con la autorización que el usuario dio en el chat para esta corrida de prueba.

| # | Sesión | Mensaje | Herramienta elegida (`intermediate_steps`) | Respuesta (resumen) |
|---|---|---|---|---|
| 1 | vecino_1 | ¿En qué estado está la casa de Almirante Barroso 256? | `consultar_propiedad` (`direccion`: "Almirante Barroso 256") | Las 8 señales y evidencia muy fuerte; advierte que la foto es de mayo de 2024 |
| 2 | vecino_1 | ¿Y esa casa tiene grafitis? | `consultar_propiedad` (`direccion`: "Almirante Barroso 256") | "Sí". Tomó la dirección del historial, pero esta vez volvió a consultar |
| 3 | vecino_2 | ¿De qué casa te pregunté recién? | ninguna | "No me has preguntado por ninguna casa todavía" |
| 4 | vecino_3 | Busca casas de un piso con ventanas tapiadas en Barrio Brasil. | `buscar_propiedades` (`barrio`: "Barrio Brasil", `pisos`: 1, `senal`: "ventanas tapiadas") | Encontró Almirante Barroso 256 |
| 5 | vecino_4 | ¿Cómo me puedo sumar a la Comunidad Brasil Alameda? | ninguna | Dice que no tiene esa información y no la inventa; explica qué sí puede hacer |
| 6 | vecino_1 | Quiero reportar a la Municipalidad la casa de Almirante Barroso 256, porque se le cayó el techo. | `reportar_a_municipalidad` | Aprobado: "Reporte enviado… (simulado)". El agente le aclara al vecino que el envío fue simulado y le recomienda llamar a Bomberos (132) si hay peligro |

### Resultado: corrida 3 (2026-11-13, líneas 13 a 20 de la traza)

Corrida hecha al agregar la herramienta de riesgo medio, con 2 consultas nuevas antes del reporte. Esta vez no se respondió nada a la aprobación (`python src/agente_comunidad.py < /dev/null`), así que el reporte quedó rechazado.

| # | Sesión | Mensaje | Herramienta elegida (`intermediate_steps`) | Respuesta (resumen) |
|---|---|---|---|---|
| 1 | vecino_1 | ¿En qué estado está la casa de Almirante Barroso 256? | `consultar_propiedad` | Evidencia muy fuerte, 1 piso, Barrio Brasil |
| 2 | vecino_1 | ¿Y esa casa tiene grafitis? | ninguna | "Sí", con la memoria |
| 3 | vecino_2 | ¿De qué casa te pregunté recién? | ninguna | "No veo ninguna pregunta anterior en esta conversación" |
| 4 | vecino_3 | Busca casas de un piso con ventanas tapiadas en Barrio Brasil. | `buscar_propiedades` | Encontró Almirante Barroso 256 |
| 5 | vecino_4 | ¿Cómo me puedo sumar a la Comunidad Brasil Alameda? | ninguna | No tiene esa información y no la inventa |
| 6 | vecino_3 | Anota en Almirante Barroso 256 que hoy vi la puerta tapiada con tablas nuevas. | `guardar_nota_vecino` (`direccion`: "Almirante Barroso 256", `nota`: "Hoy se vio la puerta tapiada con tablas nuevas.") | Confirma que guardó la nota |
| 7 | vecino_5 | ¿Hay notas de vecinos sobre Almirante Barroso 256? | `consultar_propiedad` | Muestra la nota de la consulta 6, con su fecha |
| 8 | vecino_1 | Quiero reportar a la Municipalidad la casa de Almirante Barroso 256, porque se le cayó el techo. | `reportar_a_municipalidad` | No se envió: nadie respondió la aprobación |

### Verificación (Bloques 21 y 22)

- **Cada herramienta se dispara con su propia entrada:** en las tres corridas, la consulta de estado eligió `consultar_propiedad`, la búsqueda `buscar_propiedades` y el pedido de reporte `reportar_a_municipalidad`. En la corrida 3, el pedido de anotar eligió `guardar_nota_vecino`. Todas con los argumentos correctos.
- **La nota queda en el registro de la comunidad, no en la memoria de un vecino:** vecino_5 vio la nota que dejó vecino_3, mientras que vecino_2 no supo nada de la conversación de vecino_1. El registro es compartido; el historial de la conversación, no.
- **Memoria de dos turnos:** en la consulta 2 de ambas corridas, "esa casa" se entendió como Almirante Barroso 256 sin repetir la dirección. En la corrida 1 respondió solo con el historial; en la 2 usó la dirección del historial para volver a consultar.
- **Dos sesiones no se mezclan:** en las dos corridas, vecino_2 no supo de qué casa preguntó vecino_1. La prueba `test_dos_sesiones_no_comparten_historial` lo confirma sin usar la API.
- **Sin herramienta cuando no se necesita:** se cumplió en las corridas 2 y 3, con la pregunta general en una sesión nueva (vecino_4, `intermediate_steps` vacío). En la corrida 1, con la misma pregunta dentro de la sesión de una búsqueda anterior, no se cumplió. Ver Observaciones.

### Observaciones

- **El agente repitió una herramienta que no necesitaba (consulta 5).** La memoria guarda solo el texto de las respuestas, no qué herramientas se usaron. Al leer su respuesta anterior en el historial, el agente creyó que la había dado sin consultar el registro ("En mi mensaje anterior te di ese resultado sin haber consultado el registro"), lo que es falso, porque en la 4 sí consultó. Por eso repitió la búsqueda. El problema no está en el docstring, porque la pregunta no tiene nada que ver con buscar propiedades: en la corrida 2, la misma pregunta en una sesión nueva no usó ninguna herramienta. En la corrida 2 apareció una variante más leve: en la consulta 2 volvió a llamar a `consultar_propiedad` con los mismos argumentos de la 1, aunque esta vez la respuesta sí fue correcta. El caso queda como ejemplo de revisión de trazas en el documento de límites.
- **La decisión de usar una herramienta varía entre corridas:** con los mismos mensajes, la consulta 2 se respondió sin herramientas en las corridas 1 y 3, y con `consultar_propiedad` en la 2. Por eso la verificación se hace mirando `intermediate_steps` en cada corrida, no solo la respuesta final.
- **La respuesta final con Claude:** llega como una lista de bloques, con el razonamiento (*thinking*) primero y el texto después. Por eso `extraer_texto` busca el bloque de tipo `"text"`, en vez de leer `["output"][0]["text"]` como en el ejemplo de la clase con Gemini.
- **Sin `verbose=True`:** con Claude imprimiría también los bloques de razonamiento, que son muy largos. Los pasos quedan en `trazas_agente.jsonl`.
- **Advertencia de LangChain:** `InMemoryChatMessageHistory` está marcada como obsoleta desde LangChain 1.6.4 y se eliminará en la 2.0. Se usa igual porque es la que enseña el curso. Además, el historial se pierde al cerrar el programa.
- **Un intento fallido antes de la corrida 2:** el 2026-11-12, la corrida falló en la primera llamada con el error 401 `invalid x-api-key`, porque la clave de API había vencido (duraba 30 días). No se gastó nada y no se escribió en la traza. Con una clave nueva, la corrida se repitió el 2026-11-13.
