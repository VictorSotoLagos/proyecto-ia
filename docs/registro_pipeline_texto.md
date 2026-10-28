## Registro del pipeline de texto: antes y después

- Fecha: 2026-10-28
- Comando: `python src/pipeline_texto.py` (modelo `claude-opus-5-5`)
- Prompt de sistema: "Responde en una sola oración breve, en español."
- Métrica: proporción de las palabras de la referencia que también aparecen en la respuesta
- Costo total: $0.00484 USD (3 peticiones)

| Caso | Consulta | Texto crudo | Texto procesado |
|---|---|---|---|
| 1 | ¿Qué es la tasación de una propiedad? | 73.3% | 85.7% |
| 2 | ¿Qué es el avalúo fiscal de una propiedad en Chile? | 94.7% | 100.0% |
| 3 | ¿Qué es la fachada de un edificio? | 69.2% | 76.9% |

### Caso 1

- Referencia: La tasación es la estimación del valor comercial de una propiedad, realizada por un tasador.
- Respuesta: La tasación de una propiedad es la estimación profesional y objetiva de su valor de mercado, realizada por un tasador certificado a partir de factores como la ubicación, el tamaño, el estado y los precios de inmuebles comparables.

### Caso 2

- Referencia: El avalúo fiscal es el valor que el Servicio de Impuestos Internos asigna a una propiedad para calcular las contribuciones.
- Respuesta: El avalúo fiscal es el valor que el Servicio de Impuestos Internos (SII) asigna a una propiedad y que sirve de base para calcular las contribuciones (impuesto territorial) y otros tributos.

### Caso 3

- Referencia: La fachada es el exterior visible de un edificio, especialmente su frente principal.
- Respuesta: La fachada es la parte exterior de un edificio, especialmente la cara principal que da a la calle, y define su aspecto visual.

### Resultado

En los 3 casos la coincidencia sube al pasar los dos textos por `procesar_texto`: el pipeline quita diferencias de formato (mayúsculas como "El" y "el", puntuación como "contribuciones." y "contribuciones") que no cambian el contenido. Los porcentajes varían un poco en cada ejecución, porque el modelo no responde siempre con las mismas palabras.
