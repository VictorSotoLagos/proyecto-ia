import sys

from langgraph.types import Command

# Las pruebas se ejecutan desde la carpeta raíz del proyecto; se agrega src/ para poder importar el módulo
sys.path.append("src")
from grafo_supervision import HUELLA_PROPUESTA, app_despliegue
from registro_prompts import NOMBRE_PROMPT, registro


def iniciar_despliegue(thread_id):
    # Cada prueba usa su propio thread_id: uno que ya terminó no vuelve a pasar por la aprobación
    config = {"configurable": {"thread_id": thread_id}}
    resultado = app_despliegue.invoke({"huella_nueva": HUELLA_PROPUESTA, "aprobado": False}, config=config)
    return config, resultado


def test_la_huella_propuesta_es_la_ultima_version_del_registro():
    # Si alguien cambia el prompt y no actualiza la huella del grafo, esta prueba falla
    assert HUELLA_PROPUESTA == registro.ultima(NOMBRE_PROMPT)["huella"]


def test_sin_reanudar_el_despliegue_queda_detenido():
    config, resultado = iniciar_despliegue("prueba-detenido")

    assert "__interrupt__" in resultado
    assert resultado["__interrupt__"][0].value["huella_propuesta"] == HUELLA_PROPUESTA
    assert resultado["aprobado"] is False
    assert len(app_despliegue.get_state(config).interrupts) == 1  # Sigue esperando la decisión


def test_al_aprobar_se_activa_la_version(capsys):
    config, _ = iniciar_despliegue("prueba-aprobar")
    resultado = app_despliegue.invoke(Command(resume=True), config=config)

    assert "__interrupt__" not in resultado
    assert resultado["aprobado"] is True
    assert f"version {HUELLA_PROPUESTA} activada" in capsys.readouterr().out


def test_al_rechazar_se_mantiene_la_version_anterior(capsys):
    config, _ = iniciar_despliegue("prueba-rechazar")
    resultado = app_despliegue.invoke(Command(resume=False), config=config)

    assert "__interrupt__" not in resultado
    assert resultado["aprobado"] is False
    assert "rechazada, se mantiene la anterior" in capsys.readouterr().out
