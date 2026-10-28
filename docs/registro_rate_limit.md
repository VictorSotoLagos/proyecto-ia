## Registro del ensayo de rate limit

### Ensayo con la API real

- Fecha: 2026-10-27
- Comando: `python src/cliente.py` (modelo `claude-opus-5-5`)
- Peticiones enviadas: 11 (la pregunta inicial y 10 de prueba seguidas), en 26 segundos
- Petición donde apareció el primer 429: ninguna; la API de Claude no limitó estas 11 peticiones
- Esperas observadas: ninguna, porque todas respondieron al primer intento
- Costo total del ensayo: $0.03003 USD (entre $0.00185 y $0.00422 por petición)
- Resultado: las 11 peticiones terminaron con éxito sin necesidad de reintentar

### Ensayo con la API simulada

Como la API real no devolvió ningún 429, el reintento se comprobó simulando las respuestas de la API, sin peticiones reales:

- Secuencia simulada: 429, 503 y luego 200
- Esperas observadas: 2.1s y 4.3s (backoff exponencial con jitter, correcto)
- Resultado: `consultar_modelo` respondió con éxito en el tercer intento
- Con tres 429 seguidos, se agotan los 3 intentos y `consultar_modelo` lanza `RuntimeError` con el mensaje "El servicio no respondió tras varios intentos"
- Con un 401 (credencial inválida) no se reintenta: falla de inmediato con `ValueError`
