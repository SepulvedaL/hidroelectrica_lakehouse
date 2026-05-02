# Hidroelectrica-LakeHouse

# Diseño Dimensional
## 1. ¿Cuál es el proceso de negocio que vamos a analizar?

En nuestro proyecto decidimos enfocarnos en el proceso de monitoreo de sensores dentro de una central hidroeléctrica. Específicamente, analizamos el comportamiento de variables como temperatura, presión y caudal, registradas por distintos sensores instalados en las turbinas.
El objetivo de este análisis es entender cómo se comportan estas variables a lo largo del tiempo, identificar patrones operativos y detectar posibles condiciones anómalas que puedan generar alertas o afectar el funcionamiento de la central.

## 2. ¿Cuál es la granularidad?

Definimos que la granularidad del modelo será una fila por cada lectura de sensor en un instante de tiempo específico.
Esto significa que cada registro representa un evento atómico: una medición individual capturada por un sensor en un momento determinado. Esta decisión nos permite mantener el máximo nivel de detalle posible y posteriormente realizar agregaciones según sea necesario (por hora, día o turbina).

## 3. ¿Cuáles son las dimensiones?

Para nuestro modelo definimos las siguientes dimensiones principales:

DIM_TIEMPO
Incluye atributos como fecha, año, mes, día, hora, día de la semana y si corresponde a fin de semana. Esta dimensión no cambia en el tiempo.

DIM_SENSOR
Contiene información del sensor, como su identificador, tipo de sensor (temperatura, presión, caudal), unidad de medida, ubicación y la turbina a la que está asociado. Esta dimensión puede cambiar en el tiempo, por ejemplo, si un sensor es reubicado o reasignado.

DIM_TURBINA
Describe las turbinas de la central, incluyendo su identificador, nombre, capacidad y estado operativo (activa, en mantenimiento, etc.). Esta dimensión permite contextualizar las lecturas dentro del sistema físico de la hidroeléctrica.

## 4. ¿Cuáles son las métricas (hechos)?

Las métricas principales de nuestro modelo corresponden a los valores registrados por los sensores.

Clasificamos estas métricas de la siguiente manera:

Aditiva:
El valor del sensor, ya que puede ser agregado a través de dimensiones como tiempo o sensor (por ejemplo, promedios o sumas según el caso de análisis).

No aditiva:
El nivel de alerta asociado a una lectura, ya que no tiene sentido sumarlo y su análisis se realiza mediante conteos o clasificaciones.

Estas métricas permiten analizar tanto el comportamiento operativo como posibles anomalías dentro del sistema.

## 5. Estrategia SCD para al menos una dimensión

Decidimos implementar una estrategia de Slowly Changing Dimension (SCD) Tipo 2 en la dimensión de sensores.
Esto significa que cuando un sensor cambia algún atributo relevante, como su ubicación o la turbina a la que pertenece, no se actualiza el registro existente, sino que se crea uno nuevo. De esta forma, se conserva el historial completo de cambios.
Esta estrategia nos permite analizar el comportamiento de un mismo sensor en diferentes contextos a lo largo del tiempo, lo cual es especialmente útil en escenarios donde la infraestructura puede cambiar o ser reconfigurada.