import duckdb
import pandas as pd
from pathlib import Path
 
# ── RUTAS ───────────────────────────────────────────────
SILVER = Path('lakehouse/silver')
GOLD = Path('lakehouse/gold')
 
GOLD.mkdir(parents=True, exist_ok=True)
 
# ── CONEXIÓN DUCKDB ─────────────────────────────────────
con = duckdb.connect()
 
# ── CARGAR SILVER ───────────────────────────────────────
silver_path = SILVER / 'lecturas_sensores_silver.parquet'
 
df = con.execute(f"""
    SELECT *
    FROM read_parquet('{silver_path}')
""").fetchdf()
 
print(f"Filas en Silver: {len(df)}")
 
# ── DIM_TIEMPO ──────────────────────────────────────────
dim_tiempo = con.execute(f"""
    SELECT DISTINCT
        CAST(strftime(timestamp, '%Y%m%d%H') AS BIGINT) AS tiempo_sk,
        timestamp AS fecha_hora,
        year(timestamp) AS anio,
        month(timestamp) AS mes,
        day(timestamp) AS dia,
        hour(timestamp) AS hora,
        strftime(timestamp, '%w') AS dia_semana
    FROM df
""").fetchdf()
 
dim_tiempo.to_parquet(GOLD / 'dim_tiempo.parquet', index=False)
 
print(f"dim_tiempo: {len(dim_tiempo)} filas")
 
# ── DIM_SENSOR ──────────────────────────────────────────
dim_sensor = con.execute(f"""
    SELECT DISTINCT
        sensor_id,
        tipo_sensor
    FROM df
""").fetchdf()
 
# crear surrogate key
dim_sensor['sensor_sk'] = range(1, len(dim_sensor) + 1)
 
dim_sensor.to_parquet(GOLD / 'dim_sensor.parquet', index=False)
 
print(f"dim_sensor: {len(dim_sensor)} filas")
 
# ── METRICAS ───────────────────────────────────────
metr = con.execute(f"""
    SELECT
        s.sensor_sk,
        CAST(strftime(d.timestamp, '%Y%m%d%H') AS BIGINT) AS tiempo_sk,
        d.valor,
        d.nivel_alerta_calculada AS nivel_alerta
    FROM df d
    JOIN dim_sensor s
    ON d.sensor_id = s.sensor_id
""").fetchdf()
 
metr.to_parquet(GOLD / 'metr_lecturas.parquet', index=False)
 
print(f"metr_lecturas: {len(metr)} filas")
 
print("\nGOLD generado correctamente")