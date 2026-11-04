from dotenv import load_dotenv
import os
from langchain_anthropic import ChatAnthropic
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser


def construir_cadena(modelo):
    # Paso 1: Estado observado. Describe la fachada sin juzgar si está en abandono
    plantilla_estado = PromptTemplate.from_template(
        "Lee el siguiente reporte de un vecino sobre una propiedad y describe solo el estado observado "
        "de su fachada: pisos, puertas, ventanas, muros, techo y vereda. Sé objetivo, no juzgues si "
        "está en abandono y no agregues nada que el reporte no diga. Máximo 4 líneas: \n\n {reporte}"
    )

    # Paso 2: Daño observable. Usa las mismas 8 señales del prompt evaluar_fachada del Gate 1
    plantilla_danos = PromptTemplate.from_template(
        "A partir de este estado observado, lista los daños visibles usando solo estos nombres: "
        "ventanas tapiadas, vanos abiertos o vidrios rotos, malezas, grafitis, pintura descascarada, "
        "revoque caído, techo dañado o escombros. Uno por línea, sin explicaciones. Si no hay "
        "ninguno, escribe 'Sin daños observables': \n\n {estado}"
    )

    # Paso 3: Conclusión. Usa la misma escala de evidencia del Gate 1
    plantilla_conclusion = PromptTemplate.from_template(
        "A partir de estos daños observables, concluye si la propiedad está 'En posible abandono', "
        "'No en abandono' o 'No se puede determinar'. Indica el nivel de evidencia (ninguna, débil, "
        "moderada, fuerte o muy fuerte) y justifica en una oración. Responde en 3 líneas, con los "
        "títulos Conclusión, Evidencia y Justificación, en texto simple sin markdown: \n\n {danos}"
    )

    #Sintaxis lambda -> lambda argumentos: expresion
    cadena = (
        plantilla_estado
        | modelo
        | StrOutputParser()
        | (lambda estado: {"estado": estado})
        | plantilla_danos
        | modelo
        | StrOutputParser()
        | (lambda danos: {"danos": danos})
        | plantilla_conclusion
        | modelo
        | StrOutputParser()
    )

    return cadena


if __name__ == "__main__":
    load_dotenv()
    modelo = ChatAnthropic(model="claude-opus-5-5", anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"))
    cadena = construir_cadena(modelo)

    reporte_vecino = (
        "Pasé por Almirante Barroso 256, en Barrio Brasil. Es una casa antigua de un piso, "
        "con la fachada llena de adornos. Las ventanas están tapiadas con tablas y parece que "
        "el techo se cayó, porque desde la calle se ve el cielo por arriba. Hay pasto y plantas "
        "creciendo en la entrada, los muros están rayados con grafitis y la pintura se está "
        "saltando por todos lados."
    )

    resultado = cadena.invoke(
        {"reporte": reporte_vecino} #El diccionario que corresponde al primer paso
    )

    print(resultado)
