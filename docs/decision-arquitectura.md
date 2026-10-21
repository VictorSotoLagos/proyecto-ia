# Decisión de arquitectura: elección de modelo

**Fecha:** 20-10-2026

Proyecto: detección de propiedades en posible abandono en Barrio Brasil y Concha y Toro (Comunidad Brasil Alameda).

La miniaplicación evalúa cada propiedad a partir de la foto de su fachada: el modelo busca señales visibles de posible abandono, como ventanas tapiadas, malezas o vegetación en el techo, grafitis o pintura descascarada, y con esas señales mi código calcula un puntaje de abandono de 0 a 100.

## Modelo elegido

**Claude Opus 5.5** (`claude-opus-5-5`), de Anthropic, usado a través de la API de Claude (`POST /v1/messages`).

## Diagrama de arquitectura

![Diagrama de arquitectura de la miniaplicación](diagrama-arquitectura-miniapp.png)

## Comparación de candidatos

Tabla armada el 20-10-2026 con datos reales, enviando a cada modelo la misma foto de Google Street View de la propiedad de calle Almirante Barroso 256:

| Criterio | Claude Haiku 5.5 | Claude Sonnet 5.5 | Claude Opus 5.5 | Haiku 5.5 (CLP) | Sonnet 5.5 (CLP) | Opus 5.5 (CLP) |
|---|---|---|---|---|---|---|
| **Costo por 1000 tokens de entrada** | 0,0001 USD | 0,002 USD | 0,004 USD | 0,098 CLP | 1,96 CLP | 3,93 CLP |
| **Costo por 1000 tokens de salida** | 0,0005 USD | 0,01 USD | 0,02 USD | 0,491 CLP | 9,82 CLP | 19,64 CLP |
| **Latencia promedio observada** | 4,99 segundos | 7,66 segundos | 8,63 segundos | — | — | — |
| **Calidad de respuesta para tu caso concreto** | buena: en los 4 intentos califica la evidencia como "fuerte" o "alta" y ve los escombros, pero solo en 2 de 4 menciona que la casa perdió el techo, la señal más grave | muy buena: en los 4 intentos ve que falta el techo y los escombros, y califica la evidencia como "muy fuerte" en 3 de 4; pero no respeta el límite de 5 líneas y su latencia es la más variable (4,6 a 10,6 s) | excelente: la más consistente: en los 4 intentos ve que falta el techo y los escombros, califica la evidencia como "muy fuerte" y advierte que es una ruina estructural en riesgo | — | — | — |
| *Costo promedio por petición (medido)* | *0,000472 USD* | *0,008755 USD* | *0,014880 USD* | *0,464 CLP* | *8,60 CLP* | *14,61 CLP* |

Fuentes: precios de la [página oficial de Anthropic](https://platform.claude.com/docs/en/about-claude/pricing) y dólar observado del Banco Central de Chile del 20-10-2026 ($981,86). La latencia y el costo por petición se midieron con `src/medir_latencia.py` (4 repeticiones por modelo, con la misma [foto de prueba](fachada-almirante-barroso-256.png) y la misma pregunta). El detalle de cada medición, la foto y el prompt están en [comparacion_modelos.md](comparacion_modelos.md).

## Justificación

Elegí Claude Opus 5.5 porque para mi miniaplicación el criterio que más pesa es la calidad: el puntaje de abandono depende de que el modelo detecte las señales más graves y las califique igual cada vez. Para comprobarlo, envié 4 veces a cada modelo la misma foto real de Google Street View de la propiedad de calle Almirante Barroso 256 (imagen de mayo 2024). En esas 4 repeticiones de prueba, Opus vio siempre que la casa perdió el techo y los escombros tras la puerta, calificó siempre la evidencia como "muy fuerte" y además advirtió que es una ruina estructural en riesgo. Como el Gate 1 es un prototipo que se corre pocas veces, el costo (unos US$0,015, alrededor de $15 CLP por propiedad) pesa poco, y 8,6 segundos de latencia es aceptable porque no es un chat en tiempo real.

## Alternativa descartada y por qué

Descarté Claude Haiku 5.5: es 31 veces más barato y 1,7 veces más rápido, pero en 2 de los 4 intentos no mencionó que la casa no tiene techo, que es la señal más grave, y eso podría dejar a una propiedad con un puntaje más bajo del que le corresponde. También descarté Claude Sonnet 5.5: detectó casi lo mismo que Opus, pero no respetó el límite de 5 líneas, calificó la evidencia de forma menos uniforme ("muy fuerte" en 3 de 4 intentos) y su latencia fue la más variable (de 4,6 a 10,6 segundos), a cambio de un costo solo un 40% menor. Si en el Gate 2 proceso todo el barrio (miles de propiedades), volveré a evaluar Haiku 5.5 por costo.
