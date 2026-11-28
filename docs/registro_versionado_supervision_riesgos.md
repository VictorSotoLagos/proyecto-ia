# Registro: versionado de prompts, punto de supervisión humana y matriz de riesgos (CORE del Bloque 32)

Actividad del curso: "Completa tu matriz de riesgos y el versionado de prompts". Los tres archivos están en `src/`, junto a los demás del proyecto, y cada uno tiene sus pruebas en `tests/`. Ninguno llama a una API.

| Paso | Archivo | Pruebas |
|---|---|---|
| 1. Versiones del prompt | `src/registro_prompts.py` | `tests/test_registro_prompts.py` (4) |
| 2. Punto de supervisión | `src/grafo_supervision.py` | `tests/test_grafo_supervision.py` (4) |
| 3. Matriz de riesgos | `src/matriz_riesgos.py` | `tests/test_matriz_riesgos.py` (5) |

Con estas 13 pruebas, el proyecto suma 97, y todas pasan.

## Paso 1: dos versiones del prompt real

- **Versión 1:** el `PROMPT_TEMPLATE` de `src/registro_rag.py` (Bloque 28), el prompt con que la consulta RAG genera hoy la respuesta. Se importa de ese archivo, no se copia.
- **Versión 2:** el mismo texto más la delimitación del contexto de la clase del Bloque 31. El contexto va entre `<contexto>` y `</contexto>`, y una frase le dice al modelo que eso es un dato, nunca una instrucción. Es la segunda capa contra la inyección; la primera es el filtro de `src/logging_rag.py`.

`python src/registro_prompts.py`:

```
849809fdf663 - version original: usa solo el contexto y cita las fuentes (Bloque 28)
855768cb7e7c - agrega delimitacion del contexto contra inyeccion de prompt (Bloque 31)
ultima: 855768cb7e7c
```

Las huellas son distintas y `ultima` devuelve la de la versión 2. La comparación, palabra por palabra, muestra exactamente el cambio:

- se quita `Contexto:`;
- se agregan la frase nueva, `<contexto>` y `</contexto>`.

La prueba `test_el_diff_muestra_exactamente_el_cambio` lo comprueba.

## Paso 2: la versión 2 solo se activa si alguien de la directiva la aprueba

`python src/grafo_supervision.py` usa la huella `855768cb7e7c`, escrita como texto porque los pasos son independientes. Una prueba confirma que coincide con la última versión del registro, así que si el prompt cambia y nadie actualiza la huella, la prueba falla.

```
1) tras invocar: {'huella_nueva': '855768cb7e7c', 'aprobado': False, '__interrupt__': [Interrupt(value={'motivo': 'aprobar nueva version del prompt del RAG de la comunidad', 'huella_propuesta': '855768cb7e7c'}, id='f0211c537008b4e1df7294ec7e7b446c', response_schema=None)]}
2) pendiente: {'motivo': 'aprobar nueva version del prompt del RAG de la comunidad', 'huella_propuesta': '855768cb7e7c'}
version 855768cb7e7c activada
3) tras aprobar: {'huella_nueva': '855768cb7e7c', 'aprobado': True}
version 855768cb7e7c rechazada, se mantiene la anterior
4) tras rechazar: {'huella_nueva': '855768cb7e7c', 'aprobado': False}
```

- **1 y 2:** sin reanudar, el resultado trae `__interrupt__` y el nodo `aplicar` no corrió.
- **3:** con `Command(resume=True)` la versión se activa.
- **4:** en otro `thread_id`, con `Command(resume=False)`, se rechaza y se mantiene la anterior.

El valor de `id` cambia en cada corrida. Con langgraph 1.2.19, el `Interrupt` trae además `response_schema=None`, que el ejemplo del curso (langgraph 1.2.11) no muestra.

## Paso 3: matriz de riesgos

`python src/matriz_riesgos.py`:

```
CRITICO  (20) - Se reporta a la Municipalidad o a un inversionista una casa que la foto muestra abandonada pero que esta habitada
ALTO     (12) - La busqueda de fichas trae, junto a las que cumplen, otras que no cumplen todo lo pedido (barrio, pisos o senales), porque siempre devuelve k resultados
ALTO     (10) - Una ficha compartida con un inversionista lleva notas de vecinos con testimonios sobre quienes viven en la casa
ALTO     ( 9) - Se activa una version nueva del prompt del RAG que deja de citar fuentes o rompe el formato de la respuesta
ALTO     ( 9) - La evaluacion se basa en una foto de Street View antigua y la casa ya cambio
MEDIO    ( 8) - Inyeccion de prompt via el texto de un letrero o grafiti de la fachada que la evaluacion copia a una ficha indexada
MEDIO    ( 6) - Se agotan los creditos de Gemini o vence la clave de Anthropic y el servicio deja de responder
```

La probabilidad y el impacto de cada fila se justifican en un comentario en el código. Solo la probabilidad de la última fila se apoya en un hecho del proyecto: el error 402 de Gemini del 16 de noviembre de 2026. Las demás son estimaciones.

La fila de la búsqueda no sale de la precisión de 0,311 del Bloque 27. Esa evaluación se hizo sobre los 7 documentos del proyecto, porque el índice de fichas todavía no existe. En ella, cada pregunta trajo su fragmento correcto (13 de 14), y 13 de las 14 tienen un solo fragmento relevante. Con k=3, la precisión máxima posible es 1 de 3 (0,333), así que el 0,311 no indica que la búsqueda falle. El riesgo viene de otra cosa: la búsqueda siempre devuelve k fichas, aunque cumplan menos, y no revisa condiciones exactas como el barrio o la cantidad de pisos. Seis de las siete filas quedan **al límite**, es decir, un punto más o menos les cambia la categoría. Por eso conviene revisarlas con otra persona de la directiva antes de darlas por cerradas. Solo el riesgo CRÍTICO es firme: con un punto menos sigue siendo CRÍTICO.

### Mitigaciones que apuntan a algo ya construido

| Riesgo | Mitigación construida |
|---|---|
| Casa habitada reportada como abandonada | Aprobación humana (`esperar_aprobacion`) y verificación en terreno (Bloque 23) |
| Versión nueva del prompt que rompe las citas | Banco de prompts con prueba de consistencia (Bloque 10) y registro de versiones (Bloque 32) |
| Fichas que no cumplen todo lo pedido | Métricas de precisión y recall (Bloque 27) y cita de fuentes (Bloque 26). Falta filtrar por los metadatos barrio, pisos y evidencia (sección 3 de la ficha) |
| Notas de vecinos en una ficha compartida | `armar_ficha` excluye las notas y compartir pide aprobación (Bloque 23) |
| Foto antigua | Verificación en terreno (Bloque 23). La fecha de la foto en la ficha (RF-02) todavía es un plan |
| Inyección por el texto de un letrero | Filtro de patrones (Bloque 31) y delimitación del contexto (Bloque 32) |
| Créditos agotados o clave vencida | `with_fallbacks` a Claude Haiku (Bloque 20). Gemini no tiene respaldo |

### Puntos de supervisión de los riesgos ALTO y CRÍTICO

El curso documenta los puntos de supervisión aparte. Aquí van además como un campo `supervision` de cada fila, para que una prueba compruebe que ningún ALTO o CRÍTICO quede sin uno.

- **CRÍTICO, casa habitada reportada:** un integrante de la directiva verifica la casa en terreno y responde la aprobación antes de registrar el reporte.
- **ALTO, versión nueva del prompt:** `src/grafo_supervision.py` detiene el despliegue con `interrupt()` hasta que la directiva aprueba la huella nueva.
- **ALTO, fichas que no cumplen todo lo pedido:** antes de aprobar un reporte, la directiva revisa la ficha citada como fuente de esa dirección.
- **ALTO, notas de vecinos:** un integrante de la directiva aprueba cada ficha antes de compartirla y confirma que el destinatario es conocido por la comunidad.
- **ALTO, foto antigua:** la misma verificación en terreno, antes de aprobar un reporte.

Cuatro de los cinco puntos son la misma aprobación: la del reporte o la de compartir una ficha, que es la acción con consecuencias fuera de la comunidad. Los riesgos MEDIO no llevan punto de supervisión, porque frenar cada consulta no escala.

### Límite que hay que tener presente

El código pide la aprobación, pero no exige ni registra que la verificación en terreno se haya hecho: eso depende de quien aprueba. Ya estaba anotado en `docs/limites_autonomia_agente.md` (Bloque 23).
