# ============================================================
# DATABASE.PY
# Crea y maneja la base de datos SQLite donde se guarda
# el historico de precios de cada busqueda.
# SQLite guarda todo en un solo archivo: precios.db
# ============================================================

import sqlite3          # Libreria para manejar bases de datos SQLite (ya viene con Python)
import datetime         # Libreria para manejar fechas y horas (ya viene con Python)


# Nombre del archivo donde SQLite va a guardar todos los datos
ARCHIVO_DB = "precios.db"


def crear_tabla():
    """Crea la tabla de precios si no existe todavia."""

    # Abre (o crea si no existe) el archivo de base de datos
    conexion = sqlite3.connect(ARCHIVO_DB)

    # El "cursor" es como un lapiz: permite escribir y leer en la base de datos
    cursor = conexion.cursor()

    # Ejecuta el comando SQL que crea la tabla
    # "IF NOT EXISTS" significa: solo la crea si no existe ya (evita errores al correr dos veces)
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS precios (
            id              INTEGER PRIMARY KEY AUTOINCREMENT,  -- Numero unico por cada registro
            ruta            TEXT,       -- Ej: "MAD-EZE"
            fecha_ida       TEXT,       -- Ej: "2026-08-18"
            fecha_vuelta    TEXT,       -- Ej: "2026-09-01"
            pasajeros       INTEGER,    -- Cantidad de personas
            precio_total    REAL,       -- Precio en euros para todos los pasajeros
            aerolinea       TEXT,       -- Nombre de la aerolinea
            duracion        TEXT,       -- Duracion del vuelo (ej: "14h 30m")
            escalas         TEXT,       -- Descripcion de escalas (ej: "1 escala en LHR")
            fecha_consulta  TEXT        -- Fecha y hora en que se hizo la busqueda
        )
    """)

    # Guarda los cambios en el archivo .db
    conexion.commit()

    # Cierra la conexion (buena practica: siempre cerrar cuando terminamos)
    conexion.close()


def guardar_precio(ruta, fecha_ida, fecha_vuelta, pasajeros, precio_total,
                   aerolinea, duracion, escalas):
    """Guarda un precio encontrado en la base de datos."""

    # Obtiene la fecha y hora actual para registrar cuando se hizo la busqueda
    fecha_consulta = datetime.datetime.now().strftime("%Y-%m-%d %H:%M:%S")

    # Abre la conexion a la base de datos
    conexion = sqlite3.connect(ARCHIVO_DB)
    cursor = conexion.cursor()

    # Inserta una nueva fila con todos los datos del vuelo
    # Los "?" son marcadores de posicion: evitan ataques de inyeccion SQL
    cursor.execute("""
        INSERT INTO precios
            (ruta, fecha_ida, fecha_vuelta, pasajeros, precio_total,
             aerolinea, duracion, escalas, fecha_consulta)
        VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)
    """, (ruta, fecha_ida, fecha_vuelta, pasajeros, precio_total,
          aerolinea, duracion, escalas, fecha_consulta))

    # Guarda y cierra
    conexion.commit()
    conexion.close()


def obtener_minimo_historico(ruta, fecha_ida, fecha_vuelta):
    """
    Busca el precio mas bajo que se haya registrado para
    una combinacion especifica de ruta + fechas.
    Devuelve el precio minimo, o None si no hay registros previos.
    """

    # Abre la conexion
    conexion = sqlite3.connect(ARCHIVO_DB)
    cursor = conexion.cursor()

    # Busca el valor minimo de precio_total para esa ruta y fechas exactas
    cursor.execute("""
        SELECT MIN(precio_total)
        FROM precios
        WHERE ruta = ?
          AND fecha_ida = ?
          AND fecha_vuelta = ?
    """, (ruta, fecha_ida, fecha_vuelta))

    # Obtiene el resultado (fetchone devuelve la primera fila encontrada)
    resultado = cursor.fetchone()

    # Cierra la conexion
    conexion.close()

    # resultado es una tupla como (1650.0,) o (None,) si no hay datos
    # resultado[0] extrae el numero de adentro
    return resultado[0]


def obtener_ultimos_precios(ruta, limite=10):
    """
    Devuelve los ultimos N precios registrados para una ruta.
    Util para ver el historial reciente.
    """

    conexion = sqlite3.connect(ARCHIVO_DB)
    cursor = conexion.cursor()

    # Ordena por fecha de consulta de mas reciente a mas antiguo
    # LIMIT restringe cuantas filas devuelve
    cursor.execute("""
        SELECT fecha_ida, fecha_vuelta, precio_total, aerolinea, fecha_consulta
        FROM precios
        WHERE ruta = ?
        ORDER BY fecha_consulta DESC
        LIMIT ?
    """, (ruta, limite))

    # fetchall devuelve TODAS las filas encontradas (no solo la primera)
    resultados = cursor.fetchall()

    conexion.close()

    return resultados


# ============================================================
# BLOQUE DE PRUEBA
# Este codigo solo se ejecuta si corres "python database.py"
# directamente. No se ejecuta cuando otros archivos importan
# este modulo.
# ============================================================
if __name__ == "__main__":

    print("Creando base de datos...")
    crear_tabla()                                     # Crea la tabla
    print("✓ Tabla creada correctamente en precios.db")

    print("Insertando precio de prueba...")
    guardar_precio(                                   # Guarda un dato de ejemplo
        ruta="MAD-EZE",
        fecha_ida="2026-08-18",
        fecha_vuelta="2026-09-01",
        pasajeros=2,
        precio_total=1580.50,
        aerolinea="Iberia",
        duracion="14h 20m",
        escalas="Sin escalas"
    )
    print("✓ Precio de prueba guardado")

    minimo = obtener_minimo_historico("MAD-EZE", "2026-08-18", "2026-09-01")
    print(f"✓ Minimo historico para MAD-EZE (18ago/1sep): {minimo} EUR")
