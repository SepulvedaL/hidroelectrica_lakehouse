import subprocess
import sys
from pathlib import Path
from datetime import datetime

# ── CONFIGURACIÓN ───────────────────────────────────────
SCRIPTS_DIR = Path("scripts")

# Orden del pipeline
PIPELINE = [
    "extract.py",
    "transform_silver.py",
    "transform_gold.py",
    "queries_gold.py",
    "benchmark.py"
]

# ── FUNCIONES ───────────────────────────────────────────
def ejecutar_script(script_name):
    script_path = SCRIPTS_DIR / script_name

    if not script_path.exists():
        raise FileNotFoundError(f"No existe el script: {script_path}")

    print("\n" + "=" * 60)
    print(f"Ejecutando: {script_name}")
    print("=" * 60)

    inicio = datetime.now()

    resultado = subprocess.run(
        [sys.executable, str(script_path)],
        capture_output=True,
        text=True
    )

    fin = datetime.now()
    duracion = (fin - inicio).total_seconds()

    # Mostrar salida estándar
    if resultado.stdout:
        print(resultado.stdout)

    # Mostrar errores si existen
    if resultado.stderr:
        print("ERRORES / WARNINGS:")
        print(resultado.stderr)

    # Validar ejecución
    if resultado.returncode != 0:
        raise Exception(f"Error ejecutando {script_name}")

    print(f"{script_name} finalizado en {duracion:.2f} segundos")


# ── MAIN ────────────────────────────────────────────────
if __name__ == "__main__":

    print("\nINICIANDO PIPELINE LAKEHOUSE")
    print("=" * 60)

    inicio_pipeline = datetime.now()

    try:
        for script in PIPELINE:
            ejecutar_script(script)

        fin_pipeline = datetime.now()
        duracion_total = (fin_pipeline - inicio_pipeline).total_seconds()

        print("\n" + "=" * 60)
        print("PIPELINE EJECUTADO CORRECTAMENTE")
        print("=" * 60)
        print(f"Tiempo total: {duracion_total:.2f} segundos")

    except Exception as e:
        print("\nERROR EN EL PIPELINE")
        print(str(e))