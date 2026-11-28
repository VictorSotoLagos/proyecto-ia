"""
CORE del Bloque 32, Paso 2: punto de supervisión humana antes de activar una versión nueva del prompt del RAG.

El grafo propone la huella nueva, se detiene con interrupt() hasta que un integrante de la directiva decide,
y solo entonces la activa o la rechaza. Es el grafo de la lección, con la huella de la versión 2 de
registro_prompts.py (Paso 1), escrita como texto porque los pasos son independientes.
"""
from typing import TypedDict

from langgraph.checkpoint.memory import InMemorySaver
from langgraph.graph import END, START, StateGraph
from langgraph.types import Command, interrupt

# Huella de la versión 2 del prompt: la que imprime "python src/registro_prompts.py" como "ultima"
HUELLA_PROPUESTA = "855768cb7e7c"


class EstadoDespliegue(TypedDict):
    huella_nueva: str
    aprobado: bool


def proponer(estado: EstadoDespliegue):
    return {}


def supervisar(estado: EstadoDespliegue):
    # interrupt() congela el grafo y guarda su estado en el checkpointer. No sigue hasta recibir Command(resume=...)
    decision = interrupt({
        "motivo": "aprobar nueva version del prompt del RAG de la comunidad",
        "huella_propuesta": estado["huella_nueva"],
    })
    return {"aprobado": decision}


def aplicar(estado: EstadoDespliegue):
    if estado["aprobado"]:
        print("version", estado["huella_nueva"], "activada")
    else:
        print("version", estado["huella_nueva"], "rechazada, se mantiene la anterior")
    return {}


grafo = StateGraph(EstadoDespliegue)
grafo.add_node("proponer", proponer)
grafo.add_node("supervisar", supervisar)
grafo.add_node("aplicar", aplicar)
grafo.add_edge(START, "proponer")
grafo.add_edge("proponer", "supervisar")
grafo.add_edge("supervisar", "aplicar")
grafo.add_edge("aplicar", END)

# InMemorySaver guarda el estado pausado mientras el programa sigue corriendo
app_despliegue = grafo.compile(checkpointer=InMemorySaver())


if __name__ == "__main__":
    # Camino de aprobación: primero queda interrumpido, sin reanudar
    config = {"configurable": {"thread_id": "despliegue-prompt-1"}}
    resultado = app_despliegue.invoke({"huella_nueva": HUELLA_PROPUESTA, "aprobado": False}, config=config)
    print("1) tras invocar:", resultado)
    print("2) pendiente:", app_despliegue.get_state(config).interrupts[0].value)
    # La directiva aprueba: siempre con un booleano, porque un texto como "no" contaría como verdadero
    resultado = app_despliegue.invoke(Command(resume=True), config=config)
    print("3) tras aprobar:", resultado)

    # Camino de rechazo, con otro thread_id: uno que ya terminó no vuelve a pasar por la aprobación
    config2 = {"configurable": {"thread_id": "despliegue-prompt-2"}}
    app_despliegue.invoke({"huella_nueva": HUELLA_PROPUESTA, "aprobado": False}, config=config2)
    resultado = app_despliegue.invoke(Command(resume=False), config=config2)
    print("4) tras rechazar:", resultado)
