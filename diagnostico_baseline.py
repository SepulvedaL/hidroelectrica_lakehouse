import duckdb
import time
 
con = duckdb.connect()
 
# ══════════════════════════════════════════════════════
# QUERIES ANALÍTICAS (las 3 más representativas del M3)
# ══════════════════════════════════════════════════════
 
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
 
queries = {'Q1 - Promedio mensual 2024': Q1,
           'Q2 - Alertas criticas por sensor': Q2,
           'Q3 - Resumen diario junio 2023': Q3}
 
# ══════════════════════════════════════════════════════
# PASO 1 — PLAN DE EJECUCIÓN
# ══════════════════════════════════════════════════════
print("\n" + "="*60)
print("PLANES DE EJECUCIÓN")
print("="*60)
 
for nombre, query in queries.items():
    print(f"\n{'─'*60}")
    print(f"-->{nombre}")
    print(f"{'─'*60}")
    plan = con.execute(f"EXPLAIN ANALYZE {query}").fetchall()
    for row in plan:
        print(row[1])
 
# ══════════════════════════════════════════════════════
# PASO 2 — TIEMPOS BASELINE (warm-up + mediana de 5)
# ══════════════════════════════════════════════════════
print("\n" + "="*60)
print("TIEMPOS BASELINE")
print("="*60)
 
for nombre, query in queries.items():
    # Warm-up
    for _ in range(3):
        con.execute(query).fetchall()
 
    # Medición
    tiempos = []
    for _ in range(5):
        t0 = time.perf_counter()
        con.execute(query).fetchall()
        tiempos.append((time.perf_counter() - t0) * 1000)
 
    tiempos.sort()
    print(f"\n{nombre}")
    print(f"  Mediana : {tiempos[2]:.2f} ms")
    print(f"  Mínimo  : {tiempos[0]:.2f} ms")
    print(f"  Máximo  : {tiempos[-1]:.2f} ms")