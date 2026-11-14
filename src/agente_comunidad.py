from dotenv import load_dotenv
import os
import json
import queue
import threading
from datetime import datetime, timezone
from pydantic import BaseModel, Field
from langchain_anthropic import ChatAnthropic
from langchain_core.tools import tool
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.runnables import RunnableLambda
from langchain_core.chat_history import InMemoryChatMessageHistory  # Historial de cada sesión
from langchain_core.runnables.history import RunnableWithMessageHistory  # Le agrega memoria al agente
from langchain_classic.agents import AgentExecutor, create_tool_calling_agent


#=== Registro de propiedades evaluadas ===
# Por ahora es un diccionario en memoria, como ESTADOS en la clase. Las claves van en minúsculas para
# encontrar la propiedad sin importar cómo escriba la dirección el usuario
PROPIEDADES = {
    "almirante barroso 256": {
        "direccion": "Almirante Barroso 256",
        "barrio": "Barrio Brasil",
        "pisos": 1,
        "senales": ["ventanas tapiadas", "vanos abiertos o vidrios rotos", "malezas", "grafitis",
                    "pintura descascarada", "revoque caído", "techo dañado", "escombros"],
        "evidencia": "muy fuerte",
        "fuente": "foto de Google Street View (mayo 2024), evaluada con evaluar_fachada en el Gate 1",
        "notas": [],  # Lo que los vecinos anotan con guardar_nota_vecino
    },
}


# Ficha con la evaluación de la fachada. Es lo único que sale de la comunidad (compartir_ficha_con_inversionista):
# nunca lleva las notas de los vecinos, porque ahí pueden aparecer testimonios sobre quienes viven en la casa.
# Lo limita el código, no el agente
def armar_ficha(propiedad: dict) -> str:
    senales = ", ".join(propiedad["senales"])
    return (
        f"{propiedad['direccion']} ({propiedad['barrio']}, {propiedad['pisos']} piso(s)). "
        f"Señales: {senales}. Evidencia: {propiedad['evidencia']}. Fuente: {propiedad['fuente']}."
    )


#=== Herramientas de riesgo bajo: solo leen el registro ===
@tool
def consultar_propiedad(direccion: str) -> str:
    """
    Consulta la evaluación registrada de la fachada de una propiedad específica: barrio, pisos, señales de
    abandono y nivel de evidencia. Usar cuando el usuario menciona la dirección de una propiedad (calle y
    número) y pregunta por su estado.
    """
    for clave, propiedad in PROPIEDADES.items():
        if clave in direccion.lower():
            texto = armar_ficha(propiedad)
            # Si hay notas de vecinos, se agregan con su fecha (solo dentro de la comunidad)
            notas = []
            for registro_nota in propiedad["notas"]:
                notas.append(f"{registro_nota['fecha_hora'][:10]}: {registro_nota['nota']}")
            if notas:
                texto += " Notas de vecinos: " + "; ".join(notas) + "."
            return texto
    return f"No hay una evaluación registrada para '{direccion}'. Para evaluarla se necesita una foto de su fachada."


# Esquema de argumentos: LangChain lo transforma en un JSON que el modelo lee, campo por campo
class CriteriosBusqueda(BaseModel):
    """Criterios para buscar propiedades en posible abandono."""
    barrio: str = Field(
        default="",
        description="'Barrio Brasil' o 'Concha y Toro'. Vacío si el usuario no indica el barrio."
    )
    pisos: int = Field(
        default=0,
        description="Número de pisos de la fachada. 0 si el usuario no lo indica."
    )
    senal: str = Field(
        default="",
        description="Una señal de abandono, usando solo uno de estos nombres: ventanas tapiadas, vanos abiertos "
                    "o vidrios rotos, malezas, grafitis, pintura descascarada, revoque caído, techo dañado o "
                    "escombros. Vacío si el usuario no indica ninguna."
    )


@tool(args_schema=CriteriosBusqueda)
def buscar_propiedades(barrio: str = "", pisos: int = 0, senal: str = "") -> str:
    """
    Busca, entre las propiedades registradas, las que cumplen los criterios del usuario: barrio, número de
    pisos y una señal de abandono. Usar cuando el usuario pide encontrar propiedades con ciertas
    características, sin dar una dirección específica.
    """
    encontradas = []
    for propiedad in PROPIEDADES.values():
        # Un criterio vacío (o 0 en pisos) significa que el usuario no lo pidió, así que se cumple siempre
        cumple_barrio = barrio == "" or barrio.lower() == propiedad["barrio"].lower()
        cumple_pisos = pisos == 0 or pisos == propiedad["pisos"]
        cumple_senal = senal == "" or senal.lower() in propiedad["senales"]
        if cumple_barrio and cumple_pisos and cumple_senal:
            encontradas.append(f"{propiedad['direccion']} (evidencia {propiedad['evidencia']})")

    if not encontradas:
        return "No se encontraron propiedades registradas con esos criterios."
    return "Propiedades encontradas: " + "; ".join(encontradas)


#=== Herramienta de riesgo medio: escribe en el registro, pero se puede deshacer ===
class ArgumentosNota(BaseModel):
    """Datos de la nota de un vecino sobre una propiedad."""
    direccion: str = Field(
        description="Calle y número de la propiedad, por ejemplo 'Almirante Barroso 256'."
    )
    nota: str = Field(
        description="Lo que el vecino vio en la fachada, en una o dos oraciones. Solo lo que se ve desde la "
                    "calle: sin nombres ni datos personales de quienes viven ahí."
    )


@tool(args_schema=ArgumentosNota)
def guardar_nota_vecino(direccion: str, nota: str) -> str:
    """
    Guarda en el registro de una propiedad lo que un vecino vio en su fachada, por ejemplo un cambio desde la
    última evaluación. Usar cuando el vecino pide anotar o dejar registrada una observación sobre una
    propiedad. No envía nada fuera de la comunidad, y un coordinador puede borrar la nota si está equivocada.
    """
    for clave, propiedad in PROPIEDADES.items():
        if clave in direccion.lower():
            propiedad["notas"].append({"nota": nota, "fecha_hora": datetime.now().isoformat()})
            return f"Nota guardada en el registro de {propiedad['direccion']}: {nota}"
    return f"No hay una evaluación registrada para '{direccion}', así que la nota no se guardó."


# No es una herramienta del agente: la usa un coordinador para deshacer una nota equivocada.
# numero empieza en 1 (la primera nota de la propiedad)
def borrar_nota(direccion: str, numero: int) -> bool:
    for clave, propiedad in PROPIEDADES.items():
        if clave in direccion.lower() and 1 <= numero <= len(propiedad["notas"]):
            propiedad["notas"].pop(numero - 1)
            return True
    return False


#=== Supervisión humana (Human in the Loop) ===
registro_aprobaciones = []


def esperar_aprobacion(mensaje: str, tiempo_limite_segundos: int = 15) -> bool:
    # Igual que en la clase: la pregunta se hace en un hilo aparte para poder cortar la espera.
    # El select.select() del curso no funciona en Windows
    cola_respuesta = queue.Queue()

    def pedir_entrada():
        try:
            texto = input(mensaje)
            cola_respuesta.put(texto.strip().lower())
        except (EOFError, KeyboardInterrupt, OSError):
            # OSError: no hay una consola desde donde leer (por ejemplo, al correr las pruebas con pytest)
            cola_respuesta.put("")

    hilo = threading.Thread(target=pedir_entrada, daemon=True)
    hilo.start()

    try:
        respuesta = cola_respuesta.get(timeout=tiempo_limite_segundos)
        return respuesta == "s"
    except queue.Empty:
        print("Tiempo de espera agotado. Reporte no aprobado por timeout")
        return False  # Ante la duda, la opción segura es no ejecutar la acción


def registrar_aprobacion(herramienta: str, argumentos: dict, aprobado: bool) -> None:
    registro_aprobaciones.append({
        "herramienta": herramienta,
        "argumentos": argumentos,
        "aprobado": aprobado,
        "fecha_hora": datetime.now().isoformat()
    })


#=== Herramienta de riesgo alto: sale de la comunidad y no se puede deshacer ===
class ArgumentosReporte(BaseModel):
    """Datos del reporte a la Municipalidad."""
    direccion: str = Field(
        description="Calle y número de la propiedad, por ejemplo 'Almirante Barroso 256'."
    )
    motivo: str = Field(
        description="Por qué se reporta: las señales de abandono o el riesgo que describe el usuario."
    )


@tool(args_schema=ArgumentosReporte)
def reportar_a_municipalidad(direccion: str, motivo: str) -> str:
    """
    Envía un reporte formal a la Municipalidad de Santiago sobre una propiedad en posible abandono. Usar solo
    cuando el usuario pide explícitamente reportar o denunciar una propiedad. Acción irreversible: una vez
    enviado, el reporte no se puede retirar, por eso requiere aprobación humana antes de ejecutarse.
    """
    mensaje = (
        f"[SUPERVISIÓN HUMANA REQUERIDA] El agente quiere reportar a la Municipalidad la propiedad "
        f"{direccion}. Motivo: {motivo} ¿Aprobar? (s/n): "
    )

    # Congela el proceso hasta que un coordinador de la comunidad dé el visto bueno
    aprobado = esperar_aprobacion(mensaje, tiempo_limite_segundos=15)

    # Se registra la decisión, se apruebe o no
    registrar_aprobacion(
        herramienta="reportar_a_municipalidad",
        argumentos={"direccion": direccion, "motivo": motivo},
        aprobado=aprobado
    )

    if not aprobado:
        return "El reporte no se envió: no fue aprobado por un coordinador de la comunidad o se agotó el tiempo."

    # Simulado: en el proyecto real, aquí se enviaría el reporte (por ejemplo, un correo a la Municipalidad)
    return f"Reporte enviado a la Municipalidad de Santiago (simulado) para {direccion}."


class ArgumentosFicha(BaseModel):
    """Datos para compartir la ficha de una propiedad."""
    direccion: str = Field(
        description="Calle y número de la propiedad, por ejemplo 'Almirante Barroso 256'."
    )
    destinatario: str = Field(
        description="Inversionista o tercero interesado que recibiría la ficha, tal como lo nombra el usuario."
    )


@tool(args_schema=ArgumentosFicha)
def compartir_ficha_con_inversionista(direccion: str, destinatario: str) -> str:
    """
    Comparte con un inversionista o tercero interesado la ficha de evaluación de la fachada de una propiedad
    (barrio, pisos, señales de abandono y evidencia), para que evalúe darle un nuevo uso. Usar solo cuando el
    usuario pide explícitamente compartir o enviar la información de una propiedad a un inversionista. Acción
    irreversible: una vez compartida, la información no se puede recuperar, por eso requiere aprobación humana
    antes de ejecutarse. Nunca incluye las notas de los vecinos.
    """
    for clave, propiedad in PROPIEDADES.items():
        if clave in direccion.lower():
            ficha = armar_ficha(propiedad)
            mensaje = (
                f"[SUPERVISIÓN HUMANA REQUERIDA] El agente quiere compartir con {destinatario} esta ficha: "
                f"{ficha} ¿Aprobar? (s/n): "
            )

            # Congela el proceso hasta que un coordinador de la comunidad dé el visto bueno
            aprobado = esperar_aprobacion(mensaje, tiempo_limite_segundos=15)

            # Se registra la decisión, se apruebe o no
            registrar_aprobacion(
                herramienta="compartir_ficha_con_inversionista",
                argumentos={"direccion": direccion, "destinatario": destinatario},
                aprobado=aprobado
            )

            if not aprobado:
                return "La ficha no se compartió: no fue aprobada por un coordinador de la comunidad o se agotó el tiempo."

            # Simulado: en el proyecto real, aquí se enviaría la ficha al destinatario
            return f"Ficha compartida con {destinatario} (simulado): {ficha}"

    # Si la propiedad no está registrada no hay nada que compartir, así que no se pide aprobación
    return f"No hay una evaluación registrada para '{direccion}', así que no se compartió nada."


herramientas = [
    consultar_propiedad,
    buscar_propiedades,
    guardar_nota_vecino,
    reportar_a_municipalidad,
    compartir_ficha_con_inversionista,
]


#=== Memoria: un historial por cada vecino (session_id) ===
historiales = {}


def obtener_historial(session_id: str):
    if session_id not in historiales:
        historiales[session_id] = InMemoryChatMessageHistory()
    return historiales[session_id]


#=== Respuesta final y traza de decisión ===
# Con Claude, la respuesta llega como una lista de bloques: primero el razonamiento (thinking) y después el
# texto. Por eso no sirve ["output"][0]["text"] como con Gemini: se busca el bloque de tipo "text"
def extraer_texto(salida):
    if isinstance(salida, str):
        return salida
    texto = ""
    for bloque in salida:
        if bloque.get("type") == "text":
            texto += bloque["text"]
    return texto


def registrar_traza(session_id: str, entrada: str, resultado: dict, archivo: str = "trazas_agente.jsonl") -> None:
    """
    Guarda una interacción del agente como una línea JSON: qué se preguntó, qué herramientas se usaron y con
    qué argumentos, qué devolvió cada una y la respuesta final. Si "resultado" no trae "intermediate_steps",
    acciones queda como una lista vacía en vez de fallar.
    """
    registro = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "session_id": session_id,
        "entrada": entrada,
        "acciones": [
            {
                "herramienta": accion.tool,
                "argumentos": accion.tool_input,
                "observacion": observacion,
            }
            for accion, observacion in resultado.get("intermediate_steps", [])
        ],
        "respuesta_final": extraer_texto(resultado["output"]),
    }

    with open(archivo, "a", encoding="utf-8") as f:
        f.write(json.dumps(registro, ensure_ascii=False) + "\n")


#=== Construcción del agente ===
def construir_agente(modelo):
    prompt_agente = ChatPromptTemplate.from_messages([
        (
            "system", "Eres el asistente de la Comunidad Brasil Alameda, que ayuda a los vecinos a revisar "
                      "propiedades en posible abandono en Barrio Brasil y Concha y Toro, Santiago. Usa las "
                      "herramientas disponibles cuando las necesites y no inventes información que no te "
                      "entreguen."
        ),
        MessagesPlaceholder("chat_history"),  # Lo que el vecino dijo antes, en la misma sesión
        ("human", "{entrada}"),
        MessagesPlaceholder("agent_scratchpad")  # Las herramientas que el agente llamó y lo que devolvieron
    ])

    agente = create_tool_calling_agent(modelo, herramientas, prompt_agente)

    ejecutor_agente = AgentExecutor(
        agent=agente,
        tools=herramientas,
        return_intermediate_steps=True,  # Para verificar qué herramienta eligió en cada caso
        # Sin verbose=True: con Claude imprimiría también los bloques de razonamiento, que son muy largos.
        # Los pasos quedan en trazas_agente.jsonl
    )

    limpiar_salida = RunnableLambda(
        lambda d: {**d, "output": extraer_texto(d["output"])}
    )

    return RunnableWithMessageHistory(
        ejecutor_agente | limpiar_salida,
        obtener_historial,
        input_messages_key="entrada",
        history_messages_key="chat_history",
        output_messages_key="output"
    )


def consultar_agente(agente, session_id, mensaje):
    resultado = agente.invoke(
        {"entrada": mensaje},
        config={"configurable": {"session_id": session_id}}
    )
    registrar_traza(session_id, mensaje, resultado)
    return resultado


if __name__ == "__main__":
    load_dotenv()
    modelo = ChatAnthropic(model="claude-opus-5-5", anthropic_api_key=os.getenv("ANTHROPIC_API_KEY"))
    agente = construir_agente(modelo)

    # Cada prueba es (session_id, mensaje). Las dos primeras de vecino_1 prueban la memoria;
    # la de vecino_2 prueba que las sesiones no se mezclan. La pregunta general va en una sesión nueva
    # (vecino_4) para probar que el agente no usa ninguna herramienta cuando no la necesita
    pruebas = [
        ("vecino_1", "¿En qué estado está la casa de Almirante Barroso 256?"),
        ("vecino_1", "¿Y esa casa tiene grafitis?"),
        ("vecino_2", "¿De qué casa te pregunté recién?"),
        ("vecino_3", "Busca casas de un piso con ventanas tapiadas en Barrio Brasil."),
        ("vecino_4", "¿Cómo me puedo sumar a la Comunidad Brasil Alameda?"),
        # Riesgo medio: guarda una nota sin pedir aprobación. vecino_5 la ve, porque el registro es de toda la
        # comunidad, aunque la memoria de la conversación sea de cada vecino
        ("vecino_3", "Anota en Almirante Barroso 256 que hoy vi la puerta tapiada con tablas nuevas."),
        ("vecino_5", "¿Hay notas de vecinos sobre Almirante Barroso 256?"),
        # Riesgo alto: comparte la ficha con un tercero (nombre de prueba). La ficha no lleva la nota de vecino_3
        ("vecino_6", "Comparte la ficha de Almirante Barroso 256 con el inversionista de prueba Fondo Ejemplo, "
                     "que quiere restaurarla."),
        # Riesgo alto: pide aprobación en la consola (responde s o n antes de 15 segundos)
        ("vecino_1", "Quiero reportar a la Municipalidad la casa de Almirante Barroso 256, porque se le cayó el techo."),
    ]

    for session_id, mensaje in pruebas:
        resultado = consultar_agente(agente, session_id, mensaje)
        herramientas_usadas = [accion.tool for accion, observacion in resultado["intermediate_steps"]]
        print(f"[{session_id}] {mensaje}")
        print("Herramientas usadas:", herramientas_usadas)
        print("Respuesta:", resultado["output"])
        print()

    print("Registro de aprobaciones:")
    for registro in registro_aprobaciones:
        print(registro)
