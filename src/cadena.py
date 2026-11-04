from dotenv import load_dotenv
import os
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain_core.prompts import ChatPromptTemplate


load_dotenv()

modelo = ChatAnthropic(model="claude-opus-5-5", anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"))
#respuesta = modelo.invoke("Qué es un token?")
#print(respuesta.content)

plantilla = PromptTemplate.from_template(
    "Explica el concepto de {tema} en un párrafo, para alguien que recién comienza en {area}."
)

#prompt = plantilla.invoke({"tema": "tokenizacion", "area": "procesamiento de texto"})

#print(prompt.text)

cadena_simple = plantilla | modelo | StrOutputParser()

respuesta = cadena_simple.invoke({"tema": "embeddings", "area": "búsqueda semántica"})

print(respuesta)

plantilla_conrol = ChatPromptTemplate.from_messages([
    ("system", "Eres un experto en {area} y tu tarea es explicar conceptos complejos de manera sencilla."),
    ("user", "Explica el concepto de {tema} en un párrafo, para alguien que recién comienza en {area}.")

])