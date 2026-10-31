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
    # Los 3 primeros son los mismos del Bloque 15 (pipeline_texto.py); el resto se agregó para el CORE del Bloque 17,
    # que pide al menos 20 respuestas. Cada caso es una tupla: (consulta para el modelo, referencia escrita a mano)
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
        # Propiedades y trámites en Chile
        (
            "¿Qué es la Unidad de Fomento (UF)?",
            "La UF es una unidad de cuenta chilena que se reajusta según la inflación y se usa para fijar precios de propiedades y créditos hipotecarios.",
        ),
        (
            "¿Qué institución recauda las contribuciones en Chile?",
            "La Tesorería General de la República recauda las contribuciones de bienes raíces.",
        ),
        (
            "¿En cuántas cuotas al año se pagan las contribuciones en Chile?",
            "Las contribuciones se pagan en cuatro cuotas al año: abril, junio, septiembre y noviembre.",
        ),
        (
            "¿Qué es el Conservador de Bienes Raíces?",
            "El Conservador de Bienes Raíces es el registro donde se inscriben la propiedad y los gravámenes de los inmuebles.",
        ),
        (
            "¿Qué documento acredita quién es el dueño actual de una propiedad en Chile?",
            "El certificado de dominio vigente, emitido por el Conservador de Bienes Raíces, acredita quién es el dueño actual.",
        ),
        (
            "¿Qué es un crédito hipotecario?",
            "Un crédito hipotecario es un préstamo para comprar una propiedad, que queda como garantía del pago.",
        ),
        (
            "¿Qué es el pie en la compra de una vivienda?",
            "El pie es el pago inicial que hace el comprador con sus propios fondos, y el resto se financia con un crédito.",
        ),
        (
            "¿Qué es la plusvalía de una propiedad?",
            "La plusvalía es el aumento del valor de una propiedad a lo largo del tiempo.",
        ),
        (
            "¿Qué es el rol de avalúo de una propiedad?",
            "El rol de avalúo es el número que el Servicio de Impuestos Internos asigna a cada propiedad para identificarla.",
        ),
        # Patrimonio y Barrio Brasil
        (
            "¿Qué es una zona típica en Chile?",
            "Una zona típica es un sector urbano protegido por la Ley de Monumentos Nacionales por su valor histórico o arquitectónico.",
        ),
        (
            "¿Qué ley protege los monumentos nacionales en Chile?",
            "La Ley 17.288 de Monumentos Nacionales protege el patrimonio histórico y arquitectónico de Chile.",
        ),
        (
            "¿En qué año se fundó Santiago de Chile?",
            "Santiago fue fundada en 1541 por Pedro de Valdivia.",
        ),
        (
            "¿En qué comuna está el Barrio Brasil?",
            "El Barrio Brasil está en la comuna de Santiago, en la Región Metropolitana.",
        ),
        # Estado de la construcción
        (
            "¿Qué es un muro medianero?",
            "Un muro medianero es una pared compartida entre dos propiedades vecinas.",
        ),
        (
            "¿Qué es una grieta estructural en una fachada?",
            "Una grieta estructural es una fisura que afecta la resistencia de los muros o elementos portantes del edificio.",
        ),
        (
            "¿Qué es la humedad por capilaridad en un muro?",
            "La humedad por capilaridad es el agua del suelo que sube por los muros y daña su parte baja.",
        ),
        (
            "¿Qué es un permiso de edificación?",
            "El permiso de edificación es la autorización de la Dirección de Obras Municipales para construir o ampliar una propiedad.",
        ),
        # Propiedades en abandono
        (
            "¿Cuáles son las principales señales de que una propiedad se encuentra en abandono?",
            "Las principales señales de abandono son ventanas rotas o tapiadas, basura y maleza acumuladas, rayados, correspondencia sin retirar y ausencia de luz o movimiento por mucho tiempo.",
        ),
        (
            "¿Una propiedad abandonada significa que no tiene dueño o que no tiene ocupantes?",
            "Una propiedad abandonada casi siempre tiene dueño: lo que le falta es uso y mantención, no un propietario.",
        ),
        (
            "¿Qué diferencia hay entre una propiedad desocupada y una propiedad abandonada?",
            "Una propiedad desocupada solo no tiene ocupantes, mientras que una abandonada además está sin mantención y deteriorándose.",
        ),
        (
            "¿A quién pertenece en Chile un inmueble que no tiene dueño?",
            "En Chile, un inmueble sin otro dueño pertenece al Estado, según el artículo 590 del Código Civil.",
        ),
        (
            "¿Qué riesgos genera una propiedad abandonada para el barrio?",
            "Una propiedad abandonada puede atraer ocupaciones ilegales, delitos, incendios y plagas, y bajar el valor de las propiedades vecinas.",
        ),
        (
            "¿Qué señales en la fachada indican que una propiedad no recibe mantención?",
            "La pintura descascarada, las grietas, la humedad, los rayados y los vidrios rotos indican que una fachada no recibe mantención.",
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

        # Muestra para revisar a mano (Bloque 17): los 5 de F1 más bajo y los 5 de F1 más alto.
        # Revisar también los mejores permite detectar puntajes altos que esconden un error (falsos positivos)
        muestra_para_revisar = peores_casos[:5] + peores_casos[-5:]
        print("\nMuestra para revisar a mano (F1 de menor a mayor):")
        for caso in muestra_para_revisar:
            print(f"  {caso['f1']:.2f}  {caso['consulta']}")
