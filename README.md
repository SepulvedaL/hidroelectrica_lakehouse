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


**Descripción del Proyecto:**

Este proyecto implementa una arquitectura tipo **Lakehouse** para el procesamiento y análisis de datos provenientes de sensores de una central hidroeléctrica.

La solución integra:

- Cassandra Astra como almacenamiento operacional (OLTP)
- DuckDB como motor analítico (OLAP)
- Archivos Parquet como formato intermedio
- Arquitectura Medallion teniendo en cuenta las capas que lo componen:
    - Bronze
    - Silver
    - Gold

El sistema permite:

- ingestión de datos de sensores
- limpieza y validación
- construcción de modelo dimensional
- consultas analíticas
- comparación de rendimiento entre Cassandra y DuckDB

## Arquitectura del Proyecto

Cassandra Astra  
│  
▼  
Bronze (datos crudos Parquet)  
│  
▼  
Silver (datos limpios y validados)  
│  
▼  
Gold (modelo estrella)  
│  
▼  
Consultas Analíticas DuckDB

**Requisitos**

|     |     |
| --- | --- |
| **Tecnología** | **Uso** |
| Python | Desarrollo del pipeline |
| Cassandra Astra | Base de Datos Operacional |
| DuckDB | Motor analítico |
| Pandas | Transformación de datos |
| Parquet | Almacenamiento columnar |
| Astrapy | Conexión con Astra |
| DuckDB SQL | Consultas analíticas |

**Ejecutar el pipeline completo**

**Clonar repositorio**

git clone https://github.com/SepulvedaL/hidroelectrica_lakehouse.git
<<<<<<< HEAD

=======
>>>>>>> 7ae52620a3abd773efa0512f0553abb415cfc371
cd \[repositorio\]

**Crear entorno virtual**

python -m venv .venv  
.venv\\Scripts\\activate

**Instalar dependencias**

pip install -r requirements.txt

**Ejecutar pipeline Bronze**

Ejecutar pipeline Bronze

python scripts/extract.py

**Ejecutar pipeline Silver**

Ejecutar pipeline Silver

python scripts/transform_silver.py

**Ejecutar pipeline Gold**

python scripts/transform_gold.py

**Ejecutar consultas analíticas**

python scripts/queries_gold.py

**Comparación Cassandra vs DuckDB**

python scripts/queries_cassandra.py

### Integrantes

*Luis Alberto Sepúlveda*

*Juan David Díaz Montoya*