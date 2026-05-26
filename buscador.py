# ============================================================
# BUSCADOR.PY
# Usa la libreria fast-flights para buscar precios en
# Google Flights y devuelve el vuelo mas barato encontrado
# para una combinacion de fechas y ruta especifica.
# ============================================================

import re    # Libreria para buscar patrones en texto (ej: extraer numeros de "€1,234")

# Importa las clases necesarias de fast-flights
from fast_flights import FlightData, Passengers, get_flights


# ============================================================
# FUNCION AUXILIAR: convertir precio de texto a numero
# ============================================================

def parsear_precio(texto_precio):
    """
    Convierte un precio en texto a un numero decimal.
    Ejemplos:
        "€1,234"  → 1234.0
        "$1.234"  → 1234.0
        "1234"    → 1234.0
        "1.234,50"→ 1234.5
    Devuelve None si no puede extraer un numero valido.
    """

    if not texto_precio:
        return None

    # Convierte a string por si acaso viene como otro tipo
    texto = str(texto_precio)

    # Elimina simbolos de moneda y espacios
    texto = texto.replace("€", "").replace("$", "").replace("£", "").strip()

    # Caso europeo: "1.234,50" → elimina puntos de miles, cambia coma decimal por punto
    if "," in texto and "." in texto:
        if texto.index(".") < texto.index(","):
            # Formato europeo: 1.234,50
            texto = texto.replace(".", "").replace(",", ".")
        else:
            # Formato americano: 1,234.50
            texto = texto.replace(",", "")
    elif "," in texto:
        # Solo coma: puede ser separador de miles o decimal
        # Si hay exactamente 3 digitos despues de la coma → es separador de miles
        partes = texto.split(",")
        if len(partes) == 2 and len(partes[1]) == 3:
            texto = texto.replace(",", "")    # "1,234" → "1234"
        else:
            texto = texto.replace(",", ".")   # "1,5" → "1.5"
    elif "." in texto:
        # Solo punto: puede ser separador de miles o decimal
        partes = texto.split(".")
        if len(partes) == 2 and len(partes[1]) == 3:
            texto = texto.replace(".", "")    # "1.234" → "1234"
        # Si no, lo dejamos como esta ("1234.50")

    # Extrae solo los digitos y el punto decimal
    solo_numeros = re.sub(r"[^\d.]", "", texto)

    try:
        return float(solo_numeros)
    except ValueError:
        return None    # No se pudo convertir


# ============================================================
# FUNCION PRINCIPAL: buscar el vuelo mas barato
# ============================================================

def buscar_vuelo_mas_barato(origen, destino, fecha_ida, fecha_vuelta,
                             pasajeros, solo_carry_on=True):
    """
    Busca vuelos de IDA Y VUELTA para una combinacion especifica de fechas.

    Parametros:
        origen       : codigo IATA de origen (ej: "MAD")
        destino      : codigo IATA de destino (ej: "EZE")
        fecha_ida    : fecha de salida (ej: "2026-08-18")
        fecha_vuelta : fecha de regreso (ej: "2026-09-01")
        pasajeros    : numero de adultos
        solo_carry_on: True = solo equipaje de mano

    Devuelve un diccionario con los datos del vuelo mas barato,
    o None si no encontro resultados o hubo un error.
    """

    print(f"    Buscando {origen}→{destino} | Ida: {fecha_ida} | Vuelta: {fecha_vuelta} ...", end=" ")

    try:
        # --------------------------------------------------------
        # PASO 1 y 2 combinados: buscar directamente con get_flights()
        # En esta version de fast-flights, get_flights() recibe todos
        # los parametros directamente (no hace falta create_filter aparte).
        # fetch_mode="fallback" le dice que reintente si Google bloquea.
        # --------------------------------------------------------
        resultado = get_flights(
            flight_data=[
                FlightData(
                    date=fecha_ida,           # Fecha de ida
                    from_airport=origen,      # Aeropuerto de origen
                    to_airport=destino,       # Aeropuerto de destino
                ),
                FlightData(
                    date=fecha_vuelta,        # Fecha de vuelta
                    from_airport=destino,     # En la vuelta, el destino es el origen
                    to_airport=origen,        # Y el origen es el destino
                ),
            ],
            trip="round-trip",               # Vuelo de ida y vuelta
            seat="economy",                  # Clase economica
            passengers=Passengers(adults=pasajeros),   # Cantidad de pasajeros
            fetch_mode="local",              # Usa Playwright (navegador real) - pasa el banner de cookies
        )

        # --------------------------------------------------------
        # PASO 3: Verificar que hay resultados
        # --------------------------------------------------------
        if not resultado or not resultado.flights:
            print("Sin resultados.")
            return None

        # --------------------------------------------------------
        # PASO 4: Buscar el vuelo mas barato entre los resultados
        # --------------------------------------------------------
        vuelo_mas_barato = None
        precio_minimo    = float("inf")    # Infinito: cualquier precio real sera menor

        for vuelo in resultado.flights:

            # Extrae el precio del vuelo (viene como texto, ej: "€850")
            precio_texto = getattr(vuelo, "price", None)

            # Convierte el precio de texto a numero
            precio = parsear_precio(precio_texto)

            # Si no se pudo obtener el precio, saltea este vuelo
            if precio is None:
                continue

            # fast-flights a veces devuelve precio por persona, a veces total.
            # La libreria v2.x devuelve precio TOTAL para todos los pasajeros.
            precio_total = precio

            # Guarda este vuelo si es el mas barato hasta ahora
            if precio_total < precio_minimo:
                precio_minimo    = precio_total
                vuelo_mas_barato = vuelo

        # Si no encontramos ningun vuelo con precio valido
        if vuelo_mas_barato is None:
            print("No se pudo leer el precio.")
            return None

        # --------------------------------------------------------
        # PASO 5: Extraer los datos del vuelo mas barato
        # getattr(obj, "campo", "valor_default") evita errores
        # si el campo no existe en el objeto
        # --------------------------------------------------------

        # Nombre de la aerolinea
        aerolinea = getattr(vuelo_mas_barato, "name", "Desconocida")

        # Duracion del vuelo
        duracion = getattr(vuelo_mas_barato, "duration", "Desconocida")

        # Cantidad de escalas
        stops = getattr(vuelo_mas_barato, "stops", None)
        if stops == 0:
            escalas = "Sin escalas"
        elif stops == 1:
            escalas = "1 escala"
        elif stops and stops > 1:
            escalas = f"{stops} escalas"
        else:
            # Si stops no es un numero, puede ser un texto descriptivo
            escalas = str(stops) if stops else "Desconocido"

        salida  = getattr(vuelo_mas_barato, "departure", "")
        llegada = getattr(vuelo_mas_barato, "arrival", "")
        dia_sig = getattr(vuelo_mas_barato, "arrival_time_ahead", "")
        if dia_sig:
            llegada = f"{llegada} ({dia_sig})"

        salida_vuelta  = getattr(vuelo_mas_barato, "return_departure", "")
        llegada_vuelta = getattr(vuelo_mas_barato, "return_arrival", "")
        dia_sig_vuelta = getattr(vuelo_mas_barato, "return_arrival_time_ahead", "")
        if dia_sig_vuelta:
            llegada_vuelta = f"{llegada_vuelta} ({dia_sig_vuelta})"

        print(f"Precio encontrado: {precio_minimo:.2f} EUR")

        # Devuelve un diccionario con toda la info del vuelo mas barato
        return {
            "origen":         origen,
            "destino":        destino,
            "fecha_ida":      fecha_ida,
            "fecha_vuelta":   fecha_vuelta,
            "pasajeros":      pasajeros,
            "precio_total":   precio_minimo,
            "aerolinea":      aerolinea,
            "duracion":       duracion,
            "escalas":        escalas,
            "salida":         salida,
            "llegada":        llegada,
            "salida_vuelta":  salida_vuelta,
            "llegada_vuelta": llegada_vuelta,
        }

    except Exception as e:
        # Captura cualquier error de fast-flights (timeout, bloqueo, etc.)
        print(f"Error: {e}")
        return None


# ============================================================
# FUNCION QUE BUSCA TODAS LAS COMBINACIONES DE FECHAS
# ============================================================

def buscar_todas_las_combinaciones(config_ruta):
    """
    Recibe la configuracion de UNA ruta del config.yaml y
    prueba TODAS las combinaciones posibles de fecha ida x fecha vuelta.

    Devuelve una lista de resultados (puede estar vacia si todo falla).
    """

    # Extrae los datos de configuracion de la ruta
    origen        = config_ruta["origen"]
    destino       = config_ruta["destino"]
    pasajeros     = config_ruta["pasajeros"]
    fechas_ida    = config_ruta["fechas_ida"]
    fechas_vuelta = config_ruta["fechas_vuelta"]
    solo_carry_on = config_ruta.get("solo_carry_on", True)   # True si no esta especificado

    resultados = []    # Lista donde guardamos todos los vuelos encontrados

    # Cuenta el total de combinaciones para mostrar progreso
    total = len(fechas_ida) * len(fechas_vuelta)
    print(f"  Combinaciones a buscar: {total} ({len(fechas_ida)} fechas ida x {len(fechas_vuelta)} fechas vuelta)")

    # Recorre cada combinacion posible de fecha ida y fecha vuelta
    for fecha_ida in fechas_ida:
        for fecha_vuelta in fechas_vuelta:

            # Busca el vuelo mas barato para esta combinacion especifica
            vuelo = buscar_vuelo_mas_barato(
                origen=origen,
                destino=destino,
                fecha_ida=str(fecha_ida),       # Convierte a string (YAML puede devolverlo como fecha)
                fecha_vuelta=str(fecha_vuelta),
                pasajeros=pasajeros,
                solo_carry_on=solo_carry_on,
            )

            # Si encontro un vuelo, lo agrega a la lista
            if vuelo:
                resultados.append(vuelo)

    return resultados


# ============================================================
# BLOQUE DE PRUEBA
# Ejecuta "python buscador.py" para probar UNA busqueda
# ============================================================
if __name__ == "__main__":

    print("=" * 55)
    print("TEST DE BUSQUEDA - UNA COMBINACION")
    print("=" * 55)

    resultado = buscar_vuelo_mas_barato(
        origen="MAD",
        destino="EZE",
        fecha_ida="2026-08-18",
        fecha_vuelta="2026-09-01",
        pasajeros=2,
        solo_carry_on=True,
    )

    if resultado:
        print("\n--- RESULTADO ---")
        print(f"Ruta:          {resultado['origen']} → {resultado['destino']}")
        print(f"Ida:           {resultado['fecha_ida']}")
        print(f"Vuelta:        {resultado['fecha_vuelta']}")
        print(f"Precio total:  {resultado['precio_total']:.2f} EUR")
        print(f"Por persona:   {resultado['precio_total'] / resultado['pasajeros']:.2f} EUR")
        print(f"Aerolinea:     {resultado['aerolinea']}")
        print(f"Duracion:      {resultado['duracion']}")
        print(f"Escalas:       {resultado['escalas']}")
    else:
        print("\nNo se encontraron resultados.")
        print("Posibles causas:")
        print("  - Google Flights bloqueo la busqueda temporalmente")
        print("  - No hay vuelos para esas fechas")
        print("  - Error de conexion a internet")
