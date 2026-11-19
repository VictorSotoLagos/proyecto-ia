from dotenv import load_dotenv
from langchain_core.documents import Document
from langchain_text_splitters import RecursiveCharacterTextSplitter  # Chunking recursivo
from langchain_google_genai import GoogleGenerativeAIEmbeddings  # Embeddings de Gemini (Claude no tiene modelo de embeddings)
from langchain_chroma import Chroma  # Vector store


CARPETA_VECTORSTORE = "vectorstore/"  # Está en .gitignore: se reconstruye corriendo este script

# Splitter recursivo: corta primero por párrafos y solo si un párrafo no cabe, por oraciones o palabras.
# Cada párrafo del corpus trae una sola idea y mide menos de 400 caracteres, así que un chunk queda con una idea
# completa. El overlap de 60 caracteres (15%, dentro del 10-20% visto en clase) conserva contexto si un párrafo
# largo se llega a cortar
CHUNK_SIZE = 400
CHUNK_OVERLAP = 60


#=== Corpus: documentación de la propia miniaplicación ===
# Cada documento resume una parte del proyecto. "fuente" dice de qué archivo sale, para poder citarlo después
# (Bloque 26), y "tema" sirve para armar los ids de los chunks
CORPUS = [
    Document(
        page_content=(
            "La miniaplicación es de la Comunidad Brasil Alameda y evalúa la fachada de una propiedad de Barrio "
            "Brasil o Concha y Toro, en Santiago, para detectar señales visibles de posible abandono.\n\n"
            "Con esas evaluaciones se busca armar un catastro del barrio que sirva de base para una propuesta "
            "comunitaria de renovación barrial y de recuperación del patrimonio arquitectónico y urbano.\n\n"
            "La evaluación la hace Claude Opus 5.5 a través de la API de Claude, y el resultado llega en formato JSON."
        ),
        metadata={"fuente": "README.md", "tema": "objetivo"},
    ),
    Document(
        page_content=(
            "El prompt evaluar_fachada analiza la foto de una fachada y responde un JSON con las claves "
            "fachada_visible, senales, pisos, evidencia y descripcion. Si la foto no muestra una fachada con "
            "claridad, fachada_visible es false.\n\n"
            "Las señales de abandono tienen nombres fijos: ventanas tapiadas, vanos abiertos o vidrios rotos, "
            "malezas, grafitis, pintura descascarada, revoque caído, techo dañado y escombros.\n\n"
            "La evidencia de abandono se califica con cinco niveles: ninguna, débil, moderada, fuerte o muy fuerte. "
            "La descripción tiene como máximo 2 oraciones con lo más grave que se ve."
        ),
        metadata={"fuente": "src/prompts/banco.py", "tema": "senales"},
    ),
    Document(
        page_content=(
            "La miniaplicación ofrece tres formas de pedir una evaluación: evaluar la foto de una fachada, revisar "
            "una dirección (por ejemplo, «Revisa la casa de Almirante Barroso 256») o buscar propiedades por barrio, "
            "pisos y señales. Las tres terminan en el mismo paso: el prompt evaluar_fachada.\n\n"
            "El prompt clasificar_solicitud reconoce si el usuario dio una dirección o pidió una búsqueda. En el "
            "Gate 1 solo funciona de punta a punta la evaluación de una foto; obtener las fotos desde Google Street "
            "View corresponde a los Gates 2 y 3."
        ),
        metadata={"fuente": "README.md", "tema": "formas_de_uso"},
    ),
    Document(
        page_content=(
            "Se eligió Claude Opus 5.5 porque la calidad es el criterio que más pesa: en 4 repeticiones con la misma "
            "foto de Almirante Barroso 256, Opus vio siempre que la casa perdió el techo y calificó siempre la "
            "evidencia como muy fuerte.\n\n"
            "Cada evaluación cuesta unos US$0,015 (alrededor de $15 CLP por propiedad) y tarda unos 8,6 segundos, "
            "lo que es aceptable porque no es un chat en tiempo real.\n\n"
            "Se descartó Claude Haiku 5.5, 31 veces más barato, porque en 2 de 4 intentos no mencionó el techo "
            "caído, y Claude Sonnet 5.5, porque no respetó el límite de 5 líneas y su latencia fue la más variable."
        ),
        metadata={"fuente": "docs/decision-arquitectura.md", "tema": "modelo"},
    ),
    Document(
        page_content=(
            "Si falla el modelo en una de las rutas del enrutamiento (dirección, búsqueda u otro), with_fallbacks "
            "repite la misma ruta con Claude Haiku 5.5. Si Haiku también falla, se entrega una respuesta genérica y "
            "queda un aviso WARNING con el error.\n\n"
            "Si el error ocurre antes de elegir una ruta, por ejemplo en la clasificación, lo atrapa el try/except "
            "de procesar_mensaje_seguro: registra el error con logger.error y devuelve un mensaje seguro, sin que el "
            "programa se caiga."
        ),
        metadata={"fuente": "docs/registro_orquestacion.md", "tema": "errores"},
    ),
    Document(
        page_content=(
            "El agente de la comunidad decide qué herramienta usar según la pregunta del vecino: consultar_propiedad "
            "para revisar una dirección, buscar_propiedades para buscar por barrio, pisos o señal, y "
            "guardar_nota_vecino para anotar lo que un vecino vio en una fachada.\n\n"
            "También tiene dos herramientas que salen de la comunidad: reportar_a_municipalidad y "
            "compartir_ficha_con_inversionista. Guarda un historial de conversación por vecino (session_id) y "
            "registra cada consulta en trazas_agente.jsonl."
        ),
        metadata={"fuente": "docs/registro_agente.md", "tema": "agente"},
    ),
    Document(
        page_content=(
            "Las herramientas de solo lectura del agente no piden aprobación. guardar_nota_vecino es de riesgo medio: "
            "escribe en el registro, pero un coordinador puede borrar la nota.\n\n"
            "Reportar a la Municipalidad y compartir una ficha son de riesgo alto porque no se pueden deshacer: un "
            "coordinador tiene que aprobarlas en la consola antes de 15 segundos, y si nadie responde, la acción no "
            "se hace.\n\n"
            "Antes de aprobar, el coordinador verifica la casa en terreno, sobre todo si podría estar tomada. La "
            "ficha compartida nunca incluye las notas de los vecinos."
        ),
        metadata={"fuente": "docs/limites_autonomia_agente.md", "tema": "limites"},
    ),
]


#=== Chunking ===
def dividir_corpus(corpus, chunk_size=CHUNK_SIZE, chunk_overlap=CHUNK_OVERLAP):
    splitter = RecursiveCharacterTextSplitter(chunk_size=chunk_size, chunk_overlap=chunk_overlap)
    # split_documents divide cada Document y cada chunk conserva la metadata (fuente y tema) de su documento
    return splitter.split_documents(corpus)


def generar_ids(chunks):
    # Ids estables, como el prefijo_id de la clase: "senales_1", "senales_2"... Si se vuelve a indexar, Chroma
    # actualiza los chunks con el mismo id en vez de duplicarlos
    ids = []
    contador = {}
    for chunk in chunks:
        tema = chunk.metadata["tema"]
        contador[tema] = contador.get(tema, 0) + 1
        ids.append(f"{tema}_{contador[tema]}")
    return ids


def verificar_integridad(chunks, corpus):
    # Igual que en la clase: revisar localmente, antes de gastar tokens en embeddings, que no haya chunks vacíos
    # ni duplicados
    vacios = [i for i, c in enumerate(chunks) if not c.page_content.strip()]
    textos = [c.page_content for c in chunks]
    hay_duplicados = len(textos) != len(set(textos))

    if vacios:
        raise ValueError(f"Se detectaron chunks vacíos en los índices: {vacios}")
    if hay_duplicados:
        print("Advertencia: se detectaron chunks duplicados en el corpus.")

    total_chars_chunks = sum(len(c.page_content) for c in chunks)
    total_chars_corpus = sum(len(d.page_content) for d in corpus)
    print(f"Integridad OK | Chunks: {len(chunks)} | Caracteres (corpus/chunks): {total_chars_corpus}/{total_chars_chunks}")


#=== Embeddings y vector store ===
def crear_embeddings():
    # Lee GEMINI_API_KEY del .env (por eso load_dotenv() va antes)
    return GoogleGenerativeAIEmbeddings(model="models/gemini-embedding-001")


def indexar(chunks, ids, embeddings, carpeta=CARPETA_VECTORSTORE):
    # Calcula un embedding por chunk (gasta tokens) y los guarda en disco junto a su texto y su metadata
    return Chroma.from_documents(documents=chunks, embedding=embeddings, ids=ids, persist_directory=carpeta)


def cargar_vectorstore(embeddings, carpeta=CARPETA_VECTORSTORE):
    # Abre la carpeta que ya existe en disco. NO gasta tokens
    return Chroma(persist_directory=carpeta, embedding_function=embeddings)


def inspeccionar_chunks(vectorstore):
    # Igual que en la clase: el inventario de lo que hay en Chroma (id, fuente y comienzo de cada chunk).
    # Usa vectorstore.get(), así que NO gasta tokens
    datos = vectorstore.get()
    total = len(datos["ids"])
    print(f"-- INVENTARIO DE CHUNKS EN CHROMA (Total: {total}) --")

    for i, (chunk_id, texto, meta) in enumerate(zip(datos["ids"], datos["documents"], datos["metadatas"]), start=1):
        resumen = texto.replace("\n", " ")[:100]  # Sin saltos de línea y solo los primeros 100 caracteres
        print(f"[{i}] ID: {chunk_id} | Fuente: {meta.get('fuente', 'desconocida')}")
        print(f"    Contenido: {resumen}...")


if __name__ == "__main__":
    load_dotenv()
    embeddings = crear_embeddings()

    # Primero se intenta reconectar: si el corpus ya está indexado, no se vuelven a calcular los embeddings
    vectorstore = cargar_vectorstore(embeddings)
    cantidad = vectorstore._collection.count()

    if cantidad > 0:
        print(f"El corpus ya está indexado en {CARPETA_VECTORSTORE}: {cantidad} chunks. No se recalculan embeddings.")
    else:
        chunks = dividir_corpus(CORPUS)
        verificar_integridad(chunks, CORPUS)
        ids = generar_ids(chunks)
        vectorstore = indexar(chunks, ids, embeddings)
        print(f"Indexados {len(chunks)} chunks de {len(CORPUS)} documentos en {CARPETA_VECTORSTORE}")

    inspeccionar_chunks(vectorstore)
