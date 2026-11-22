import os

# CORE del Bloque 30: método de decisión de la actividad (Paso 1) y esqueleto del documento (Paso 2).
# El documento se guarda en docs/, como el resto de la evidencia del proyecto, y después se completa a mano
ARCHIVO_DECISION = "docs/decision_personalizacion.md"

# El caso candidato del Bloque 29, descrito sin nombrar ninguna técnica
PROBLEMA = (
    "La miniaplicación clasifica cada mensaje de un vecino como direccion, busqueda u otro para elegir su "
    "ruta, y la etiqueta tiene que llegar exacta: con tilde o con texto extra, el mensaje cae sin aviso en "
    "la ruta equivocada. Hoy la clasificación la hace Claude Opus 5.5 con un prompt, y en una muestra de "
    "20 respuestas reales (docs/muestra_formato_clasificacion.json) 0 fallaron el formato y 0 tuvieron la "
    "categoría equivocada."
)


# Paso 1: el método de decisión de la actividad
def recomendar_estrategia(respuestas):
    puntos = {"RAG": 0, "Fine-tuning completo": 0, "PEFT": 0}

    if respuestas["informacion_cambia_seguido"]:
        puntos["RAG"] += 3
    if respuestas["problema_de_formato_o_tono"]:
        puntos["PEFT"] += 2
        puntos["Fine-tuning completo"] += 1
    if respuestas["dataset_grande_y_de_calidad"]:
        puntos["Fine-tuning completo"] += 2
        puntos["PEFT"] += 1
    if respuestas["presupuesto_limitado_o_iterar_rapido"]:
        puntos["RAG"] += 2
        puntos["PEFT"] += 1
    if respuestas["necesita_multiples_variantes"]:
        puntos["PEFT"] += 2

    maximo = max(puntos.values())
    ganadoras = [tecnica for tecnica, p in puntos.items() if p == maximo]
    return puntos, ganadoras


# Las respuestas de este proyecto, cada una con la evidencia que la sustenta
respuestas_mi_caso = {
    # Las 3 categorías y las 3 etiquetas de barrio están en src/prompts/banco.py desde el 22-10-2026, y el
    # enrutador usa las mismas desde el 04-11-2026: 0 cambios desde entonces (umbral: 1 cambio al mes)
    "informacion_cambia_seguido": False,
    # Muestra de 20 respuestas reales del clasificador del enrutador (src/muestra_formato.py):
    # 0 de 20 fallaron el formato (umbral: 3 de 20, el 15 %)
    "problema_de_formato_o_tono": False,
    # Hay 15 ejemplos etiquetados en src/dataset_tuning.py (umbral: 200)
    "dataset_grande_y_de_calidad": False,
    # El presupuesto alcanza para más de 2 entrenamientos (cada uno costó cerca de US$0,01 y tardó 27 minutos)
    # y no se necesita ver el efecto de un cambio en menos de un día
    "presupuesto_limitado_o_iterar_rapido": False,
    # Un solo clasificador para los 2 barrios y las 3 categorías
    "necesita_multiples_variantes": False,
}


# Paso 2: el esqueleto del documento, armado con el resultado real del método
def generar_esqueleto_decision(problema, puntos, ganadoras):
    empate = len(ganadoras) > 1
    lineas = []
    lineas.append("# Decision de personalizacion")
    lineas.append("")
    lineas.append("## 1. El problema")
    lineas.append(problema)
    lineas.append("")
    lineas.append("## 2. Resultado del metodo de decision")
    for tecnica, p in sorted(puntos.items(), key=lambda x: -x[1]):
        lineas.append(f"- {tecnica}: {p} puntos")
    if empate:
        lineas.append("")
        lineas.append(f"**Empate entre: {', '.join(ganadoras)}**")
    lineas.append("")
    lineas.append("## 3. Tecnica elegida y por que")
    if empate:
        lineas.append(
            "[COMPLETAR: el puntaje no resolvio el empate solo -- "
            "justifica aqui con criterio propio]"
        )
    else:
        lineas.append(f"[COMPLETAR: por que {ganadoras[0]} responde mejor a este caso]")
    lineas.append("")
    lineas.append("## 4. Que necesitarias para ejecutarla")
    lineas.append(
        "[COMPLETAR: corpus faltante, o cantidad de ejemplos etiquetados que faltan]"
    )
    return "\n".join(lineas)


if __name__ == "__main__":
    if any(valor is None for valor in respuestas_mi_caso.values()):
        raise SystemExit("Completa las cinco respuestas con True o False antes de continuar.")

    puntos, ganadoras = recomendar_estrategia(respuestas_mi_caso)
    print(puntos)
    print("candidatas:", ganadoras)

    # "Cómo se prueba": se corre el método otra vez cambiando solo la respuesta más dudosa. Con Claude no hay
    # fallas de formato, pero un modelo más barato sí las tuvo (el Gemini ajustado del Bloque 29: 3 de 3)
    respuestas_variante = dict(respuestas_mi_caso)
    respuestas_variante["problema_de_formato_o_tono"] = True
    puntos_variante, ganadoras_variante = recomendar_estrategia(respuestas_variante)
    print("Si problema_de_formato_o_tono fuera True:", puntos_variante, "candidatas:", ganadoras_variante)

    esqueleto = generar_esqueleto_decision(PROBLEMA, puntos, ganadoras)
    print()
    print(esqueleto)

    # El documento se completa a mano después de generarlo: si ya existe, no se sobrescribe
    if os.path.exists(ARCHIVO_DECISION):
        print(f"\n{ARCHIVO_DECISION} ya existe y no se sobrescribe, para no perder lo completado a mano.")
    else:
        with open(ARCHIVO_DECISION, "w", encoding="utf-8") as f:
            f.write(esqueleto)
        print(f"\nEsqueleto guardado en {ARCHIVO_DECISION}")
