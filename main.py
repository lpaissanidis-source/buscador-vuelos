# ============================================================
# MAIN.PY
# Archivo principal. Lo unico que tenes que ejecutar:
#   python main.py
#
# Coordina todo el sistema:
#   1. Lee las rutas desde config.yaml
#   2. Busca vuelos con Playwright (Google Flights)
#   3. Guarda cada precio encontrado en la base de datos
#   4. Manda alerta por Telegram si el precio baja del umbral
#      o si es un nuevo minimo historico
# ============================================================

import yaml        # Para leer el archivo config.yaml
import datetime    # Para mostrar la hora de inicio/fin de cada ejecucion

# Importa las funciones de los otros archivos del proyecto
from database     import crear_tabla, guardar_precio, obtener_minimo_historico
from buscador     import buscar_todas_las_combinaciones
from telegram_bot import enviar_alerta_precio, enviar_mensaje


# ============================================================
# FUNCION: leer configuracion
# ============================================================

def leer_config():
    """Lee el archivo config.yaml y devuelve la lista de rutas."""

    # Abre el archivo config.yaml en modo lectura
    with open("config.yaml", "r", encoding="utf-8") as archivo:
        # yaml.safe_load convierte el YAML a un diccionario de Python
        config = yaml.safe_load(archivo)

    # Devuelve la lista de rutas (la clave "rutas" del YAML)
    return config.get("rutas", [])


# ============================================================
# FUNCION: procesar una ruta completa
# ============================================================

def procesar_ruta(config_ruta):
    """
    Recibe la configuracion de una ruta, busca todos los vuelos,
    guarda los precios y manda alerta si corresponde.

    Regla anti-spam: manda como maximo 1 alerta por ruta
    (la combinacion de fechas con el precio mas bajo encontrado).
    """

    nombre    = config_ruta["nombre"]
    origen    = config_ruta["origen"]
    destino   = config_ruta["destino"]
    umbral    = config_ruta["umbral_precio"]
    pasajeros = config_ruta["pasajeros"]

    # Codigo de ruta para la base de datos (ej: "MAD-EZE")
    codigo_ruta = f"{origen}-{destino}"

    print(f"\n{'='*55}")
    print(f"  Ruta: {nombre}")
    print(f"  Umbral: {umbral} EUR para {pasajeros} pasajeros")
    print(f"{'='*55}")

    # --------------------------------------------------------
    # PASO 1: Buscar todas las combinaciones de fechas
    # --------------------------------------------------------
    resultados = buscar_todas_las_combinaciones(config_ruta)

    if not resultados:
        print(f"  Sin resultados para esta ruta.")
        return

    print(f"\n  Resultados obtenidos: {len(resultados)} combinaciones con precio")

    # --------------------------------------------------------
    # PASO 2: Guardar TODOS los resultados en la base de datos
    # y detectar el mejor precio de esta ejecucion
    # --------------------------------------------------------
    mejor_vuelo          = None    # El vuelo mas barato de esta ejecucion
    mejor_precio         = float("inf")
    mejor_es_nuevo_min   = False   # Si es nuevo minimo historico

    for vuelo in resultados:

        fecha_ida    = vuelo["fecha_ida"]
        fecha_vuelta = vuelo["fecha_vuelta"]
        precio_total = vuelo["precio_total"]

        # Guarda el precio en la base de datos (siempre, sin importar si es bajo)
        guardar_precio(
            ruta         = codigo_ruta,
            fecha_ida    = fecha_ida,
            fecha_vuelta = fecha_vuelta,
            pasajeros    = pasajeros,
            precio_total = precio_total,
            aerolinea    = vuelo["aerolinea"],
            duracion     = vuelo["duracion"],
            escalas      = vuelo["escalas"],
        )

        # Muestra el resultado en pantalla
        bajo_umbral = "✓ BAJO UMBRAL" if precio_total < umbral else ""
        print(f"    {fecha_ida} → {fecha_vuelta} | {precio_total:.0f} EUR | "
              f"{vuelo['aerolinea']} | {vuelo['escalas']} {bajo_umbral}")

        # --------------------------------------------------------
        # Verifica si este vuelo es el mejor de esta ejecucion
        # --------------------------------------------------------
        if precio_total < mejor_precio:
            mejor_precio = precio_total
            mejor_vuelo  = vuelo

            # Consulta el minimo historico guardado en la base de datos
            # para esta combinacion especifica de ruta + fechas
            minimo_historico = obtener_minimo_historico(
                ruta         = codigo_ruta,
                fecha_ida    = fecha_ida,
                fecha_vuelta = fecha_vuelta,
            )

            # Es nuevo minimo si no habia registro previo (None)
            # o si el precio actual es menor al minimo guardado.
            # Nota: el precio ya fue guardado arriba, entonces el minimo
            # historico puede ser igual al precio actual en la primera vez.
            # Por eso comparamos con estricto menor (<).
            if minimo_historico is None or precio_total < minimo_historico:
                mejor_es_nuevo_min = True
            else:
                mejor_es_nuevo_min = False

    # --------------------------------------------------------
    # PASO 3: Decidir si mandar alerta (maximo 1 por ruta)
    # Se manda si el mejor precio esta bajo el umbral
    # O si es un nuevo minimo historico
    # --------------------------------------------------------
    if mejor_vuelo is None:
        return

    debe_alertar = (mejor_precio < umbral) or mejor_es_nuevo_min

    if debe_alertar:
        print(f"\n  *** ALERTA: Precio {mejor_precio:.0f} EUR")
        if mejor_es_nuevo_min:
            print(f"  *** Es nuevo minimo historico para esta ruta/fechas")
        print(f"  Enviando Telegram...")

        exito = enviar_alerta_precio(
            ruta               = nombre,
            fecha_ida          = mejor_vuelo["fecha_ida"],
            fecha_vuelta       = mejor_vuelo["fecha_vuelta"],
            precio_total       = mejor_precio,
            aerolinea          = mejor_vuelo["aerolinea"],
            duracion           = mejor_vuelo["duracion"],
            escalas            = mejor_vuelo["escalas"],
            pasajeros          = pasajeros,
            es_minimo_historico = mejor_es_nuevo_min,
        )

        if exito:
            print(f"  ✓ Telegram enviado correctamente")
        else:
            print(f"  ✗ Error al enviar Telegram")
    else:
        print(f"\n  Mejor precio encontrado: {mejor_precio:.0f} EUR")
        print(f"  Umbral: {umbral} EUR — No se manda alerta (precio sobre el umbral)")


# ============================================================
# PROGRAMA PRINCIPAL
# Todo lo que esta dentro de "if __name__ == '__main__':"
# se ejecuta cuando corres "python main.py"
# ============================================================

if __name__ == "__main__":

    # Muestra la hora de inicio
    hora_inicio = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\nBuscador de vuelos iniciado: {hora_inicio}")

    # --------------------------------------------------------
    # PASO 0: Asegurarse de que la base de datos existe
    # Si ya existe, crear_tabla() no hace nada (es seguro llamarla siempre)
    # --------------------------------------------------------
    crear_tabla()

    # --------------------------------------------------------
    # PASO 1: Leer las rutas del archivo config.yaml
    # --------------------------------------------------------
    try:
        rutas = leer_config()
    except FileNotFoundError:
        print("ERROR: No se encontro config.yaml en la carpeta actual.")
        print("Asegurate de ejecutar el script desde la carpeta del proyecto.")
        exit(1)

    if not rutas:
        print("ERROR: No hay rutas configuradas en config.yaml")
        exit(1)

    print(f"Rutas a buscar: {len(rutas)}")

    # --------------------------------------------------------
    # PASO 2: Procesar cada ruta una por una
    # --------------------------------------------------------
    for ruta in rutas:
        try:
            procesar_ruta(ruta)
        except Exception as e:
            # Si una ruta falla (ej: Google la bloquea), continua con la siguiente
            # en vez de detener todo el programa
            print(f"\n  ERROR procesando {ruta.get('nombre', '?')}: {e}")
            print(f"  Continuando con la siguiente ruta...")

    # Muestra la hora de fin
    hora_fin = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    print(f"\n{'='*55}")
    print(f"Busqueda completada: {hora_fin}")
    print(f"{'='*55}\n")
