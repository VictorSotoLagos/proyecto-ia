from dotenv import load_dotenv
from datetime import date
from indexar_corpus import crear_embeddings, cargar_vectorstore, CHUNK_SIZE, CHUNK_OVERLAP

K = 3  # Cuántos chunks recupera el retriever y cuántos evalúan las métricas (el mismo valor en los dos lados)
K_COMPARACION = 5  # Para ver el trade-off: con más chunks, el recall sube o se mantiene y la precisión baja o se mantiene


#=== Conjunto de evaluación ===
# Los ids relevantes se etiquetaron a mano leyendo el texto de cada chunk (inspeccionar_chunks), ANTES de correr el
# retriever, para medir contra un criterio independiente y no ajustar las etiquetas hasta que la métrica dé bien
CASOS_EVALUACION = [
    {"pregunta": "¿Para qué sirve la miniaplicación de la Comunidad Brasil Alameda?",
     "ids_relevantes": {"objetivo_1"}},
    {"pregunta": "¿Qué modelo de IA evalúa las fachadas y en qué formato entrega el resultado?",
     "ids_relevantes": {"objetivo_2"}},
    {"pregunta": "¿Qué claves tiene el JSON que devuelve la evaluación de una fachada?",
     "ids_relevantes": {"senales_1"}},
    {"pregunta": "¿Cuáles son las señales de abandono que se buscan en una fachada?",
     "ids_relevantes": {"senales_2"}},
    {"pregunta": "¿Qué niveles de evidencia de abandono existen?",
     "ids_relevantes": {"senales_2"}},
    {"pregunta": "¿De qué maneras puede un vecino pedir que se evalúe una propiedad?",
     "ids_relevantes": {"formas_de_uso_1"}},
    {"pregunta": "¿Cuándo se van a obtener las fotos desde Google Street View?",
     "ids_relevantes": {"formas_de_uso_2"}},
    {"pregunta": "¿Cuánto cuesta evaluar una propiedad y cuánto se demora?",
     "ids_relevantes": {"modelo_1"}},
    {"pregunta": "¿Por qué no se usó un modelo más barato como Haiku?",
     "ids_relevantes": {"modelo_2"}},
    {"pregunta": "¿Qué pasa si la clasificación del mensaje falla?",
     "ids_relevantes": {"errores_2"}},
    {"pregunta": "¿Qué herramientas puede usar el agente sin salir de la comunidad?",
     "ids_relevantes": {"agente_1"}},
    {"pregunta": "¿Qué acciones del agente necesitan que un coordinador las apruebe?",
     "ids_relevantes": {"limites_1"}},
    {"pregunta": "¿Qué debe revisar el coordinador antes de aprobar un reporte?",
     "ids_relevantes": {"limites_2"}},
    {"pregunta": "¿Qué cuidados se toman antes de reportar o compartir una propiedad?",
     "ids_relevantes": {"limites_1", "limites_2"}},
    # Sin respuesta en el corpus: su recall queda como "n/a" y no entra al promedio de recall
    {"pregunta": "¿Cuál es el horario de atención de la Municipalidad de Santiago?",
     "ids_relevantes": set()},
]


#=== Métricas (las mismas de la clase) ===
def precision_at_k(ids_recuperados, ids_relevantes):
    """De los k chunks que trajo el retriever, ¿qué fracción realmente sirve? (0.0 si no trajo ninguno)."""
    if not ids_recuperados:
        return 0.0
    acertados = [i for i in ids_recuperados if i in ids_relevantes]
    return len(acertados) / len(ids_recuperados)


def recall_at_k(ids_recuperados, ids_relevantes):
    """De todos los chunks relevantes, ¿qué fracción se recuperó? (None si la pregunta no tiene respuesta en el corpus)."""
    if not ids_relevantes:
        return None
    acertados = [i for i in ids_recuperados if i in ids_relevantes]
    return len(acertados) / len(ids_relevantes)


def f1_score(precision, recall):
    """Media armónica entre precisión y recall (0.0 si no hay recall o si ambos son 0)."""
    if recall is None or (precision + recall) == 0:
        return 0.0
    return 2 * precision * recall / (precision + recall)


def promediar(valores):
    """Promedio que ignora los None y evita dividir por cero."""
    validos = [v for v in valores if v is not None]
    return sum(validos) / len(validos) if validos else 0.0


def evaluar_recuperacion(retriever, casos, k=K):
    """Corre cada caso contra el retriever real y promedia precisión, recall y F1."""
    resultados = []
    for caso in casos:
        chunks = retriever.invoke(caso["pregunta"])  # Gasta tokens: el embedding de la pregunta
        ids_recuperados = [c.id for c in chunks][:k]
        p = precision_at_k(ids_recuperados, caso["ids_relevantes"])
        r = recall_at_k(ids_recuperados, caso["ids_relevantes"])
        # Sin respuesta en el corpus, el F1 tampoco se puede calcular: queda en None, igual que el recall
        f1 = None if r is None else f1_score(p, r)
        resultados.append({"pregunta": caso["pregunta"], "ids_recuperados": ids_recuperados,
                           "precision": p, "recall": r, "f1": f1})

    precision_promedio = promediar(x["precision"] for x in resultados)
    recall_promedio = promediar(x["recall"] for x in resultados)
    f1_promedio = promediar(x["f1"] for x in resultados)
    return resultados, precision_promedio, recall_promedio, f1_promedio


#=== Registro de la corrida ===
def formatear_linea(resultado):
    recall_txt = "n/a" if resultado["recall"] is None else f"{resultado['recall']:.2f}"
    f1_txt = "n/a" if resultado["f1"] is None else f"{resultado['f1']:.2f}"
    return f"{resultado['precision']:.2f} {recall_txt} {f1_txt} {resultado['pregunta']}"


def guardar_resultados(archivo, k, resultados, precision_promedio, recall_promedio, f1_promedio):
    # chunk_size y chunk_overlap se leen de indexar_corpus.py, así la configuración anotada es la que se usó
    with open(archivo, "w", encoding="utf-8") as f:
        f.write(f"Fecha: {date.today()}\n")
        f.write(f"Configuracion: k={k}, chunk_size={CHUNK_SIZE}, chunk_overlap={CHUNK_OVERLAP}\n")
        f.write("Columnas: precision recall f1 pregunta\n\n")
        for r in resultados:
            f.write(formatear_linea(r) + "\n")
        f.write(f"\npromedio -> precision: {precision_promedio:.3f} recall: {recall_promedio:.3f} f1: {f1_promedio:.3f}\n")


if __name__ == "__main__":
    load_dotenv()
    vectorstore = cargar_vectorstore(crear_embeddings())

    # La corrida principal (k=3) y la de comparación (k=5), cada una en su propio archivo
    for k, archivo in [(K, "docs/resultados_evaluacion.txt"), (K_COMPARACION, "docs/resultados_evaluacion_k5.txt")]:
        retriever = vectorstore.as_retriever(search_kwargs={"k": k})
        resultados, precision_promedio, recall_promedio, f1_promedio = evaluar_recuperacion(
            retriever, CASOS_EVALUACION, k=k
        )

        print(f"=== k={k} | columnas: precision recall f1 pregunta ===")
        for r in resultados:
            print(formatear_linea(r))
        print(f"\npromedio -> precision: {precision_promedio:.3f} recall: {recall_promedio:.3f} f1: {f1_promedio:.3f}\n")

        guardar_resultados(archivo, k, resultados, precision_promedio, recall_promedio, f1_promedio)
        print(f"Resultados guardados en {archivo}\n")
