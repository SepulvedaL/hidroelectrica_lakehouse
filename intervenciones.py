import duckdb
import pandas as pd
import time
import os
 
# ══════════════════════════════════════════════════════
# INTERVENCIÓN I-3 para Q1 y Q3:
# Ordenar fact_lecturas por tiempo_sk → activa data skipping
# ══════════════════════════════════════════════════════
print("Aplicando I-3: Ordenando fact_lecturas por tiempo_sk...")
df = pd.read_parquet('lakehouse/gold/fact_lecturas.parquet')
df_ordenado = df.sort_values('tiempo_sk')
df_ordenado.to_parquet(
    'lakehouse/gold/fact_lecturas.parquet',
    index=False,
    row_group_size=100_000
)
print(f"fact_lecturas reescrito y ordenado ({len(df_ordenado):,} filas)")
 
# ══════════════════════════════════════════════════════
# INTERVENCIÓN I-4 para Q2:
# Corregir tipos en dim_sensor para eliminar CAST implícito
# sensor_sk: int64 en dim_sensor, int32 en fact_lecturas
# ══════════════════════════════════════════════════════
print("\nAplicando I-4: Corrigiendo tipos en dim_sensor...")
df_sensor = pd.read_parquet('lakehouse/gold/dim_sensor.parquet')
df_sensor['sensor_sk'] = df_sensor['sensor_sk'].astype('int32')
df_sensor['sensor_id'] = df_sensor['sensor_id'].astype('int32')
df_sensor.to_parquet('lakehouse/gold/dim_sensor.parquet', index=False)
print(f"dim_sensor corregido — sensor_sk ahora es int32")
print(f"   Tipos: {dict(df_sensor.dtypes)}")
 
# ══════════════════════════════════════════════════════
# MEDIR DESPUÉS de las intervenciones
# ══════════════════════════════════════════════════════
con = duckdb.connect()
 
Q1 = """
SELECT t.anio, t.mes, AVG(f.valor) AS promedio_valor, COUNT(*) AS total_lecturas
FROM read_parquet('lakehouse/gold/fact_lecturas.parquet') f
JOIN read_parquet('lakehouse/gold/dim_tiempo.parquet') t
  ON f.tiempo_sk = t.tiempo_sk
WHERE t.anio = 2024
GROUP BY t.anio, t.mes
ORDER BY t.mes
"""
 
Q2 = """
SELECT s.tipo_sensor, f.nivel_alerta, COUNT(*) AS total, AVG(f.valor) AS promedio
FROM read_parquet('lakehouse/gold/fact_lecturas.parquet') f
JOIN read_parquet('lakehouse/gold/dim_sensor.parquet') s
  ON f.sensor_sk = s.sensor_sk
WHERE f.nivel_alerta = 'critico'
GROUP BY s.tipo_sensor, f.nivel_alerta
ORDER BY total DESC
"""
 
Q3 = """
SELECT t.anio, t.mes, t.dia, s.tipo_sensor,
       MAX(f.valor) AS max_valor,
       MIN(f.valor) AS min_valor,
       COUNT(*) AS lecturas_dia
FROM read_parquet('lakehouse/gold/fact_lecturas.parquet') f
JOIN read_parquet('lakehouse/gold/dim_tiempo.parquet') t
  ON f.tiempo_sk = t.tiempo_sk
JOIN read_parquet('lakehouse/gold/dim_sensor.parquet') s
  ON f.sensor_sk = s.sensor_sk
WHERE t.anio = 2023 AND t.mes = 6
GROUP BY t.anio, t.mes, t.dia, s.tipo_sensor
ORDER BY t.dia, s.tipo_sensor
"""
 
queries = {
    'Q1 - Promedio mensual 2024':      Q1,
    'Q2 - Alertas criticas por sensor': Q2,
    'Q3 - Resumen diario junio 2023':  Q3,
}
 
# ── Planes DESPUÉS ─────────────────────────────────────
print("\n" + "="*60)
print("PLANES DE EJECUCIÓN — DESPUÉS DE INTERVENCIONES")
print("="*60)
for nombre, query in queries.items():
    print(f"\n{'─'*60}")
    print(f"▶ {nombre}")
    print(f"{'─'*60}")
    plan = con.execute(f"EXPLAIN ANALYZE {query}").fetchall()
    for row in plan:
        print(row[1])
 
# ── Tiempos DESPUÉS ────────────────────────────────────
print("\n" + "="*60)
print("TIEMPOS DESPUÉS DE INTERVENCIONES")
print("="*60)
 
baseline = {'Q1 - Promedio mensual 2024': 19.88,
            'Q2 - Alertas criticas por sensor': 13.59,
            'Q3 - Resumen diario junio 2023': 21.92}
 
for nombre, query in queries.items():
    for _ in range(3):
        con.execute(query).fetchall()
    tiempos = []
    for _ in range(5):
        t0 = time.perf_counter()
        con.execute(query).fetchall()
        tiempos.append((time.perf_counter() - t0) * 1000)
    tiempos.sort()
    mediana = tiempos[2]
    factor = baseline[nombre] / mediana
    print(f"\n{nombre}")
    print(f"  Antes   : {baseline[nombre]:.2f} ms")
    print(f"  Después : {mediana:.2f} ms")
    print(f"  Factor  : {factor:.2f}x")
    print(f"  Mínimo  : {tiempos[0]:.2f} ms | Máximo: {tiempos[-1]:.2f} ms")