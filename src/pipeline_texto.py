import re  # expresiones regulares: buscar y reemplazar patrones de texto
from collections import Counter  # cuenta cuántas veces aparece cada elemento de una lista

from cliente import consultar_modelo


def limpiar_texto(texto: str) -> str:
    """Normaliza el texto: minúsculas y sin puntuación."""
    # Si no llega un str (por ejemplo None, un número o la respuesta completa de la API),
    # se avisa con un TypeError claro en vez de un AttributeError confuso en texto.lower()
    if not isinstance(texto, str):
        tipo = type(texto).__name__  # el nombre del tipo que llegó, por ejemplo "NoneType" o "dict"
        raise TypeError(f"limpiar_texto espera str, no {tipo}")

    texto = texto.lower()
    # [^\w\s] es "cualquier cosa que no sea letra, número o espacio": se reemplaza por nada
    texto = re.sub(r"[^\w\s]", "", texto)
    # \s+ es "uno o más espacios seguidos": se reemplazan por uno solo; strip() quita los de los bordes
    texto = re.sub(r"\s+", " ", texto).strip()
    return texto

def tokenizar(texto_limpio: str) -> list[str]:
    """Convierte texto limpio en una lista de tokens."""
    return texto_limpio.split()  # separa por espacios: cada palabra es un token

def procesar_texto(texto: str) -> list[str]:
    """Limpia y tokeniza el texto en un solo paso."""
    # Juntar los dos pasos en una función evita olvidar alguno antes de calcular una métrica
    texto_limpio = limpiar_texto(texto)
    return tokenizar(texto_limpio)

def vectorizar(tokens: list[str]) -> Counter:
    """Cuenta cuántas veces aparece cada token."""
    return Counter(tokens)


if __name__ == "__main__": # Solo se ejecuta al correr este archivo directamente, NO cuando otro archivo lo importa
    # Cada caso: una consulta para el modelo y una referencia escrita a mano con la respuesta esperada
    casos = [
        {
            "consulta": "¿Qué es la tasación de una propiedad?",
            "referencia": "La tasación es la estimación del valor comercial de una propiedad, realizada por un tasador.",
        },
        {
            "consulta": "¿Qué es el avalúo fiscal de una propiedad en Chile?",
            "referencia": "El avalúo fiscal es el valor que el Servicio de Impuestos Internos asigna a una propiedad para calcular las contribuciones.",
        },
        {
            "consulta": "¿Qué es la fachada de un edificio?",
            "referencia": "La fachada es el exterior visible de un edificio, especialmente su frente principal.",
        },
    ]
    # Se pide una respuesta corta para que se pueda comparar con una referencia de una sola oración
    system_instruction = "Responde en una sola oración breve, en español."

    try:
        # enumerate entrega el número de cada caso (desde 1) junto con el caso
        for numero, caso in enumerate(casos, start=1):
            referencia = caso["referencia"]
            respuesta = consultar_modelo(caso["consulta"], system_instruction)

            # Antes: texto crudo, separado solo por espacios
            crudo_ref = referencia.split()
            crudo_resp = respuesta.split()
            comunes_crudo = set(crudo_ref) & set(crudo_resp)
            if crudo_ref:
                pct_crudo = len(comunes_crudo) / len(set(crudo_ref))
            else:
                pct_crudo = 0.0

            # Después: los dos lados pasan por el pipeline
            tokens_ref = procesar_texto(referencia)
            tokens_resp = procesar_texto(respuesta)
            comunes = set(tokens_ref) & set(tokens_resp)
            if tokens_ref:
                pct_proc = len(comunes) / len(set(tokens_ref))
            else:
                pct_proc = 0.0

            print(f"\n[Caso {numero}] Consulta: {caso['consulta']}")
            print(f"[Caso {numero}] Referencia: {referencia}")
            print(f"[Caso {numero}] Respuesta: {respuesta}")
            print(f"[Caso {numero}] Coincidencia texto crudo: {pct_crudo:.1%}")
            print(f"[Caso {numero}] Coincidencia texto procesado: {pct_proc:.1%}")
    except (ValueError, RuntimeError, TimeoutError) as error:
        print("No se pudo completar la operación:", error)
