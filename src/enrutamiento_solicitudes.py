from dotenv import load_dotenv
import os
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import ChatPromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnableBranch, RunnablePassthrough

# Rol del sistema que comparten las 4 plantillas, igual que el system_instruction del banco de prompts del Gate 1
instruccion_sistema = (
    "Eres el asistente de una aplicación de la Comunidad Brasil Alameda que detecta propiedades "
    "en posible abandono en Barrio Brasil y Concha y Toro, Santiago."
)

# 1. Clasificación de la entrada: las mismas categorías del prompt clasificar_solicitud del Gate 1
plantilla_clasificacion = ChatPromptTemplate.from_messages([
    ("system", instruccion_sistema),
    ("human", "Clasifica el siguiente mensaje en una sola palabra, sin tilde: direccion (si menciona "
              "la dirección de una propiedad específica), busqueda (si pide encontrar propiedades con "
              "ciertas características) u otro (si no es ninguna de las dos). Responde solo con esa "
              "palabra.\n\n{mensaje}")
])

# 2. Las tres rutas posibles, cada una con su propio prompt
plantilla_direccion = ChatPromptTemplate.from_messages([
    ("system", instruccion_sistema),
    ("human", "El usuario menciona la dirección de una propiedad. Extrae los datos y responde en "
              "3 líneas: 'Calle: ...', 'Número: ...' y 'Barrio: ...' (Barrio Brasil, Concha y Toro "
              "o no indicado). Si falta un dato, escribe 'no indicado'.\n\n{mensaje}")
])

plantilla_busqueda = ChatPromptTemplate.from_messages([
    ("system", instruccion_sistema),
    ("human", "El usuario pide buscar propiedades en posible abandono. Extrae sus criterios y "
              "responde en 3 líneas: 'Barrio: ...' (Barrio Brasil, Concha y Toro o no indicado), "
              "'Pisos: ...' (número o no indicado) y 'Señales: ...' usando solo estos nombres: "
              "ventanas tapiadas, vanos abiertos o vidrios rotos, malezas, grafitis, pintura "
              "descascarada, revoque caído, techo dañado o escombros.\n\n{mensaje}")
])

plantilla_otro = ChatPromptTemplate.from_messages([
    ("system", instruccion_sistema),
    ("human", "El siguiente mensaje no es una dirección ni una búsqueda. Responde con amabilidad, "
              "en máximo dos oraciones, y explica que puede indicar la dirección de una propiedad "
              "o pedir una búsqueda por barrio, pisos o señales de abandono.\n\n{mensaje}")
])


def construir_paso_clasificacion(modelo):
    return (
        plantilla_clasificacion
        | modelo
        | StrOutputParser()
        | (lambda texto: texto.strip().lower())
    )


# 3. La bifurcación que conecta la clasificación con las rutas
def construir_cadena_con_enrutamiento(
    paso_clasificacion,
    cadena_direccion=None,
    cadena_busqueda=None,
    cadena_otro=None,
):
    # Si una ruta no se recibe, se usa RunnablePassthrough(); en las pruebas basta con pasar la ruta que se verifica
    cadena_direccion = cadena_direccion or RunnablePassthrough()
    cadena_busqueda = cadena_busqueda or RunnablePassthrough()
    cadena_otro = cadena_otro or RunnablePassthrough()
    bifurcacion = RunnableBranch(
        (lambda x: x["categoria"] == "direccion", cadena_direccion),
        (lambda x: x["categoria"] == "busqueda", cadena_busqueda),
        cadena_otro,  # Ruta por defecto: cualquier categoría que no sea direccion ni busqueda
    )
    return (
        RunnablePassthrough.assign(categoria=paso_clasificacion)
        | bifurcacion
    )


if __name__ == "__main__":
    load_dotenv()
    modelo = ChatAnthropic(model="claude-opus-5-5", anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"))

    paso_clasificacion = construir_paso_clasificacion(modelo)
    cadena_con_enrutamiento = construir_cadena_con_enrutamiento(
        paso_clasificacion=paso_clasificacion,
        cadena_direccion=plantilla_direccion | modelo | StrOutputParser(),
        cadena_busqueda=plantilla_busqueda | modelo | StrOutputParser(),
        cadena_otro=plantilla_otro | modelo | StrOutputParser(),
    )

    # Un mensaje por cada ruta, tomados de las formas de uso del README
    mensajes = [
        "Revisa la casa de Almirante Barroso 256, en Barrio Brasil.",
        "Dame una casa en Barrio Brasil de un piso, con ventanas tapiadas y malezas.",
        "Hola, ¿quién creó esta aplicación?",
    ]

    for mensaje in mensajes:
        print("Mensaje:", mensaje)
        print(cadena_con_enrutamiento.invoke({"mensaje": mensaje}))
        print()
