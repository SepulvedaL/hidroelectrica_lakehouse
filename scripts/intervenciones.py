import duckdb
import pandas as pd
import time
import os
from datetime import datetime

# ==========================================================
# DIRECTORIO DE SALIDA
# ==========================================================

os.makedirs("lakehouse/analyze", exist_ok=True)

fecha_ejecucion = datetime.now().strftime("%Y%m%d_%H%M%S")

archivo_salida = (
    f"lakehouse/analyze/"
    f"reporte_intervenciones_{fecha_ejecucion}.txt"
)

# ==========================================================
# INTERVENCIÓN I-3
# Ordenar fact_lecturas por tiempo_sk
# ==========================================================

df = pd.read_parquet(
    'lakehouse/gold/fact_lecturas.parquet'
)

df_ordenado = df.sort_values(
    'tiempo_sk'
)

df_ordenado.to_parquet(
    'lakehouse/gold/fact_lecturas.parquet',
    index=False,
    row_group_size=100_000
)

# ==========================================================
# INTERVENCIÓN I-4
# Corregir tipos de dim_sensor
# ==========================================================

df_sensor = pd.read_parquet(
    'lakehouse/gold/dim_sensor.parquet'
)

df_sensor['sensor_sk'] = (
    df_sensor['sensor_sk']
    .astype('int32')
)

df_sensor['sensor_id'] = (
    df_sensor['sensor_id']
    .astype('int32')
)

df_sensor.to_parquet(
    'lakehouse/gold/dim_sensor.parquet',
    index=False
)

# ==========================================================
# CONEXIÓN DUCKDB
# ==========================================================

con = duckdb.connect()

# ==========================================================
# QUERIES
# ==========================================================

Q1 = """
SELECT t.anio, t.mes,
       AVG(f.valor) AS promedio_valor,
       COUNT(*) AS total_lecturas
FROM read_parquet('lakehouse/gold/fact_lecturas.parquet') f
JOIN read_parquet('lakehouse/gold/dim_tiempo.parquet') t
  ON f.tiempo_sk = t.tiempo_sk
WHERE t.anio = 2024
GROUP BY t.anio, t.mes
ORDER BY t.mes
"""

Q2 = """
SELECT s.tipo_sensor,
       f.nivel_alerta,
       COUNT(*) AS total,
       AVG(f.valor) AS promedio
FROM read_parquet('lakehouse/gold/fact_lecturas.parquet') f
JOIN read_parquet('lakehouse/gold/dim_sensor.parquet') s
  ON f.sensor_sk = s.sensor_sk
WHERE f.nivel_alerta = 'critico'
GROUP BY s.tipo_sensor, f.nivel_alerta
ORDER BY total DESC
"""

Q3 = """
SELECT t.anio,
       t.mes,
       t.dia,
       s.tipo_sensor,
       MAX(f.valor) AS max_valor,
       MIN(f.valor) AS min_valor,
       COUNT(*) AS lecturas_dia
FROM read_parquet('lakehouse/gold/fact_lecturas.parquet') f
JOIN read_parquet('lakehouse/gold/dim_tiempo.parquet') t
  ON f.tiempo_sk = t.tiempo_sk
JOIN read_parquet('lakehouse/gold/dim_sensor.parquet') s
  ON f.sensor_sk = s.sensor_sk
WHERE t.anio = 2023
  AND t.mes = 6
GROUP BY
    t.anio,
    t.mes,
    t.dia,
    s.tipo_sensor
ORDER BY
    t.dia,
    s.tipo_sensor
"""

queries = {
    'Q1 - Promedio mensual 2024': Q1,
    'Q2 - Alertas criticas por sensor': Q2,
    'Q3 - Resumen diario junio 2023': Q3
}

# ==========================================================
# BASELINE ORIGINAL
# ==========================================================

baseline = {
    'Q1 - Promedio mensual 2024': 19.88,
    'Q2 - Alertas criticas por sensor': 13.59,
    'Q3 - Resumen diario junio 2023': 21.92
}

# ==========================================================
# REPORTE
# ==========================================================

with open(
    archivo_salida,
    "w",
    encoding="utf-8"
) as reporte:

    reporte.write("=" * 80 + "\n")
    reporte.write("REPORTE DE INTERVENCIONES - DUCKDB\n")
    reporte.write("=" * 80 + "\n\n")

    # ------------------------------------------------------
    # INTERVENCIONES
    # ------------------------------------------------------

    reporte.write("INTERVENCIONES APLICADAS\n")
    reporte.write("-" * 80 + "\n")

    reporte.write(
        f"I-3: fact_lecturas ordenado por tiempo_sk "
        f"({len(df_ordenado):,} filas)\n"
    )

    reporte.write(
        "I-4: dim_sensor corregido "
        "(sensor_sk y sensor_id -> int32)\n"
    )

    reporte.write(
        f"Tipos finales: {dict(df_sensor.dtypes)}\n\n"
    )

    # ------------------------------------------------------
    # PLANES DE EJECUCIÓN
    # ------------------------------------------------------

    reporte.write("=" * 80 + "\n")
    reporte.write("PLANES DE EJECUCIÓN DESPUÉS DE INTERVENCIONES\n")
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

    # ------------------------------------------------------
    # TIEMPOS POSTERIORES
    # ------------------------------------------------------

    reporte.write("=" * 80 + "\n")
    reporte.write("RESULTADOS DE OPTIMIZACIÓN\n")
    reporte.write("=" * 80 + "\n\n")

    for nombre, query in queries.items():

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

        mediana = tiempos[2]

        factor = (
            baseline[nombre] / mediana
        )

        reporte.write(f"{nombre}\n")
        reporte.write(
            f"Antes   : {baseline[nombre]:.2f} ms\n"
        )
        reporte.write(
            f"Después : {mediana:.2f} ms\n"
        )
        reporte.write(
            f"Factor  : {factor:.2f}x\n"
        )
        reporte.write(
            f"Mínimo  : {tiempos[0]:.2f} ms\n"
        )
        reporte.write(
            f"Máximo  : {tiempos[-1]:.2f} ms\n"
        )
        reporte.write("\n")

# ==========================================================
# FIN
# ==========================================================

print("=" * 60)
print("INTERVENCIONES FINALIZADAS")
print("=" * 60)
print(f"Reporte generado en:\n{archivo_salida}")