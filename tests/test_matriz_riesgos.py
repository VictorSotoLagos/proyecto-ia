import re
import sys

# Las pruebas se ejecutan desde la carpeta raíz del proyecto; se agrega src/ para poder importar el módulo
sys.path.append("src")
from matriz_riesgos import categoria_riesgo, esta_en_el_limite, mis_riesgos, puntaje_riesgo


def test_la_fila_modelo_de_la_leccion_da_critico_al_limite():
    assert puntaje_riesgo(4, 4) == 16
    assert categoria_riesgo(16) == "CRITICO"
    assert esta_en_el_limite(4, 4) is True
    assert esta_en_el_limite(4, 5) is False  # 20: con un punto menos sigue siendo CRITICO


def test_hay_al_menos_cinco_riesgos_completos():
    assert len(mis_riesgos) >= 5
    for r in mis_riesgos:
        assert r["riesgo"] and r["mitigacion"]
        assert 1 <= r["probabilidad"] <= 5
        assert 1 <= r["impacto"] <= 5


def test_hay_algun_alto_o_critico_y_no_todos_en_la_misma_categoria():
    categorias = {r["categoria"] for r in mis_riesgos}
    assert categorias & {"ALTO", "CRITICO"}
    assert len(categorias) > 1


def test_cada_alto_o_critico_tiene_su_punto_de_supervision():
    for r in mis_riesgos:
        if r["categoria"] in ("ALTO", "CRITICO"):
            assert r["supervision"], r["riesgo"]


def test_al_menos_dos_mitigaciones_apuntan_a_un_bloque_ya_construido():
    # Los bloques ya construidos en el programa llegan hasta el 32
    con_bloque_construido = [
        r for r in mis_riesgos
        if any(int(numero) <= 32 for numero in re.findall(r"Bloque (\d+)", r["mitigacion"]))
    ]
    assert len(con_bloque_construido) >= 2
