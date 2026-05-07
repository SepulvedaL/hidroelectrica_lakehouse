import time
from astrapy import DataAPIClient
import pandas as pd
from dotenv import load_dotenv
import os

load_dotenv()


# ── CONFIG ───────────────────────────────────────────────
API_ENDPOINT = os.getenv("API_ENDPOINT")
API_TOKEN = os.getenv("API_TOKEN")

client = DataAPIClient()
db = client.get_database(API_ENDPOINT, token=API_TOKEN)
collection = db.get_collection("lecturas_sensores")

print("\n EJECUTANDO CONSULTAS EN CASSANDRA (ASTRA)\n")

# ── CARGA GENERAL (simula extracción completa) ───────────
start_total = time.time()
docs = list(collection.find({}, limit=10000))
df = pd.DataFrame(docs)
end_total = time.time()

print(f"Carga total de datos: {end_total - start_total:.4f} segundos\n")

# ── RESULTADOS PARA REPORTE ──────────────────────────────
reporte = []

def registrar(nombre, tipo, tiempo, descripcion):
    reporte.append({
        "consulta": nombre,
        "tipo_consulta": tipo,
        "tiempo_segundos": round(tiempo, 4),
        "descripcion": descripcion
    })

# ───────────────────────────────────────────────────────
# 1. Promedio por sensor
# ───────────────────────────────────────────────────────
start = time.time()
resultado = df.groupby('sensor_id')['valor'].mean()
end = time.time()

registrar(
    "Promedio por sensor",
    "Agregación",
    end - start,
    "Requiere procesamiento en memoria (no nativo en Cassandra)"
)

# ───────────────────────────────────────────────────────
# 2. Lecturas por hora
# ───────────────────────────────────────────────────────
start = time.time()
df['timestamp'] = pd.to_datetime(df['timestamp'])
df['hora'] = df['timestamp'].dt.hour
resultado = df.groupby('hora').size()
end = time.time()

registrar(
    "Lecturas por hora",
    "Agregación temporal",
    end - start,
    "Transformación + agregación fuera de Cassandra"
)

# ───────────────────────────────────────────────────────
# 3. Conteo por nivel de alerta
# ───────────────────────────────────────────────────────
start = time.time()
resultado = df['nivel_alerta'].value_counts()
end = time.time()

registrar(
    "Conteo por alerta",
    "Agregación simple",
    end - start,
    "No soportado directamente sin índices"
)

# ───────────────────────────────────────────────────────
# 4. Promedio por tipo de sensor
# ───────────────────────────────────────────────────────
start = time.time()
resultado = df.groupby('tipo_sensor')['valor'].mean()
end = time.time()

registrar(
    "Promedio por tipo",
    "Agregación categórica",
    end - start,
    "Requiere procesamiento en cliente"
)

# ───────────────────────────────────────────────────────
# 5. Eventos críticos
# ───────────────────────────────────────────────────────
start = time.time()
resultado = df[df['nivel_alerta'] == 'CRITICA']
end = time.time()

registrar(
    "Eventos críticos",
    "Filtro",
    end - start,
    "Consulta posible pero ineficiente sin índice"
)

# ── GENERAR REPORTE FINAL ───────────────────────────────
reporte_df = pd.DataFrame(reporte)

print("\n REPORTE DE CONSULTAS CASSANDRA\n")
print(reporte_df)

# Guardar reporte
reporte_df.to_csv("lakehouse/gold/reporte_cassandra.csv", index=False)

print("\n Reporte guardado en lakehouse/gold/reporte_cassandra.csv")