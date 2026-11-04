## Registro de la chain de tres pasos: ficha de la propiedad

- Fecha: 2026-11-04
- Comando: `python src/cadena_ficha.py` (modelo `claude-opus-5-5`, con LangChain)
- Pruebas: `pytest` (`tests/test_cadena_ficha.py`, con el modelo simulado con `MagicMock`; no usa la API)

### Qué hace

`construir_cadena(modelo)` arma una chain de tres pasos que convierte el reporte escrito de un vecino en una conclusión sobre la propiedad. Cada paso tiene su propio `PromptTemplate` y una sola responsabilidad:

| Paso | Responsabilidad | Recibe | Entrega |
|---|---|---|---|
| 1. Estado observado | Describir la fachada de forma objetiva, sin juzgar si está en abandono | `{reporte}` | Descripción de pisos, puertas, ventanas, muros, techo y vereda |
| 2. Daño observable | Listar los daños con las 8 señales fijas del prompt `evaluar_fachada` del Gate 1 | `{estado}` | Un daño por línea |
| 3. Conclusión | Decidir si la propiedad está en posible abandono, con la escala de evidencia del Gate 1 | `{danos}` | Conclusión, evidencia y justificación |

Los pasos se conectan con `|`, `StrOutputParser()` y una `lambda` que arma el diccionario que espera la plantilla siguiente, como en la clase del 2026-11-03.

### Por qué tres pasos y no uno

- El reporte de un vecino viene en lenguaje informal ("se ve el cielo por arriba", "la pintura se está saltando"). El paso 1 lo ordena en una descripción objetiva antes de evaluar.
- El paso 2 traduce esa descripción a las mismas 8 señales que usa la evaluación de fotos del Gate 1, así los reportes escritos y las fotos hablan el mismo idioma.
- El paso 3 concluye solo a partir de los daños listados, no del texto original, así la conclusión se apoya en señales concretas y no en la forma en que el vecino escribió el reporte.

### Entrada

> Pasé por Almirante Barroso 256, en Barrio Brasil. Es una casa antigua de un piso, con la fachada llena de adornos. Las ventanas están tapiadas con tablas y parece que el techo se cayó, porque desde la calle se ve el cielo por arriba. Hay pasto y plantas creciendo en la entrada, los muros están rayados con grafitis y la pintura se está saltando por todos lados.

### Resultado

```
Conclusión: En posible abandono
Evidencia: Muy fuerte
Justificación: Las ventanas tapiadas, junto con el techo dañado o los escombros, son señales claras de desocupación y falta de mantenimiento, y la presencia simultánea de malezas, grafitis y pintura descascarada refuerza un patrón de descuido prolongado.
```

### Observaciones

- La conclusión coincide con la evaluación de la foto real de la misma propiedad en el Gate 1 (evidencia "muy fuerte").
- El nivel de evidencia varía entre ejecuciones: en una corrida anterior del mismo día, con el mismo reporte, fue "fuerte".
- La justificación menciona escombros, que el reporte no nombra. Probablemente el paso 2 los dedujo de "parece que el techo se cayó". Como la chain solo entrega el resultado del último paso, para confirmarlo hay que correr cada paso por separado con `.invoke()`.
- En la primera corrida la conclusión llegó con negritas de markdown (`**Conclusión:**`). Se agregó "en texto simple sin markdown" al prompt del paso 3.
