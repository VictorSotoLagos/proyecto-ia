import time  # para esperar entre un intento y otro, con time.sleep
import random  # para sumar a cada espera un pequeño azar (jitter)
from typing import Callable, Any  # solo describen los tipos de datos: no cambian cómo funciona el código

from consumir_claude import MODELO, PRECIO_ENTRADA, PRECIO_SALIDA, armar_peticion, enviar_peticion, extraer_texto, calcular_costo

# Ejecuta "funcion" y, si falla por un error momentáneo (TimeoutError), la vuelve a intentar.
# - funcion: lo que se quiere ejecutar (más abajo se entrega envuelto en un lambda)
# - intentos: cuántas veces se intenta en total; si no se indica, son 3
# - espera_base: segundos de espera después del primer fallo; se duplica en cada intento (backoff exponencial)
# - espera_maxima: tope de segundos de espera, para que no crezca sin límite
def con_reintento(
    funcion: Callable[[], Any],
    intentos: int = 3,
    espera_base: float = 2,
    espera_maxima: float = 30,
) -> Any:
    for intento in range(1, intentos + 1):  # con 3 intentos, "intento" vale 1, 2 y 3
        try:
            return funcion()  # si funciona, devuelve el resultado y la función termina aquí
        except TimeoutError:
            # Solo se reintentan los errores momentáneos; un ValueError (credencial inválida) sale de inmediato
            if intento == intentos:
                raise  # era el último intento: se rinde y deja pasar el mismo error a quien llamó
            espera = min(espera_base * (2 ** (intento - 1)), espera_maxima)  # 2 s, 4 s, 8 s... hasta 30 s
            espera_con_jitter = espera + random.uniform(0, espera * 0.1)  # hasta un 10% extra al azar
            print(f"Intento {intento} de {intentos} falló. Reintentando en {espera_con_jitter:.1f}s...")
            time.sleep(espera_con_jitter)


costo_total_sesion = 0.0  # suma del costo de todas las operaciones de esta ejecución

def registrar_costo(respuesta: dict) -> float:
    global costo_total_sesion  # para poder modificar la variable de afuera de la función
    uso = respuesta.get("usage", {})
    total_tokens = uso.get("input_tokens", 0) + uso.get("output_tokens", 0)
    # Se reutiliza calcular_costo, con los precios reales de Claude Opus 5.5 por tipo de token
    costo_estimado = calcular_costo(respuesta, PRECIO_ENTRADA, PRECIO_SALIDA)
    costo_total_sesion += costo_estimado
    print(f"Operación: {total_tokens} tokens, costo estimado: ${costo_estimado:.5f} (acumulado: ${costo_total_sesion:.5f})")
    return costo_estimado


def consultar_modelo(pregunta: str, system_instruction: str = "") -> str:
    url, headers, body = armar_peticion(MODELO, pregunta, system_instruction)
    try:
        # El lambda "envuelve" la llamada sin ejecutarla, para que con_reintento pueda repetirla cuantas veces haga falta
        respuesta = con_reintento(lambda: enviar_peticion(url, headers, body))
    except TimeoutError:
        raise RuntimeError("El servicio no respondió tras varios intentos. Intenta más tarde.")
    registrar_costo(respuesta)
    return extraer_texto(respuesta)


if __name__ == "__main__": # Solo se ejecuta al correr este archivo directamente, NO cuando otro archivo lo importa
    try:
        # Claude acepta un prompt de sistema vacío (""), pero rechaza uno que sea solo un espacio (" ")
        resultado = consultar_modelo("¿Cuál es la capital de Chile?")
        print(resultado)

        # 10 peticiones seguidas, para ver el reintento y el costo acumulado en acción
        for i in range(10):
            try:
                respuesta = consultar_modelo(f"Pregunta de prueba número {i}")
                print(f"Respuesta {i}: {respuesta[:40]}...")
            except RuntimeError as error:
                print(f"Respuesta {i} falló definitivamente: {error}")
    except (ValueError, RuntimeError, TimeoutError) as error:
        print("No se pudo completar la operación:", error)
