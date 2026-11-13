# Límites de autonomía: asistente de la Comunidad Brasil Alameda

Agente de `src/agente_comunidad.py`, que ayuda a los vecinos a revisar propiedades en posible abandono en Barrio Brasil y Concha y Toro. Este documento describe el agente tal como está construido y corrido el 2026-11-10 y el 2026-11-13 (traza real en `trazas_agente.jsonl`, 12 líneas). La corrida y las pruebas están en [registro_agente.md](registro_agente.md).

## Herramientas y nivel de riesgo

- `consultar_propiedad`: **bajo**. Solo lee el registro de evaluaciones de fachadas y no modifica nada. Si el agente la usa mal, el peor resultado es una respuesta equivocada sobre una casa, que el vecino puede comprobar mirando la fachada.
- `buscar_propiedades`: **bajo**. Solo lee y filtra el registro por barrio, pisos y señal. Tampoco modifica nada, ni ejecuta ninguna acción fuera de la aplicación.
- `reportar_a_municipalidad`: **alto**. Es la única acción que sale de la comunidad y no se puede deshacer: una vez enviado, el reporte no se puede retirar. Un reporte equivocado (la dirección que no corresponde, o una casa que sí está habitada) puede afectar a sus dueños o a quienes viven ahí, y le quita credibilidad a la comunidad ante el municipio. Por ahora el envío es **simulado**: la herramienta no envía nada de verdad.

El agente no tiene herramientas de riesgo medio (escritura reversible). Si más adelante se agrega una, por ejemplo guardar la nota de un vecino sobre una casa, iría sin aprobación, porque un error se corrige después; se revisaría con la traza.

## Herramientas que requieren aprobación humana

- `reportar_a_municipalidad`: requiere la aprobación de un coordinador de la comunidad antes de ejecutarse, porque es irreversible y su efecto lo sufren personas externas a la conversación (los dueños o habitantes de la casa), no solo el vecino que lo pide.
  - Cómo funciona: `esperar_aprobacion` muestra en la consola la dirección y el motivo, y espera una respuesta "s" o "n". Si nadie responde en 15 segundos, o no hay una consola desde donde responder, devuelve `False`: ante la duda, el reporte **no** se envía. Usa un hilo aparte, como el ejemplo de la clase, porque el `select.select()` del curso no funciona en Windows.
  - Cada decisión, aprobada o no, se guarda con `registrar_aprobacion` (herramienta, argumentos, resultado y fecha y hora), y la observación que recibe el agente dice si se envió o no.
- `consultar_propiedad` y `buscar_propiedades`: no requieren aprobación. Solo leen, y pedir confirmación para cada consulta haría que quien aprueba deje de leer las solicitudes con atención.

Verificación contra el código (2026-11-12), con el comando de la actividad:

```
$ grep -n "esperar_aprobacion(" src/agente_comunidad.py
95:def esperar_aprobacion(mensaje: str, tiempo_limite_segundos: int = 15) -> bool:
152:    aprobado = esperar_aprobacion(mensaje, tiempo_limite_segundos=15)
```

La línea 95 es la definición, y la 152 es la llamada dentro de `reportar_a_municipalidad`, la única herramienta marcada como alto riesgo. La prueba `test_reporte_no_se_envia_sin_aprobacion_y_queda_registrado` confirma, sin usar la API, que sin aprobación el reporte no se envía y que el rechazo queda registrado.

Los dos resultados posibles quedaron en la traza real:

- **Rechazado (línea 6, 2026-11-10):** no había nadie en la consola, así que se aplicó el valor seguro. La observación dice "El reporte no se envió…" y `registro_aprobaciones` quedó con `'aprobado': False`.
- **Aprobado (línea 12, 2026-11-13):** la observación dice "Reporte enviado a la Municipalidad de Santiago (simulado)…" y `registro_aprobaciones` quedó con `'aprobado': True`. El agente le aclaró al vecino que el envío fue simulado. Esta "s" **no la escribió una persona en vivo**: se envió por la entrada estándar (`printf 's\n' | python src/agente_comunidad.py`), con la autorización que el usuario dio en el chat para esta corrida de prueba. En un uso real, la debe responder un coordinador frente a la consola.

Lo que todavía **no** está resuelto:

- **La aprobación no identifica a quién aprobó:** solo registra que alguien escribió "s" en la consola donde corre el agente. En un uso real, la aprobación debería venir de un coordinador identificado, desde una interfaz aparte.
- **`registro_aprobaciones` vive en memoria** y se pierde al cerrar el programa. Lo único que queda guardado es la observación en `trazas_agente.jsonl`.

## Revisión de trazas

Cada consulta queda como una línea de `trazas_agente.jsonl`, escrita por `registrar_traza`, con `timestamp`, `session_id`, `entrada`, `acciones` (herramienta, argumentos y observación de cada paso) y `respuesta_final`.

- **Frecuencia:**
  - **Todas** las trazas con `reportar_a_municipalidad`, el mismo día en que ocurren, porque cada una es una acción de riesgo alto.
  - Una muestra de **10 consultas por semana**, más cualquier sesión donde un vecino haya reclamado por una respuesta.
- **Qué se busca** (patrones del Bloque 23 aplicados a este agente):
  1. **La misma herramienta repetida con argumentos iguales o parecidos**, dentro de una consulta o **entre consultas seguidas de la misma sesión**. El script `marcar_repeticiones_sospechosas` del curso solo compara herramientas dentro de una misma línea, así que no detectaría el caso que apareció aquí (ver abajo).
  2. **`reportar_a_municipalidad` sin aprobación registrada:** la observación debe decir "Reporte enviado" o "El reporte no se envió", y los argumentos (dirección y motivo) deben corresponder a lo que pidió el vecino.
  3. **Una respuesta final que afirma algo que ninguna observación respalda:** por ejemplo, señales que la herramienta no devolvió, o afirmaciones sobre lo que el propio agente hizo antes.

Revisión de la traza real antes de entregar (2026-11-13):

```
$ wc -l trazas_agente.jsonl
12 trazas_agente.jsonl
$ grep -c '"herramienta": "reportar_a_municipalidad"' trazas_agente.jsonl
2
```

| Línea | Sesión | Herramientas | Resultado de la revisión |
|---|---|---|---|
| 1 | vecino_1 | `consultar_propiedad` | ✅ La respuesta coincide con la observación (8 señales, evidencia muy fuerte) |
| 2 | vecino_1 | ninguna | ✅ Respondió con la memoria; los grafitis sí estaban en la observación de la línea 1 |
| 3 | vecino_2 | ninguna | ✅ No mezcló la sesión con la de vecino_1 |
| 4 | vecino_3 | `buscar_propiedades` | ✅ Argumentos correctos (Barrio Brasil, 1 piso, ventanas tapiadas) |
| 5 | vecino_3 | `buscar_propiedades` | ⚠️ **Patrones 1 y 3.** Repitió la búsqueda de la línea 4 con los mismos argumentos, ante una pregunta que no la necesitaba ("¿Cómo me puedo sumar a la Comunidad?"). Además afirmó "te di ese resultado sin haber consultado el registro", lo que es falso según la línea 4 |
| 6 | vecino_1 | `reportar_a_municipalidad` | ✅ La observación registra el rechazo ("El reporte no se envió…"); dirección y motivo corresponden al pedido |
| 7 | vecino_1 | `consultar_propiedad` | ✅ La respuesta coincide con la observación |
| 8 | vecino_1 | `consultar_propiedad` | ⚠️ **Patrón 1, más leve.** Volvió a consultar con los mismos argumentos de la línea 7 en el turno siguiente. La respuesta fue correcta, pero la llamada sobraba: la línea 2 respondió lo mismo solo con el historial |
| 9 | vecino_2 | ninguna | ✅ No mezcló la sesión con la de vecino_1 |
| 10 | vecino_3 | `buscar_propiedades` | ✅ Argumentos correctos |
| 11 | vecino_4 | ninguna | ✅ La pregunta general, en una sesión nueva, no usó herramientas. Dijo que no tenía la información, en vez de inventarla |
| 12 | vecino_1 | `reportar_a_municipalidad` | ✅ La observación registra el envío aprobado (simulado); dirección y motivo corresponden al pedido |

La causa de las líneas 5 y 8: la memoria guarda solo el texto de las respuestas anteriores, no las herramientas usadas. El agente no puede saber que su respuesta anterior venía del registro, y a veces vuelve a consultar. Como el patrón apareció en las dos corridas, en turnos distintos, no es un caso aislado. Es la primera corrección pendiente (paso 3 de la sección siguiente).

## Qué hacer ante un comportamiento inesperado

1. **Si `reportar_a_municipalidad` aparece en la traza sin una aprobación registrada, o con una dirección o motivo distintos a lo que pidió el vecino:**
   - Desactivarla de inmediato: sacarla de la lista `herramientas` en `src/agente_comunidad.py`.
   - Si el envío ya fuera real, avisar a la Municipalidad que el reporte fue un error.
2. **Ubicar el caso** en `trazas_agente.jsonl`, por `session_id` y `timestamp`, y copiar la `entrada`. Reproducirlo en una sesión nueva para saber si depende del historial o pasa siempre.
3. **Si eligió una herramienta que no correspondía:** revisar primero su docstring, por si describe un caso demasiado amplio, y después el prompt de sistema. Para el caso de las líneas 5 y 8, la corrección propuesta es agregar al prompt de sistema: "Si tu respuesta anterior en esta conversación ya entregó un resultado, no vuelvas a consultar la misma herramienta salvo que el vecino pida algo nuevo".
4. **Si afirmó algo que ninguna observación respalda:** reforzar en el prompt de sistema la instrucción "no inventes información que no te entreguen las herramientas", incluida la información sobre sus propias acciones anteriores.
5. **Escribir una prueba** que reproduzca el caso en `tests/test_agente_comunidad.py` (sin API cuando se pueda). Si la causa está en la decisión del modelo, agregar el mensaje a las pruebas manuales del bloque `__main__`.
6. **Correr `pytest`** y una corrida real con el mismo mensaje. Comparar la nueva línea de la traza con la anterior antes de dar el cambio por bueno y, si se desactivó, volver a activar la herramienta.
7. **Anotar el caso y el cambio en este documento**, en la tabla de revisión.
