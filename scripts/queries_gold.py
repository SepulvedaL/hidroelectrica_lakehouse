import duckdb
 
con = duckdb.connect()
 
# ── CARGAR TABLAS GOLD ──────────────────────────────────
con.execute("""
    CREATE OR REPLACE VIEW metr AS
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
 
print("\nEJECUTANDO CONSULTAS...\n")
 
# ───────────────────────────────────────────────────────
# 1. Promedio de valores por sensor
# ───────────────────────────────────────────────────────
q1 = con.execute("""
    SELECT
        s.sensor_id,
        AVG(f.valor) AS promedio_valor
    FROM metr f
    JOIN dim_sensor s ON f.sensor_sk = s.sensor_sk
    GROUP BY s.sensor_id
""").fetchdf()
 
print("\n 1.Promedio por sensor:")
print(q1)
 
# ───────────────────────────────────────────────────────
# 2. Lecturas por hora
# ───────────────────────────────────────────────────────
q2 = con.execute("""
    SELECT
        t.anio,
        t.mes,
        t.dia,
        t.hora,
        COUNT(*) AS total_lecturas
    FROM metr f
    JOIN dim_tiempo t ON f.tiempo_sk = t.tiempo_sk
    GROUP BY t.anio, t.mes, t.dia, t.hora
    ORDER BY t.anio, t.mes, t.dia, t.hora
""").fetchdf()
 
print("\n 2. Lecturas por hora:")
print(q2)
 
# ───────────────────────────────────────────────────────
# 3. Conteo por nivel de alerta
# ───────────────────────────────────────────────────────
q3 = con.execute("""
    SELECT
        nivel_alerta,
        COUNT(*) AS cantidad
    FROM metr
    GROUP BY nivel_alerta
""").fetchdf()
 
print("\n 3.Conteo por nivel de alerta:")
print(q3)
 
# ───────────────────────────────────────────────────────
# 4. Promedio por tipo de sensor
# ───────────────────────────────────────────────────────
q4 = con.execute("""
    SELECT
        s.tipo_sensor,
        AVG(f.valor) AS promedio
    FROM metr f
    JOIN dim_sensor s ON f.sensor_sk = s.sensor_sk
    GROUP BY s.tipo_sensor
""").fetchdf()
 
print("\n 4. Promedio por tipo de sensor:")
print(q4)
 
# ───────────────────────────────────────────────────────
# 5. Detección de valores críticos
# ───────────────────────────────────────────────────────
q5 = con.execute("""
    SELECT
        s.sensor_id,
        t.fecha_hora,
        f.valor,
        f.nivel_alerta
    FROM metr f
    JOIN dim_sensor s ON f.sensor_sk = s.sensor_sk
    JOIN dim_tiempo t ON f.tiempo_sk = t.tiempo_sk
    WHERE f.nivel_alerta = 'CRITICA'
    ORDER BY t.fecha_hora
""").fetchdf()
 
print("\n 5.Lecturas críticas:")
print(q5)
 
print("\n Consultas ejecutadas correctamente")