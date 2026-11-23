import os

# CORE del Bloque 30: método de decisión de la actividad (Paso 1) y esqueleto del documento (Paso 2).
# El documento se guarda en docs/, como el resto de la evidencia del proyecto, y después se completa a mano
ARCHIVO_DECISION = "docs/decision_personalizacion.md"

# El caso principal de la app, descrito sin nombrar ninguna técnica
PROBLEMA = (
    "Los vecinos van a buscar viviendas por señales de abandono (por ejemplo, \"casas de un piso con "
    "ventanas tapiadas en Barrio Brasil\"), y esas señales salen de evaluar fotos de Google Street View. "
    "El modelo no sabe qué casas del barrio ya están evaluadas, con qué señales ni qué anotaron los vecinos, "
    "porque ese inventario crece con cada foto evaluada; además, es una demo con presupuesto propio, y "
    "evaluar cada foto con Claude Opus 5.5 cuesta US$0,0149 (docs/decision-arquitectura.md)."
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
    # Los datos de propiedades que consulta el agente (src/agente_comunidad.py) cambiaron en 3 commits en
    # noviembre de 2026 (12, 13 y 14), y el inventario crece con cada foto evaluada y con cada nota de un
    # vecino (umbral: 1 cambio al mes)
    "informacion_cambia_seguido": True,
    # Muestra de 20 evaluaciones de la foto de Almirante Barroso 256 con gemini-3.5-flash-lite sin ajuste
    # (src/muestra_evaluacion_fachada.py): 0 de 20 fallaron los 4 criterios fijos (umbral: 3 de 20, el 15 %)
    "problema_de_formato_o_tono": False,
    # Hay 1 evaluación de fachada etiquetada, la de Almirante Barroso 256 (umbral: 200)
    "dataset_grande_y_de_calidad": False,
    # Es una demo con presupuesto propio: alcanza para muestras y para entrenamientos de PEFT de centavos
    # (US$0,01 cada uno), pero no para un fine-tuning completo. Se usa este criterio en vez del umbral de
    # "2 intentos", porque el límite real de la demo es el costo de cada técnica
    "presupuesto_limitado_o_iterar_rapido": True,
    # Un solo evaluador de fachadas para los 2 barrios
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

    # "Cómo se prueba": se corre el método otra vez cambiando solo la respuesta más dudosa. La muestra usó una
    # sola foto, de una casa en ruina evidente: con fotos de casas en estados intermedios podría haber fallas
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
