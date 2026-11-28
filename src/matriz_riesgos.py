"""
CORE del Bloque 32, Paso 3: matriz de riesgos del sistema de la Comunidad Brasil Alameda.

Cada fila tiene los cuatro campos de la lección (riesgo, probabilidad, impacto y mitigacion). Además lleva
"supervision": el curso lo documenta aparte, aquí va en la misma fila para poder comprobar con una prueba
que ningún riesgo ALTO o CRITICO queda sin su punto de supervisión. En los MEDIO queda en None.

La probabilidad y el impacto (de 1 a 5) son estimaciones: las filas [AL LIMITE] conviene revisarlas con
otra persona de la directiva antes de darlas por cerradas.
"""


def puntaje_riesgo(probabilidad, impacto):
    return probabilidad * impacto


def categoria_riesgo(puntaje):
    if puntaje >= 15:
        return "CRITICO"
    if puntaje >= 9:
        return "ALTO"
    if puntaje >= 4:
        return "MEDIO"
    return "BAJO"


def esta_en_el_limite(probabilidad, impacto):
    # Un riesgo está al límite si subir o bajar un punto la probabilidad o el impacto le cambia la categoría
    categoria_actual = categoria_riesgo(puntaje_riesgo(probabilidad, impacto))
    vecinos = [
        (probabilidad + 1, impacto), (probabilidad - 1, impacto),
        (probabilidad, impacto + 1), (probabilidad, impacto - 1),
    ]
    for p2, i2 in vecinos:
        if not (1 <= p2 <= 5 and 1 <= i2 <= 5):
            continue
        if categoria_riesgo(puntaje_riesgo(p2, i2)) != categoria_actual:
            return True
    return False


mis_riesgos = [
    {"riesgo": "Se reporta a la Municipalidad o a un inversionista una casa que la foto muestra abandonada "
               "pero que esta habitada",
     "probabilidad": 4,  # La foto solo muestra la fachada: una fachada deteriorada no prueba que nadie viva ahí
     "impacto": 5,  # Expone a quienes viven en la casa y daña la confianza en la comunidad
     "mitigacion": "Reporte solo con aprobacion humana (esperar_aprobacion) y criterio de verificacion "
                   "en terreno (Bloque 23)",
     "supervision": "Un integrante de la directiva verifica la casa en terreno y responde la aprobacion "
                    "antes de registrar el reporte"},

    {"riesgo": "Se activa una version nueva del prompt del RAG que deja de citar fuentes o rompe el formato "
               "de la respuesta",
     "probabilidad": 3,  # El prompt ya cambió en este bloque y va a seguir cambiando hasta el Gate 2
     "impacto": 3,  # La directiva recibe direcciones sin la ficha que las respalda
     "mitigacion": "Banco de prompts con prueba de consistencia (Bloque 10) y registro de versiones con "
                   "huella y diff (Bloque 32)",
     "supervision": "grafo_supervision.py: interrupt() detiene el despliegue hasta que la directiva aprueba "
                    "la huella nueva (Bloque 32)"},

    {"riesgo": "La busqueda de fichas trae, junto a las que cumplen, otras que no cumplen todo lo pedido "
               "(barrio, pisos o senales), porque siempre devuelve k resultados",
     "probabilidad": 4,  # Estimación: si cumplen menos de k fichas, igual llegan k. En el corpus actual, cada
                         # pregunta trajo su fragmento correcto (13 de 14) más dos que sobraban (Bloque 27)
     "impacto": 3,  # Lleva a revisar o reportar propiedades equivocadas, aunque cada una trae su fuente
     "mitigacion": "Metricas de precision y recall (Bloque 27) y cita de la fuente de cada afirmacion "
                   "(Bloque 26); falta filtrar por los metadatos barrio, pisos y evidencia (seccion 3 de la ficha)",
     "supervision": "Antes de aprobar un reporte, la directiva revisa la ficha citada como fuente de esa "
                    "direccion"},

    {"riesgo": "Una ficha compartida con un inversionista lleva notas de vecinos con testimonios sobre "
               "quienes viven en la casa",
     "probabilidad": 2,  # armar_ficha nunca incluye las notas, y hay pruebas que lo comprueban
     "impacto": 5,  # Saca datos personales de vecinos fuera de la comunidad, y eso no se puede deshacer
     "mitigacion": "armar_ficha excluye las notas por codigo y compartir_ficha_con_inversionista pide "
                   "aprobacion (Bloque 23)",
     "supervision": "Un integrante de la directiva aprueba cada ficha antes de compartirla y confirma que "
                    "el destinatario es conocido por la comunidad"},

    {"riesgo": "La evaluacion se basa en una foto de Street View antigua y la casa ya cambio",
     "probabilidad": 3,  # La foto de Almirante Barroso 256 es de mayo de 2024, y Street View no se renueva cada año
     "impacto": 3,  # El registro queda con un estado que ya no es real
     "mitigacion": "La verificacion en terreno revisa que la fachada siga como la registra la evaluacion "
                   "(Bloque 23); la ficha guardara la fecha de la foto (RF-02 del MVP)",
     "supervision": "La misma verificacion en terreno, antes de aprobar un reporte"},

    {"riesgo": "Inyeccion de prompt via el texto de un letrero o grafiti de la fachada que la evaluacion "
               "copia a una ficha indexada",
     "probabilidad": 2,  # Es raro que una fachada tenga texto con forma de instrucción, pero las fichas copian lo que se ve
     "impacto": 4,  # El modelo podría ignorar sus instrucciones y responder con datos que no están en las fichas
     "mitigacion": "Filtro de patrones sobre el contexto y la pregunta (Bloque 31) y delimitacion del "
                   "contexto en la version 2 del prompt (Bloque 32)",
     "supervision": None},

    {"riesgo": "Se agotan los creditos de Gemini o vence la clave de Anthropic y el servicio deja de responder",
     "probabilidad": 3,  # Ya pasó: el 16 de noviembre Gemini respondió 402 por créditos agotados
     "impacto": 2,  # La directiva no puede consultar mientras tanto, pero no se pierde ni se expone nada
     "mitigacion": "Para Claude, with_fallbacks a Claude Haiku y respuesta generica con aviso (Bloque 20); "
                   "para Gemini no hay respaldo y el error queda en el log",
     "supervision": None},
]

# Se completa cada fila con su puntaje, su categoría y si está al límite
for r in mis_riesgos:
    r["puntaje"] = puntaje_riesgo(r["probabilidad"], r["impacto"])
    r["categoria"] = categoria_riesgo(r["puntaje"])
    r["al_limite"] = esta_en_el_limite(r["probabilidad"], r["impacto"])


if __name__ == "__main__":
    for r in sorted(mis_riesgos, key=lambda x: -x["puntaje"]):
        print(f"{r['categoria']:8} ({r['puntaje']:2}) - {r['riesgo']}")
    print()

    for r in mis_riesgos:
        if r["al_limite"]:
            print("revisar con otra persona:", r["riesgo"])
    print()

    # Los puntos de supervisión de los riesgos ALTO y CRITICO
    for r in mis_riesgos:
        if r["categoria"] in ("ALTO", "CRITICO"):
            print(f"supervision [{r['categoria']}]: {r['supervision']}")
