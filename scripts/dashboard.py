import duckdb
import pandas as pd
import matplotlib.pyplot as plt
from pathlib import Path

# ── Conexión ─────────────────────────────────────────────
con = duckdb.connect()

# ── Leer gold ────────────────────────────────────────────
fact = con.execute("""
SELECT * 
FROM read_parquet('lakehouse/gold/fact_lecturas.parquet')
""").fetchdf()

dim_sensor = con.execute("""
SELECT * 
FROM read_parquet('lakehouse/gold/dim_sensor.parquet')
""").fetchdf()

dim_tiempo = con.execute("""
SELECT * 
FROM read_parquet('lakehouse/gold/dim_tiempo.parquet')
""").fetchdf()

# ── Joins ────────────────────────────────────────────────
df = fact.merge(dim_sensor, on="sensor_sk")
df = df.merge(dim_tiempo, on="tiempo_sk")

# ── Cear figura ─────────────────────────────────────────
fig, axs = plt.subplots(2, 2, figsize=(14, 10))

# ───────────────────────────────────────────────────────
# 1. Lecturas por tipo de sensor
# ───────────────────────────────────────────────────────
tipo_counts = df["tipo_sensor"].value_counts()

axs[0, 0].bar(tipo_counts.index, tipo_counts.values)
axs[0, 0].set_title("Lecturas por Tipo de Sensor")
axs[0, 0].set_xlabel("Tipo Sensor")
axs[0, 0].set_ylabel("Cantidad")

# ───────────────────────────────────────────────────────
# 2. Distribución de alertas
# ───────────────────────────────────────────────────────
alertas = df["nivel_alerta"].value_counts()

axs[0, 1].pie(
    alertas.values,
    labels=alertas.index,
    autopct='%1.1f%%'
)

axs[0, 1].set_title("Distribución de Alertas")

# ───────────────────────────────────────────────────────
# 3. Promedio por sensor
# ───────────────────────────────────────────────────────
promedios = df.groupby("sensor_id")["valor"].mean()

axs[1, 0].bar(
    promedios.index.astype(str),
    promedios.values
)

axs[1, 0].set_title("Promedio por Sensor")
axs[1, 0].tick_params(axis='x', rotation=45)

# ───────────────────────────────────────────────────────
# 4. Evolución temporal
# ───────────────────────────────────────────────────────
temporal = df.groupby("fecha_hora")["valor"].mean()

axs[1, 1].plot(
    temporal.index,
    temporal.values
)

axs[1, 1].set_title("Evolución Temporal")
axs[1, 1].tick_params(axis='x', rotation=45)

# ── Ajustes ──────────────────────────────────────────────
plt.tight_layout()

# ── Guardar ─────────────────────────────────────────────
output_dir = Path("lakehouse/dashboard")
output_dir.mkdir(parents=True, exist_ok=True)

dashboard_path = output_dir / "dashboard_gold.png"

plt.savefig(dashboard_path)

print(f"\nDashboard guardado en: {dashboard_path}")