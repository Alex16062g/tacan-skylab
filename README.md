# Tacaná Skylab

[**Ver demo**](https://alex16062g.github.io/tacan-skylab/)

[Descripción](#descripción) · [Datos utilizados](#datos-utilizados) · [Ecuaciones](#ecuaciones) · [Referencias](#referencias) · [Instalación y ejecución](#instalación-y-ejecución)

## Descripción

Tacaná Skylab es un proyecto de análisis y visualización geoespacial que estudia semejanzas entre el terreno del volcán Tacaná, situado en la frontera entre México y Guatemala, y regiones de la Luna y Marte. Integra modelos de elevación, imágenes orbitales, datos ambientales y registros sísmicos en una aplicación web.

Su objetivo es identificar regiones con características cuantitativas comparables al Tacaná y facilitar la consulta de los datos que sustentan cada comparación. El procesamiento se realiza en Python; la aplicación presenta los resultados mediante mapas, tablas y comparaciones visuales.

## Datos utilizados

| Componente | Fuentes | Uso en el proyecto |
| --- | --- | --- |
| Relieve terrestre | Copernicus DEM GLO-30 | Caracterización del terreno del Tacaná |
| Relieve lunar | NASA, Lunar Orbiter Laser Altimeter (LOLA) | Elevación y descriptores del terreno lunar |
| Relieve marciano | NASA, Mars Orbiter Laser Altimeter (MOLA) | Elevación y descriptores del terreno marciano |
| Regiones planetarias | Gazetteer of Planetary Nomenclature, IAU/USGS | Identificadores, nombres y coordenadas de referencia |
| Imágenes | Landsat 8, LROC WAC y mosaico CTX del Murray Lab | Comparación visual de las áreas de estudio |
| Condiciones ambientales | MODIS, Diviner, Mars Climate Sounder y NASA POWER | Análisis y contextualización de temperatura, presión y otras condiciones, según su disponibilidad |
| Sismicidad | Servicio Sismológico Nacional, UNAM | Selección de epicentros dentro del área de estudio del Tacaná |

## Ecuaciones

### Preparación y alcance

El catálogo utiliza el centro de cada región para construir un entorno de 12 km. Las alturas se interpolan en una malla de cálculo de 250 m y se suavizan con un filtro gaussiano de desviación espacial $d/2$, antes de obtener una malla con separación $d=2\,000$ m. La evaluación de sensibilidad repite el procedimiento con $d=3\,000$ m. La interpolación no mejora la resolución nativa del producto. Las mallas de 7 × 7 y 5 × 5 alturas producen, respectivamente, 25 y 9 observaciones interiores por descriptor.

El índice del catálogo se calcula para cada lugar por separado. Los ANOVA locales y térmicos constituyen análisis independientes: no se realiza un ANOVA entre los 11,141 lugares para obtener sus porcentajes. En el análisis local previo se usan bloques de 1 km y una evaluación de sensibilidad de 2 km, sobre modelos remuestreados a 100 m. Sus resultados no son intercambiables con los del catálogo.

### 1. Pendiente y relieve

Sea $z_{i,j}$ la elevación en metros y $d$ la separación horizontal entre muestras, también en metros.

$$
g_x=\frac{z_{i,j+1}-z_{i,j-1}}{2d},\qquad
g_y=\frac{z_{i+1,j}-z_{i-1,j}}{2d}
$$

$$
\theta_{i,j}=\frac{180}{\pi}\arctan\!\left(\sqrt{g_x^2+g_y^2}\right)
$$

La pendiente $\theta$ se expresa en grados. El relieve local $R$ es la diferencia entre los percentiles 95 y 5 de las alturas en cada vecindario de 3 × 3 muestras.

$$
R=Q_{0.95}(Z_{3\times3})-Q_{0.05}(Z_{3\times3})
$$

### 2. Descriptores complementarios

Para la elevación central $z_i$ y sus ocho vecinos $z_k$, se calculan altura relativa, posición topográfica y rugosidad.

$$
H_i=z_i-\operatorname{mediana}(Z_{12\,\mathrm{km}})
$$

$$
TPI_i=z_i-\frac{1}{8}\sum_{k=1}^{8}z_k,\qquad
TRI_i=\sqrt{\sum_{k=1}^{8}(z_k-z_i)^2}
$$

Los tres descriptores se expresan en metros. TRI utiliza la variante Riley, sin dividir la suma entre ocho. Estos descriptores son complementarios y tienen peso cero en el índice general.

### 3. Distancia entre distribuciones

La comparación utiliza las distribuciones empíricas de cada descriptor, no solo sus medias. Para la región $R$ y el Tacaná $T$, sean $F_R$ y $F_T$ sus funciones de distribución acumulada.

$$
W_1(R,T)=\int_{-\infty}^{\infty}|F_R(x)-F_T(x)|\,dx
$$

Una distancia menor indica distribuciones más próximas. La distancia conserva las unidades de la variable: grados para pendiente y metros para relieve.

### 4. Índice de similitud

Para la variable $j$, la distancia se normaliza por la desviación estándar muestral $s_{T,j}$ del Tacaná.

$$
s_{T,j}=\sqrt{\frac{1}{n_T-1}\sum_{i=1}^{n_T}(x_{T,ij}-\bar{x}_{T,j})^2}
$$

$$
S_j=\frac{100}{1+W_{1,j}/s_{T,j}},\qquad
S=0.5S_{\mathrm{pendiente}}+0.5S_{\mathrm{relieve}}
$$

Una distancia nula produce 100 puntos; una distancia igual a una desviación estándar del Tacaná produce 50. Los pesos iguales y esta transformación son decisiones del proyecto, no una fórmula oficial de NASA. Si faltan datos o la desviación de referencia no es positiva, no se asigna una coincidencia. Se ordenan las regiones de cada cuerpo por $S$ y se selecciona la mayor puntuación. El índice es direccional porque se normaliza respecto al Tacaná.

Para describir los valores compartidos se calcula la intersección de rangos observados. Solo se informa cuando su límite inferior es menor que el superior.

$$
I_j=[\max(\min T_j,\min R_j),\;\min(\max T_j,\max R_j)]
$$

### 5. ANOVA de Welch

En los análisis locales y térmicos, $k$ representa el número de grupos; $n_i$, $\bar{x}_i$ y $s_i^2$ son el tamaño, la media y la varianza muestral del grupo $i$. Se necesitan grupos con suficientes observaciones válidas y varianzas positivas. La hipótesis nula es igualdad de medias; la alternativa es que al menos una difiere.

$$
\bar{x}_i=\frac{1}{n_i}\sum_{j=1}^{n_i}x_{ij},\qquad
s_i^2=\frac{\sum_{j=1}^{n_i}(x_{ij}-\bar{x}_i)^2}{n_i-1},\qquad
H_0:\mu_1=\cdots=\mu_k
$$

Los pesos, la media ponderada y el término de corrección son:

$$
w_i=\frac{n_i}{s_i^2},\qquad W=\sum_{i=1}^{k}w_i,\qquad
\bar{x}_w=\frac{\sum_{i=1}^{k}w_i\bar{x}_i}{W}
$$

$$
A=\sum_{i=1}^{k}\frac{(1-w_i/W)^2}{n_i-1}
$$

El estadístico y sus grados de libertad se calculan como:

$$
F_W=\frac{\frac{1}{k-1}\sum_{i=1}^{k}w_i(\bar{x}_i-\bar{x}_w)^2}
{1+\frac{2(k-2)}{k^2-1}A},\qquad
\nu_1=k-1,\qquad \nu_2=\frac{k^2-1}{3A}
$$

$$
p=\Pr(F_{\nu_1,\nu_2}\geq F_W\mid H_0)
$$

Welch admite varianzas diferentes, pero no elimina el supuesto de independencia. El valor $p$ no es una probabilidad de similitud ni se utiliza como porcentaje.

### 6. Comparaciones por pares y tamaño del efecto

Para comparar una región $R$ con Tacaná $T$, se utiliza la prueba bilateral de Welch.

$$
\Delta=\bar{x}_R-\bar{x}_T,\qquad a=\frac{s_R^2}{n_R},\qquad b=\frac{s_T^2}{n_T}
$$

$$
SE=\sqrt{a+b},\qquad t=\frac{\Delta}{SE},\qquad
\nu=\frac{(a+b)^2}{a^2/(n_R-1)+b^2/(n_T-1)}
$$

$$
p_{\mathrm{bilateral}}=2\Pr(T_\nu\geq|t|),\qquad
IC_{95\%}(\Delta)=\Delta\pm t_{0.975,\nu}SE
$$

El análisis local de relieve también registra $g$ de Hedges mediante una corrección aproximada.

$$
s_p=\sqrt{\frac{(n_R-1)s_R^2+(n_T-1)s_T^2}{n_R+n_T-2}},\qquad
g=\left(1-\frac{3}{4(n_R+n_T)-9}\right)\frac{\Delta}{s_p}
$$

Los intervalos anteriores no están ajustados por comparaciones múltiples. $g$ describe una diferencia estandarizada y no interviene en el índice de similitud.

### 7. Corrección de Holm

Al realizar $m$ pruebas, sus valores se ordenan como $p_{(1)}\leq\cdots\leq p_{(m)}$.

$$
p^{\mathrm{Holm}}_{(i)}=
\min\left(1,\max_{1\leq j\leq i}\{(m-j+1)p_{(j)}\}\right)
$$

Los valores ajustados se devuelven al orden original. El ajuste se aplica por familia de pruebas; no se mezclan indiscriminadamente los análisis locales, térmicos y de sectores. Holm controla el error familiar cuando los valores $p$ de partida son válidos.

### Interpretación y condiciones de uso

Temperatura, presión, oxígeno e irradiancia se mantienen como información complementaria porque su cobertura, resolución y definición física no son necesariamente comparables. La dependencia espacial puede limitar la inferencia estadística. Un índice alto no demuestra igualdad del entorno ni semejanza visual. Las imágenes ilustran los lugares, pero no se utilizan para calcular el índice.

Los datos NASA, incluido el ZIP inicial de Marte, se consideran autorizados para este proyecto según lo indicado por su responsable; se conservan su procedencia y créditos. Copernicus y los servicios cartográficos exigen atribución. El catálogo SSN permite reproducción no lucrativa con crédito; otros usos requieren permiso. Los logos no tienen una licencia abierta acreditada en el proyecto. Por ello no se presenta todo el repositorio como de libre reutilización irrestricta.

## Referencias

### Datos científicos

- NASA Scientific Visualization Studio. *CGI Moon Kit: lunar elevation and imagery products*. [Documentación del producto](https://svs.gsfc.nasa.gov/4720/).
- NASA Planetary Data System, Geosciences Node. *Mars Global Surveyor: MOLA Mission Experiment Gridded Data Records*. [Archivo MEGDR](https://pds-geosciences.wustl.edu/missions/mgs/megdr.html).
- IAU Working Group for Planetary System Nomenclature / USGS Astrogeology Science Center. *Gazetteer of Planetary Nomenclature*. [Catálogo de regiones planetarias](https://planetarynames.wr.usgs.gov/).
- Copernicus Data Space Ecosystem. *Copernicus DEM*. [Descripción del producto](https://dataspace.copernicus.eu/explore-data/data-collections/copernicus-contributing-missions/collections-description/COP-DEM).
- USGS Astrogeology Science Center. *Moon LRO LROC WAC Global Morphology Mosaic 100 m*. [Documentación del mosaico](https://astrogeology.usgs.gov/search/map/moon_lro_lroc_wac_global_morphology_mosaic_100m).
- NASA/JPL/MSSS/The Murray Lab. *CTX Beta01 mosaic*, distribuido mediante OnMars/CTX1. [Metadatos del servicio](https://astro.arcgis.com/arcgis/rest/services/OnMars/CTX1/MapServer).
- NASA POWER Project. *Data documentation*. [Definición y acceso a los datos](https://power.larc.nasa.gov/docs/faqs/data/).
- Servicio Sismológico Nacional, Universidad Nacional Autónoma de México. *Catálogo de sismos*. [DOI: 10.21766/SSNMX/EC/MX](https://doi.org/10.21766/SSNMX/EC/MX).

### Métodos estadísticos

- SciPy. *f_oneway*: ANOVA de un factor y ANOVA de Welch. [Documentación](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.f_oneway.html).
- SciPy. *wasserstein_distance*: distancia entre distribuciones unidimensionales. [Documentación](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.wasserstein_distance.html).
- NIST/SEMATECH. *Two-Sample t-Test for Equal Means*. [Manual de estadística](https://www.itl.nist.gov/div898/handbook/eda/section3/eda353.htm).
- R Core Team. *p.adjust*: ajuste de valores p, incluido el método de Holm. [Documentación](https://stat.ethz.ch/R-manual/R-devel/library/stats/html/p.adjust.html).

- GDAL contributors. (s. f.). *gdaldem: Terrain analysis*, TPI y TRI. [Documentación](https://gdal.org/en/stable/programs/gdaldem.html).
- Hedges, L. V. (1981). Distribution theory for Glass’s estimator of effect size and related estimators. *Journal of Educational Statistics, 6*(2), 107–128. [Texto completo](https://faculty.ucmerced.edu/jvevea/classes/290_21/readings/week%2010/Hedges%201981.pdf).

La transformación del índice y sus pesos son decisiones del proyecto; las referencias sustentan los métodos estadísticos de base.

## Instalación y ejecución

### Requisitos

Python y las dependencias indicadas a continuación. Ejecutar los comandos desde la raíz del proyecto. Los análisis requieren sus archivos originales y productos intermedios; `recursos/datos/` y la caché de imágenes no se incluyen automáticamente al clonar el código.

```powershell
python -m pip install -r recursos/scripts/requirements-analisis.txt
```

### Ejecutar la aplicación

```powershell
python -B recursos/scripts/servir_resultados.py --puerto 8000
```

Abrir [http://localhost:8000](http://localhost:8000).

### Recalcular los resultados

Con los insumos disponibles, recalcular las comparaciones e iniciar el servidor.

```powershell
python -B recursos/scripts/servir_resultados.py --actualizar --puerto 8000
```

### Ejecutar las comprobaciones

```powershell
python -B recursos/scripts/auditar_calculos.py
```

### Ejecutar la demo estática local

Exportar los resultados y las imágenes ya preparadas. `--allow-incomplete` permite una exportación parcial; la cobertura se registra en `recursos/github-pages/build-report.json`.

```powershell
python -B recursos/scripts/exportar_demo_estatica.py --allow-incomplete
python -B recursos/scripts/verificar_imagenes_html.py
python -m http.server 8080 --directory recursos
```

Abrir [http://localhost:8080/github-pages/](http://localhost:8080/github-pages/).

Para preparar las imágenes del selector principal:

```powershell
python -B recursos/scripts/construir_demo_estatica.py --priority-only
```

La cartografía externa requiere conexión a Internet.
