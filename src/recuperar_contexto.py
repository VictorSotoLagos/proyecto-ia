from dotenv import load_dotenv
from indexar_corpus import crear_embeddings, cargar_vectorstore  # Se reconecta al índice: no vuelve a indexar


def formatear_contexto(chunks_recuperados):
    # Igual que en la clase: numera cada chunk recuperado y guarda de qué fuente salió, para poder citarla
    lineas = []
    citas = {}

    for i, doc in enumerate(chunks_recuperados, start=1):
        # Si un chunk no tiene "fuente" en su metadata, queda como "desconocida"
        fuente = doc.metadata.get("fuente", "desconocida")
        lineas.append(f"[{i}] {doc.page_content}")
        citas[i] = fuente

    contexto = "\n\n".join(lineas)
    return contexto, citas


if __name__ == "__main__":
    load_dotenv()
    vectorstore = cargar_vectorstore(crear_embeddings())

    # as_retriever adapta Chroma para poder usarlo dentro de una chain o de un agente de LangChain.
    # k = cantidad de chunks que devuelve
    retriever = vectorstore.as_retriever(search_kwargs={"k": 2})

    pregunta = "¿Qué hace la aplicación si falla el modelo?"
    chunks_recuperados = retriever.invoke(pregunta)  # 1 llamada a Gemini: el embedding de la pregunta

    contexto, citas = formatear_contexto(chunks_recuperados)
    print("Pregunta:", pregunta)
    print("--CONTEXTO FORMATEADO--")
    print(contexto)
    print("--DICCIONARIO DE CITAS--")
    print(citas)
