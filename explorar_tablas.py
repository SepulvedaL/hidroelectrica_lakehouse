import pandas as pd 
tablas = ['dim_sensor', 'dim_tiempo', 'fact_lecturas'] 
ruta = 'lakehouse/gold/'  
# ajusta esta ruta a donde tengas tus Parquet for tabla in tablas:     
for tabla in tablas:
    df = pd.read_parquet(f'{ruta}{tabla}.parquet')     
    print(f"\n{'='*50}")     
    print(f"TABLA: {tabla}")     
    print(f"Filas: {len(df):,}")     
    print(f"Columnas: {list(df.columns)}")     
    print(f"Tipos:\n{df.dtypes}")