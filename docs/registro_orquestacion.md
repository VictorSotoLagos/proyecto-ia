## Registro del manejo de errores en el flujo orquestado

- Fecha: 2026-11-04
- Comando: `python src/enrutamiento_solicitudes.py` (modelo principal `claude-opus-5-5`, modelo de respaldo `claude-haiku-5-5`, con LangChain)
- Pruebas: `pytest` (`tests/test_orquestacion.py` para los fallos simulados y `tests/test_enrutamiento_solicitudes.py` para el camino normal; ninguna usa la API)

### Qué hace

El flujo de enrutamiento del Bloque 19 (clasificación → `direccion`, `busqueda` u `otro`) ahora tiene tres capas de protección, para que un fallo en cualquier paso no detenga el programa sin dar una respuesta:

| Capa | Dónde | Qué pasa si falla el paso |
|---|---|---|
| 1. Modelo secundario | Cada una de las 3 rutas, con `with_fallbacks` | La misma ruta, con el mismo prompt, se repite con Claude Haiku 5.5 |
| 2. Respuesta genérica | Cada una de las 3 rutas, segundo elemento de `with_fallbacks` | Si Haiku también falla, `respuesta_generica` (un `RunnableLambda`) entrega un texto fijo |
| 3. `try/except` general | `procesar_mensaje_seguro(cadena, mensaje)`, alrededor de `.invoke()` | Atrapa cualquier error que las capas 1 y 2 no cubren, lo registra con `logger.error` y devuelve un mensaje seguro |

- `construir_ruta_segura(ruta, ruta_secundaria)` devuelve `ruta.with_fallbacks([ruta_secundaria, respuesta_generica])`. LangChain prueba las alternativas en orden y se detiene en la primera que funciona.
- `procesar_mensaje_seguro` recibe la cadena como parámetro, como pide la actividad, para poder pasarle una cadena falsa en las pruebas.

### Resultado

La corrida se hizo con una clave falsa (`ANTHROPIC_API_KEY=clave-falsa-para-probar-fallback`), para provocar un error real de la API sin costo:

```
ERROR:__main__:Error procesando mensaje: Error code: 401 - {'type': 'error', 'error': {'type': 'authentication_error', 'message': 'invalid x-api-key'}, ...}
ERROR:__main__:Error procesando mensaje: Error code: 401 - ...
ERROR:__main__:Error procesando mensaje: Error code: 401 - ...
Mensaje: Revisa la casa de Almirante Barroso 256, en Barrio Brasil.
No pudimos procesar tu mensaje en este momento. Intenta de nuevo más tarde.

Mensaje: Dame una casa en Barrio Brasil de un piso, con ventanas tapiadas y malezas.
No pudimos procesar tu mensaje en este momento. Intenta de nuevo más tarde.

Mensaje: Hola, ¿quién creó esta aplicación?
No pudimos procesar tu mensaje en este momento. Intenta de nuevo más tarde.
```

Con la clave falsa falla primero la clasificación, antes de que `RunnableBranch` elija una ruta, así que actúa la capa 3. Para ver las capas 1 y 2, se invocó la ruta de dirección protegida directamente, con la misma clave falsa en Opus y en Haiku:

```
No pudimos revisar tu solicitud en este momento. La Comunidad Brasil Alameda la va a revisar y te responderá pronto.
```

Fallaron los dos modelos (error 401) y la ruta entregó `respuesta_generica` sin lanzar ningún error.

### Checklist del Bloque 20

| Pregunta | Respuesta | Prueba |
|---|---|---|
| ¿La clasificación tiene una prueba de normalización? | Sí | `test_clasificacion_normaliza_antes_de_comparar` |
| ¿Cada ruta tiene su propia prueba de enrutamiento, incluida la ruta por defecto? | Sí | `test_enrutamiento_va_a_cadena_direccion`, `test_enrutamiento_va_a_cadena_busqueda`, `test_enrutamiento_usa_default_ante_categoria_desconocida` |
| ¿Al menos una ruta tiene un `with_fallbacks` probado, y la prueba confirma que el fallback se ejecuta? | Sí, las 3 rutas usan `construir_ruta_segura`. Las pruebas comparan el resultado con la respuesta de cada respaldo | `test_ruta_usa_modelo_secundario_ante_fallo_del_principal`, `test_ruta_usa_respuesta_generica_si_fallan_los_dos_modelos` |
| ¿El `try/except` general tiene una prueba que simule un fallo fuera de las rutas? | Sí, un fallo en la clasificación | `test_procesar_mensaje_seguro_no_propaga_excepciones` |

Los fallos se simulan con un `RunnableLambda` real que lanza `ConnectionError`, no con un `MagicMock`, como recomienda el curso. En la prueba del `try/except` la clasificación es un `MagicMock` con `side_effect`.

### Observaciones

- La clasificación no tiene `with_fallbacks`: si falla, ninguna ruta llega a ejecutarse, y el mensaje pasa directo a la capa 3. Por eso la corrida con clave falsa terminó en "No pudimos procesar tu mensaje" y no en el texto de las rutas.
- El error queda registrado con `logger.error` (nivel `ERROR`), así el flujo no se cae pero tampoco oculta el problema.
- Haiku 5.5 se descartó como modelo principal en el Gate 1 porque, al evaluar fotos, no siempre detectó el techo caído ([decision-arquitectura.md](decision-arquitectura.md)). Aquí solo actúa como respaldo de rutas de texto (extraer una dirección o criterios de búsqueda, o responder un saludo), que son tareas más simples.
- Se usa el mismo ID de modelo que `src/medir_latencia.py` (`claude-haiku-5-5`), que funcionó en el Gate 1. Si el ID estuviera mal escrito, el respaldo fallaría siempre y el usuario recibiría el texto genérico sin aviso. La respuesta real de Haiku como respaldo no se ha probado con la clave verdadera.
- `with_fallbacks` solo reacciona a errores, no a demoras: si un modelo se queda esperando sin responder, el respaldo no se activa. El curso menciona el parámetro `timeout` del modelo para eso; no se configuró.
