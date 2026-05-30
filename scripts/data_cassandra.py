# ==========================================================
# GENERADOR MASIVO ASTRA DB - CASSANDRA
# Proyecto Hidroeléctrica Lakehouse
# ==========================================================

from astrapy import DataAPIClient
from datetime import datetime, timedelta, timezone
from dotenv import load_dotenv

import uuid
import random
import time
import os

# ==========================================================
# VARIABLES ENTORNO
# ==========================================================

load_dotenv()

API_TOKEN = os.getenv("API_TOKEN")
API_ENDPOINT = os.getenv("API_ENDPOINT")

# ==========================================================
# CONEXIÓN ASTRA
# ==========================================================

client = DataAPIClient()

db = client.get_database(
    API_ENDPOINT,
    token=API_TOKEN
)

sensor_table = db.get_table("sensor")

lecturas_table = db.get_table("lecturas_sensores")

print("=====================================")
print("CONECTADO A ASTRA DB")
print("=====================================")

# ==========================================================
# CONFIGURACIÓN GENERAL
# ==========================================================

TOTAL_REGISTROS = 600000

BATCH_SIZE = 250

FECHA_INICIO_GLOBAL = datetime(
    2025, 4, 1,
    tzinfo=timezone.utc
)

FECHA_FIN_GLOBAL = datetime(
    2026, 4, 1,
    tzinfo=timezone.utc
)

# ==========================================================
# CONFIGURACIÓN TIPOS SENSOR
# ==========================================================

TIPOS_SENSOR = {

    "temperatura": {

        "NORMAL": (50, 75),

        "ADVERTENCIA": (76, 89),

        "CRITICA": (90, 100)
    },

    "presion": {

        "NORMAL": (20, 40),

        "ADVERTENCIA": (41, 59),

        "CRITICA": (60, 80)
    },

    "vibracion": {

        "NORMAL": (1, 5),

        "ADVERTENCIA": (6, 9),

        "CRITICA": (10, 15)
    },

    "nivel_agua": {

        "NORMAL": (10, 18),

        "ADVERTENCIA": (19, 24),

        "CRITICA": (25, 35)
    }
}

# ==========================================================
# DEFINICIÓN SENSORES (15 SENSORES)
# ==========================================================

sensores = [

    # ======================================================
    # TEMPERATURA
    # ======================================================

    {
        "sensor_id": 101,
        "tipo_sensor": "temperatura",

        "fecha_inicio": datetime(
            2025, 4, 1,
            tzinfo=timezone.utc
        ),

        "fecha_final": datetime(
            2025, 10, 1,
            tzinfo=timezone.utc
        ),

        "sensor_reemplazo": 201
    },

    {
        "sensor_id": 201,
        "tipo_sensor": "temperatura",

        "fecha_inicio": datetime(
            2025, 10, 1,
            tzinfo=timezone.utc
        ),

        "fecha_final": None,

        "sensor_reemplazo": None
    },

    {
        "sensor_id": 105,
        "tipo_sensor": "temperatura",

        "fecha_inicio": datetime(
            2025, 5, 1,
            tzinfo=timezone.utc
        ),

        "fecha_final": None,

        "sensor_reemplazo": None
    },

    {
        "sensor_id": 109,
        "tipo_sensor": "temperatura",

        "fecha_inicio": datetime(
            2025, 6, 15,
            tzinfo=timezone.utc
        ),

        "fecha_final": None,

        "sensor_reemplazo": None
    },

    # ======================================================
    # PRESIÓN
    # ======================================================

    {
        "sensor_id": 102,
        "tipo_sensor": "presion",

        "fecha_inicio": datetime(
            2025, 4, 1,
            tzinfo=timezone.utc
        ),

        "fecha_final": datetime(
            2025, 11, 15,
            tzinfo=timezone.utc
        ),

        "sensor_reemplazo": 202
    },

    {
        "sensor_id": 202,
        "tipo_sensor": "presion",

        "fecha_inicio": datetime(
            2025, 11, 15,
            tzinfo=timezone.utc
        ),

        "fecha_final": None,

        "sensor_reemplazo": None
    },

    {
        "sensor_id": 106,
        "tipo_sensor": "presion",

        "fecha_inicio": datetime(
            2025, 6, 1,
            tzinfo=timezone.utc
        ),

        "fecha_final": None,

        "sensor_reemplazo": None
    },

    {
        "sensor_id": 110,
        "tipo_sensor": "presion",

        "fecha_inicio": datetime(
            2025, 7, 15,
            tzinfo=timezone.utc
        ),

        "fecha_final": None,

        "sensor_reemplazo": None
    },

    # ======================================================
    # VIBRACIÓN
    # ======================================================

    {
        "sensor_id": 103,
        "tipo_sensor": "vibracion",

        "fecha_inicio": datetime(
            2025, 4, 1,
            tzinfo=timezone.utc
        ),

        "fecha_final": None,

        "sensor_reemplazo": None
    },

    {
        "sensor_id": 107,
        "tipo_sensor": "vibracion",

        "fecha_inicio": datetime(
            2025, 7, 1,
            tzinfo=timezone.utc
        ),

        "fecha_final": None,

        "sensor_reemplazo": None
    },

    {
        "sensor_id": 111,
        "tipo_sensor": "vibracion",

        "fecha_inicio": datetime(
            2025, 8, 10,
            tzinfo=timezone.utc
        ),

        "fecha_final": None,

        "sensor_reemplazo": None
    },

    {
        "sensor_id": 112,
        "tipo_sensor": "vibracion",

        "fecha_inicio": datetime(
            2025, 9, 5,
            tzinfo=timezone.utc
        ),

        "fecha_final": None,

        "sensor_reemplazo": None
    },

    # ======================================================
    # NIVEL AGUA
    # ======================================================

    {
        "sensor_id": 104,
        "tipo_sensor": "nivel_agua",

        "fecha_inicio": datetime(
            2025, 4, 1,
            tzinfo=timezone.utc
        ),

        "fecha_final": None,

        "sensor_reemplazo": None
    },

    {
        "sensor_id": 108,
        "tipo_sensor": "nivel_agua",

        "fecha_inicio": datetime(
            2025, 8, 1,
            tzinfo=timezone.utc
        ),

        "fecha_final": None,

        "sensor_reemplazo": None
    },

    {
        "sensor_id": 113,
        "tipo_sensor": "nivel_agua",

        "fecha_inicio": datetime(
            2025, 9, 20,
            tzinfo=timezone.utc
        ),

        "fecha_final": None,

        "sensor_reemplazo": None
    }
]

# ==========================================================
# INSERTAR SENSORES
# ==========================================================

print("=====================================")
print("INSERTANDO SENSORES")
print("=====================================")

for sensor in sensores:

    try:

        sensor_table.insert_one(sensor)

        print(
            f"Sensor {sensor['sensor_id']} insertado"
        )

    except Exception:

        print(
            f"Sensor {sensor['sensor_id']} ya existe"
        )

# ==========================================================
# FUNCIONES AUXILIARES
# ==========================================================

def generar_fecha(fecha_inicio, fecha_fin):

    delta = fecha_fin - fecha_inicio

    segundos_random = random.randint(
        0,
        int(delta.total_seconds())
    )

    fecha_generada = fecha_inicio + timedelta(
        seconds=segundos_random
    )

    return fecha_generada.astimezone(
        timezone.utc
    )


def generar_valor_y_alerta(tipo_sensor):

    probabilidad = random.random()

    if probabilidad < 0.70:

        alerta = "NORMAL"

    elif probabilidad < 0.90:

        alerta = "ADVERTENCIA"

    else:

        alerta = "CRITICA"

    rango = TIPOS_SENSOR[tipo_sensor][alerta]

    valor = round(

        random.uniform(
            rango[0],
            rango[1]
        ),

        2
    )

    return valor, alerta


def obtener_sensor_valido(
    tipo_sensor,
    fecha_evento
):

    sensores_validos = []

    for sensor in sensores:

        mismo_tipo = (
            sensor["tipo_sensor"] == tipo_sensor
        )

        inicio_ok = (
            fecha_evento >= sensor["fecha_inicio"]
        )

        fin_ok = (

            sensor["fecha_final"] is None

            or

            fecha_evento < sensor["fecha_final"]
        )

        if mismo_tipo and inicio_ok and fin_ok:

            sensores_validos.append(sensor)

    return random.choice(sensores_validos)

# ==========================================================
# GENERACIÓN MASIVA
# ==========================================================

print("=====================================")
print("GENERANDO REGISTROS")
print("=====================================")

inicio = time.time()

batch = []

insertados = 0

tipos_sensores = [

    "temperatura",
    "presion",
    "vibracion",
    "nivel_agua"
]

for i in range(TOTAL_REGISTROS):

    # ======================================================
    # GENERAR FECHA GLOBAL
    # ======================================================

    timestamp_evento = generar_fecha(

        FECHA_INICIO_GLOBAL,

        FECHA_FIN_GLOBAL
    )

    # ======================================================
    # ESCOGER TIPO SENSOR
    # ======================================================

    tipo_sensor = random.choice(
        tipos_sensores
    )

    # ======================================================
    # OBTENER SENSOR ACTIVO EN ESA FECHA
    # ======================================================

    sensor = obtener_sensor_valido(

        tipo_sensor,

        timestamp_evento
    )

    # ======================================================
    # FECHA PARTICIÓN
    # ======================================================

    fecha = timestamp_evento.date()

    # ======================================================
    # VALOR Y ALERTA
    # ======================================================

    valor, alerta = generar_valor_y_alerta(
        tipo_sensor
    )

    # ======================================================
    # DOCUMENTO FINAL
    # ======================================================

    documento = {

        "sensor_id": sensor["sensor_id"],

        "fecha": fecha,

        "timestamp": timestamp_evento,

        "lectura_id": str(uuid.uuid4()),

        "tipo_sensor": tipo_sensor,

        "valor": valor,

        "nivel_alerta": alerta
    }

    batch.append(documento)

    # ======================================================
    # INSERTAR LOTE
    # ======================================================

    if len(batch) >= BATCH_SIZE:

        try:

            lecturas_table.insert_many(batch)

            insertados += len(batch)

            print(
                f"{insertados:,} registros insertados"
            )

        except Exception as e:

            print("=================================")
            print("ERROR INSERTANDO BATCH")
            print("=================================")

            print(e)

        batch = []

# ==========================================================
# INSERTAR ÚLTIMO LOTE
# ==========================================================

if batch:

    try:

        lecturas_table.insert_many(batch)

        insertados += len(batch)

    except Exception as e:

        print(e)

# ==========================================================
# FINALIZACIÓN
# ==========================================================

fin = time.time()

print("=====================================")
print("CARGA COMPLETADA")
print("=====================================")

print(
    f"Total registros insertados: "
    f"{insertados:,}"
)

print(
    f"Tiempo total: "
    f"{round(fin - inicio, 2)} segundos"
)