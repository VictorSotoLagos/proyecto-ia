import sys

from langchain_core.documents import Document

# Las pruebas se ejecutan desde la carpeta raíz del proyecto; se agrega src/ para poder importar el módulo
sys.path.append("src")
from recuperar_contexto import formatear_contexto

# Estas pruebas usan Documents armados a mano: no consultan Chroma ni gastan tokens


def test_formatear_contexto_numera_los_chunks_y_cita_su_fuente():
    chunks = [
        Document(page_content="Si falla el modelo, se repite la ruta con Haiku.",
                 metadata={"fuente": "docs/registro_orquestacion.md"}),
        Document(page_content="Se eligió Claude Opus 5.5 por su calidad.",
                 metadata={"fuente": "docs/decision-arquitectura.md"}),
    ]

    contexto, citas = formatear_contexto(chunks)

    assert contexto.startswith("[1] Si falla el modelo")
    assert "[2] Se eligió Claude Opus 5.5" in contexto
    assert citas == {1: "docs/registro_orquestacion.md", 2: "docs/decision-arquitectura.md"}


def test_formatear_contexto_marca_la_fuente_desconocida():
    contexto, citas = formatear_contexto([Document(page_content="Texto sin metadata.")])

    assert citas == {1: "desconocida"}
