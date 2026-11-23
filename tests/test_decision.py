import sys

# Las pruebas se ejecutan desde la carpeta raíz del proyecto; se agrega src/ para poder importar el módulo
sys.path.append("src")
from decision import recomendar_estrategia, generar_esqueleto_decision, respuestas_mi_caso, PROBLEMA

# Estas pruebas no usan ninguna API: el método de decisión es Python estándar


def test_las_cinco_respuestas_estan_completas():
    assert len(respuestas_mi_caso) == 5
    assert all(valor in (True, False) for valor in respuestas_mi_caso.values())


def test_con_las_respuestas_del_proyecto_gana_rag():
    puntos, ganadoras = recomendar_estrategia(respuestas_mi_caso)

    assert puntos == {"RAG": 5, "Fine-tuning completo": 0, "PEFT": 1}
    assert ganadoras == ["RAG"]


def test_si_hubiera_problema_de_formato_peft_sube_pero_sigue_ganando_rag():
    respuestas_variante = dict(respuestas_mi_caso)
    respuestas_variante["problema_de_formato_o_tono"] = True

    puntos, ganadoras = recomendar_estrategia(respuestas_variante)

    assert puntos == {"RAG": 5, "Fine-tuning completo": 1, "PEFT": 3}
    assert ganadoras == ["RAG"]


def test_un_empate_queda_declarado_en_el_esqueleto():
    # Con las cinco respuestas en False, las tres técnicas empatan en 0 y el esqueleto lo dice
    puntos, ganadoras = recomendar_estrategia({clave: False for clave in respuestas_mi_caso})

    esqueleto = generar_esqueleto_decision(PROBLEMA, puntos, ganadoras)

    assert "**Empate entre: RAG, Fine-tuning completo, PEFT**" in esqueleto


def test_el_esqueleto_tiene_las_cuatro_secciones_en_orden():
    puntos, ganadoras = recomendar_estrategia(respuestas_mi_caso)

    esqueleto = generar_esqueleto_decision(PROBLEMA, puntos, ganadoras)

    secciones = ["## 1. El problema", "## 2. Resultado del metodo de decision",
                 "## 3. Tecnica elegida y por que", "## 4. Que necesitarias para ejecutarla"]
    posiciones = [esqueleto.index(s) for s in secciones]
    assert posiciones == sorted(posiciones)
    assert "Empate" not in esqueleto
    assert "[COMPLETAR: por que RAG responde mejor a este caso]" in esqueleto
