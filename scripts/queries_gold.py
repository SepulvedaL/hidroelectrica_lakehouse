import duckdb
import pandas as pd
import time

# ── CONEXIÓN ─────────────────────────────────────────────
con = duckdb.connect()

# ── CARGAR TABLAS GOLD ───────────────────────────────────
con.execute("""
CREATE OR REPLACE VIEW fact AS 
SELECT * FROM read_parquet('lakehouse/gold/metr_lecturas.parquet')
""")

con.execute("""
CREATE OR REPLACE VIEW dim_tiempo AS 
SELECT * FROM read_parquet('lakehouse/gold/dim_tiempo.parquet')
""")

con.execute("""
CREATE OR REPLACE VIEW dim_sensor AS 
SELECT * FROM read_parquet('lakehouse/gold/dim_sensor.parquet')
""")

print("\n EJECUTANDO CONSULTAS EN DUCKDB\n")

# ── REPORTE ──────────────────────────────────────────────
reporte = []

def registrar(nombre, tipo, tiempo, descripcion):
    reporte.append({
        "consulta": nombre,
        "tipo_consulta": tipo,
        "tiempo_segundos": round(tiempo, 6),
        "descripcion": descripcion
    })

# ───────────────────────────────────────────────────────
# 1. Promedio por sensor
# ───────────────────────────────────────────────────────
start = time.time()

q1 = con.execute("""
SELECT 
    s.sensor_id,
    AVG(f.valor) AS promedio_valor
FROM fact f
JOIN dim_sensor s ON f.sensor_sk = s.sensor_sk
GROUP BY s.sensor_id
""").fetchdf()

end = time.time()

print("1️. Promedio por sensor:")
print(q1)

registrar(
    "Promedio por sensor",
    "Agregación",
    end - start,
    "Agregación SQL ejecutada nativamente en DuckDB"
)

# ───────────────────────────────────────────────────────
# 2. Lecturas por hora
# ───────────────────────────────────────────────────────
start = time.time()

q2 = con.execute("""
SELECT 
    t.anio,
    t.mes,
    t.dia,
    t.hora,
    COUNT(*) AS total_lecturas
FROM fact f
JOIN dim_tiempo t ON f.tiempo_sk = t.tiempo_sk
GROUP BY t.anio, t.mes, t.dia, t.hora
ORDER BY t.anio, t.mes, t.dia, t.hora
""").fetchdf()

end = time.time()

print("\n2️. Lecturas por hora:")
print(q2)

registrar(
    "Lecturas por hora",
    "Agregación temporal",
    end - start,
    "Agrupación temporal optimizada en motor columnar"
)

# ───────────────────────────────────────────────────────
# 3. Conteo por nivel de alerta
# ───────────────────────────────────────────────────────
start = time.time()

q3 = con.execute("""
SELECT 
    nivel_alerta,
    COUNT(*) AS cantidad
FROM fact
GROUP BY nivel_alerta
""").fetchdf()

end = time.time()

print("\n3️. Conteo por nivel de alerta:")
print(q3)

registrar(
    "Conteo por alerta",
    "Agregación simple",
    end - start,
    "Conteo ejecutado directamente sobre Parquet"
)

# ───────────────────────────────────────────────────────
# 4. Promedio por tipo de sensor
# ───────────────────────────────────────────────────────
start = time.time()

q4 = con.execute("""
SELECT 
    s.tipo_sensor,
    AVG(f.valor) AS promedio
FROM fact f
JOIN dim_sensor s ON f.sensor_sk = s.sensor_sk
GROUP BY s.tipo_sensor
""").fetchdf()

end = time.time()

print("\n4. Promedio por tipo de sensor:")
print(q4)

registrar(
    "Promedio por tipo",
    "Agregación categórica",
    end - start,
    "Consulta analítica con JOIN y GROUP BY"
)

# ───────────────────────────────────────────────────────
# 5. Eventos críticos
# ───────────────────────────────────────────────────────
start = time.time()

q5 = con.execute("""
SELECT 
    s.sensor_id,
    t.fecha_hora,
    f.valor,
    f.nivel_alerta
FROM fact f
JOIN dim_sensor s ON f.sensor_sk = s.sensor_sk
JOIN dim_tiempo t ON f.tiempo_sk = t.tiempo_sk
WHERE f.nivel_alerta = 'CRITICA'
ORDER BY t.fecha_hora
""").fetchdf()

end = time.time()

print("\n5️. Lecturas críticas:")
print(q5)

registrar(
    "Eventos críticos",
    "Filtro",
    end - start,
    "Filtro analítico ejecutado directamente en DuckDB"
)

# ── REPORTE FINAL ───────────────────────────────────────
reporte_df = pd.DataFrame(reporte)

print("\n REPORTE DE CONSULTAS DUCKDB\n")
print(reporte_df)

# Guardar CSV
reporte_df.to_csv("lakehouse/gold/reporte_duckdb.csv", index=False)

print("\n Reporte guardado en lakehouse/gold/reporte_duckdb.csv")

print("\n Consultas DuckDB ejecutadas correctamente")