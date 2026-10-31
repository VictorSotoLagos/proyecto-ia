# Revisión manual del CORE del Bloque 17: los 10 casos de la muestra de precision.py
# (los 5 con F1 más bajo y los 5 con F1 más alto, sobre 26 respuestas generadas el 2026-10-30).
#
# Para cada caso, lee la referencia y la respuesta (en los comentarios) y completa la rúbrica:
# - correccion_factual: ¿todo dato verificable de la respuesta coincide con la referencia? "si", "no" o "parcialmente"
# - completitud: ¿la respuesta cubre todo lo que cubre la referencia? "si", "no" o "parcialmente"
# - contradiccion: ¿la respuesta afirma lo contrario de algo de la referencia? "si" o "no"
# - nota: por qué elegiste esas respuestas (sin la nota, la rúbrica no sirve cuando vuelvas a leerla)

import json

revision_manual = [
    # ---------- Los 5 con F1 más bajo ----------

    # Referencia: La pintura descascarada, las grietas, la humedad, los rayados y los vidrios rotos indican que una fachada no recibe mantención.
    # Respuesta: Pintura descascarada, grietas en muros, canaletas tapadas u oxidadas, maleza crecida, ventanas rotas o selladas,
    #            manchas de humedad y techos con tejas faltantes o hundidos.
    {
        "consulta": "¿Qué señales en la fachada indican que una propiedad no recibe mantención?",
        "f1": 0.22,
        "correccion_factual": "si",
        "completitud": "no",
        "contradiccion": "no",
        "nota": "La respuesta no incluye los rayados, que sí están en la referencia. Tampoco menciona que las canaletas tapadas u oxidadas, la maleza crecida y los techos con tejas faltantes o hundidos son señales de falta de mantención.",
    },

    # Referencia: Una propiedad abandonada casi siempre tiene dueño: lo que le falta es uso y mantención, no un propietario.
    # Respuesta: Normalmente significa que **no tiene ocupantes ni recibe uso o mantenimiento**, pero casi siempre sigue teniendo
    #            un dueño legal, salvo que este renuncie formalmente a ella o la pierda por vía judicial.
    {
        "consulta": "¿Una propiedad abandonada significa que no tiene dueño o que no tiene ocupantes?",
        "f1": 0.32,
        "correccion_factual": "si",
        "completitud": "si",
        "contradiccion": "no",
        "nota": "La respuesta incluye toda la información de la referencia y no contiene información contradictoria.",
    },

    # Referencia: Una propiedad desocupada solo no tiene ocupantes, mientras que una abandonada además está sin mantención y deteriorándose.
    # Respuesta: Una propiedad desocupada simplemente no tiene ocupantes en ese momento, pero su dueño la sigue cuidando y tiene la intención
    #            de usarla, venderla o alquilarla, mientras que una propiedad abandonada ha sido dejada por su dueño sin mantenimiento ni
    #            intención aparente de regresar o de ejercer sus derechos sobre ella.
    {
        "consulta": "¿Qué diferencia hay entre una propiedad desocupada y una propiedad abandonada?",
        "f1": 0.36,
        "correccion_factual": "si",
        "completitud": "si",
        "contradiccion": "no",
        "nota": "La respuesta incluye toda la información de la referencia, e incluso la complementa satisfactoriamente. No contiene información errónea ni contradictoria.",
    },

    # Referencia: La tasación es la estimación del valor comercial de una propiedad, realizada por un tasador.
    # Respuesta: La tasación de una propiedad es la valoración profesional que determina su valor de mercado según factores como la
    #            ubicación, el tamaño, el estado y las características del inmueble.
    {
        "consulta": "¿Qué es la tasación de una propiedad?",
        "f1": 0.41,
        "correccion_factual": "si",
        "completitud": "si",
        "contradiccion": "no",
        "nota": "La respuesta incluye toda la información de la referencia. Sin embargo, ni la referencia ni la respuesta son completamente exhaustivas. No se hace diferencia entre tasación comercial y tasación fiscal, ni se mencionan los métodos de tasación.",
    },

    # Referencia: El Conservador de Bienes Raíces es el registro donde se inscriben la propiedad y los gravámenes de los inmuebles.
    # Respuesta: El Conservador de Bienes Raíces es, en Chile, un auxiliar de la administración de justicia encargado de llevar los registros
    #            públicos de inmuebles, inscribiendo propiedades, hipotecas, gravámenes y prohibiciones para dar publicidad y certeza
    #            jurídica a su dominio.
    {
        "consulta": "¿Qué es el Conservador de Bienes Raíces?",
        "f1": 0.42,
        "correccion_factual": "si",
        "completitud": "si",
        "contradiccion": "no",
        "nota": "La informacion de la respuesta coincide con la referencia y no contiene información contradictoria. Sin embargo, ni la referencia ni la respuesta son completamente exhaustivas. No se mencionan los Conservadores de Bienes Raíces como funcionarios públicos ni su relación con el Ministerio de Justicia.",
    },

    # ---------- Los 5 con F1 más alto ----------

    # Referencia: La UF es una unidad de cuenta chilena que se reajusta según la inflación y se usa para fijar precios de propiedades y créditos hipotecarios.
    # Respuesta: La Unidad de Fomento (UF) es una unidad de cuenta chilena que se reajusta diariamente según la inflación (IPC) y se usa para
    #            fijar precios, créditos hipotecarios y contratos manteniendo su valor real.
    {
        "consulta": "¿Qué es la Unidad de Fomento (UF)?",
        "f1": 0.83,
        "correccion_factual": "si",
        "completitud": "no",
        "contradiccion": "no",
        "nota": "Solo le falta indicar que es para fijar precios de propiedades, pero no es un error grave. La respuesta es correcta y completa en lo demás.",
    },

    # Referencia: Las contribuciones se pagan en cuatro cuotas al año: abril, junio, septiembre y noviembre.
    # Respuesta: En Chile, las contribuciones se pagan en **cuatro cuotas al año**, con vencimiento en abril, junio, septiembre y noviembre.
    {
        "consulta": "¿En cuántas cuotas al año se pagan las contribuciones en Chile?",
        "f1": 0.85,
        "correccion_factual": "si",
        "completitud": "si",
        "contradiccion": "no",
        "nota": "La respuesta es correcta y completa.",
    },

    # Referencia: El certificado de dominio vigente, emitido por el Conservador de Bienes Raíces, acredita quién es el dueño actual.
    # Respuesta: El **Certificado de Dominio Vigente**, emitido por el Conservador de Bienes Raíces correspondiente, acredita quién es el
    #            dueño actual de una propiedad en Chile.
    {
        "consulta": "¿Qué documento acredita quién es el dueño actual de una propiedad en Chile?",
        "f1": 0.86,
        "correccion_factual": "si",
        "completitud": "si",
        "contradiccion": "no",
        "nota": "La respuesta es correcta y completa.",
    },

    # Referencia: El Barrio Brasil está en la comuna de Santiago, en la Región Metropolitana.
    # Respuesta: El Barrio Brasil está en la comuna de **Santiago** (Santiago Centro), en la Región Metropolitana de Chile.
    {
        "consulta": "¿En qué comuna está el Barrio Brasil?",
        "f1": 0.87,
        "correccion_factual": "si",
        "completitud": "si",
        "contradiccion": "no",
        "nota": "La respuesta es correcta y completa.",
    },

    # Referencia: Santiago fue fundada en 1541 por Pedro de Valdivia.
    # Respuesta: Santiago de Chile fue fundada en 1541 por Pedro de Valdivia.
    {
        "consulta": "¿En qué año se fundó Santiago de Chile?",
        "f1": 0.90,
        "correccion_factual": "si",
        "completitud": "si",
        "contradiccion": "no",
        "nota": "La respuesta es correcta y completa.",
    },
]

# Antes de guardar, se revisa que no quede ningún campo de la rúbrica sin completar
pendientes = []
for caso in revision_manual:
    if "" in (caso["correccion_factual"], caso["completitud"], caso["contradiccion"], caso["nota"]):
        pendientes.append(caso["consulta"])

if pendientes:
    print(f"Faltan {len(pendientes)} casos por completar:")
    for consulta in pendientes:
        print(" -", consulta)
else:
    with open("docs/revision_manual.json", "w", encoding="utf-8") as archivo:
        json.dump(revision_manual, archivo, indent=2, ensure_ascii=False)
    print("Revisión guardada en docs/revision_manual.json")
