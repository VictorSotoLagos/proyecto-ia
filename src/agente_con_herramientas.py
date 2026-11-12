from dotenv import load_dotenv
import os
from langchain_anthropic import ChatAnthropic
from langchain_core.tools import tool
from langchain_classic.agents import (
    AgentExecutor,
    create_tool_calling_agent,
)
from langchain_core.prompts import (
    ChatPromptTemplate,
    MessagesPlaceholder,
)

load_dotenv()

modelo = ChatAnthropic(model="claude-opus-5-5", anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"))

#Tool/Herramienta es una función común de Python. Descripción en lenguaje natural será lo que el modelo lea (prompt) para decidir si elige o no esa herramienta
@tool
def buscar_en_documentacion(consulta:str) -> str:
    """
    Busca información relevante de la documentación interna del producto.
    Usar cuando la pregunta es sobre cómo funciona algo del sistema.
    """
    documentacion = {
        "reintentos": "El cliente reintenta hasta 3 veces ante un TimeoutError, con espera creciente",
        "costos": "El costo se calcula a patir de totalTokenCount, según la tarifa vigente."
    }

    for clave, texto in documentacion.items():
        if clave in consulta.lower():
            return texto

    return "No se encontró información sobre esa consulta en la documentación."

@tool
def calcular(expresion: str) -> str:
    """
    Evalúa una expresión aritmética simple, como '350 + 250'.
    Usar cuando la pregunta require un cálculo numérico.
    """
    permitido = set("0123456789+-*/().")
    if not set(expresion) <= permitido:
        return "Expresión no permitida."
    try:
        return str(eval(expresion))
    except Exception as e:
        return f"Error al evaluar: {e}"

herramientas = [buscar_en_documentacion, calcular] #Lista de Herramientas

#Plantilla, con system_instructions
prompt_agente = ChatPromptTemplate.from_messages([
    (
        "system", "Eres un asistente que responde preguntas usando las herramientas disponibles cuando las necesites."
    ),
    # (
    #     "system", "Eres un asistente que responde preguntas solamente usando las herramientas disponibles cuando las necesites. No inventes información que no tengas."
    # ),
    (
        "human", "{entrada}"
    ),
    MessagesPlaceholder("agent_scratchpad") #El espacio donde LangChain va anotando, pasos/ciclos razonar-actuar-observar, qué herramientas llamó y qué devolvieron
])

#Agente: modelo, herramientas, prompt, formato
agente = create_tool_calling_agent(
    modelo, herramientas, prompt_agente
)

#Orquestador: es el que controla el ciclo entre razonar-actuar-observar
ejecutor_agente = AgentExecutor(
    agent=agente,
    tools=herramientas,
    verbose=True, #Imprime los pasos que va siguiendo
)

#Con Claude, la respuesta llega como una lista de bloques: primero el razonamiento (thinking) y después el texto.
#Por eso no sirve resultado["output"][0]["text"] como con Gemini: se busca el bloque de tipo "text"
def extraer_texto(salida):
    if isinstance(salida, str):
        return salida
    texto = ""
    for bloque in salida:
        if bloque.get("type") == "text":
            texto += bloque["text"]
    return texto

resultado = ejecutor_agente.invoke(
    {"entrada": "¿Qué es LangChain?"}
)

print("Respuesta Final:", extraer_texto(resultado["output"]))
