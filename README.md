# Hidroelectrica-LakeHouse

# Diseño Dimensional
## 1. ¿Cuál es el proceso de negocio que vamos a analizar?

El proceso de negocio que analizamos es el monitoreo continuo de sensores industriales en una central hidroeléctrica. Este proceso es crítico para garantizar la operación segura y eficiente de las turbinas, ya que una falla no detectada a tiempo puede provocar paradas no planificadas, daños en los equipos y pérdidas económicas considerables.
Los sensores registran de forma continua variables como temperatura, presión y caudal. 
El flujo del proceso inicia con la captura de datos en los sensores, continúa con el procesamiento en tiempo real para evaluación de umbrales, generación de alertas y finaliza con el almacenamiento histórico que soporta análisis de tendencias y modelos predictivos.
Dado el alto volumen de sensores activos (~10.000) y la frecuencia de muestreo, el sistema genera aproximadamente 85.000 eventos por segundo, lo que posiciona este caso como un escenario de Big Data de alta velocidad.

## 2. ¿Cuál es la granularidad?

La granularidad del modelo se define como una fila por cada lectura individual de sensor en un instante de tiempo específico, representando el nivel más fino de detalle posible.
Cada registro es un evento atómico que contiene: sensor_id, timestamp, tipo_sensor y valor. La combinación de sensor_id + timestamp actúa como identificador único de cada evento.
Cada sensor genera lecturas con una frecuencia aproximada de una por segundo, lo que con ~10.000 sensores activos produce cerca de 85.000 eventos por segundo, equivalente a ~7.3 mil millones de registros diarios y ~134 TB anuales.
Se eligió esta granularidad, ya que el sistema requiere detectar anomalías en tiempo real. Agregar los datos desde la captura (por minuto o por hora) haría imposible identificar momentos críticos que ocurren en fracciones de segundo. Las agregaciones por hora, día o turbina se realizan en una capa posterior, en ClickHouse, sin sacrificar el detalle original que se tiene en Cassandra.

## 3. ¿Cuáles son las dimensiones?

Para nuestro modelo definimos las siguientes dimensiones principales:
DIM_TIEMPO
Incluye atributos como tiempo_id, fecha, año, mes, día, hora, minuto, día de la semana y un indicador de fin de semana o festivo. Es una dimensión estática que no cambia una vez creada. Permite realizar análisis temporales con distintos niveles de agregación.
DIM_SENSOR
Contiene sensor_id (surrogate key), tipo de sensor (temperatura, presión, caudal), unidad de medida, ubicación y la turbina asociada. Al ser una dimensión que puede cambiar en el tiempo (reubicación o reasignación del sensor), se clasifica como Slowly Changing Dimension (SCD) Tipo 2, lo que permite conservar el historial completo de cada sensor sin perder trazabilidad en las lecturas históricas.
DIM_TURBINA
Describe las turbinas con atributos como turbina_id, nombre, capacidad instalada y estado operativo (activa, en mantenimiento, fuera de servicio). Puede tratarse como SCD Tipo 1 si solo interesa el estado actual, o SCD Tipo 2 si se requiere rastrear el historial de cambios de estado.
DIM_ALERTA (dimensión sugerida)
Clasificaría los niveles de alerta del sistema: BAJA, MEDIA, ALTA y CRÍTICA, junto con la descripción del umbral y la acción recomendada. Permitiría analizar la frecuencia y distribución de alertas por sensor, turbina o período de tiempo.

## 4. ¿Cuáles son las métricas (hechos)?

Las métricas principales del modelo se almacenan en la tabla FACT_LECTURAS_SENSORES y se clasifican de la siguiente manera:

Aditivas:

cantidad_alertas: número de alertas generadas en un período. Puede sumarse a través de todas las dimensiones (por turbina, por día, por tipo de sensor).
duracion_anomalia: tiempo en segundos que un sensor permaneció fuera del umbral. Es sumable y permite calcular el tiempo total de condiciones críticas.
desviacion_umbral: diferencia entre el valor medido y el umbral configurado, útil para medir la magnitud de una anomalía.

Semi-aditivas:

valor_lectura: el valor registrado por el sensor (temperatura, presión, caudal). Puede agregarse mediante promedio o máximo a través de la dimensión tiempo, pero no tiene sentido sumarlo entre sensores de distinto tipo. Su agregación válida depende del tipo de variable física.

No aditivas:

nivel_alerta: clasificación categórica (BAJA, MEDIA, ALTA, CRÍTICA). No puede sumarse; su análisis se realiza mediante conteos, distribuciones o clasificaciones.

Esta clasificación permite definir correctamente las operaciones de agregación aplicables en dashboards y reportes analíticos, evitando métricas sin sentido físico u operativo.

## 5. Estrategia SCD para al menos una dimensión

Implementamos SCD Tipo 2 en la dimensión DIM_SENSOR, ya que los sensores pueden cambiar atributos relevantes como su ubicación física o la turbina a la que están asignados a lo largo del tiempo.
Mecanismo de implementación:
Cuando un sensor cambia, no se actualiza el registro existente. En su lugar, se cierra el registro anterior (asignando una fecha_fin) y se crea un nuevo registro con los datos actualizados. Los campos técnicos que hacen posible este mecanismo son:

sensor_sk: Surrogate Key única por versión del registro
sensor_id: Clave de negocio original (se repite entre versiones)
fecha_inicio / fecha_fin: Rango de validez del registro
es_activo: Indica si el registro corresponde al estado actual

¿Por qué no SCD Tipo 1?
Se descartó la sobreescritura porque eliminaría el historial de ubicaciones, imposibilitando analizar el comportamiento del sensor en contextos anteriores, lo cual es crítico y no es conveniente en un sistema de monitoreo a gran escala.


# Descripción General

Este proyecto implementa una arquitectura Lakehouse para el análisis de datos provenientes de sensores de una hidroeléctrica.

La solución integra:

- Cassandra Astra DB como fuente operacional.
- Arquitectura Medallion (Bronze, Silver, Gold).
- DuckDB como motor OLAP.
- Parquet como formato columnar.
- Python para orquestación y transformación.

El objetivo principal fue comparar el comportamiento de Cassandra frente a DuckDB en consultas analíticas y demostrar cómo un Lakehouse mejora el rendimiento para escenarios OLAP.

---

# Arquitectura del Proyecto

```text
┌────────────────────┐
│  Cassandra Astra   │
│  (Datos Sensores)  │
└─────────┬──────────┘
          │
          ▼
┌────────────────────┐
│      Bronze        │
│ Extracción Raw     │
│ Archivos Parquet   │
└─────────┬──────────┘
          │
          ▼
┌────────────────────┐
│      Silver        │
│ Limpieza Calidad   │
│ Normalización      │
└─────────┬──────────┘
          │
          ▼
┌────────────────────┐
│       Gold         │
│ Modelo Estrella    │
│ Hechos + Dim       │
└─────────┬──────────┘
          │
          ▼
┌────────────────────┐
│      DuckDB        │
│ Consultas OLAP     │
│ Dashboard          │
└────────────────────┘
```

---

# Modelo de Datos

## Tabla Sensor

Representa el ciclo de vida de los sensores utilizando Slowly Changing Dimension (SCD).

| Campo | Tipo | Descripción |
|---|---|---|
| id | INT | Identificador del sensor |
| fecha_inicio | TIMESTAMP | Fecha inicio operación |
| fecha_final | TIMESTAMP | Fecha fin operación |
| sensor_scd | INT | Sensor reemplazo |

---

## Tabla Lecturas Sensores

Tabla operacional que almacena las lecturas generadas por cada sensor.

| Campo | Tipo |
|---|---|
| sensor_id | INT |
| timestamp | TIMESTAMP |
| tipo_sensor | TEXT |
| valor | DOUBLE |
| nivel_alerta | TEXT |

---

# Tecnologías Utilizadas

| Tecnología | Uso |
|---|---|
| Cassandra Astra DB | Base operacional NoSQL |
| DuckDB | Motor analítico OLAP |
| Python | ETL y automatización |
| Pandas | Transformación de datos |
| Parquet | Formato columnar |
| VSCode | Desarrollo |

---

# Estructura del Proyecto

```text
hidroelectrica_lakehouse/
│
├── lakehouse/
│   ├── bronze/
│   ├── silver/
│   └── gold/
│
├── scripts/
│   ├── bronze.py
│   ├── silver.py
│   ├── gold.py
│   ├── queries_gold.py
│   ├── queries_cassandra.py
│   └── main.py
│
├── dashboards/
├── README.md
└── requirements.txt
```

---

# Pipeline Medallion

## Bronze

En esta etapa se realiza:

- Extracción desde Astra DB.
- Almacenamiento raw.
- Conversión a Parquet.
- Preservación de datos sucios.

### Características

- No se eliminan errores.
- Se preservan nulos.
- Se conserva la trazabilidad.

---

## Silver

En esta etapa se realiza:

- Limpieza de nulos.
- Validación de rangos.
- Normalización de alertas.
- Creación de reporte de calidad.

### Validaciones

| Tipo Sensor | Rango Válido |
|---|---|
| temperatura | 50 - 100 |
| presion | 20 - 80 |
| vibracion | 1 - 15 |
| nivel_agua | 10 - 35 |

### Salidas

- `lecturas_sensores_silver.parquet`
- `reporte_calidad.txt`

---

## Gold

En esta etapa se construye:

- Modelo estrella.
- Tabla de hechos.
- Dimensiones.
- Consultas OLAP.

### Tablas Generadas

| Tabla |
|---|
| fact_lecturas |
| dim_sensor |
| dim_tiempo |

---

# Generación Masiva de Datos

Se implementó un generador masivo de datos capaz de producir:

- 600.000 registros.
- Datos limpios.
- Datos nulos.
- Datos fuera de rango.
- Sensores SCD.
- Reemplazos históricos.

### Características

- Distribución temporal entre 2025 y 2026.
- Inserción masiva en Astra DB.
- Simulación realista de sensores.
- Alertas críticas y advertencias.

---

# Comparación Cassandra vs DuckDB

## Resultados Cassandra

| Consulta | Tipo Consulta | Tiempo (s) | Descripción |
|---|---|---|---|
| Promedio por sensor | Agregación | 0.001 | Requiere procesamiento en memoria |
| Lecturas por hora | Agregación temporal | 0.002 | Transformación fuera de Cassandra |
| Conteo por alerta | Agregación simple | 0.0015 | No soportado directamente |
| Promedio por tipo | Agregación categórica | 0.001 | Procesamiento en cliente |
| Eventos críticos | Filtro | 0.0 | Consulta limitada |

---

## Resultados DuckDB

| Consulta | Tipo Consulta | Tiempo (s) | Descripción |
|---|---|---|---|
| Promedio por sensor | Agregación | 0.004025 | Agregación OLAP nativa |
| Lecturas por hora | Agregación temporal | 0.006005 | Optimización columnar |
| Conteo por alerta | Agregación simple | 0.002002 | Lectura directa Parquet |
| Promedio por tipo | Agregación categórica | 0.002537 | JOIN + GROUP BY |
| Eventos críticos | Filtro | 0.028709 | Filtro analítico |

---

# EXPLAIN ANALYZE en DuckDB

Se realizaron análisis detallados de planes de ejecución para identificar:

- Hash Joins.
- Group By.
- ORDER BY.
- Data Skipping.
- Lecturas Parquet.
- Optimización columnar.

---

## Consulta Q1

Promedio mensual de lecturas.

### Operadores Detectados

- HASH_JOIN
- PERFECT_HASH_GROUP_BY
- ORDER_BY
- READ_PARQUET

### Resultado

DuckDB ejecutó la agregación directamente sobre archivos Parquet sin necesidad de importar los datos.

---

## Consulta Q2

Alertas críticas por sensor.

### Problema Detectado

Existía un CAST implícito entre `sensor_sk`.

### Solución

Se homologaron tipos `int32`.

### Resultado

Eliminación de conversiones innecesarias.

---

## Consulta Q3

Resumen diario de sensores.

### Características

- Doble JOIN.
- Agregaciones.
- MAX/MIN.
- Filtros temporales.

### Resultado

Excelente rendimiento OLAP incluso con múltiples agregaciones.

---

# Intervenciones Aplicadas

## Intervención I-3

### Objetivo

Ordenar `fact_lecturas` por `tiempo_sk`.

### Beneficio

Activación de Data Skipping.

### Resultado

Reducción de bloques leídos.

---

## Intervención I-4

### Objetivo

Corregir tipos entre dimensiones y hechos.

### Beneficio

Eliminar CAST implícitos.

### Resultado

Mejoras en HASH_JOIN.

---

# Resultados Finales

| Query | Antes | Después | Mejora |
|---|---|---|---|
| Q1 | 19.88 ms | 3.32 ms | 5.98x |
| Q2 | 13.59 ms | 2.20 ms | 6.17x |
| Q3 | 21.92 ms | 3.87 ms | 5.66x |

---

# Dashboard Analítico

Se construyó un dashboard básico utilizando DuckDB y consultas analíticas.

### Visualizaciones

- Promedio por sensor.
- Alertas críticas.
- Tendencia temporal.
- Distribución de sensores.

---

# Conclusiones

- Cassandra funciona correctamente para cargas operacionales y almacenamiento distribuido.
- DuckDB ofrece un rendimiento superior para cargas analíticas OLAP.
- El formato Parquet mejora significativamente la eficiencia.
- La arquitectura Medallion facilita la calidad y gobernanza.
- Las optimizaciones físicas impactan directamente el rendimiento.
- DuckDB demostró ser ideal para análisis locales de alto rendimiento.

---

# Ejecución del Proyecto

## Instalar dependencias

```bash
pip install -r requirements.txt
```

## Ejecutar generador de datos

```bash
python data_cassandra.py
```

## Ejecutar pipeline completo

```bash
python main.py
```

---

### Para revisar los diagnosticos de consultas debemos ejecutar de forma indepediente cada archivo, dado que no esta incluido en el pipeline

```bash
python diagnostico_baseline.py
python intervenciones.py
```

### Integrantes

*Luis Alberto Sepúlveda*

*Juan David Díaz Montoya*