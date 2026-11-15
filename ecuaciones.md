# Metodología propuesta para comparar el Tacaná con regiones de la Luna y Marte

La verificación numérica y los límites observados se documentan por separado en [Verificación de cálculos y alcance de los resultados](recursos/comparacion_tacana/auditoria_metodologica.md). Esta propuesta metodológica no constituye una certificación de los resultados ni una validación por NASA.

Se propone investigar qué regiones de la Luna y Marte presentan mayor semejanza con el relieve del volcán Tacaná. El inventario abarcará todos los accidentes con nombre incluidos en los archivos oficiales IAU/USGS de la Luna y Marte. Connecting Ridge, el borde de Shackleton y Cerberus Tholi constituirán el conjunto local inicial con datos detallados compatibles para la comparación con Tacaná. La comparación se realizará mediante datos de elevación y medidas de pendiente y relieve local, utilizando Python para su procesamiento.

La pregunta central será: ¿cuál de las regiones consideradas presenta mayor cercanía al Tacaná cuando la pendiente y el relieve se evalúan conjuntamente a una escala espacial común? Se analizarán las diferencias entre medias y, por separado, se construirá un índice descriptivo de similitud para ordenar las regiones. No se anticipará qué región ocupará el primer lugar ni qué porcentaje obtendrá.

Se aplicará ANOVA de Welch para contrastar las medias de los grupos y la prueba t de Welch para comparar cada región con Tacaná. La distancia de Wasserstein permitirá describir la separación entre las distribuciones. A partir de ella se propondrá un índice porcentual con el mismo peso para pendiente y relieve. Este índice será una definición metodológica del proyecto, no una probabilidad de igualdad ni una medida validada por NASA.

La temperatura superficial se estudiará por separado. Solo se planteará su incorporación al índice si se dispone de observaciones con correspondencia geográfica y física suficiente. La presentación de los resultados se organizará en tarjetas con una región por cuerpo, su puntuación y los intervalos que comparta con Tacaná.

## Datos y preparación del terreno

### Inventario de accidentes con nombre oficial

Se consultará el [Gazetteer of Planetary Nomenclature de IAU/USGS](https://planetarynames.wr.usgs.gov/GIS_Downloads). Se descargarán los archivos KMZ completos de Luna y Marte y se conservarán los originales, su fecha de descarga y sus huellas SHA-256. La autoridad de los nombres será IAU/USGS; los modelos globales de elevación procederán de NASA.

El inventario incluirá todos los tipos disponibles: cráteres, cráteres satélite identificados por letras, montañas, valles, llanuras y otros accidentes. No se eliminarán registros por su tamaño o por falta de mediciones detalladas. El alcance será el conjunto de nombres del catálogo oficial, no todos los puntos de la superficie ni todos los nombres informales o unidades geológicas sin nombre propio.

Se utilizará el identificador oficial de cada accidente. Si aparecen registros idénticos con el mismo identificador, se unificarán conservando los identificadores de las entradas originales; si sus atributos difieren, el procesamiento se detendrá para evitar una fusión incorrecta.

Cada registro conservará nombre, tipo, coordenadas planetocéntricas con longitud positiva al este, diámetro cuando exista, fecha y estado de aprobación, origen del nombre, atributos originales y enlace a su ficha oficial. El centro del catálogo se utilizará como punto de referencia, no como polígono de toda la región.

### Contexto de relieve global para todos los lugares

Se añadirá contexto de elevación LOLA a los registros lunares y de MOLA a los marcianos. La elevación se interpolará en la coordenada de referencia. Las longitudes se tratarán de forma periódica y las latitudes se limitarán a los centros válidos del raster, sin conectar artificialmente el polo norte con el sur.

Para obtener muestras alrededor del punto se utilizará un desplazamiento sobre una esfera. Dados la latitud $\varphi$, la longitud $\lambda$, el desplazamiento al este $e$, el desplazamiento al norte $n$ y el radio $R$:

$$
\delta=\frac{\sqrt{e^2+n^2}}{R},\qquad \beta=\operatorname{atan2}(e,n),
$$

$$
\varphi'=\arcsin(\sin\varphi\cos\delta+\cos\varphi\sin\delta\cos\beta),
$$

$$
\lambda'=\lambda+\operatorname{atan2}(\sin\beta\sin\delta\cos\varphi,\cos\delta-\sin\varphi\sin\varphi').
$$

Se usarán radios de 1 737 400 m para la Luna y 3 396 000 m para Marte. La aproximación esférica permitirá describir el contexto, sin sustituir una georreferenciación detallada del terreno marciano.

La pendiente global se calculará por diferencias centrales con desplazamientos de 10 km, y el relieve del entorno mediante P95 − P5 sobre 25 puntos de una cuadrícula local de 40 km de lado. Estas medidas no serán las mismas que la pendiente y el relieve de bloques locales de 1 km. Una ventana podrá exceder el tamaño del accidente; se indicará expresamente que describe el entorno del punto y no toda su superficie. También se marcarán los accidentes cuyo diámetro sea menor que el tamaño nominal de un píxel del DEM.

Cuando exista información térmica del sector que contiene el punto, se añadirá como contexto del sector, conservando su escala de 30° × 60°. No se atribuirá esa temperatura a una medición individual del accidente. Los casos sin cobertura mantendrán ese estado; no se reemplazarán por cero.

El inventario completo se comparará mediante el procedimiento global siguiente. Esta clasificación se mantendrá separada del análisis local de alta resolución y no reutilizará sus porcentajes.

### Comparación del catálogo completo a escala común

Se evaluará un entorno de 12 km de lado alrededor del punto oficial de cada accidente. Se conservarán todos los registros únicos, incluidos los pequeños; la ventana describirá el entorno del punto, no necesariamente la extensión completa del accidente. Se conservarán también los registros sin coordenadas o sin mediciones válidas, con motivo de exclusión y sin porcentaje inventado.

Se utilizarán LOLA LDEM de 16 píxeles por grado para la Luna, MOLA MEGDR de 32 píxeles por grado para Marte y Copernicus GLO-30 para Tacaná. Los productos planetarios tendrán separaciones latitudinales próximas a 1,9 km. Las coordenadas locales se obtendrán mediante las ecuaciones esféricas anteriores; para la referencia terrestre se adoptará un radio de 6 371 008,8 m y el centro 15,132° N, 92,109° O. La aproximación esférica y las diferencias entre sensores se reconocerán como limitaciones.

Se interpolarán las alturas bilinealmente sobre una malla computacional de 250 m, extendida hasta 11 km desde el centro en ambos ejes para cubrir el soporte del filtro. Esta interpolación no aportará resolución física de 250 m. Se aplicará un filtro gaussiano con desviación estándar $\sigma=h/2$ y truncamiento a $3\sigma$, donde $h$ será la separación de análisis. Se evaluarán $h=2\,000$ m como escala principal y $h=3\,000$ m como sensibilidad. El núcleo de 12 km contendrá, respectivamente, 7 × 7 y 5 × 5 alturas suavizadas. El soporte adicional evitará usar los bordes del filtro en el núcleo.

En cada posición interior se calcularán:

$$
g_x=\frac{z_{i,j+1}-z_{i,j-1}}{2h},\qquad
g_y=\frac{z_{i+1,j}-z_{i-1,j}}{2h},\qquad
\theta=\frac{180}{\pi}\arctan\sqrt{g_x^2+g_y^2}.
$$

El relieve se definirá como $R=P_{95}(Z_{3\times3})-P_5(Z_{3\times3})$, con percentiles de interpolación lineal sobre las nueve alturas vecinas. La extensión entre centros extremos del vecindario será $2h$: 4 km o 6 km. Se obtendrán 25 descriptores por variable a 2 km y nueve a 3 km. La clave técnica `mean_slope_deg` conservará su nombre por compatibilidad; en este procedimiento almacenará pendientes puntuales del terreno suavizado, cuyo promedio se mostrará en la interfaz, no medias de bloques de 1 km.

Se aplicará exactamente la misma preparación a Tacaná y a cada punto planetario. Para cada variable $j$ se calculará la distancia de Wasserstein $W_j$ entre los descriptores del punto y los de Tacaná, y la desviación estándar muestral $s_{T,j}$ de Tacaná. Se propondrá el índice:

$$
S_j=\frac{100}{1+W_j/s_{T,j}},\qquad
S=0.5S_{\theta}+0.5S_R.
$$

Se requerirán valores finitos, al menos tres descriptores y $s_{T,j}>0$. La escala de normalización será común a todos los candidatos de una misma variable y resolución. Se ordenará cada cuerpo por $S$ descendente a 2 km; los empates se resolverán por identificador oficial. El cálculo a 3 km se conservará por separado para estudiar sensibilidad y no se promediará con el principal. El primer resultado será el máximo de esta búsqueda, no una equivalencia física validada.

Las ventanas y los vecindarios se superpondrán; por ello, estos descriptores no se considerarán réplicas independientes y no se les aplicará ANOVA ni se informarán valores p. Los contrastes locales descritos en las secciones siguientes constituirán un estudio complementario con otra escala y otro conjunto de observaciones. El porcentaje global será un índice experimental del terreno, no un resultado de ANOVA ni una probabilidad de semejanza ambiental. Temperatura, oxígeno y elevación absoluta no se incorporarán al índice sin mediciones comparables y referencias físicas compatibles.

El algoritmo se implementará en `recursos/scripts/comparar_catalogo_completo.py`. Los archivos `similitud_catalogo_moon.json` y `similitud_catalogo_mars.json` conservarán todos los candidatos, descriptores, distancias, componentes, rangos compartidos y posiciones. `similitud_catalogo_resumen.json` contendrá los parámetros, huellas de los insumos, muestras de Tacaná, conteos, limitaciones y selección por cuerpo. La interfaz leerá esta selección y el catálogo mostrará todos los porcentajes en orden descendente. Los resultados locales anteriores se conservarán en archivos separados.

### Descriptores complementarios del terreno

Se añadirán tres comparaciones descriptivas a todas las regiones del catálogo, con la misma malla, suavizado y ventanas de la comparación global. Se conservarán las 25 muestras interiores a 2 km y las nueve a 3 km, tanto para Tacaná como para cada región planetaria.

La altura relativa se definirá respecto de la mediana de todas las alturas de la ventana de 12 km de cada lugar:

$$
H_i=z_i-\operatorname{mediana}(Z_{12\,km}).
$$

Esta definición del proyecto permitirá comparar la distribución vertical del terreno respecto de su propio entorno. No representará altitud sobre el nivel del mar ni sobre el radio de referencia planetario. Los valores negativos indicarán posiciones inferiores a la mediana de la ventana.

Se calcularán la posición topográfica y la rugosidad con las definiciones documentadas en [GDAL: TPI y TRI](https://gdal.org/en/stable/programs/gdaldem.html). Para la altura central $z_i$ y sus ocho vecinos $z_k$, se utilizarán:

$$
TPI_i=z_i-\frac{1}{8}\sum_{k=1}^{8}z_k,
\qquad
TRI_i=\sqrt{\sum_{k=1}^{8}(z_k-z_i)^2}.
$$

El TPI conservará su signo: positivo por encima de la media vecina y negativo por debajo. El TRI seguirá la variante Riley, sin dividir la suma entre ocho; por tanto, no será una desviación estándar ni un RMS. Ambos se expresarán en metros. La rugosidad corresponderá a la escala kilométrica del modelo, no a la textura de rocas o suelos.

Para cada descriptor se utilizará $S_j=100/(1+W_j/s_{T,j})$, con su propia desviación estándar muestral de Tacaná y la distancia de Wasserstein entre sus distribuciones. Se conservarán las muestras, distancias, mínimos, máximos y rangos compartidos; la interfaz mostrará las tablas numéricas y los porcentajes individuales, sin sustituirlos por explicaciones narrativas.

Estos tres descriptores se mostrarán como comparaciones adicionales con peso cero en el índice general. La selección principal continuará utilizando pendiente y relieve con pesos de 0,5. Esta separación evitará aumentar arbitrariamente la puntuación por contar repetidamente características correlacionadas del mismo modelo de elevación. Los porcentajes complementarios no se interpretarán como pruebas independientes ni como condiciones ambientales equivalentes. Las tablas adicionales se ordenarán por su puntuación dentro de cada región; no se ocultarán los resultados con poca semejanza.

### Comparación visual de superficies en tres dimensiones

Se exportarán los terrenos de Tacaná y de la región seleccionada de cada cuerpo mediante `recursos/scripts/exportar_terrenos_3d.py`. Se conservará la misma malla de 7 × 7 alturas suavizadas y separadas 2 km que se utilizará en el análisis principal. El exportador comprobará que sus diferencias centrales reproducen las muestras de pendiente almacenadas. Se guardarán los centros, las alturas, la mediana, las huellas de los insumos y los resultados en `recursos/comparador_3d/moon.json` y `mars.json`.

Para presentar las superficies se interpolará bilinealmente la malla a 49 × 49 vértices. Esa operación mejorará la continuidad visual, sin añadir detalle observado ni cambiar los datos del análisis. Las filas se interpretarán de sur a norte y las columnas de oeste a este. A cada superficie se le restará su propia mediana para comparar formas sin mezclar referencias verticales planetarias.

La página `recursos/comparador_3d/index.html` mostrará ambas superficies con idénticas unidades horizontales y verticales, sin exageración de alturas, y con giro, inclinación y zoom sincronizados. Se utilizarán el mismo intervalo de colores, iluminación y orientación; la flecha norte y la barra de 2 km conservarán su relación con la geometría. Los colores representarán alturas relativas, no imágenes del suelo ni su composición. La interpolación y el sombreado no sustituirán la resolución física de los modelos originales.

El porcentaje conservará la fórmula del índice descriptivo y se mostrará con seis decimales de representación. Esos decimales no se interpretarán como precisión física ni como equivalencia exacta. El visor no recalculará la similitud al girar o acercar las superficies. Las características complementarias mantendrán peso cero en el total y podrán consultarse junto con el resultado de sensibilidad a 3 km.

### Comparación de imágenes orbitales y satelitales

Se ofrecerá una página independiente con una división deslizante entre imágenes de Tacaná y de la región planetaria seleccionada. Se usarán ventanas geográficas de aproximadamente 12 km de lado, centradas en las mismas coordenadas del análisis y orientadas con el norte arriba. La longitud se ajustará con el coseno de la latitud central para aproximar una extensión horizontal común. No se girarán, deformarán ni desplazarán las imágenes para forzar coincidencias entre accidentes distintos.

Para Tacaná se consultará [Esri World Imagery](https://services.arcgisonline.com/ArcGIS/rest/services/World_Imagery/MapServer), con atribución a sus proveedores. Para la Luna se utilizará el [mosaico LROC WAC de 100 m/píxel](https://astrogeology.usgs.gov/search/map/moon_lro_lroc_wac_global_morphology_mosaic_100m), servido por Lunaserv. Para Marte se utilizará el [mosaico CTX V01 de Caltech Murray Lab](https://murray-lab.caltech.edu/CTX/), producido con observaciones NASA/JPL/MSSS y distribuido por Esri. Las teselas CTX se ensamblarán según sus coordenadas; el recorte se remuestreará bilinealmente a 1024 × 1024 píxeles. Ese tamaño de presentación no se interpretará como resolución nativa: WAC conservará su límite de 100 m/píxel y CTX se consultará a unos 10 m/píxel aunque su mosaico original tenga 5 m/píxel.

El archivo `recursos/comparador_imagenes/fuentes.json` conservará las coordenadas centrales, límites de los recortes, fuentes, solicitudes y huellas de los archivos. Las fechas individuales de adquisición de los mosaicos permanecerán sin determinar. Se reconocerán las diferencias de iluminación, vegetación, sombras, sensores y resolución. La división deslizante facilitará una inspección visual; no representará una correspondencia espacial entre los dos lugares ni medirá similitud fotográfica. El índice que acompañe las imágenes seguirá procediendo de los modelos de elevación, no de sus colores o texturas.

Los archivos se obtendrán con `python recursos/scripts/descargar_imagenes_comparador.py`. Si cambia la región seleccionada al recalcular el catálogo, se volverá a ejecutar ese comando. La página comprobará que los identificadores de las imágenes coinciden con la selección vigente antes de mostrarlas.

### Integración de meteorología, atmósfera y radiación

Se integrarán los registros ambientales existentes con una consulta de [NASA POWER Daily API](https://power.larc.nasa.gov/docs/services/api/temporal/daily/) para las coordenadas de Tacaná, del 24 al 31 de octubre de 2011, en UTC. La elección del periodo coincidirá con el compuesto terrestre MODIS y contendrá el día de observaciones MCS utilizado en la comparación térmica. Ocho días constituirán un periodo meteorológico, no una climatología ni una muestra suficiente para describir todas las estaciones.

Se conservarán `T2M`, `T2M_MIN`, `T2M_MAX`, `RH2M`, `PS`, `WS2M`, `PRECTOTCORR`, `ALLSKY_SFC_SW_DWN` y `TOA_SW_DWN`, con las unidades incluidas en la respuesta de POWER. La temperatura del aire a 2 m se mantendrá separada de la temperatura superficial MODIS. Se excluirá el valor de relleno declarado por la API y los valores no finitos, conservando fechas y recuentos válidos. Se calcularán mínimo, máximo, media y desviación estándar muestral de cada variable, sin fabricar réplicas planetarias.

El producto POWER representará una celda de su modelo: la respuesta incluirá una elevación de 1 508,37 m, frente a los 4 064 m de la cima de Tacaná. No se corregirán implícitamente temperatura ni presión para convertir esos valores en observaciones de la cima. Las diferentes resoluciones de los productos meteorológicos y radiativos se conservarán como limitación de representatividad.

Para la Luna y Marte se recuperarán los grupos existentes de temperatura superficial y las comparaciones exploratorias de Welch. Para la región elegida se identificará el sector de 30° × 60° que contiene su centro. Una medición del sector no se atribuirá al accidente de 12 km. Si no hay muestras del sector en la ventana horaria, se mostrará ausencia de cobertura, no una temperatura cero ni la media global del cuerpo.

Las recuperaciones de presión MCS se agruparán por sector y fecha, manteniendo observaciones, incertidumbres y horas originales. Para presentarlas junto a POWER se convertirá $P_{kPa}=P_{Pa}/1000$. La tabla terrestre usará únicamente el día coincidente cuando exista; no se extenderán los datos de 2011 a fechas de 2025. Esta presentación será descriptiva porque un promedio diario de una celda terrestre y perfiles dispersos de un sector planetario no son réplicas equivalentes. La temperatura atmosférica MCS a aproximadamente 106 Pa se mostrará por separado y no se comparará con aire terrestre a 2 m.

Se distinguirán dos magnitudes de radiación: energía solar diaria sobre una superficie horizontal, en kWh/m²/día según POWER, e irradiancia extraterrestre perpendicular a los rayos solares, en W/m², de las fichas [lunar](https://nssdc.gsfc.nasa.gov/planetary/factsheet/moonfact.html) y [marciana](https://nssdc.gsfc.nasa.gov/planetary/factsheet/marsfact.html) de NASA. Se conservarán como referencias 1 361 W/m² para Tierra y Luna y 586,2 W/m² para Marte. No se interpretarán como radiación recibida por una ladera específica, ni se convertirán en muestras regionales para ANOVA. El valor lunar no implicará exposición continua: la geometría, la noche y las sombras no se representan mediante esa constante.

Las referencias de composición atmosférica conservarán su procedencia: las fracciones de gases medidas por Curiosity/SAM en Gale no se atribuirán a Ophir Cavus ni a todos los sectores de Marte. No se inventará una fracción regional de oxígeno lunar. La radiación ionizante o dosis biológica no se confundirá con la energía solar de onda corta; no se dispondrá de una serie local comparable de dosis en estos insumos.

El script `recursos/scripts/integrar_ambiente.py` generará `recursos/comparacion_tacana/ambiente_integrado.json`, con registros diarios, resúmenes, grupos por sector y fecha, contrastes térmicos existentes, cobertura, referencias y huellas SHA-256 de los insumos. La interfaz ofrecerá tablas en `recursos/comparacion_tacana/ambiente.html`. Las variables ambientales no se sumarán al índice del relieve y no se definirá un porcentaje global ambiental mientras falten observaciones físicamente comparables. La incorporación de constantes o datos sin cobertura no modificará el orden de las regiones de relieve.

### Perfiles de condiciones para todos los lugares del catálogo

El análisis se ampliará a todos los accidentes catalogados, no solamente a los dos seleccionados por relieve. `recursos/scripts/catalogar_condiciones.py` vinculará cada coordenada con un perfil ambiental de sector y conservará por separado sus referencias planetarias. Se registrarán 23 condiciones: temperaturas superficiales diurna y nocturna, presión observada, temperatura del aire a 2 m y sus extremos diarios, humedad, viento, precipitación, energía solar diaria superficial y sobre la atmósfera, gravedad, irradiancia extraterrestre, duración del día solar, albedo de Bond, oxígeno, dióxido de carbono, presión atmosférica de referencia, dosis ionizante, radiación UV, opacidad del polvo, inercia térmica y agua local disponible. Las observaciones adicionales de temperatura, incluida la temperatura a 106 Pa, se conservarán en grupos propios de fecha y fase.

Cada condición indicará unidad, referencia terrestre, valor planetario, periodo, procedencia y alcance espacial. Se distinguirán observaciones de sector, referencias generales, ausencia de datos y magnitudes que no correspondan a una exosfera lunar. No se sustituirá un dato ausente por cero. Los estados de cobertura describirán los archivos disponibles, no la inexistencia de información en toda la literatura científica.

Cuando existan valores comparables dimensionalmente, se calculará una diferencia descriptiva $\Delta_j=\overline{x}_{P,j}-\overline{x}_{T,j}$ y el intervalo compartido entre rangos. Esos resultados no se interpretarán como igualdad física, validación estadística ni porcentaje de semejanza. Se evitarán cocientes de temperaturas Celsius. La presión observada se comparará en kPa con la celda POWER del mismo día, el 31 de octubre de 2011, sin utilizar el valor terrestre de 2011 para fechas marcianas de 2025.

Se utilizarán las fichas oficiales NASA de [Tierra](https://nssdc.gsfc.nasa.gov/planetary/factsheet/earthfact.html), [Luna](https://nssdc.gsfc.nasa.gov/planetary/factsheet/moonfact.html) y [Marte](https://nssdc.gsfc.nasa.gov/planetary/factsheet/marsfact.html) para las referencias generales. La duración del día solar lunar se derivará del periodo sinódico de 29,53 días multiplicado por 24, no de su rotación sideral. La presión nocturna lunar de referencia se convertirá de $3\times10^{-15}$ bar a $3\times10^{-13}$ kPa. El albedo de Bond será una propiedad del cuerpo, no una medición de reflectancia del accidente; las fracciones de gases de referencia no constituirán mapas de composición regional.

El catálogo se ordenará por nombre y mostrará las condiciones observadas y su cobertura junto al índice exclusivamente topográfico. Cada lugar enlazará a una ficha con sus 23 condiciones y las observaciones suplementarias. Las constantes del cuerpo no se usarán para ordenar regiones del mismo cuerpo, pues se repetirán para todas ellas. Tampoco se contarán dos accidentes del mismo sector como dos mediciones ambientales independientes. Se conservarán perfiles compartidos por sector para evitar esa falsa replicación.

No se definirá una clasificación ambiental general ni un promedio ponderado de todas las condiciones mientras falten criterios de comparación, tolerancias justificadas y mediciones con soporte físico compatible. Se retirará la etiqueta genérica «similitud estimada» de la columna topográfica para no confundir cercanía de pendientes con condiciones ambientales semejantes. Las limitaciones y los datos ausentes permanecerán visibles en la ficha de cada lugar.

Los perfiles se guardarán en `recursos/catalogo_regiones/condiciones_moon.json` y `condiciones_mars.json`. Cada registro de `moon.json` y `mars.json` incluirá el identificador de su perfil y cobertura. Estos archivos permitirán posteriores análisis de variables individuales sin alterar los datos originales ni inventar un índice ambiental validado.

### Datos locales que se considerarán

El análisis local de relieve partirá de cuatro grupos con datos detallados; el inventario general conservará además los demás accidentes oficiales, aun cuando solo dispongan de información parcial:

| Grupo propuesto | Producto de referencia | Uso previsto |
|---|---|---|
| Tacaná | Copernicus DEM GLO-30, distribuido mediante Microsoft Planetary Computer | Referencia terrestre; modelo de superficie que puede incluir vegetación e infraestructura |
| Connecting Ridge | Modelo lunar LOLA, archivo `Site01_final_adj_5mpp_surf.tif` | Primera región lunar |
| Borde de Shackleton | Modelo lunar LOLA, archivo `Site04_final_adj_5mpp_surf.tif` | Segunda región lunar |
| Cerberus Tholi | Modelo estereoscópico HiRISE, archivo `DTEED_044184_1850_044039_1850_A01.IMG` | Región marciana |

Los datos lunares y marcianos proceden de productos de misiones NASA. La referencia terrestre de relieve procede de Copernicus; Microsoft proporciona el acceso, pero no es el autor de las mediciones. Las pendientes, los bloques, las comparaciones y la ordenación se calcularán localmente a partir de los productos de origen.

La procedencia de los archivos, sus identificadores y los límites geográficos se conservarán en `recursos/comparacion_tacana/metodologia.json`. Este archivo también registrará huellas SHA-256 de los insumos, que permiten comprobar si cambia el contenido de los archivos de entrada. Las huellas verifican identidad de archivos, no exactitud científica.

### Tipo de algoritmo

Se utilizará una secuencia de procesamiento numérico y análisis estadístico programada en Python. La disponibilidad y cobertura de los productos definirán las regiones elegibles; el programa calculará sus características y sus diferencias.

Se utilizará un procedimiento determinista para la comparación local: con los mismos archivos y parámetros deberá producir los mismos cálculos, salvo diferencias mínimas de redondeo entre entornos. El análisis de sectores globales utilizará muestreo aleatorio con una semilla fija de `20261114`.

### Preparación de los modelos de elevación

Los archivos se leerán con NumPy y Pillow. Para el producto marciano PDS, el código interpretará la etiqueta del archivo para obtener dimensiones, desplazamiento del bloque de datos y escala espacial. Los valores no finitos y los códigos de ausencia de datos se tratarán como faltantes.

Para reducir las diferencias de resolución se aplicará la función `common_grid()` de `recursos/scripts/analizar_nasa.py`. Esta función realizará un suavizado gaussiano normalizado, seguido de un remuestreo bilineal a 100 m. El suavizado tendrá una desviación estándar nominal equivalente a 50 m:

$$
\sigma_x=\frac{50}{d_x},\qquad \sigma_y=\frac{50}{d_y},
$$

donde $d_x$ y $d_y$ son las separaciones originales del raster en metros; las desviaciones estándar resultantes se expresan en píxeles de origen.

Para evitar que los datos faltantes se interpreten como elevación cero, el suavizado se normalizará por una máscara de validez:

$$
\widetilde{z}=\frac{G_\sigma * (M z)}{G_\sigma * M}.
$$

Aquí $M$ vale 1 en celdas válidas y 0 en faltantes, $G_\sigma$ es el filtro gaussiano y $*$ representa convolución. En el código se sustituirá el valor faltante por cero solo en el numerador y se protegerá el denominador con un mínimo de $10^{-9}$. Luego se interpolará tanto la superficie suavizada como su soporte. Las celdas cuyo soporte interpolado es inferior a 0.999 se descartarán.

El remuestreo bilineal estima cada valor de la nueva malla a partir de los cuatro vecinos de la malla suavizada. Si $a,b\in[0,1]$ son las posiciones relativas entre esos vecinos:

$$
z(a,b)=(1-a)(1-b)z_{00}+a(1-b)z_{10}+(1-a)b z_{01}+ab z_{11}.
$$

No crea nuevas mediciones independientes ni recupera detalles ausentes en el producto original. La malla de 100 m permite comparar una escala nominal común, pero no garantiza que todos los sensores tengan idéntica resolución efectiva.

### Cálculo de la pendiente

Con la elevación remuestreada se estimará el gradiente mediante `np.gradient`. En las celdas interiores válidas, la aproximación por diferencias centrales es:

$$
 g_x\approx\frac{z(x+h,y)-z(x-h,y)}{2h},\qquad
 g_y\approx\frac{z(x,y+h)-z(x,y-h)}{2h},\qquad h=100\ \mathrm{m}.
$$

La pendiente en grados se obtendrá como:

$$
\theta=\frac{180}{\pi}\arctan\left(\sqrt{g_x^2+g_y^2}\right).
$$

Las elevaciones y las distancias horizontales se expresan en metros, de modo que el gradiente es adimensional. Una erosión de la máscara de validez eliminará pendientes junto a bordes o datos faltantes. No se compararán directamente las altitudes absolutas entre cuerpos porque sus superficies de referencia vertical son distintas.

### Construcción de observaciones por bloques

La malla se dividirá en bloques contiguos no superpuestos dentro de cada escala: 10 × 10 celdas para 1 km de lado y 20 × 20 celdas para 2 km. Los fragmentos de borde que no completan un bloque se excluirán. Cada bloque se conservará únicamente si al menos el 90 % de sus celdas tienen elevación y pendiente válidas.

Para un bloque con $m$ celdas válidas se calcularán:

$$
\overline{\theta}_{\mathrm{bloque}}=\frac{1}{m}\sum_{j=1}^{m}\theta_j,
$$

$$
R_{\mathrm{bloque}}=P_{95}(z)-P_{5}(z).
$$

La primera cantidad es la pendiente media; la segunda es el relieve local, medido como la diferencia entre los percentiles 95 y 5 de la elevación. El uso de percentiles reduce la influencia de extremos aislados frente a una diferencia máximo–mínimo. El valor calculado es una decisión metodológica del proyecto y no una medida universal de similitud geológica.

Cada bloque aporta una observación por medida. Se realizan pruebas distintas para pendiente y relieve, y se repetirá el procedimiento en cada escala. No se mezclarán grados y metros en una misma prueba ni se combinarán bloques de 1 km y 2 km como si fueran observaciones independientes.

### Secuencia del análisis de relieve

El algoritmo previsto para `comparar_tacana.py` seguirá esta secuencia:

```text
Cargar las cuatro regiones en una malla de 100 m.
Para cada lado de bloque: 1 km y 2 km:
    Construir los bloques completos de cada región.
    Excluir bloques con menos de 90 % de celdas válidas.
    Calcular pendiente media y relieve P95 − P5 de cada bloque.
    Para cada medida: pendiente y relieve:
        Agrupar las observaciones por región.
        Ejecutar ANOVA de Welch entre los cuatro grupos.
        Para cada región extraterrestre:
            Compararla con Tacaná mediante t de Welch.
            Calcular diferencia de medias e intervalo de confianza.
            Calcular g de Hedges y distancia de Wasserstein.
Ajustar con Holm los cuatro valores p del ANOVA.
Ajustar con Holm los doce valores p de las comparaciones por pares.
Ordenar las regiones por Wasserstein, por separado para cada medida y escala.
Guardar observaciones, resultados, gráficos y metodología.
Calcular el índice conjunto de pendiente y relieve para cada región.
Seleccionar por cuerpo la región con el mayor índice a escala de 1 km.
Exportar la selección y el desglose a similitud.json.
```

Las pruebas por pares se calcularán siempre; el código no las condicionará a que el ANOVA global resulte significativo. Los bloques de mayor tamaño constituyen un análisis de sensibilidad a la escala. Se exigirá un mínimo de tres bloques por grupo antes del ANOVA local.

## Notación y estadísticas básicas

| Símbolo | Significado |
|---|---|
| $k$ | Número de grupos en la prueba |
| $n_i$ | Número de observaciones del grupo $i$ |
| $x_{ij}$ | Observación $j$ del grupo $i$ |
| $N=\sum_i n_i$ | Número total de observaciones |
| $\bar{x}_i$ | Media observada del grupo $i$ |
| $s_i^2$ | Varianza muestral del grupo $i$ |
| $\mu_i$ | Media poblacional desconocida del grupo $i$ |

La media y la varianza muestral se calcularán así:

$$
\bar{x}_i=\frac{1}{n_i}\sum_{j=1}^{n_i}x_{ij},
\qquad
s_i^2=\frac{\sum_{j=1}^{n_i}(x_{ij}-\bar{x}_i)^2}{n_i-1}.
$$

El divisor $n_i-1$ corresponde a `np.var(..., ddof=1)`. Para las fórmulas de Welch que siguen se necesitan al menos dos observaciones por grupo y varianzas positivas.

## Hipótesis que se contrastarán

$$
H_0:\mu_1=\mu_2=\cdots=\mu_k
$$

$$
H_1:\text{al menos una media poblacional es diferente.}
$$

Un resultado significativo del ANOVA global no identifica qué regiones difieren. Tampoco indica que todas las parejas sean diferentes. Por eso el proyecto calcula comparaciones individuales contra Tacaná.

## ANOVA de Welch

El script aplicará:

```python
test = stats.f_oneway(*groups.values(), equal_var=False)
```

En temperatura se pasará primero el grupo de referencia:

```python
test = stats.f_oneway(ref, *groups.values(), equal_var=False)
```

`equal_var=False` selecciona Welch, que admite varianzas diferentes entre grupos. Esto no elimina el requisito de independencia de las observaciones. [Documentación de SciPy: f_oneway](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.f_oneway.html).

### Pesos y media ponderada

$$
w_i=\frac{n_i}{s_i^2},\qquad W=\sum_{i=1}^{k}w_i,
\qquad \bar{x}_w=\frac{\sum_{i=1}^{k}w_i\bar{x}_i}{W}.
$$

Un grupo tiene mayor peso si su media se estimará con menor varianza: $s_i^2/n_i$. La media ponderada $\bar{x}_w$ es el centro respecto al que Welch compara las medias de los grupos.

### Corrección y estadístico F

Definimos:

$$
A=\sum_{i=1}^{k}\frac{(1-w_i/W)^2}{n_i-1}.
$$

Entonces:

$$
F_W=\frac{\displaystyle\frac{1}{k-1}\sum_{i=1}^{k}w_i(\bar{x}_i-\bar{x}_w)^2}
{\displaystyle 1+\frac{2(k-2)}{k^2-1}A}.
$$

El numerador mide la separación de las medias, ponderada por su precisión. El denominador incorpora la corrección de Welch. Esta fórmula corresponde a la rama `equal_var=False` de SciPy.

### Grados de libertad y valor p

$$
\nu_1=k-1,\qquad \nu_2=\frac{k^2-1}{3A}.
$$

$$
p=\Pr\left(F_{\nu_1,\nu_2}\geq F_W\mid H_0\right).
$$

$\nu_2$ puede ser fraccionario. El valor p es la probabilidad de obtener un estadístico al menos tan grande como el observado bajo la hipótesis nula y los supuestos del modelo. **No es la probabilidad de que las regiones sean iguales.**

## Comparación de cada región con Tacaná

Para cada región, los scripts ejecutarán una prueba t bilateral de Welch:

```python
test = stats.ttest_ind(values, ref, equal_var=False)
```

Esta es una prueba por pares, distinta del ANOVA global. [Documentación de SciPy: ttest_ind](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.ttest_ind.html).

Sean $R$ la región y $T$ el Tacaná:

$$
\Delta=\bar{x}_R-\bar{x}_T,\qquad
a=\frac{s_R^2}{n_R},\qquad b=\frac{s_T^2}{n_T}.
$$

$$
SE=\sqrt{a+b},\qquad t=\frac{\Delta}{SE}.
$$

Los grados de libertad de Welch–Satterthwaite son:

$$
\nu=\frac{(a+b)^2}{a^2/(n_R-1)+b^2/(n_T-1)}.
$$

El valor p bilateral es $2\Pr(T_\nu\geq |t|)$. El intervalo de confianza se construirá como:

$$
IC_{95\%}(\Delta)=\Delta\pm t_{0.975,\nu}\,SE.
$$

Los intervalos que se guardarán **no están ajustados por comparaciones múltiples**. Una diferencia positiva indica que la media regional es mayor. Los JSON conservan tanto la diferencia con signo como su magnitud $|\Delta|$. La interfaz presenta promedios, porcentajes y rangos comunes; no utilizará la diferencia de medias como porcentaje de similitud.

## Ajuste de pruebas múltiples con Holm

Realizar varias pruebas aumenta la posibilidad de encontrar resultados significativos por azar. La función `holm()` ajustará sus valores p.

Se ordenarán los $m$ valores: $p_{(1)}\leq\cdots\leq p_{(m)}$. Para la posición $i$:

$$
p^{\mathrm{Holm}}_{(i)}=
\min\left(1,\max_{1\leq j\leq i}\left[(m-j+1)p_{(j)}\right]\right).
$$

Después se devolverá cada valor ajustado a su prueba original. El máximo acumulado mantiene el orden de los valores ajustados.

Las familias de pruebas se ajustarán por separado:

| Análisis | Familia |
|---|---|
| Relieve global contra Tacaná | 4 ANOVA: 2 medidas × 2 escalas |
| Relieve por pares | 12 pruebas: 3 regiones × 2 medidas × 2 escalas |
| Temperatura global contra Tacaná | 4 ANOVA: 2 cuerpos × 2 horarios |
| Temperatura por pares | Todas las comparaciones generadas en esa ejecución; su número dependerá de los grupos que superen los filtros |
| Muestreo de sectores globales | 6 ANOVA de Welch: 2 cuerpos × 3 medidas |

Holm controla el error familiar cuando los valores p individuales son válidos. No corrige la dependencia espacial que pueda invalidar esos valores de partida.

## Tamaño del efecto: g de Hedges

El análisis de relieve guardará un tamaño del efecto estandarizado, separado del ANOVA y de Wasserstein:

$$
s_p=\sqrt{\frac{(n_R-1)s_R^2+(n_T-1)s_T^2}{n_R+n_T-2}},
$$

$$
g=\left(1-\frac{3}{4(n_R+n_T)-9}\right)\frac{\Delta}{s_p}.
$$

Se empleará esta corrección aproximada en el cálculo del tamaño del efecto. El signo sigue el de $\Delta$ y su magnitud expresa la diferencia en unidades de desviación estándar combinada. Se guardará como `hedges_g`; no se usará para seleccionar la región de la tarjeta.

## Distancia de Wasserstein

La ordenación usa la distancia de Wasserstein de orden 1:

$$
D_W(R,T)=\int_{-\infty}^{+\infty}|G_R(x)-G_T(x)|\,dx,
$$

donde $G_R$ y $G_T$ son las funciones de distribución acumulada empíricas. Cada observación tiene el mismo peso dentro de su muestra. Una distancia menor indica distribuciones más próximas; conserva la unidad de la medida: grados, metros o grados Celsius. [Documentación de SciPy: wasserstein_distance](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.wasserstein_distance.html).

```python
distance = stats.wasserstein_distance(values, ref)
```

Para una muestra de tamaño $n$, su distribución acumulada empírica es:

$$
G(x)=\frac{1}{n}\sum_{i=1}^{n}\mathbf{1}(x_i\leq x),
$$

donde $\mathbf{1}$ vale 1 cuando se cumple la condición y 0 en caso contrario. Si $u_1<\cdots<u_L$ son los valores distintos de la unión de ambas muestras, la integral se puede expresar como:

$$
D_W=\sum_{\ell=1}^{L-1}|G_R(u_\ell)-G_T(u_\ell)|\,(u_{\ell+1}-u_\ell).
$$

Esta expresión permite comparar muestras de tamaños distintos sin emparejar físicamente cada bloque. Describe las distribuciones de valores; no compara la forma espacial ni la ubicación de montañas, laderas o cráteres.

La distancia se calculará para cada característica y escala. El índice conjunto combinará las distancias normalizadas de pendiente y relieve; el valor p no interviene en esta selección.

## Porcentaje de similitud y selección de región

### Alcance y decisión de diseño

Para mostrar una sola región por cuerpo y un porcentaje se utilizará `recursos/scripts/calcular_similitud.py`. Este índice es una decisión explícita del proyecto: no es una fórmula de NASA, un resultado del ANOVA, una probabilidad de igualdad ni una métrica calibrada externamente. Las referencias bibliográficas respaldan Welch y Wasserstein, pero no validan científicamente esta transformación porcentual específica.

Se utilizarán todas las observaciones válidas de los bloques locales disponibles. Las dos características comparables en la misma región son pendiente y relieve local. Ambas deben estar presentes y recibirán el mismo peso. No se sustituirán datos ausentes por ceros ni se redistribuirán pesos si falta una característica.

### Normalización y ecuaciones

Para cada característica $j$, se calculará la distancia de Wasserstein $D_j$ entre la región y Tacaná y la desviación estándar muestral $s_{T,j}$ de los bloques de Tacaná, a la misma escala. Se define:

$$
d_j=\frac{D_j}{s_{T,j}},\qquad S_j=\frac{100}{1+d_j}.
$$

La similitud conjunta es:

$$
S=0.5\,S_{\mathrm{pendiente}}+0.5\,S_{\mathrm{relieve}}.
$$

La división por la dispersión de Tacaná vuelve adimensional cada distancia antes de combinar los resultados. La referencia fija es Tacaná: invertir referencia y región puede cambiar el índice. Pendiente y relieve pueden estar correlacionados; el promedio de sus puntuaciones no elimina esa correlación ni evalúa su distribución conjunta. $D_j=0$ produce 100 puntos; una distancia de una desviación estándar produce 50; dos desviaciones producen aproximadamente 33.3. Estos puntos de referencia provienen de la función elegida, no de umbrales científicos de equivalencia. Cambiar la función, la escala o los pesos puede cambiar el índice y el orden de regiones.

No se calculará el índice si hay menos de tres observaciones, valores no finitos o dispersión nula en la referencia. Los valores positivos de afinidad no significan necesariamente que se intersecten los rangos: la proximidad y la intersección son descripciones distintas.

### Selección y sensibilidad

Se ordenarán las regiones de cada cuerpo por el mayor $S$ a escala de 1 km, usando el identificador de región para resolver empates de manera reproducible. Se calculará también $S$ a 2 km como análisis de sensibilidad, sin promediar ambas escalas ni tratarlas como observaciones independientes.

La selección lunar comparará dos regiones. La región marciana prevista permitirá una comparación individual con Tacaná, pero no una búsqueda entre múltiples candidatos de Marte. La puntuación no se interpretará como proporción de superficie o propiedades físicas idénticas.

El archivo `recursos/comparacion_tacana/similitud.json` conservará todos los candidatos, componentes, pesos, tamaños muestrales, desviaciones estándar, distancias, resultados por escala y la huella SHA-256 de `bloques.json`.

### Cobertura de los demás datos

| Información | Uso en el índice |
|---|---|
| Pendiente y relieve local | Incluidos con pesos iguales |
| Temperaturas diurnas y nocturnas | Excluidas: los sectores y soportes difieren del relieve local; los datos marcianos disponibles son polares, sin cobertura coincidente de Cerberus |
| Oxígeno y presión | Excluidos: no existen series regionales comparables para las regiones seleccionadas y Tacaná |
| Gravedad, masa, diámetro y propiedades orbitales | Contexto de cuerpos completos, no observaciones de semejanza del terreno regional |
| Sismicidad | Sin catálogos comparables de las tres localizaciones |
| Altitud absoluta | Excluida por referencias verticales diferentes; se usa relieve local |
| Coordenadas e imágenes | Localización y visualización, sin puntuación |

Por tanto, el porcentaje mostrado se denominará **índice de similitud del relieve**, no similitud total. Para ampliar el índice a temperatura o composición se requieren datos con correspondencia geográfica y física suficiente, una normalización defendible y pesos documentados; no basta con incorporar todos los números que aparecen en archivos JSON.

## Identificación de características compartidas

Las tarjetas destacarán el intervalo compartido entre los rangos observados de los bloques de 1 km. Para cada medida se calcularán los mínimos y máximos de Tacaná y de la región seleccionada. La intersección es:

$$
I=[\max(\min T,\min R),\ \min(\max T,\max R)].
$$

Se mostrará un rango común cuando el extremo inferior es estrictamente menor que el superior. Es una descripción de la intersección de intervalos mínimo–máximo; no implica igual frecuencia de valores, coincidencia de cada observación ni equivalencia estadística. Es sensible a los extremos y no es un porcentaje de similitud. La selección regional utilizará el índice conjunto del apartado «Porcentaje de similitud y selección de región»; los rangos comunes se presentarán como información descriptiva adicional, sin modificar las pruebas estadísticas.

Para cada región se determinará si existe un intervalo compartido. Cuando no exista intersección, se indicará su ausencia sin asignarle un rango artificial. La presencia de un intervalo común no se interpretará como equivalencia estadística.

## Temperatura superficial

`comparar_temperatura_tacana.py` utilizará temperatura superficial terrestre MODIS/Aqua MYD11A2.061, temperatura lunar Diviner y observaciones marcianas MCS. Estas mediciones tienen definiciones espectrales distintas, por lo que su comparación es exploratoria.

En Tacaná se seleccionarán los píxeles dentro del recorte de referencia. La conversión del valor digital MODIS a grados Celsius es:

$$
T_{^\circ C}=0.02\,DN-273.15.
$$

El filtro conservará valores digitales de al menos 7500, indicadores obligatorios de calidad 0 o 1, calidad detallada 0 y una clase nominal de error de temperatura de hasta 2 K. Además exigirá observaciones en las ventanas de 12:00 a antes de 14:00 para día, y de 01:00 a antes de 02:00 para noche, en hora solar local.

Las observaciones planetarias se agruparán en sectores de 30° de latitud y 60° de longitud. Para la Luna se promediarán registros de una misma ubicación dentro de la ventana horaria y se requerirán al menos dos registros por ubicación. Para Marte se usarán observaciones del 31 de octubre de 2011 y se agruparán en celdas de un grado. Se conservarán grupos con al menos diez valores y varianza positiva. Tacaná se incorporará como grupo adicional en cada ANOVA.

Se considerará un archivo terrestre que corresponde al compuesto de ocho días del 24 al 31 de octubre de 2011; la información lunar es acumulada de 2009–2015. No existe coincidencia temporal completa. El número de píxeles aceptados, su media y su dispersión se determinarán después del filtrado. Se informará cuántos pertenecen a cada categoría de calidad; los píxeles de la categoría “other produced” no se describirán como observaciones de máxima calidad.

Se aplicará Welch por cuerpo y horario, se comparará cada sector contra Tacaná y se ajustarán los valores p con Holm. Este análisis térmico se guardará por separado y no interviene en la selección de las regiones de relieve de las tarjetas.

## Resultados que se obtendrán e interpretación prevista

Se generarán tablas de tamaños muestrales, medias, desviaciones estándar, estadísticos F y t, grados de libertad y valores p. Se presentarán los valores p ajustados con Holm, los intervalos de confianza de las diferencias, el tamaño del efecto y las distancias de Wasserstein. Los intervalos de confianza por pares se identificarán como no ajustados por multiplicidad.

Para cada región se obtendrá una puntuación de pendiente, otra de relieve y un índice conjunto. La tabla de selección incluirá todos los candidatos elegibles, no únicamente la región con mayor puntuación. Se informará cuántas regiones se comparan en cada cuerpo y se presentará la sensibilidad a bloques de 2 km.

Se utilizará un nivel de significación de referencia de $\alpha=0.05$, aplicado a los valores p ajustados dentro de cada familia. Un resultado significativo se interpretará como evidencia de diferencias bajo los supuestos del modelo. Un resultado no significativo no se interpretará como demostración de igualdad.

No se fijará de antemano una región ganadora ni un porcentaje esperado. Tampoco se establecerá un umbral de “equivalencia” sin una justificación física independiente de los datos.

### Ejemplo hipotético del índice

El siguiente ejemplo utilizará valores supuestos para ilustrar la operación; no representará mediciones de Shackleton, Cerberus Tholi o Tacaná. Si una región tuviera una distancia de pendiente de 5° y la referencia una desviación estándar de 5°, se obtendría:

$$
S_{\mathrm{pendiente}}=\frac{100}{1+5/5}=50.
$$

Si la distancia de relieve fuera 50 m y la desviación estándar de referencia 100 m:

$$
S_{\mathrm{relieve}}=\frac{100}{1+50/100}\approx66.67.
$$

Con pesos iguales, el índice sería:

$$
S=0.5(50)+0.5(66.67)\approx58.33\%.
$$

Este ejemplo mostrará cómo la fórmula combina medidas con unidades distintas después de normalizarlas. El 58.33 % no significará que esa proporción de terreno sea idéntica; será una puntuación definida por el método propuesto.

## Análisis complementario de sectores globales

`anova_regiones.py` también calculará el ANOVA clásico, separado para cada cuerpo, con 36 sectores y 80 muestras por sector. Este análisis de sectores no incluye Tacaná como grupo y no interviene en el porcentaje de las tarjetas.

La media general, las sumas de cuadrados y el estadístico son:

$$
\bar{x}=\frac{1}{N}\sum_{i=1}^{k}n_i\bar{x}_i,
$$

$$
SS_B=\sum_{i=1}^{k}n_i(\bar{x}_i-\bar{x})^2,
\qquad SS_W=\sum_{i=1}^{k}\sum_{j=1}^{n_i}(x_{ij}-\bar{x}_i)^2,
$$

$$
F=\frac{SS_B/(k-1)}{SS_W/(N-k)},\qquad
p=\Pr(F_{k-1,N-k}\geq F_{\mathrm{observado}}\mid H_0).
$$

Aquí se comparará variación entre grupos con variación dentro de los grupos. El ANOVA clásico supone una varianza poblacional común. En ese script también se calcularán Welch y diagnósticos de varianzas y normalidad; estos diagnósticos no convierten automáticamente el muestreo espacial en independiente.

## Límites de interpretación

- Welch permite varianzas diferentes, pero no elimina los supuestos sobre independencia ni los problemas causados por distribuciones muy alejadas del modelo.
- Los bloques vecinos pueden estar correlacionados. Los resultados se interpretarán como exploratorios mientras no se demuestre independencia espacial.
- Usar bloques de 2 km comprueba sensibilidad a la escala, pero no prueba independencia.
- Un p guardado como `0.0` puede deberse a límites de precisión numérica: no es una probabilidad matemáticamente nula.
- Las temperaturas provienen de sensores, períodos y soportes espaciales distintos. No equivalen a un experimento controlado.
- No se compararán altitudes absolutas entre cuerpos con referencias verticales diferentes.
- El análisis no se utilizará para concluir habitabilidad, disponibilidad de oxígeno ni equivalencia física global.

## Organización prevista de archivos y presentación

| Archivo del proyecto | Contenido |
|---|---|
| `recursos/scripts/comparar_tacana.py` | Bloques, Welch, comparaciones por pares, Holm, Hedges y Wasserstein para relieve |
| `recursos/scripts/comparar_temperatura_tacana.py` | Filtrado y comparación de temperatura superficial |
| `recursos/scripts/anova_regiones.py` | Muestreo de sectores globales, ANOVA clásico y Welch |
| `recursos/comparacion_tacana/bloques.json` | Observaciones del ANOVA local de relieve |
| `recursos/comparacion_tacana/anova.json` | Resultados globales de relieve |
| `recursos/comparacion_tacana/comparaciones.json` | Resultados por pares y distancias |
| `recursos/comparacion_tacana/metodologia.json` | Fuentes, escalas, archivos originales y limitaciones del relieve |
| `recursos/comparacion_tacana/temperatura_metodologia.json` | Procedencia y limitaciones de temperatura |
| `resultados-python.js` | Lectura de la selección y presentación del porcentaje, componentes y rangos comunes |
| `recursos/scripts/calcular_similitud.py` | Índice conjunto, selección por cuerpo y sensibilidad a escala de 2 km |
| `recursos/comparacion_tacana/similitud.json` | Candidatos, puntuaciones, selección, cobertura y fórmula del índice |
| `recursos/scripts/servir_resultados.py` | Servidor local y actualización de cálculos e inventario |
| `recursos/scripts/ampliar_catalogo_regiones.py` | Descarga del catálogo oficial y contexto global NASA |
| `recursos/datos/nomenclatura/manifest.json` | Procedencia, fecha y huellas de los KMZ |
| `recursos/catalogo_regiones/moon.json` y `mars.json` | Todos los registros únicos de cada cuerpo y sus datos disponibles |
| `recursos/catalogo_regiones/regiones.geojson` | Puntos del inventario para cartografía |
| `recursos/catalogo_regiones/resumen.json` | Recuento, fuentes, cobertura y limitaciones |
| `recursos/catalogo_regiones/index.html` | Consulta paginada y búsqueda del inventario |

Se emplearán métodos estadísticos establecidos para los contrastes y Wasserstein para las distancias. El índice porcentual será una propuesta propia. NASA y los demás proveedores aportarán los productos de origen; el procesamiento y las comparaciones se realizarán dentro del proyecto.

## Ejecución y comprobación

Los cálculos de comparación se ejecutarán desde la raíz del proyecto, siempre que estén presentes los archivos originales y los productos intermedios indicados en el apartado «Organización prevista de archivos y presentación»:

```powershell
cd D:\space
python recursos/scripts/comparar_tacana.py
python recursos/scripts/comparar_temperatura_tacana.py
python recursos/scripts/calcular_similitud.py
python recursos/scripts/ampliar_catalogo_regiones.py
python recursos/scripts/comparar_catalogo_completo.py
python recursos/scripts/integrar_ambiente.py
python recursos/scripts/catalogar_condiciones.py
python recursos/scripts/exportar_terrenos_3d.py
```

Estos comandos generarán o actualizarán los resultados y requerirán los archivos de entrada originales y los productos intermedios. Los insumos se deberán obtener y verificar antes de ejecutar el análisis. `f_oneway(..., equal_var=False)` requiere SciPy 1.16 o posterior; se utilizará como versión de referencia SciPy 1.18.0.

Para recalcular y abrir el servidor local se utilizará:

```powershell
python recursos/scripts/servir_resultados.py --actualizar
```

La página se servirá en `http://127.0.0.1:8000`. El argumento `--actualizar` ejecutará, en orden, la comparación de relieve, la comparación térmica, el cálculo del índice conjunto y la actualización del inventario a partir de sus archivos locales y la comparación global de todos sus puntos. Sin ese argumento, el servidor mostrará los archivos existentes.

El navegador obtendrá los JSON mediante `fetch`. Abrir o cerrar una tarjeta no ejecuta Python ni vuelve a calcular ANOVA. La selección global se leerá de `similitud_catalogo_resumen.json`, y la interfaz mostrará el candidato, su puntuación, sus componentes y los intervalos compartidos. Los valores numéricos mantienen su precisión en los archivos; la interfaz los redondeará para su lectura.

Para renovar los archivos originales de nombres oficiales se ejecutará:

```powershell
python recursos/scripts/ampliar_catalogo_regiones.py --actualizar
python recursos/scripts/comparar_catalogo_completo.py
python recursos/scripts/integrar_ambiente.py
python recursos/scripts/catalogar_condiciones.py
python recursos/scripts/exportar_terrenos_3d.py
```

Sin `--actualizar`, el catálogo se reconstruirá desde los KMZ locales; solo se descargarán si faltan. Se conservarán los JSON de datos planetarios y del Tacaná en `datos/`, mientras que el nuevo inventario y sus archivos auxiliares permanecerán en `recursos/`.

### Comprobaciones de consistencia

Se evaluarán directamente las ecuaciones de Welch con las observaciones por bloque y se compararán con los resultados de SciPy. Se utilizarán tolerancias relativas de referencia de 1e-12 para F y 1e-10 para valores p distintos de cero, revisando separadamente los casos de subdesbordamiento numérico.

Se comprobará que el índice permanezca entre 0 y 100, que una distancia nula produzca 100 puntos y que una distancia mayor reduzca la puntuación al mantener fija la dispersión de referencia. También se comprobará que una distancia de una desviación estándar produzca 50 puntos.

Se evaluarán entradas con datos faltantes, valores no finitos y desviaciones no positivas. Se verificará que ningún dato ausente se convierta en una coincidencia y que la región seleccionada corresponda al mayor índice del cuerpo considerado. Se contrastarán los resultados a ambas escalas y se comprobará que los valores de la interfaz coincidan con los JSON.

Estas comprobaciones permitirán revisar la implementación, pero no sustituirán la evaluación de los supuestos estadísticos ni una validación externa del índice.

## Referencias gratuitas

Las siguientes fuentes permiten consultar las ecuaciones y sus implementaciones sin suscripción:

| Método | Recurso abierto | Dónde consultar |
|---|---|---|
| ANOVA de Welch | [Documentación oficial de SciPy](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.f_oneway.html) y [código de SciPy 1.18.0](https://github.com/scipy/scipy/blob/v1.18.0/scipy/stats/_stats_py.py) | Buscar `def f_oneway`, después `w_t = n_t / s_t2`, `numerator`, `denominator` y `hat_f2`; es la implementación de las ecuaciones del apartado «ANOVA de Welch». La documentación describe el método; el código muestra las operaciones completas. |
| Prueba t de Welch | [NIST: Two-Sample t-Test for Equal Means](https://www.itl.nist.gov/div898/handbook/eda/section3/eda353.htm) | Las secciones *Test Statistic* y *Critical Region* presentan el estadístico y los grados de libertad de Welch–Satterthwaite. |
| ANOVA clásico | [NIST: The ANOVA table and tests of hypotheses about means](https://www.itl.nist.gov/div898/handbook/prc/section4/prc433.htm) | Cuadrados medios, grados de libertad y cociente F. |
| Holm | [Manual oficial de R: p.adjust](https://stat.ethz.ch/R-manual/R-devel/library/stats/html/p.adjust.html) y [código de p.adjust](https://raw.githubusercontent.com/wch/r-source/trunk/src/library/stats/R/p.adjust.R) | El manual explica el procedimiento; la rama `holm` del código expresa el ajuste mediante `pmin` y `cummax`, equivalente a la ecuación del apartado «Ajuste de pruebas múltiples con Holm». |
| Wasserstein | [Documentación oficial de SciPy](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.wasserstein_distance.html) | La sección *Notes* muestra la integral entre distribuciones acumuladas. |
| Hedges | [Artículo completo alojado en University of California, Merced](https://faculty.ucmerced.edu/jvevea/classes/290_21/readings/week%2010/Hedges%201981.pdf) | Texto de 1981 sobre el estimador y la corrección de sesgo. |

La fórmula porcentual `100 / (1 + distancia / desviación de Tacaná)` y los pesos de 0.5 son decisiones del proyecto. Las referencias respaldan los métodos estadísticos de base, no una validación externa de ese índice ni un porcentaje oficial de NASA.
