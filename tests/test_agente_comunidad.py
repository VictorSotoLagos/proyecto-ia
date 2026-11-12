import sys
import os
import json

from langchain_core.agents import AgentAction

# Las pruebas se ejecutan desde la carpeta raíz del proyecto; se agrega src/ para poder importar el módulo
sys.path.append("src")
from agente_comunidad import (
    consultar_propiedad,
    buscar_propiedades,
    reportar_a_municipalidad,
    registro_aprobaciones,
    obtener_historial,
    extraer_texto,
    registrar_traza,
)


# ---------- Herramientas de riesgo bajo: se invocan directo, sin el agente ni la API ----------

def test_consultar_propiedad_registrada():
    resultado = consultar_propiedad.invoke({"direccion": "Almirante Barroso 256"})

    assert "muy fuerte" in resultado
    assert "techo dañado" in resultado


def test_consultar_propiedad_encuentra_la_direccion_aunque_traiga_el_barrio():
    resultado = consultar_propiedad.invoke({"direccion": "almirante barroso 256, Barrio Brasil"})

    assert "muy fuerte" in resultado


def test_consultar_propiedad_desconocida_devuelve_texto_y_no_error():
    resultado = consultar_propiedad.invoke({"direccion": "Calle Inventada 999"})

    assert "No hay una evaluación registrada" in resultado


def test_buscar_propiedades_por_barrio_pisos_y_senal():
    resultado = buscar_propiedades.invoke(
        {"barrio": "Barrio Brasil", "pisos": 1, "senal": "ventanas tapiadas"}
    )

    assert "Almirante Barroso 256" in resultado


def test_buscar_propiedades_sin_resultados():
    resultado = buscar_propiedades.invoke({"barrio": "Concha y Toro", "pisos": 3})

    assert "No se encontraron" in resultado


# ---------- Herramienta de riesgo alto ----------
# En pytest no hay una consola desde donde responder, así que esperar_aprobacion devuelve False:
# es el mismo resultado seguro que si nadie responde a tiempo

def test_reporte_no_se_envia_sin_aprobacion_y_queda_registrado():
    resultado = reportar_a_municipalidad.invoke(
        {"direccion": "Almirante Barroso 256", "motivo": "Se cayó el techo."}
    )

    assert "no se envió" in resultado
    assert registro_aprobaciones[-1]["herramienta"] == "reportar_a_municipalidad"
    assert registro_aprobaciones[-1]["aprobado"] is False


# ---------- Memoria ----------

def test_dos_sesiones_no_comparten_historial():
    obtener_historial("vecino_prueba_1").add_user_message("Pregunto por Almirante Barroso 256.")

    assert len(obtener_historial("vecino_prueba_1").messages) == 1
    assert len(obtener_historial("vecino_prueba_2").messages) == 0


# ---------- Respuesta final y traza ----------

def test_extraer_texto_salta_el_bloque_de_razonamiento_de_claude():
    salida_de_claude = [
        {"type": "thinking", "thinking": "", "signature": "abc"},
        {"type": "text", "text": "La casa está en posible abandono."},
    ]

    assert extraer_texto(salida_de_claude) == "La casa está en posible abandono."
    assert extraer_texto("Texto simple") == "Texto simple"


def test_registrar_traza_guarda_una_linea_con_la_herramienta_usada():
    archivo_prueba = "tests/trazas_prueba.jsonl"
    accion = AgentAction(tool="consultar_propiedad", tool_input={"direccion": "Almirante Barroso 256"}, log="")
    resultado_falso = {
        "intermediate_steps": [(accion, "Evidencia: muy fuerte.")],
        "output": "La casa tiene evidencia muy fuerte de abandono.",
    }

    registrar_traza("vecino_prueba", "¿Cómo está Almirante Barroso 256?", resultado_falso, archivo=archivo_prueba)

    with open(archivo_prueba, encoding="utf-8") as f:
        registro = json.loads(f.readline())
    os.remove(archivo_prueba)

    assert registro["session_id"] == "vecino_prueba"
    assert registro["acciones"][0]["herramienta"] == "consultar_propiedad"
    assert registro["respuesta_final"] == "La casa tiene evidencia muy fuerte de abandono."
