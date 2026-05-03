import pandas as pd
from pathlib import Path

# ── RUTAS ───────────────────────────────────────────────
BRONZE = Path('lakehouse/bronze')
SILVER = Path('lakehouse/silver')

SILVER.mkdir(parents=True, exist_ok=True)

# ── CARGA ───────────────────────────────────────────────
archivos = list(BRONZE.glob('lecturas_sensores_*.parquet'))

if not archivos:
    raise Exception("No hay archivos en Bronze")

df = pd.concat([pd.read_parquet(f) for f in archivos], ignore_index=True)

print(f"Filas en Bronze: {len(df)}")

# ── LIMPIEZA ────────────────────────────────────────────

# 1. Eliminar columnas innecesarias (_id de Astra)
if '_id' in df.columns:
    df.drop(columns=['_id'], inplace=True)

# 2. Convertir timestamp
df['timestamp'] = pd.to_datetime(df['timestamp'], errors='coerce')

# 3. Eliminar filas con nulos críticos
df = df.dropna(subset=['sensor_id', 'timestamp', 'valor'])

# 4. Normalizar texto
df['tipo_sensor'] = df['tipo_sensor'].str.lower().str.strip()
df['nivel_alerta'] = df['nivel_alerta'].str.upper().str.strip()

# 5. Eliminar duplicados
df = df.drop_duplicates()

# ── VALIDACIÓN ──────────────────────────────────────────

print("\nResumen de calidad:")
print(df.describe(include='all'))

print("\nValores nulos:")
print(df.isnull().sum())

# ── GUARDAR ─────────────────────────────────────────────
ruta = SILVER / 'lecturas_sensores_silver.parquet'
df.to_parquet(ruta, index=False)

print(f"\nSilver guardado en: {ruta}")

with open(SILVER / "reporte_calidad.txt", "w") as f:
    f.write(f"Filas Bronze: {len(archivos)}\n")
    f.write(f"Filas Silver: {len(df)}\n")
    f.write("\nValores nulos:\n")
    f.write(str(df.isnull().sum()))