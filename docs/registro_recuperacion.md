## Registro de la recuperación con fuente citada (avance del Bloque 26)

- Fecha: 2026-11-16
- Comando: `python src/recuperar_contexto.py` (1 llamada a Gemini por pregunta: el embedding de la pregunta; los chunks ya están en `vectorstore/`)
- Pruebas: `pytest` (`tests/test_recuperar_contexto.py`, con Documents armados a mano; no consulta Chroma ni gasta tokens)
- Índice: el de [registro_indexacion.md](registro_indexacion.md) (14 chunks de 7 documentos)

### Qué hace

`src/recuperar_contexto.py` es el script de consulta. Está separado del de indexación: se reconecta al índice con `cargar_vectorstore` y nunca vuelve a llamar a `from_documents`.

- `vectorstore.as_retriever(search_kwargs={"k": 2})` adapta Chroma para poder usarlo dentro de una chain o de un agente de LangChain, y devuelve los 2 chunks más parecidos a la pregunta.
- `formatear_contexto` numera los chunks recuperados (`[1]`, `[2]`…) y arma un diccionario de citas con la `fuente` de cada uno, como en la clase. Si un chunk no tiene fuente, queda como "desconocida".
- En `src/indexar_corpus.py`, `inspeccionar_chunks` muestra el inventario del índice (id, fuente y comienzo de cada chunk) sin gastar tokens.

### Resultado

```
Pregunta: ¿Qué hace la aplicación si falla el modelo?
--CONTEXTO FORMATEADO--
[1] Si falla el modelo en una de las rutas del enrutamiento (dirección, búsqueda u otro), with_fallbacks repite la misma ruta con Claude Haiku 5.5. Si Haiku también falla, se entrega una respuesta genérica y queda un aviso WARNING con el error.

[2] Si el error ocurre antes de elegir una ruta, por ejemplo en la clasificación, lo atrapa el try/except de procesar_mensaje_seguro: registra el error con logger.error y devuelve un mensaje seguro, sin que el programa se caiga.
--DICCIONARIO DE CITAS--
{1: 'docs/registro_orquestacion.md', 2: 'docs/registro_orquestacion.md'}
```

Inventario (primeras líneas de `python src/indexar_corpus.py`, que ya no re-indexa):

```
El corpus ya está indexado en vectorstore/: 14 chunks. No se recalculan embeddings.
-- INVENTARIO DE CHUNKS EN CHROMA (Total: 14) --
[1] ID: objetivo_1 | Fuente: README.md
    Contenido: La miniaplicación es de la Comunidad Brasil Alameda y evalúa la fachada de una propiedad de Barrio B...
[2] ID: objetivo_2 | Fuente: README.md
...
```

### Observaciones

- Los 2 chunks recuperados son los dos párrafos del documento de manejo de errores (`errores_1` y `errores_2`), que es justo lo que responde la pregunta. Por eso las dos citas apuntan a la misma fuente.
- Los ids estables del índice (`objetivo_1`, `senales_2`…) hacen que el inventario se lea más fácil que con los ids automáticos de Chroma, que son códigos aleatorios.
- La segunda mitad del Bloque 26, el prompt dinámico en el que Claude responde la pregunta usando este contexto y citando sus fuentes, quedó en `src/registro_rag.py`, junto con la medición de latencia y costo del Bloque 28 (ver [registro_latencia_costo.md](registro_latencia_costo.md)).
