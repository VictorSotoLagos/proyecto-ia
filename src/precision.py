import json  # para guardar los resultados en un archivo
from collections import Counter  # cuenta cuántas veces aparece cada elemento de una lista

from cliente import consultar_modelo
from pipeline_texto import procesar_texto


def contar_coincidencias(
    tokens_referencia: list[str],
    tokens_respuesta: list[str],
) -> int:
    """Cuenta las coincidencias entre referencia y respuesta."""
    conteo_referencia = Counter(tokens_referencia)
    conteo_respuesta = Counter(tokens_respuesta)
    # & entre dos Counter toma, para cada palabra, el mínimo de veces que aparece en los dos lados:
    # así una palabra repetida de más en la respuesta no suma coincidencias extra (set() no hacía esa diferencia)
    interseccion = conteo_referencia & conteo_respuesta
    return sum(interseccion.values())  # el total de coincidencias

def calcular_precision_cobertura_f1(
    tokens_referencia: list[str],
    tokens_respuesta: list[str],
) -> dict[str, float]:
    """Calcula precisión, cobertura y F1 de dos listas de tokens."""
    coincidencias = contar_coincidencias(
        tokens_referencia, tokens_respuesta
    )

    # Si algún lado quedó vacío (por ejemplo, una respuesta vacía), se evita dividir por cero
    if not tokens_respuesta or not tokens_referencia:
        return {"precision": 0.0, "cobertura": 0.0, "f1": 0.0}

    # Precisión: de todo lo que respondió el modelo, cuánto aparece en la referencia
    precision = coincidencias / len(tokens_respuesta)
    # Cobertura: de todo lo que debía decir (la referencia), cuánto dijo
    cobertura = coincidencias / len(tokens_referencia)

    # F1 combina precisión y cobertura en un solo número balanceado
    if precision + cobertura == 0:
        f1 = 0.0
    else:
        f1 = 2 * precision * cobertura / (precision + cobertura)

    resultado = {
        "precision": precision,
        "cobertura": cobertura,
        "f1": f1,
    }

    return resultado

def calcular_metricas(texto_referencia: str, texto_respuesta: str) -> dict[str, float]:
    """Procesa los dos textos y calcula precisión, cobertura y F1 en una sola llamada."""
    # Los dos lados pasan por el pipeline: así nunca se compara un texto procesado con uno crudo
    tokens_referencia = procesar_texto(texto_referencia)
    tokens_respuesta = procesar_texto(texto_respuesta)

    return calcular_precision_cobertura_f1(
        tokens_referencia, tokens_respuesta
    )

def resumir_metricas(resultados: list[dict]) -> dict[str, float]:
    """Calcula el promedio de precisión, cobertura y F1 de varios resultados."""
    if not resultados:
        return {
            "precision_promedio": 0,
            "cobertura_promedio": 0,
            "f1_promedio": 0,
        }

    n = len(resultados)

    # sum(r["precision"] for r in resultados) recorre cada resultado y suma su precisión
    return {
        "precision_promedio": sum(
            r["precision"] for r in resultados
        ) / n,

        "cobertura_promedio": sum(
            r["cobertura"] for r in resultados
        ) / n,

        "f1_promedio": sum(r["f1"] for r in resultados) / n,
    }


if __name__ == "__main__": # Solo se ejecuta al correr este archivo directamente, NO cuando otro archivo lo importa
    # Los mismos casos del Bloque 15 (pipeline_texto.py), para comparar la métrica vieja con la nueva.
    # Cada caso es una tupla: (consulta para el modelo, referencia escrita a mano)
    casos = [
        (
            "¿Qué es la tasación de una propiedad?",
            "La tasación es la estimación del valor comercial de una propiedad, realizada por un tasador.",
        ),
        (
            "¿Qué es el avalúo fiscal de una propiedad en Chile?",
            "El avalúo fiscal es el valor que el Servicio de Impuestos Internos asigna a una propiedad para calcular las contribuciones.",
        ),
        (
            "¿Qué es la fachada de un edificio?",
            "La fachada es el exterior visible de un edificio, especialmente su frente principal.",
        ),
    ]
    # Se pide una respuesta corta para que se pueda comparar con una referencia de una sola oración
    system_instruction = "Responde en una sola oración breve, en español."

    resultados = []

    try:
        # El for separa cada tupla en sus dos partes: consulta y referencia
        for consulta, referencia in casos:
            respuesta = consultar_modelo(consulta, system_instruction)
            metricas = calcular_metricas(referencia, respuesta)

            print(f"\nConsulta: {consulta}")
            print(f"Respuesta: {respuesta}")
            print(f"Precisión: {metricas['precision']:.2f} | Cobertura: {metricas['cobertura']:.2f} | F1: {metricas['f1']:.2f}")

            # **metricas agrega a este diccionario las tres claves de metricas: precision, cobertura y f1
            resultados.append({
                "consulta": consulta,
                "referencia": referencia,
                "respuesta": respuesta,
                **metricas,
            })
    except (ValueError, RuntimeError, TimeoutError) as error:
        print("No se pudo completar la operación:", error)

    # Se guarda lo que se alcanzó a calcular, aunque alguna petición haya fallado a mitad de camino
    if resultados:
        with open("docs/resultados_metricas.json", "w", encoding="utf-8") as archivo:
            json.dump(resultados, archivo, indent=2, ensure_ascii=False)
        print("\nResultados guardados en docs/resultados_metricas.json")

        promedios = resumir_metricas(resultados)
        print(f"\nPromedios -> Precisión: {promedios['precision_promedio']:.2f} | Cobertura: {promedios['cobertura_promedio']:.2f} | F1: {promedios['f1_promedio']:.2f}")

        # Peores casos primero: sorted ordena de menor a mayor, y lambda le indica que mire el F1 de cada resultado
        peores_casos = sorted(resultados, key=lambda r: r["f1"])
        print("\nPeores casos (F1 de menor a mayor):")
        for caso in peores_casos[:3]:
            print(f"  {caso['f1']:.2f}  {caso['consulta']}")
