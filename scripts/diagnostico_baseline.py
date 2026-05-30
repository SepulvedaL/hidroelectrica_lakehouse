import duckdb
import time
import os
from datetime import datetime

con = duckdb.connect()

# ==========================================================
# CREAR DIRECTORIO DE SALIDA
# ==========================================================

os.makedirs("lakehouse/analyze", exist_ok=True)

fecha_ejecucion = datetime.now().strftime("%Y%m%d_%H%M%S")

archivo_salida = (
    f"lakehouse/analyze/"
    f"reporte_baseline_{fecha_ejecucion}.txt"
)

# ==========================================================
# QUERIES ANALÍTICAS (las 3 más representativas del M3)
# ==========================================================

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
    'Q1 - Promedio mensual 2024': Q1,
    'Q2 - Alertas criticas por sensor': Q2,
    'Q3 - Resumen diario junio 2023': Q3
}

# ==========================================================
# GENERAR REPORTE
# ==========================================================

with open(archivo_salida, "w", encoding="utf-8") as reporte:

    reporte.write("=" * 80 + "\n")
    reporte.write("ANALISIS BASELINE - DUCKDB\n")
    reporte.write("=" * 80 + "\n\n")

    # ======================================================
    # PLANES DE EJECUCIÓN
    # ======================================================

    reporte.write("=" * 80 + "\n")
    reporte.write("PLANES DE EJECUCION (EXPLAIN ANALYZE)\n")
    reporte.write("=" * 80 + "\n\n")

    for nombre, query in queries.items():

        reporte.write("-" * 80 + "\n")
        reporte.write(f"{nombre}\n")
        reporte.write("-" * 80 + "\n\n")

        plan = con.execute(
            f"EXPLAIN ANALYZE {query}"
        ).fetchall()

        for row in plan:
            reporte.write(str(row[1]))
            reporte.write("\n")

        reporte.write("\n\n")

    # ======================================================
    # TIEMPOS BASELINE
    # ======================================================

    reporte.write("=" * 80 + "\n")
    reporte.write("TIEMPOS BASELINE\n")
    reporte.write("=" * 80 + "\n\n")

    for nombre, query in queries.items():

        # Warm-up
        for _ in range(3):
            con.execute(query).fetchall()

        tiempos = []

        for _ in range(5):
            inicio = time.perf_counter()

            con.execute(query).fetchall()

            fin = time.perf_counter()

            tiempos.append(
                (fin - inicio) * 1000
            )

        tiempos.sort()

        reporte.write(f"{nombre}\n")
        reporte.write(f"  Mediana : {tiempos[2]:.2f} ms\n")
        reporte.write(f"  Minimo  : {tiempos[0]:.2f} ms\n")
        reporte.write(f"  Maximo  : {tiempos[-1]:.2f} ms\n")
        reporte.write("\n")

# ==========================================================
# FIN
# ==========================================================

print("=" * 60)
print("ANALISIS FINALIZADO")
print("=" * 60)
print(f"Reporte generado en:\n{archivo_salida}")