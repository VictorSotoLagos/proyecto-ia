import json
from collections import Counter  # Cuenta cuántas veces aparece cada valor
from google.genai import types

# Archivo que se sube al bucket de Google Cloud para entrenar, con el mismo formato que docs/ejemplos_tuning.jsonl
# de la clase
ARCHIVO_JSONL = "docs/ejemplos_tuning.jsonl"
CLAVES_ESPERADAS = ("categoria", "barrio")

# Paso 1: el dataset. Es una tarea de comportamiento consistente (clasificación con formato fijo), no de
# conocimiento, que sería un caso para RAG. El modelo clasifica el mensaje de un vecino con las mismas categorías
# del prompt clasificar_solicitud y del enrutador (direccion, busqueda u otro), y dice qué barrio nombra, con las
# 3 etiquetas de extraer_direccion. El barrio sale solo de lo que dice el mensaje: si no lo nombra, es
# "no indicado", aunque la calle sea conocida.
ejemplos_raw = [
    # direccion
    ("Revisa la casa de Almirante Barroso 256, en Barrio Brasil.",  # text_input
     {"categoria": "direccion", "barrio": "Barrio Brasil"}),  # output
    ("hola, me puedes evaluar la fachada de maturana 520? queda en el barrio brasil",
     {"categoria": "direccion", "barrio": "Barrio Brasil"}),
    ("Necesito la ficha de la propiedad de Erasmo Escala 2140, en el barrio Concha y Toro.",
     {"categoria": "direccion", "barrio": "Concha y Toro"}),
    ("Pasé por Romero 2045, en Concha y Toro. ¿Me ayudas a evaluar esa fachada?",
     {"categoria": "direccion", "barrio": "Concha y Toro"}),
    ("¿En qué estado está la casa de Almirante Barroso 256?",
     {"categoria": "direccion", "barrio": "no indicado"}),
    # busqueda
    ("Muéstrame propiedades de dos pisos en Barrio Brasil que tengan grafitis y vidrios rotos.",
     {"categoria": "busqueda", "barrio": "Barrio Brasil"}),
    ("¿Hay casas con el techo dañado y escombros en la entrada en Concha y Toro?",
     {"categoria": "busqueda", "barrio": "Concha y Toro"}),
    ("necesito encontrar propiedades en concha y toro con la pintura descascarada",
     {"categoria": "busqueda", "barrio": "Concha y Toro"}),
    ("Quiero ver casas de un piso con revoque caído.",
     {"categoria": "busqueda", "barrio": "no indicado"}),
    ("Busca propiedades con ventanas tapiadas, da lo mismo el barrio.",
     {"categoria": "busqueda", "barrio": "no indicado"}),
    # otro
    ("¿Qué día pasa el camión de la basura por el Barrio Brasil?",
     {"categoria": "otro", "barrio": "Barrio Brasil"}),
    ("Cuéntame la historia del Barrio Brasil.",
     {"categoria": "otro", "barrio": "Barrio Brasil"}),
    ("¿Cuándo es la próxima reunión de vecinos en Concha y Toro?",
     {"categoria": "otro", "barrio": "Concha y Toro"}),
    ("¿Cómo me puedo sumar a la Comunidad Brasil Alameda?",
     {"categoria": "otro", "barrio": "no indicado"}),
    ("¿Cuánto se demora la aplicación en evaluar una fachada?",
     {"categoria": "otro", "barrio": "no indicado"}),
]

# Cada ejemplo queda como un TuningExample: el texto de entrada y la salida exacta que el modelo debe aprender
examples = [
    types.TuningExample(text_input=texto, output=json.dumps(salida, ensure_ascii=False))
    for texto, salida in ejemplos_raw
]


# Paso 2: el balance. Un dataset muy desbalanceado entrena un modelo sesgado hacia la categoría más frecuente
def chequear_balance(ejemplos_raw: list[tuple[str, dict]], clave: str) -> Counter:
    categorias = Counter(salida[clave] for _, salida in ejemplos_raw)
    return categorias


# Paso 3: la validación. Tiene que devolver una lista vacía antes de enviar nada a entrenar
def validar_dataset(
    examples: list[types.TuningExample], claves_esperadas: tuple[str, ...]
) -> list[str]:
    problemas = []
    vistos = set()
    for i, ej in enumerate(examples):
        if not ej.text_input or not ej.text_input.strip():
            problemas.append(f"ejemplo {i}: text_input vacio")
        if not ej.output or not ej.output.strip():
            problemas.append(f"ejemplo {i}: output vacio")
            continue
        if ej.text_input in vistos:
            problemas.append(f"ejemplo {i}: text_input duplicado")
        vistos.add(ej.text_input)
        try:
            salida = json.loads(ej.output)
        except json.JSONDecodeError:
            problemas.append(f"ejemplo {i}: output no es JSON valido")
            continue
        for clave in claves_esperadas:
            if clave not in salida:
                problemas.append(f'ejemplo {i}: output no tiene la clave "{clave}"')
    return problemas


def guardar_jsonl(ejemplos_raw: list[tuple[str, dict]], ruta_archivo: str = ARCHIVO_JSONL) -> None:
    """
    Escribe el dataset en el formato que lee Google Cloud: una línea por ejemplo, con un turno "user" (el mensaje)
    y un turno "model" (el JSON de salida). Es el mismo patrón de guardar_registro_jsonl del Bloque 28.
    """
    # newline="\n" deja saltos de línea LF también en Windows, igual que en el archivo de la clase
    with open(ruta_archivo, "w", encoding="utf-8", newline="\n") as f:
        for texto, salida in ejemplos_raw:
            linea = {"contents": [
                {"role": "user", "parts": [{"text": texto}]},
                {"role": "model", "parts": [{"text": json.dumps(salida, ensure_ascii=False)}]},
            ]}
            f.write(json.dumps(linea, ensure_ascii=False) + "\n")


if __name__ == "__main__":
    print(len(examples), "ejemplos construidos")
    print(examples[0])

    for clave in CLAVES_ESPERADAS:
        print(f"\nBalance por {clave}:")
        for valor, cuenta in chequear_balance(ejemplos_raw, clave).most_common():
            print(f"{valor}: {cuenta}")

    problemas = validar_dataset(examples, claves_esperadas=CLAVES_ESPERADAS)
    print(f"\n{len(examples)} ejemplos, {len(problemas)} problemas encontrados")
    for p in problemas:
        print(" -", p)

    # Solo un dataset sin problemas se guarda para subirlo al bucket
    if not problemas:
        guardar_jsonl(ejemplos_raw)
        print(f"Dataset guardado en {ARCHIVO_JSONL}, listo para subirlo al bucket")
