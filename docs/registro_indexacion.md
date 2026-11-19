## Registro de la indexación del corpus (Bloque 24)

- Fecha: 2026-11-16
- Comando: `python src/indexar_corpus.py` (embeddings `models/gemini-embedding-001` de Gemini, vector store Chroma en `vectorstore/`)
- Pruebas: `pytest` (`tests/test_indexar_corpus.py`: corpus, chunking, ids e integridad; ninguna calcula embeddings)

### Qué hace

El script indexa un corpus de 7 documentos cortos sobre la propia miniaplicación y guarda los embeddings en disco. Así la recuperación de los próximos bloques puede consultarlos sin volver a calcularlos.

| Tema | Fuente | Contenido |
|---|---|---|
| `objetivo` | README.md | Para qué es la miniaplicación y qué modelo evalúa las fachadas |
| `senales` | src/prompts/banco.py | Las claves del JSON de `evaluar_fachada`, las 8 señales y la escala de evidencia |
| `formas_de_uso` | README.md | Las tres formas de pedir una evaluación y qué cubre el Gate 1 |
| `modelo` | docs/decision-arquitectura.md | Por qué se eligió Claude Opus 5.5, su costo y latencia, y los modelos descartados |
| `errores` | docs/registro_orquestacion.md | Qué pasa cuando falla un paso del enrutamiento |
| `agente` | docs/registro_agente.md | Las herramientas del agente, la memoria y la traza |
| `limites` | docs/limites_autonomia_agente.md | Qué herramientas piden aprobación y por qué |

- **Chunking:** `RecursiveCharacterTextSplitter` con `chunk_size=400` y `chunk_overlap=60`. Cada párrafo del corpus trae una sola idea y mide menos de 400 caracteres, así que el splitter recursivo, que corta primero por párrafos, deja una idea completa en cada chunk. El overlap del 15% (dentro del 10-20% visto en clase) conserva contexto si un párrafo largo se llega a cortar. Con un splitter de tamaño fijo, un chunk podría terminar a mitad de una idea.
- **Metadata:** cada chunk conserva la `fuente` y el `tema` de su documento. La `fuente` sirve para citar en el Bloque 26.
- **Ids estables:** `objetivo_1`, `objetivo_2`, `senales_1`…, como el `prefijo_id` de la clase. Si se vuelve a indexar, Chroma actualiza los chunks con el mismo id en vez de duplicarlos.
- **Integridad:** antes de calcular embeddings, `verificar_integridad` revisa que no haya chunks vacíos ni duplicados, igual que en la clase.
- **Embeddings con Gemini:** Claude no tiene un modelo de embeddings propio, así que los embeddings los calcula Gemini, como pide la actividad. Claude sigue siendo el modelo que genera las respuestas.
- **Sin re-indexar:** el script primero se reconecta a `vectorstore/` con `Chroma(persist_directory=...)`. Si la carpeta ya tiene chunks, no vuelve a llamar a `from_documents` ni gasta tokens.

### Resultado

Primera corrida, que calcula los embeddings:

```
Integridad OK | Chunks: 14 | Caracteres (corpus/chunks): 3676/3662
Indexados 14 chunks de 7 documentos en vectorstore/
IDs almacenados: ['objetivo_1', 'objetivo_2', 'senales_1', 'senales_2', 'formas_de_uso_1', 'formas_de_uso_2', 'modelo_1', 'modelo_2', 'errores_1', 'errores_2', 'agente_1', 'agente_2', 'limites_1', 'limites_2']
```

Segunda corrida, en un proceso nuevo, que se reconecta sin recalcular:

```
El corpus ya está indexado en vectorstore/: 14 chunks. No se recalculan embeddings.
```

### Cómo se probó (los 3 escenarios de la actividad)

1. **La carpeta se crea con archivos:** `vectorstore/` quedó con `chroma.sqlite3` y una subcarpeta del índice (1,6 MB).
2. **Reconexión sin re-indexar:** la segunda corrida devolvió los 14 chunks esperados sin llamar a `from_documents`.
3. **Fuera de git:** `vectorstore/` está en `.gitignore`, y `git status` no la muestra. También se ignoran `chroma_db/` y `vectorstore_ejemplo/`, que crean las prácticas de clase al ejecutarse.

### Observaciones

- Los 7 documentos quedaron en 14 chunks: los cortes cayeron entre párrafos, ningún chunk supera los 400 caracteres, y la diferencia de 14 caracteres entre corpus y chunks son los saltos de párrafo que el splitter quita al cortar.
- **Búsqueda de prueba** (`similarity_search_with_score`, `k=2`), que no es parte de este bloque, para confirmar que el índice sirve:

  ```
  Chunks en el índice: 14
  Pregunta: ¿Qué pasa si se cae el modelo de IA?
    0.5588 | docs/registro_orquestacion.md | Si falla el modelo en una de las rutas del enrutamiento (dirección, búsqueda u otro), with_fallbacks repite la...
    0.6757 | docs/decision-arquitectura.md | Se eligió Claude Opus 5.5 porque la calidad es el criterio que más pesa: en 4 repeticiones con la misma foto d...
  ```

  El chunk más cercano (menor distancia) es el de manejo de errores, aunque la pregunta dice "se cae" y el documento dice "falla": la búsqueda es por significado, no por palabra exacta. El primer intento de esta búsqueda, justo después de indexar, falló con `402 RESOURCE_EXHAUSTED: Your prepayment credits are depleted`, porque la cuenta de Gemini se quedó sin saldo. El índice no se afectó, y la búsqueda funcionó una vez resuelta la facturación.
- Al instalar `langchain-google-genai` y `langchain-chroma` se actualizaron `langchain-core` (1.7.4 → 1.8.1) y `pydantic` (2.14.1 → 2.14.3). `pip check` no encontró conflictos y todas las pruebas anteriores siguen pasando.
- Los archivos de práctica de la clase (`prueba_embeddings.py`, `test_chunking.py`, `rag_indexer.py`) se copiaron sin cambios y no se ejecutaron.
