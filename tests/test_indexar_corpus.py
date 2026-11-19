import sys

import pytest
from langchain_core.documents import Document

# Las pruebas se ejecutan desde la carpeta raíz del proyecto; se agrega src/ para poder importar el módulo
sys.path.append("src")
from indexar_corpus import (
    CORPUS,
    CHUNK_SIZE,
    dividir_corpus,
    generar_ids,
    verificar_integridad,
)

# Estas pruebas no calculan embeddings: revisan el corpus y el chunking, que se hacen antes de gastar tokens


def test_corpus_tiene_al_menos_5_documentos_con_fuente():
    assert len(CORPUS) >= 5
    for documento in CORPUS:
        assert documento.metadata["fuente"] != ""
        assert documento.metadata["tema"] != ""


def test_chunks_no_superan_el_tamano_y_conservan_la_fuente():
    chunks = dividir_corpus(CORPUS)

    assert len(chunks) >= len(CORPUS)  # Ningún documento se pierde; los largos se dividen en más de un chunk
    for chunk in chunks:
        assert len(chunk.page_content) <= CHUNK_SIZE
        assert "fuente" in chunk.metadata


def test_ids_son_unicos_y_usan_el_tema():
    chunks = dividir_corpus(CORPUS)
    ids = generar_ids(chunks)

    assert len(ids) == len(set(ids))
    assert ids[0] == "objetivo_1"


def test_verificar_integridad_detecta_un_chunk_vacio():
    chunks = [Document(page_content="Texto válido."), Document(page_content="   ")]

    with pytest.raises(ValueError):
        verificar_integridad(chunks, chunks)
