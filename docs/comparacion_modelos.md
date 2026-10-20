# Comparación de modelos para la miniaplicación

**Fecha de la tabla:** 20-10-2026

Proyecto: detección de propiedades en posible abandono en Barrio Brasil y Concha y Toro (Comunidad Brasil Alameda).

## Tabla comparativa

| Criterio | Claude Haiku 5.5 | Claude Sonnet 5.5 | Claude Opus 5.5 | Haiku 5.5 (CLP) | Sonnet 5.5 (CLP) | Opus 5.5 (CLP) |
|---|---|---|---|---|---|---|
| **Costo por 1000 tokens de entrada** | 0,0001 USD | 0,002 USD | 0,004 USD | 0,098 CLP | 1,96 CLP | 3,93 CLP |
| **Costo por 1000 tokens de salida** | 0,0005 USD | 0,01 USD | 0,02 USD | 0,491 CLP | 9,82 CLP | 19,64 CLP |
| **Latencia promedio observada** | 3,59 segundos | 4,85 segundos | 6,27 segundos | — | — | — |
| **Calidad de respuesta para tu caso concreto** | buena: evalúa las 4 señales descritas y advierte que no son concluyentes, pero su conclusión cambia entre intentos (de "moderada" a "moderada a fuerte") | muy buena: siempre responde con el mismo formato (fuerte / moderada / conclusión), fácil de llevar a un puntaje, pero cambia qué señales considera "fuertes" de un intento a otro | excelente: la más consistente (en los 4 intentos marca las ventanas tapiadas y la vegetación como las señales más fuertes) y la que más contexto del Barrio Brasil aporta (grafitis comunes en casas habitadas, Zona Típica, sucesión o litigio) | — | — | — |
| *Costo promedio por petición (medido)* | *0,000284 USD* | *0,004080 USD* | *0,009240 USD* | *0,279 CLP* | *4,01 CLP* | *9,07 CLP* |

## De dónde sale cada dato

- **Costo por 1000 tokens (USD):** página oficial de precios de Anthropic, consultada el 20-10-2026: <https://platform.claude.com/docs/en/about-claude/pricing>. Precios por millón de tokens (entrada / salida): Haiku 5.5 USD 0,10 / 0,50; Sonnet 5.5 USD 2 / 10; Opus 5.5 USD 4 / 20.
- **Conversión a CLP:** dólar observado del Banco Central de Chile del 20-10-2026, **$981,86 por dólar** (<https://www.bcentral.cl/>).
- **Latencia promedio:** medida con `src/medir_latencia.py`, que cronometra con `time.perf_counter()` el tiempo de `enviar_peticion()`. Se hicieron 4 repeticiones del mismo prompt por modelo y se promediaron.
- **Costo promedio por petición:** calculado con `calcular_costo()` a partir de `usage` (tokens de entrada y salida) de cada respuesta. En estos modelos los tokens de salida incluyen el razonamiento.
- **Calidad:** evaluada leyendo las 4 respuestas de cada modelo al mismo prompt.

## Prompt de prueba

> Analiza esta fachada de una casona en Av. Brasil, Santiago: ventanas tapiadas con tablas, grafitis en el portón, pintura descascarada y vegetación creciendo en el techo. ¿Qué señales de posible abandono ves y qué tan fuerte es la evidencia? Responde en máximo 5 líneas.

Nota: la prueba usa una **descripción en texto** de la fachada, sin foto. Con fotos reales el costo por petición sube, porque la imagen suma tokens de entrada.

## Mediciones individuales

| Intento | Haiku 5.5 | Sonnet 5.5 | Opus 5.5 |
|---|---|---|---|
| 1 | 3,90 s · 0,000293 USD | 4,71 s · 0,004040 USD | 5,56 s · 0,007940 USD |
| 2 | 2,63 s · 0,000189 USD | 5,44 s · 0,004360 USD | 7,07 s · 0,011380 USD |
| 3 | 3,76 s · 0,000316 USD | 4,77 s · 0,004310 USD | 7,28 s · 0,010220 USD |
| 4 | 4,10 s · 0,000336 USD | 4,48 s · 0,003610 USD | 5,17 s · 0,007420 USD |
| **Promedio** | **3,59 s · 0,000284 USD** | **4,85 s · 0,004080 USD** | **6,27 s · 0,009240 USD** |

Referencia de escala: procesar 1000 propiedades costaría unos $279 CLP con Haiku 5.5, $4.006 CLP con Sonnet 5.5 y $9.072 CLP con Opus 5.5.
