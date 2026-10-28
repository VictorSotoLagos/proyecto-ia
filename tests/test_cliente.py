import sys
from unittest.mock import patch, Mock

import pytest

# Las pruebas se ejecutan desde la carpeta raíz del proyecto; se agrega src/ para poder importar el módulo
sys.path.append("src")
import cliente
from consumir_claude import enviar_peticion
from cliente import con_reintento, registrar_costo, consultar_modelo


# ---------- fixture: se ejecuta solo, antes de cada prueba ----------
# Con autouse=True, pytest lo aplica a todas las pruebas del archivo sin que haya que llamarlo.
# Deja el costo acumulado en cero, para que ninguna prueba dependa de lo que dejó la anterior

@pytest.fixture(autouse=True)
def reiniciar_costo_total():
    cliente.costo_total_sesion = 0.0
    yield  # en este punto se ejecuta la prueba


# ---------- enviar_peticion: clasificación de errores y respuesta exitosa ----------

def test_enviar_peticion_credencial_invalida():
    # Respuesta falsa con código 401: así se prueba sin llamar a la API real ni gastar tokens
    respuesta_falsa = Mock(status_code=401)

    # patch reemplaza requests.post por la respuesta falsa, solo dentro de este bloque
    with patch("consumir_claude.requests.post", return_value=respuesta_falsa):
        # La prueba pasa solo si enviar_peticion lanza ValueError
        with pytest.raises(ValueError):
            enviar_peticion("https://ejemplo.invalid", {}, {"pregunta": "test"})

def test_enviar_peticion_limite_de_uso():
    # Respuesta falsa con código 429: el límite de uso es un error momentáneo, así que debe lanzar TimeoutError
    respuesta_falsa = Mock(status_code=429)

    with patch("consumir_claude.requests.post", return_value=respuesta_falsa):
        with pytest.raises(TimeoutError):
            enviar_peticion("https://ejemplo.invalid", {}, {"pregunta": "test"})

def test_enviar_peticion_exito():
    # Camino feliz: respuesta 200. Hay que indicarle al Mock qué devuelve .json(),
    # porque si no devuelve otro objeto falso genérico y no el diccionario que se compara abajo
    respuesta_falsa = Mock(status_code=200)
    respuesta_falsa.json.return_value = {"texto": "respuesta simulada"}

    with patch("consumir_claude.requests.post", return_value=respuesta_falsa):
        resultado = enviar_peticion("https://ejemplo.invalid", {}, {"pregunta": "test"})

    assert resultado == {"texto": "respuesta simulada"}

def test_enviar_peticion_sin_permiso():
    # 403 (sin permiso) también es un problema de credencial: ValueError, igual que el 401
    respuesta_falsa = Mock(status_code=403)

    with patch("consumir_claude.requests.post", return_value=respuesta_falsa):
        with pytest.raises(ValueError):
            enviar_peticion("https://ejemplo.invalid", {}, {"pregunta": "test"})

def test_enviar_peticion_error_proveedor():
    # 500 o más (falla del proveedor) es momentáneo, igual que el 429: TimeoutError
    respuesta_falsa = Mock(status_code=500)

    with patch("consumir_claude.requests.post", return_value=respuesta_falsa):
        with pytest.raises(TimeoutError):
            enviar_peticion("https://ejemplo.invalid", {}, {"pregunta": "test"})


# ---------- con_reintento: cuándo reintenta y cuándo no ----------
# time.sleep se reemplaza por un mock: la prueba no espera de verdad y no se compara
# el valor exacto de la espera, porque el jitter lo hace aleatorio

def test_con_reintento_espera_entre_intentos():
    intentos = {"n": 0}

    def funcion_que_falla_una_vez():
        intentos["n"] += 1
        if intentos["n"] == 1:
            raise TimeoutError("simulado")
        return "ok"

    with patch("cliente.time.sleep") as mock_sleep:
        resultado = con_reintento(funcion_que_falla_una_vez)

    assert resultado == "ok"
    mock_sleep.assert_called_once()  # esperó una vez, sin importar cuántos segundos

def test_con_reintento_agota_intentos():
    # Una función que siempre falla con TimeoutError: se intenta 3 veces y luego se deja pasar el error original
    funcion_falsa = Mock(side_effect=TimeoutError("simulado"))

    with patch("cliente.time.sleep"):
        with pytest.raises(TimeoutError):
            con_reintento(funcion_falsa)

    assert funcion_falsa.call_count == 3

def test_con_reintento_no_reintenta_value_error():
    # Un ValueError (credencial inválida) no se reintenta: se llama una sola vez y no se espera
    funcion_falsa = Mock(side_effect=ValueError("credencial inválida"))

    with patch("cliente.time.sleep") as mock_sleep:
        with pytest.raises(ValueError):
            con_reintento(funcion_falsa)

    assert funcion_falsa.call_count == 1
    mock_sleep.assert_not_called()


# ---------- registrar_costo: cálculo y acumulación ----------

def test_registrar_costo_acumula():
    # El costo acumulado parte en cero gracias al fixture reiniciar_costo_total
    # 1.000 tokens de entrada (a US$4 por millón) y 500 de salida (a US$20 por millón) = 0,004 + 0,010
    respuesta_falsa = {"usage": {"input_tokens": 1000, "output_tokens": 500}}

    costo = registrar_costo(respuesta_falsa)
    registrar_costo(respuesta_falsa)

    assert round(costo, 6) == 0.014
    assert round(cliente.costo_total_sesion, 6) == 0.028  # las dos operaciones quedaron sumadas


# ---------- consultar_modelo: conversión y propagación de errores ----------
# armar_peticion también se reemplaza, para que la prueba no dependa de tener una API key en .env

def test_consultar_modelo_convierte_error():
    # Si se agotan los reintentos (TimeoutError), quien usa el cliente recibe un RuntimeError
    with patch("cliente.armar_peticion", return_value=("url", {}, {})), \
         patch("cliente.enviar_peticion", side_effect=TimeoutError("simulado")), \
         patch("cliente.time.sleep"):
        with pytest.raises(RuntimeError):
            consultar_modelo("pregunta de prueba")

def test_consultar_modelo_propaga_value_error():
    # Un ValueError (credencial inválida) llega sin cambios: no se convierte en RuntimeError
    with patch("cliente.armar_peticion", return_value=("url", {}, {})), \
         patch("cliente.enviar_peticion", side_effect=ValueError("credencial inválida")):
        with pytest.raises(ValueError):
            consultar_modelo("pregunta de prueba")
