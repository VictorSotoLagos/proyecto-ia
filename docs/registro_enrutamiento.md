## Registro del enrutamiento condicional de solicitudes

- Fecha: 2026-11-04
- Comando: `python src/enrutamiento_solicitudes.py` (modelo `claude-opus-5-5`, con LangChain; 2 peticiones por mensaje)
- Pruebas: `pytest` (`tests/test_enrutamiento_solicitudes.py`, con la clasificación y las rutas simuladas con `MagicMock`; no usa la API)

### Qué hace

El flujo clasifica el mensaje del usuario y lo envía por una ruta distinta según su tipo. Las categorías son las mismas del prompt `clasificar_solicitud` del Gate 1, y cada ruta corresponde a una de las formas de uso de la miniaplicación (ver el README):

| Categoría | Ruta | Qué responde |
|---|---|---|
| `direccion` | `cadena_direccion` | Calle, número y barrio (como `extraer_direccion`) |
| `busqueda` | `cadena_busqueda` | Barrio, pisos y señales de abandono (como `extraer_criterios_busqueda`) |
| `otro` o cualquier otra respuesta | `cadena_otro` (ruta por defecto) | Explica qué puede pedir el usuario |

- `construir_paso_clasificacion(modelo)`: plantilla, modelo, `StrOutputParser()` y una `lambda` con `.strip().lower()` que limpia la categoría antes de comparar.
- `construir_cadena_con_enrutamiento(...)`: `RunnablePassthrough.assign` agrega la categoría sin perder el mensaje original, y `RunnableBranch` elige la ruta.
- Las 4 plantillas usan `ChatPromptTemplate` con el mismo rol de sistema ("Eres el asistente de una aplicación de la Comunidad Brasil Alameda…"), igual que el `system_instruction` del banco de prompts del Gate 1.

### Resultado

```
Mensaje: Revisa la casa de Almirante Barroso 256, en Barrio Brasil.
Calle: Almirante Barroso
Número: 256
Barrio: Barrio Brasil

Mensaje: Dame una casa en Barrio Brasil de un piso, con ventanas tapiadas y malezas.
Barrio: Barrio Brasil
Pisos: 1
Señales: ventanas tapiadas, malezas

Mensaje: Hola, ¿quién creó esta aplicación?
¡Hola! Esta aplicación es de la Comunidad Brasil Alameda y ayuda a detectar propiedades en posible abandono en Barrio Brasil y Concha y Toro. Puedes indicarme la dirección de una propiedad o pedirme una búsqueda por barrio, número de pisos o señales de abandono.
```

### Observaciones

- Los 3 mensajes llegaron a la ruta correcta. Esto confirma que el clasificador respondió exactamente `direccion` y `busqueda`. Si hubiera respondido con tilde ("dirección"), ninguna condición de `RunnableBranch` sería verdadera y el mensaje caería en la ruta por defecto sin ningún error, por eso el prompt pide la palabra "sin tilde".
- Cada ruta usa un prompt distinto y entrega un formato distinto, así que la ruta elegida se reconoce en la respuesta sin imprimir la categoría (imprimirla aparte habría costado una petición más por mensaje).
- Las pruebas cubren las dos rutas con condición, la ruta por defecto con una categoría inventada y la normalización (" Direccion \n" queda como "direccion").
