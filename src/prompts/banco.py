# Banco de prompts de la miniaplicación de detección de propiedades en posible abandono
# (Barrio Brasil y Concha y Toro). Los esquemas usan el formato de Claude:
# tipos en minúsculas y "additionalProperties": False en cada objeto.

BANCO_DE_PROMPTS = [
    # 1. Decide si el usuario dio una dirección o pidió una búsqueda
    {
        "nombre": "clasificar_solicitud",
        "system_instruction": (
            "Eres el asistente de una aplicación que detecta propiedades en posible abandono "
            "en Barrio Brasil y Concha y Toro, Santiago. Clasifica el mensaje del usuario como "
            "'direccion' si menciona una dirección específica, 'busqueda' si pide encontrar "
            "casas con ciertas características, u 'otro' si no es ninguna de las dos. Responde "
            "solo con un JSON con las claves 'tipo' ('direccion', 'busqueda' u 'otro') y "
            "'confianza' (número entre 0 y 1)."
        ),
        "ejemplo_usuario": "Dame una casa en Barrio Brasil que sea de un piso y que tenga ventanas tapiadas con madera, pintura descascarada y malezas en la entrada.",
        "claves_esperadas": ["tipo", "confianza"],
        "response_schema": {
            "type": "object",
            "properties": {
                "tipo": {"type": "string"},
                "confianza": {"type": "number"}
            },
            "required": ["tipo", "confianza"],
            "additionalProperties": False
        }
    },
    # 2. Saca los datos de la dirección, para pedir después la foto a Street View
    {
        "nombre": "extraer_direccion",
        "system_instruction": (
            "Eres el asistente de una aplicación que detecta propiedades en posible abandono "
            "en Barrio Brasil y Concha y Toro, Santiago. El usuario menciona la dirección de "
            "una propiedad. Extráela y responde solo con un JSON con las claves 'calle' "
            "(nombre de la calle, sin el número), 'numero' (número de la propiedad, como texto), "
            "'barrio' ('Barrio Brasil', 'Concha y Toro' o 'no indicado') y 'direccion_completa' "
            "(true si el mensaje trae calle y número, false si falta alguno). Si falta la calle "
            "o el número, usa 'no indicado' en ese campo."
        ),
        "ejemplo_usuario": "Revisa la casa de Almirante Barroso 256, en Barrio Brasil.",
        "claves_esperadas": ["calle", "numero", "barrio", "direccion_completa"],
        "response_schema": {
            "type": "object",
            "properties": {
                "calle": {"type": "string"},
                "numero": {"type": "string"},
                "barrio": {"type": "string"},
                "direccion_completa": {"type": "boolean"}
            },
            "required": ["calle", "numero", "barrio", "direccion_completa"],
            "additionalProperties": False
        }
    },
    # 3. Convierte una búsqueda en criterios: barrio, pisos y lista de señales
    {
        "nombre": "extraer_criterios_busqueda",
        "system_instruction": (
            "Eres el asistente de una aplicación que detecta propiedades en posible abandono "
            "en Barrio Brasil y Concha y Toro, Santiago. El usuario pide buscar casas con "
            "ciertas características. Extrae los criterios de búsqueda y responde solo con un "
            "JSON con las claves 'barrio' ('Barrio Brasil', 'Concha y Toro' o 'no indicado'), "
            "'pisos' (número entero; usa 0 si no lo menciona) y 'senales' (lista con las "
            "señales de abandono que pide, usando solo estos nombres: 'ventanas tapiadas', "
            "'vanos abiertos o vidrios rotos', 'malezas', 'grafitis', 'pintura descascarada', "
            "'revoque caído', 'techo dañado' o 'escombros'; si pide una señal parecida que no "
            "está en la lista, usa el nombre más parecido; usa una lista vacía si no menciona "
            "ninguna)."
        ),
        "ejemplo_usuario": "Dame una casa en Barrio Brasil que sea de un piso y que tenga ventanas tapiadas con madera, pintura descascarada y malezas en la entrada.",
        "claves_esperadas": ["barrio", "pisos", "senales"],
        "response_schema": {
            "type": "object",
            "properties": {
                "barrio": {"type": "string"},
                "pisos": {"type": "integer"},
                "senales": {"type": "array", "items": {"type": "string"}}
            },
            "required": ["barrio", "pisos", "senales"],
            "additionalProperties": False
        }
    },
    # 4. Evalúa la foto de la fachada: es el prompt principal de la miniapp.
    #    Es el único con imagen: la clave "imagen" guarda la ruta de la foto de prueba.
    #    Si "fachada_visible" es false, la foto no sirve para evaluar (no es una fachada o no se ve bien).
    {
        "nombre": "evaluar_fachada",
        "system_instruction": (
            "Eres un evaluador de fachadas para una aplicación que detecta propiedades en posible "
            "abandono en Barrio Brasil y Concha y Toro, Santiago. Analiza la foto de la fachada "
            "y responde solo con un JSON con las claves 'fachada_visible' (true si la foto "
            "muestra la fachada de una propiedad con claridad suficiente para evaluarla; false "
            "si no es una fachada o no se ve bien), 'senales' (lista con las señales de "
            "abandono que se ven en la foto, usando solo estos nombres: 'ventanas tapiadas', "
            "'vanos abiertos o vidrios rotos', 'malezas', 'grafitis', 'pintura descascarada', "
            "'revoque caído', 'techo dañado' o 'escombros'; lista vacía si no ves ninguna), "
            "'pisos' (número entero de pisos de la fachada; 0 si no se puede saber), "
            "'evidencia' ('ninguna', 'débil', 'moderada', 'fuerte' o 'muy fuerte') y "
            "'descripcion' (máximo 2 oraciones con lo más grave que ves). Incluye solo lo "
            "que se ve en la foto, sin suponer lo que no se ve."
        ),
        "ejemplo_usuario": "Evalúa la fachada de la propiedad de calle Almirante Barroso 256, Barrio Brasil.",
        "imagen": "docs/fachada-almirante-barroso-256.png",
        "claves_esperadas": ["fachada_visible", "senales", "pisos", "evidencia", "descripcion"],
        "response_schema": {
            "type": "object",
            "properties": {
                "fachada_visible": {"type": "boolean"},
                "senales": {"type": "array", "items": {"type": "string"}},
                "pisos": {"type": "integer"},
                "evidencia": {"type": "string"},
                "descripcion": {"type": "string"}
            },
            "required": ["fachada_visible", "senales", "pisos", "evidencia", "descripcion"],
            "additionalProperties": False
        }
    },
]
