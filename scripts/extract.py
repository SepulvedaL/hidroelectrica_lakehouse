import pandas as pd
from astrapy import DataAPIClient
from pathlib import Path
from datetime import datetime
from dotenv import load_dotenv
import os

load_dotenv()

# ── CONFIG ───────────────────────────────────────────────
API_ENDPOINT = os.getenv("API_ENDPOINT")
API_TOKEN = os.getenv("API_TOKEN")


BRONZE = Path('lakehouse/bronze')
BRONZE.mkdir(parents=True, exist_ok=True)

# ── CONEXIÓN ─────────────────────────────────────────────
client = DataAPIClient()
db = client.get_database(API_ENDPOINT, token=API_TOKEN)

# nombre de la colección (tabla en Astra)
collection = db.get_collection("lecturas_sensores")

# ── EXTRACCIÓN ───────────────────────────────────────────
print("Extrayendo datos desde Astra (Data API)...")

docs = list(collection.find({}, limit=1000))

df = pd.DataFrame(docs)

# ── Metadata ─────────────────────────────────────────────
df['_extraido_en'] = datetime.now()
df['_fuente'] = 'astra_api'

# ── Guardar ──────────────────────────────────────────────
fecha = datetime.now().strftime('%Y%m%d_%H%M')
ruta = BRONZE / f'lecturas_sensores_{fecha}.parquet' 

df.to_parquet(ruta, index=False)

print(f"{len(df)} registros guardados en {ruta}")
print("Bronze completo.")