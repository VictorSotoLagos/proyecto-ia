# Detección de propiedades en posible abandono — Barrio Brasil y Concha y Toro

Miniaplicación para la Comunidad Brasil Alameda que evalúa la fachada de una propiedad y detecta señales visibles de posible abandono: ventanas tapiadas, vanos abiertos o vidrios rotos, malezas, grafitis, pintura descascarada, revoque caído, techo dañado y escombros. La evaluación la hace **Claude Opus 5.5** a través de la API de Claude, y el resultado llega en formato JSON.

Este repositorio corresponde al **Gate 1** de la Especialización en Desarrollo con IA Generativa (Accenture · Skillnest). La miniaplicación se construye por etapas a lo largo del programa: el Gate 1 entrega su base técnica y la evaluación de fachadas funcionando de punta a punta, y los Gates 2 y 3 suman las fuentes automáticas de fotos y el puntaje de abandono.

## Formas de usar la miniaplicación

La miniaplicación ofrecerá tres formas de pedir una evaluación. Las tres terminan en el mismo paso: el prompt `evaluar_fachada`, que analiza la foto de la fachada.

| Forma de uso | Ejemplo | Qué incluye el Gate 1 | Qué se suma en los Gates 2 y 3 |
|---|---|---|---|
| Evaluar la foto de una fachada | Una foto de la propiedad de calle Almirante Barroso 256 | La evaluación completa de la foto con el prompt `evaluar_fachada` | Nada: ya funciona de punta a punta |
| Revisar una dirección | «Revisa la casa de Almirante Barroso 256, en Barrio Brasil» | La interpretación de la dirección (calle, número y barrio) con el prompt `extraer_direccion` | Obtener la foto de esa dirección desde Google Street View |
| Buscar propiedades | «Dame una casa en Barrio Brasil de un piso, con ventanas tapiadas y malezas» | La conversión del pedido en criterios de búsqueda (barrio, pisos y señales) con el prompt `extraer_criterios_busqueda` | Obtener las fotos de las propiedades del barrio, desde Street View o desde un Excel con sus URL, y quedarse con las que cumplen los criterios |

El prompt `clasificar_solicitud`, también incluido en el Gate 1, reconoce si el usuario dio una dirección o pidió una búsqueda.

Como la conexión con Google Street View corresponde a las próximas etapas, el Gate 1 trabaja con la primera forma de uso: una foto real de fachada, tomada de Google Street View y guardada en `docs/`. Así se prueba de punta a punta el paso que comparten las tres formas.

## Qué entrega el Gate 1

`src/consumir_claude.py` envía a Claude la foto de prueba de la propiedad de calle Almirante Barroso 256 (tomada de Google Street View), junto con un prompt de sistema, y recibe una respuesta JSON con estas claves fijas:

| Clave | Contenido |
|---|---|
| `fachada_visible` | `true` si la foto muestra la fachada con claridad; `false` si no sirve para evaluar (no es una fachada o no se ve bien) |
| `senales` | Lista de las señales de abandono visibles en la foto, con nombres fijos |
| `pisos` | Cantidad de pisos de la fachada |
| `evidencia` | `ninguna`, `débil`, `moderada`, `fuerte` o `muy fuerte` |
| `descripcion` | Máximo 2 oraciones con lo más grave que se ve |

Además, calcula el costo de cada petición a partir de los tokens usados.

El repositorio incluye también el banco de prompts con su prueba de consistencia y la comparación de modelos que justificó la elección de Claude Opus 5.5.

## Requisitos

- Python 3.10 o superior (probado con Python 3.14.8): las dependencias de `requirements.txt` no se instalan en versiones anteriores.
- Git.
- Una API key de Anthropic, que se crea en la consola de Claude: <https://platform.claude.com>

## Instalación

Clona el repositorio, crea un entorno virtual, instala las dependencias y crea tu archivo `.env` a partir de la plantilla.

**Windows (PowerShell):**

```powershell
git clone https://github.com/VictorSotoLagos/proyecto-ia.git
cd proyecto-ia
python -m venv venv
.\venv\Scripts\Activate.ps1
pip install -r requirements.txt
Copy-Item .env.example .env
```

**macOS / Linux:**

```bash
git clone https://github.com/VictorSotoLagos/proyecto-ia.git
cd proyecto-ia
python3 -m venv venv
source venv/bin/activate
pip install -r requirements.txt
cp .env.example .env
```

## Configurar la API key

Abre el archivo `.env` que acabas de crear. Contiene esta línea de ejemplo:

```
ANTHROPIC_API_KEY=tu_llave_aqui
```

Reemplaza `tu_llave_aqui` por tu API key de Anthropic. Para confirmar que Python la lee, ejecuta desde la carpeta raíz del proyecto:

```
python prueba_env.py
```

Debe imprimir `True`. El script solo indica si la variable existe; nunca muestra la clave.

El archivo `.env` está excluido en `.gitignore`, así que nunca se sube al repositorio. `.env.example` es solo una plantilla, sin valores reales.

## Cómo ejecutar

> ⚠️ Ejecuta todos los comandos **desde la carpeta raíz del proyecto** (la que contiene este README) y con el entorno virtual activado. Las rutas a la foto de prueba y al registro de resultados son relativas a esa carpeta: si ejecutas desde `src/`, el programa no las encuentra.

En macOS / Linux, usa `python3` en lugar de `python`. Cada comando hace peticiones reales a la API de Claude; su costo aproximado se indica en cada caso.

### 1. Evaluar la fachada de prueba (programa principal)

```
python src/consumir_claude.py
```

Salida real del 24-10-2026:

```
{'fachada_visible': True, 'senales': ['ventanas tapiadas', 'vanos abiertos o vidrios rotos', 'malezas', 'grafitis', 'pintura descascarada', 'revoque caído', 'techo dañado', 'escombros'], 'pisos': 1, 'evidencia': 'muy fuerte', 'descripcion': 'Fachada ornamentada de un piso con el techo aparentemente ausente o colapsado...'}
Costo estimado: $0.019056 USD
```

El texto de `descripcion` y la lista exacta de `senales` pueden variar levemente entre ejecuciones; la estructura del JSON se mantiene siempre. Costo aproximado: US$0,02 por ejecución.

### 2. Probar la consistencia del banco de prompts

```
python src/prompts/test_consistencia.py
```

Ejecuta 3 veces cada uno de los 4 prompts del banco, valida que cada respuesta sea un JSON con las claves esperadas y guarda el resultado en `src/prompts/registro_resultados.json`. Muestra una línea por intento y, al final, este resumen (salida real del 24-10-2026):

```
clasificar_solicitud: 3/3 respuestas válidas
extraer_direccion: 3/3 respuestas válidas
extraer_criterios_busqueda: 3/3 respuestas válidas
evaluar_fachada: 3/3 respuestas válidas
```

Costo aproximado: US$0,10 por ejecución (12 peticiones).

### 3. Comparar modelos

```
python src/medir_latencia.py
```

Envía 4 veces la misma foto y la misma pregunta a Claude Haiku 5.5, Claude Sonnet 5.5 y Claude Opus 5.5, y muestra la latencia, el costo y la respuesta de cada intento. Los resultados están documentados en [docs/comparacion_modelos.md](docs/comparacion_modelos.md). Costo aproximado: US$0,10 por ejecución (12 peticiones).

## Estructura del proyecto

```
proyecto-ia/
├── src/
│   ├── consumir_claude.py        # módulo principal: arma, envía y procesa la petición a Claude
│   ├── medir_latencia.py         # comparación de latencia y costo entre modelos
│   └── prompts/
│       ├── banco.py              # banco de 4 prompts, cada uno con su esquema JSON
│       ├── test_consistencia.py  # prueba de consistencia del banco de prompts
│       └── registro_resultados.json   # resultado de la prueba de consistencia
├── docs/
│   ├── decision-arquitectura.md       # decisión de arquitectura y elección de modelo
│   ├── comparacion_modelos.md         # comparación de modelos con datos reales
│   ├── diagrama-arquitectura-miniapp.png
│   ├── fachada-almirante-barroso-256.png   # foto de prueba (Google Street View, mayo 2024)
│   └── evidencia_peticion_autenticada.png
├── tests/                        # reservada para las pruebas automatizadas del Módulo 2
├── funcion1.py                   # ejercicio de práctica: función simple
├── funcion2.py                   # ejercicio de práctica: manejo de errores con requests
├── prueba_env.py                 # verifica que la API key se lee desde .env
├── requirements.txt
├── .env.example
└── .gitignore
```

## Cómo funciona `consumir_claude.py`

El módulo consume la API de Claude (`POST https://api.anthropic.com/v1/messages`) directamente con `requests` y lee la API key desde `.env` con `python-dotenv`. Cada función cumple una sola tarea:

| Función | Qué hace |
|---|---|
| `leer_imagen_base64(ruta)` | Lee la foto y la convierte a base64 para enviarla dentro del JSON |
| `armar_peticion(modelo, pregunta, system_instruction, response_schema=None, imagen_b64=None)` | Arma la URL, los headers y el body. El prompt de sistema va separado de la pregunta; el esquema JSON y la foto son opcionales |
| `enviar_peticion(url, headers, body)` | Envía la petición, maneja los errores de conexión y de tiempo de espera, y revisa el código de estado de la API: 401/403 (API key inválida), 429 (límite de solicitudes) y 5xx (error del proveedor) |
| `extraer_texto(datos)` | Devuelve el texto de la respuesta o, si la API respondió con un error, muestra su mensaje |
| `parsear_respuesta_json(texto, claves_requeridas)` | Limpia la respuesta, la convierte en diccionario y valida que traiga las claves esperadas |
| `calcular_costo(datos, precio_entrada, precio_salida)` | Calcula el costo en USD a partir de `usage` (los tokens de salida ya incluyen el razonamiento del modelo) |
| `obtener_dato_de_prueba(pregunta, imagen_b64)` | Une todo lo anterior usando el prompt `evaluar_fachada` del banco |

## Banco de prompts

`src/prompts/banco.py` reúne los cuatro prompts de la miniaplicación, que cubren sus tres formas de uso. Cada uno tiene su prompt de sistema, un ejemplo de entrada, las claves esperadas y su esquema JSON:

| Prompt | Para qué sirve |
|---|---|
| `clasificar_solicitud` | Decide si el usuario dio una dirección, pidió una búsqueda u otra cosa |
| `extraer_direccion` | Extrae la calle, el número y el barrio de una dirección |
| `extraer_criterios_busqueda` | Convierte una búsqueda en criterios: barrio, pisos y señales |
| `evaluar_fachada` | Evalúa la foto de la fachada (el prompt principal de la miniaplicación) y avisa si la foto no sirve para evaluar |

Resultado de la prueba de consistencia del 24-10-2026: 12 de 12 respuestas válidas (3/3 en cada prompt). El detalle está en [src/prompts/registro_resultados.json](src/prompts/registro_resultados.json).

## Documentación

- [Decisión de arquitectura y elección de modelo](docs/decision-arquitectura.md)
- [Comparación de modelos con datos reales](docs/comparacion_modelos.md)
- [Diagrama de arquitectura](docs/diagrama-arquitectura-miniapp.png)

## Registro del ensayo de instalación limpia

- Fecha: 2026-10-24
- Cómo se hizo: se clonó el repositorio desde GitHub en una carpeta nueva (`prueba-gate1`), con un entorno virtual nuevo y el Python del sistema (3.14.8), siguiendo solo las instrucciones de este README para Windows (PowerShell).
- Encontrado: sin hallazgos. `pip install -r requirements.txt` instaló todo sin errores, `.env` no aparece en `git status`, `python prueba_env.py` imprimió `True` y `python src/consumir_claude.py` devolvió la evaluación de la fachada sin errores.
- Corregido: nada que corregir.
- Resultado: el proyecto se instala y se ejecuta sin intervención manual.
- Verificación de la versión final (2026-10-24): después de agregar el manejo de errores a `medir_latencia.py` y las mejoras del banco de prompts (`fachada_visible` y la señal 'vanos abiertos o vidrios rotos', commit `a7ea91a`), se trajo la última versión de GitHub a la carpeta del ensayo, cuyo entorno virtual se creó solo desde `requirements.txt`, y se ejecutaron los 4 comandos de este README contra la API real: `prueba_env.py` imprimió `True`, `consumir_claude.py` devolvió la evaluación de la fachada, `test_consistencia.py` dio 12/12 respuestas válidas y `medir_latencia.py` completó sus 12 peticiones, todos sin errores.
- Revisión final (2026-10-24): se encontró que el README no indicaba la versión mínima de Python (las dependencias exigen 3.10 o superior) y que su ejemplo de la API key no coincidía con `.env.example`. Se corrigieron ambos (commit `08d5916`) y se subió `MAX_TOKENS` de 1000 a 2000 para dar margen al razonamiento del modelo (commit `2b9e700`). Con esa versión, los 4 comandos de este README volvieron a correr contra la API real sin errores (`test_consistencia.py`: 12/12).
- Ensayo manual de la versión de entrega (2026-10-24): el autor clonó desde GitHub la versión `2b9e700` en una carpeta nueva, creó un entorno virtual nuevo con Python 3.14.8, instaló las dependencias de `requirements.txt`, configuró su `.env` y el programa funcionó sin errores. `.env` no aparece en `git status`.

## Próximas etapas

El Gate 1 entrega la base técnica de la miniaplicación. Las próximas etapas del programa (Gate 2 y Gate 3) suman estas piezas; las dos primeras ya están en el diagrama de arquitectura:

- `obtener_imagen_fachada()`: obtener desde Google Street View la foto de cada dirección (usará `GOOGLE_MAPS_API_KEY`), para las formas de uso por dirección y por búsqueda.
- `calcular_puntaje()`: convertir las señales detectadas en un puntaje de abandono de 0 a 100.
- Un Excel con las propiedades del barrio y la URL de la foto de cada fachada (Gate 2), como fuente complementaria a Street View. Su objetivo es optimizar las peticiones: si la foto de una propiedad ya está en el Excel, la miniaplicación no necesita pedirla a la API de Street View.

---

Autor: Victor Soto
