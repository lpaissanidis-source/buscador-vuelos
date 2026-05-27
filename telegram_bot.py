# ============================================================
# TELEGRAM_BOT.PY
# Maneja el envio de mensajes por Telegram.
# Lee el TOKEN y CHAT_ID desde credenciales.txt
# y usa la API de Telegram para mandar alertas.
# ============================================================

import requests    # Para hacer llamadas a internet (a la API de Telegram)
import os          # Para leer archivos del sistema


# ============================================================
# LECTURA DE CREDENCIALES
# Lee el archivo credenciales.txt y extrae el TOKEN y CHAT_ID
# ============================================================

def leer_credenciales():
    """
    Lee credenciales.txt y devuelve un diccionario con
    las claves TOKEN y CHAT_ID.
    El archivo debe tener el formato:
        TELEGRAM_BOT_TOKEN=xxxxx
        TELEGRAM_CHAT_ID=xxxxx
    """

    credenciales = {}    # Diccionario vacio donde vamos a guardar los valores

    # Abre el archivo en modo lectura ("r")
    with open("credenciales.txt", "r") as archivo:

        # Recorre cada linea del archivo
        for linea in archivo:

            linea = linea.strip()    # Elimina espacios y saltos de linea al inicio/final

            # Ignora lineas vacias o comentarios (que empiezan con #)
            if not linea or linea.startswith("#"):
                continue

            # Divide la linea en dos partes usando "=" como separador
            # Ejemplo: "TELEGRAM_BOT_TOKEN=abc123" → ["TELEGRAM_BOT_TOKEN", "abc123"]
            if "=" in linea:
                clave, valor = linea.split("=", 1)   # maxsplit=1: solo divide en el primer "="
                credenciales[clave.strip()] = valor.strip()

    return credenciales


# Primero prueba variables de entorno (GitHub Actions usa secrets como env vars)
TOKEN   = os.environ.get("TELEGRAM_BOT_TOKEN", "")
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")

# Si no hay variables de entorno, lee el archivo local (ejecucion en PC)
if not TOKEN or not CHAT_ID:
    try:
        _credenciales = leer_credenciales()
        TOKEN   = _credenciales.get("TELEGRAM_BOT_TOKEN", TOKEN)
        CHAT_ID = _credenciales.get("TELEGRAM_CHAT_ID", CHAT_ID)
    except FileNotFoundError:
        pass

# URL base de la API de Telegram (con el TOKEN incluido)
URL_API = f"https://api.telegram.org/bot{TOKEN}"


# ============================================================
# FUNCIONES PRINCIPALES
# ============================================================

def enviar_mensaje(texto):
    """
    Envia un mensaje de texto simple por Telegram.
    Devuelve True si se envio correctamente, False si hubo error.
    """

    # Endpoint de la API para enviar mensajes
    url = f"{URL_API}/sendMessage"

    # Datos que le mandamos a Telegram
    datos = {
        "chat_id":    CHAT_ID,    # A quien mandamos el mensaje
        "text":       texto,      # El contenido del mensaje
        "parse_mode": "HTML"      # Permite usar <b>negrita</b> y <i>italica</i> en el texto
    }

    try:
        # Hace la llamada POST a la API de Telegram
        respuesta = requests.post(url, data=datos, timeout=10)

        # Convierte la respuesta JSON a un diccionario de Python
        resultado = respuesta.json()

        # Verifica si Telegram confirmo que el mensaje se mando correctamente
        if resultado.get("ok"):
            return True    # Exito
        else:
            # Telegram devolvio un error (ej: TOKEN incorrecto, CHAT_ID invalido)
            print(f"  Error de Telegram: {resultado.get('description', 'Error desconocido')}")
            return False

    except requests.exceptions.Timeout:
        # La conexion tardo mas de 10 segundos
        print("  Error: Timeout al conectar con Telegram")
        return False

    except requests.exceptions.ConnectionError:
        # No hay conexion a internet
        print("  Error: Sin conexion a internet")
        return False

    except Exception as e:
        # Cualquier otro error inesperado
        print(f"  Error inesperado: {e}")
        return False


def enviar_alerta_precio(ruta, fecha_ida, fecha_vuelta, precio_total,
                         aerolinea, duracion, escalas, pasajeros,
                         salida="", llegada="", salida_vuelta="", llegada_vuelta="",
                         buscador="", es_minimo_historico=False):
    """
    Envia una alerta formateada cuando se encuentra un precio bajo el umbral.
    es_minimo_historico=True agrega un mensaje especial si es el minimo historico.
    """

    if es_minimo_historico:
        encabezado = "NUEVO MINIMO HISTORICO"
    else:
        encabezado = "PRECIO BAJO UMBRAL"

    linea_horario_ida    = f"<b>🕐 Horario ida:</b> {salida} → {llegada}\n" if (salida or llegada) else ""
    linea_horario_vuelta = f"<b>🕐 Horario vuelta:</b> {salida_vuelta} → {llegada_vuelta}\n" if (salida_vuelta or llegada_vuelta) else ""

    mensaje = (
        f"<b>📁 {buscador}</b>\n"
        f"<b>✈️ {encabezado}</b>\n"
        f"\n"
        f"<b>Ruta:</b> {ruta}\n"
        f"<b>Ida:</b> {fecha_ida}\n"
        f"<b>Vuelta:</b> {fecha_vuelta}\n"
        f"<b>Pasajeros:</b> {pasajeros}\n"
        f"\n"
        f"<b>💰 Precio total:</b> {precio_total:.2f} EUR\n"
        f"<b>Precio por persona:</b> {precio_total / pasajeros:.2f} EUR\n"
        f"\n"
        f"<b>Aerolínea:</b> {aerolinea}\n"
        f"<b>Duración:</b> {duracion}\n"
        f"<b>Escalas:</b> {escalas}\n"
        f"{linea_horario_ida}"
        f"{linea_horario_vuelta}"
    )

    return enviar_mensaje(mensaje)


def enviar_mensaje_prueba():
    """
    Manda un mensaje simple para verificar que el bot funciona.
    Se usa antes de la primera ejecucion real.
    """

    mensaje = (
        "<b>✅ Test de conexion exitoso</b>\n"
        "\n"
        "El buscador de vuelos esta configurado correctamente.\n"
        "Vas a recibir alertas aqui cuando encuentre precios bajos."
    )

    return enviar_mensaje(mensaje)


# ============================================================
# BLOQUE DE PRUEBA
# Ejecuta "python telegram_bot.py" para probar la conexion
# ============================================================
if __name__ == "__main__":

    print("Leyendo credenciales...")
    print(f"  TOKEN encontrado: {'Si' if TOKEN else 'NO - revisar credenciales.txt'}")
    print(f"  CHAT_ID encontrado: {'Si' if CHAT_ID else 'NO - revisar credenciales.txt'}")

    print("\nEnviando mensaje de prueba a Telegram...")
    exito = enviar_mensaje_prueba()

    if exito:
        print("✓ Mensaje enviado correctamente. Revisa tu Telegram.")
    else:
        print("✗ No se pudo enviar. Revisa el TOKEN y CHAT_ID en credenciales.txt")
