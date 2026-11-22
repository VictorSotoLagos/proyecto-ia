## Registro del dataset y del ajuste con PEFT (laboratorio del Bloque 29)

- Fecha: 2026-11-20
- Comandos:
  - `python src/dataset_tuning.py`: dataset, balance y validación. No se conecta a nada y es gratis.
  - `python src/tuning_peft.py`: lanza el PEFT en Google Cloud, espera el resultado y prueba el modelo ajustado.
- Pruebas: `pytest` (`tests/test_dataset_tuning.py` y `tests/test_tuning_peft.py`). El cliente de Google es un `MagicMock`, así que no gastan.
- Dataset: [ejemplos_tuning.jsonl](ejemplos_tuning.jsonl), que lo genera `guardar_jsonl` solo si la validación no encuentra problemas.

### La tarea

El laboratorio pide un problema de comportamiento consistente del propio proyecto, no de información faltante. Si al modelo le faltara información, sería un caso para RAG.

Aquí el modelo clasifica el mensaje de un vecino con las mismas categorías del prompt `clasificar_solicitud` y del enrutador. Además indica qué barrio nombra el mensaje, con las 3 etiquetas de `extraer_direccion`. La salida es siempre un JSON con dos claves:

| Clave | Valores |
|---|---|
| `categoria` | `direccion`, `busqueda` u `otro` |
| `barrio` | `Barrio Brasil`, `Concha y Toro` o `no indicado` |

Reglas que enseñan los ejemplos:
- El barrio sale solo de lo que dice el mensaje. Almirante Barroso 256 aparece dos veces: con "en Barrio Brasil" el barrio es `Barrio Brasil`, y sin barrio es `no indicado`.
- El nombre "Comunidad Brasil Alameda" no cuenta como barrio.
- Hablar de una fachada sin dar una dirección es `otro`.
- Una pregunta que no es sobre propiedades pero nombra un barrio es `otro`, con ese barrio.

No se incluyó la `confianza` que devuelve `clasificar_solicitud`, porque el curso pide outputs exactos y ese número habría que inventarlo.

### Resultado del dataset

```
15 ejemplos construidos

Balance por categoria:
direccion: 5
busqueda: 5
otro: 5

Balance por barrio:
Barrio Brasil: 5
Concha y Toro: 5
no indicado: 5

15 ejemplos, 0 problemas encontrados
Dataset guardado en docs/ejemplos_tuning.jsonl, listo para subirlo al bucket
```

### Cómo se probó (los 4 pasos de la actividad)

1. **Balance:** ninguna categoría ni barrio domina, con 5 ejemplos de cada uno.
2. **Validación:** `validar_dataset` devuelve una lista vacía.
3. **El validador detecta errores:** las pruebas rompen ejemplos a propósito y el validador encuentra los tres casos:
   - un `text_input` duplicado;
   - un output sin la clave `barrio`;
   - un output con comillas simples, que no es JSON válido.
4. **Envío del trabajo de tuning:**
   - El dataset se subió al bucket privado `gs://proyecto-ia-515221-tuning`, y la copia en la nube es idéntica a la local (mismo md5).
   - `tuning_peft.py` lanzó el trabajo con `client.tunings.tune`. `esperar_a_que_termine` consultó el estado cada 30 segundos hasta el final.

| Dato del trabajo | Valor |
|---|---|
| Modelo base | `gemini-3.5-flash-lite`, en la región múltiple `us` |
| Modo | `TUNING_MODE_PEFT_ADAPTER`, adapter de tamaño 4 |
| Épocas | 5. Google fijó por su cuenta un multiplicador de tasa de aprendizaje de 2.0 |
| Ejemplos y tokens leídos | 15 ejemplos, 474 tokens por época |
| Pasos de entrenamiento | 5: un checkpoint por época, con 1 paso cada uno |
| Tiempo | 1 min 21 s en cola (`PENDING`) y 25 min 56 s entrenando (`RUNNING`) |
| Estado final | `JOB_STATE_SUCCEEDED` |
| ID del trabajo | 1722249724980887552 |

Por qué cambió el modelo respecto de la clase: la profe usó `gemini-2.5-flash` en `us-central1`, pero según la documentación de Google ese modelo se retiró el 20 de octubre de 2026. `gemini-3.5-flash-lite` está vigente y acepta tuning. Los modelos Gemini 3 o posteriores se entrenan en la región `us` o `eu`.

### Prueba del modelo ajustado

Se le enviaron 3 mensajes que no están en el dataset, uno por categoría. Se usó el razonamiento `MINIMAL`, que Google recomienda para las tareas ajustadas de Gemini 3.

| Mensaje | Salida esperada | Lo que respondió |
|---|---|---|
| Quiero que revises la fachada de Compañía 2150, en el Barrio Brasil. | `{"categoria": "direccion", "barrio": "Barrio Brasil"}` | Una revisión arquitectónica larga del Barrio Brasil, que termina preguntando qué necesita el usuario |
| ¿Hay propiedades con grafitis y malezas en Concha y Toro? | `{"categoria": "busqueda", "barrio": "Concha y Toro"}` | Dice que no puede ver las calles y ubica Concha y Toro en "la avenida Concha y Toro (ubicada en Puente Alto)" |
| ¿A qué hora abre la feria del barrio? | `{"categoria": "otro", "barrio": "no indicado"}` | Pregunta de qué feria y de qué barrio se trata |

**Ninguna de las 3 respuestas fue el JSON.** El modelo ajustado respondió como un chat general, igual que lo haría el modelo base.

### Observaciones

- **El trabajo terminó bien, pero el modelo no aprendió el comportamiento.** Con 15 ejemplos, Google procesó el dataset completo en un solo paso por época, así que el adapter se actualizó solo 5 veces. Es demasiado poco entrenamiento para cambiar cómo responde el modelo. La documentación de Google recomienda partir con unos 100 ejemplos. El mínimo de 10 del curso sirve para practicar el flujo, no para obtener un modelo útil.
- **Lo que más cuesta en el PEFT son los datos.** El entrenamiento costó muy poco: 474 tokens por 5 épocas, unos 2.400 tokens. A la tarifa que Google publica para el tuning de Gemini 2.5, de US$5 por millón de tokens, son cerca de 1 centavo de dólar. Lo caro es reunir y etiquetar a mano los cientos de ejemplos que hacen falta para que el modelo aprenda.
- **La segunda respuesta muestra la diferencia entre conocimiento y comportamiento.** El modelo confundió el Barrio Concha y Toro (Santiago centro) con la avenida Concha y Toro (Puente Alto). Esa es información que le falta, un problema para RAG, mientras que responder siempre con el mismo JSON es un problema de comportamiento, que es lo que corrige el tuning.
- **Para esta tarea, hoy funciona mejor el prompt que el tuning.** Con Claude, el prompt `clasificar_solicitud` (probado en `src/prompts/test_consistencia.py`) y el clasificador del enrutador ya entregan la categoría exacta, sin necesidad de un dataset grande. En la corrida de [registro_enrutamiento.md](registro_enrutamiento.md), los 3 mensajes llegaron a la ruta correcta.
- **Nada queda cobrando.** Según la documentación de Google, el modelo ajustado se publica en un endpoint compartido que no tiene costo propio. Solo se cobra por token cuando alguien lo usa, a la tarifa del modelo base. El bucket guarda un archivo de 3 KB.
