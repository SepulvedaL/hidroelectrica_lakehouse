import pandas as pd
from pathlib import Path

# ── RUTAS ───────────────────────────────────────────────
BRONZE = Path('lakehouse/bronze')
SILVER = Path('lakehouse/silver')

SILVER.mkdir(parents=True, exist_ok=True)

# ── CARGA DE DATOS ──────────────────────────────────────
archivos = list(BRONZE.glob('lecturas_sensores_*.parquet'))

if not archivos:
    raise Exception("No hay archivos en Bronze")

# Leer todos los archivos Bronze
df_bronze = pd.concat([pd.read_parquet(f) for f in archivos], ignore_index=True)

print(f"Filas totales en Bronze: {len(df_bronze)}")

# Copia para transformación
df = df_bronze.copy()


# ── LIMPIEZA ────────────────────────────────────────────

# 1. Eliminar columna técnica de Astra si existe
df = df.drop(columns=['_id'], errors='ignore')

# 2. Convertir timestamp
df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')

# 3. Eliminar filas con nulos críticos
df = df.dropna(subset=['sensor_id', 'timestamp', 'valor'])

# 4. Normalizar texto
df['tipo_sensor'] = df['tipo_sensor'].astype(str).str.lower().str.strip()
df['nivel_alerta'] = df['nivel_alerta'].astype(str).str.upper().str.strip()

# 5. Validación de valores (no negativos)
df = df[df['valor'] >= 0]

# 6. Clasificación automática de alerta (opcional pero recomendado)
def clasificar_alerta(valor):
    if valor > 80:
        return "CRITICA"
    elif valor > 60:
        return "ADVERTENCIA"
    else:
        return "NORMAL"

df['nivel_alerta_calculada'] = df['valor'].apply(clasificar_alerta)

# 7. Eliminar duplicados
df = df.drop_duplicates()

# 8. Ordenar por tiempo
df = df.sort_values(by='timestamp')

# ── VALIDACIÓN ──────────────────────────────────────────

print("\nResumen de calidad:")
print(df.describe(include='all'))

print("\nValores nulos por columna:")
print(df_bronze.isnull().sum())

# ── REPORTE DE CALIDAD ──────────────────────────────────

filas_bronze = len(df_bronze)
filas_silver = len(df)

reporte_path = SILVER / "reporte_calidad.txt"

with open(reporte_path, "w") as f:
    f.write("REPORTE DE CALIDAD\n")
    f.write("=====================\n\n")
    f.write(f"Filas en Bronze: {filas_bronze}\n")
    f.write(f"Filas en Silver: {filas_silver}\n\n")
    f.write("Valores nulos por columna:\n")
    f.write(str(df_bronze.isnull().sum()))

print(f"\nReporte de calidad guardado en: {reporte_path}")

# ── GUARDAR PARQUET ─────────────────────────────────────

silver_path = SILVER / 'lecturas_sensores_silver.parquet'
df.to_parquet(silver_path, index=False)

print(f"\nSilver guardado en: {silver_path}")