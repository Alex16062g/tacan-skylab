# Ecuaciones utilizadas en el análisis del Tacaná, la Luna y Marte

Este documento describe las ecuaciones implementadas en `recursos/scripts/comparar_tacana.py`, `recursos/scripts/comparar_temperatura_tacana.py` y, como antecedente, `recursos/scripts/anova_regiones.py`. Se revisó también la implementación instalada de SciPy 1.18.0.

**El ANOVA detecta diferencias entre medias; no calcula un porcentaje de parecido.** En este proyecto, el ANOVA de Welch evalúa el conjunto de regiones, la prueba t de Welch compara cada región con Tacaná y la distancia de Wasserstein ordena el parecido de sus distribuciones.

## 1. Datos que entran al análisis

En el análisis local de relieve hay cuatro grupos: Tacaná, Connecting Ridge, borde de Shackleton y Cerberus Tholi. Cada observación es un resumen de un bloque de terreno, no una región completa ni un píxel aislado.

La malla tiene una separación de 100 m. Se calculan pruebas separadas para bloques de 1 km y de 2 km de lado. Solo se conservan bloques con al menos 90 % de celdas válidas conjuntamente en elevación y pendiente.

Para cada bloque se calculan:

$$
\overline{\theta}_{\mathrm{bloque}}=\frac{1}{m}\sum_{j=1}^{m}\theta_j
$$

$$
R_{\mathrm{bloque}}=P_{95}(z)-P_{5}(z)
$$

Aquí, $m$ es el número de celdas válidas, $\theta_j$ es la pendiente en grados y $z$ es la elevación en metros. $P_{95}$ y $P_5$ son percentiles. El relieve local expresa la separación entre elevaciones altas y bajas del bloque; no es su altitud sobre el nivel del mar.

Se ejecuta un ANOVA para pendiente y otro para relieve, en cada tamaño de bloque. **No se suman grados y metros ni se mezclan las dos escalas en una sola prueba.**

En temperatura se hacen pruebas separadas por cuerpo y horario: Luna/día, Luna/noche, Marte/día y Marte/noche. Cada una incluye Tacaná como grupo de referencia. Las observaciones son temperaturas superficiales de píxeles o agregados espaciales; no son temperaturas del aire. Los horarios son 12:00–14:00 y 01:00–02:00, en hora solar local, con extremo superior excluido.

## 2. Símbolos y estadísticas básicas

| Símbolo | Significado |
|---|---|
| $k$ | Número de grupos en la prueba |
| $n_i$ | Número de observaciones del grupo $i$ |
| $x_{ij}$ | Observación $j$ del grupo $i$ |
| $N=\sum_i n_i$ | Número total de observaciones |
| $\bar{x}_i$ | Media observada del grupo $i$ |
| $s_i^2$ | Varianza muestral del grupo $i$ |
| $\mu_i$ | Media poblacional desconocida del grupo $i$ |

La media y la varianza muestral se calculan así:

$$
\bar{x}_i=\frac{1}{n_i}\sum_{j=1}^{n_i}x_{ij},
\qquad
s_i^2=\frac{\sum_{j=1}^{n_i}(x_{ij}-\bar{x}_i)^2}{n_i-1}.
$$

El divisor $n_i-1$ corresponde a `np.var(..., ddof=1)`. Para las fórmulas de Welch que siguen se necesitan al menos dos observaciones por grupo y varianzas positivas.

## 3. Hipótesis del ANOVA

$$
H_0:\mu_1=\mu_2=\cdots=\mu_k
$$

$$
H_1:\text{al menos una media poblacional es diferente.}
$$

Un resultado significativo del ANOVA global no identifica qué regiones difieren. Tampoco indica que todas las parejas sean diferentes. Por eso el proyecto calcula comparaciones individuales contra Tacaná.

## 4. ANOVA de Welch: prueba utilizada para Tacaná

La llamada del script es:

```python
test = stats.f_oneway(*groups.values(), equal_var=False)
```

En temperatura se pasa primero el grupo de referencia:

```python
test = stats.f_oneway(ref, *groups.values(), equal_var=False)
```

`equal_var=False` selecciona Welch, que admite varianzas diferentes entre grupos. Esto no elimina el requisito de independencia de las observaciones. [Documentación de SciPy: f_oneway](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.f_oneway.html).

### 4.1. Pesos y media ponderada

$$
w_i=\frac{n_i}{s_i^2},\qquad W=\sum_{i=1}^{k}w_i,
\qquad \bar{x}_w=\frac{\sum_{i=1}^{k}w_i\bar{x}_i}{W}.
$$

Un grupo tiene mayor peso si su media se estima con menor varianza: $s_i^2/n_i$. La media ponderada $\bar{x}_w$ es el centro respecto al que Welch compara las medias de los grupos.

### 4.2. Corrección y estadístico F

Definimos:

$$
A=\sum_{i=1}^{k}\frac{(1-w_i/W)^2}{n_i-1}.
$$

Entonces:

$$
F_W=\frac{\displaystyle\frac{1}{k-1}\sum_{i=1}^{k}w_i(\bar{x}_i-\bar{x}_w)^2}
{\displaystyle 1+\frac{2(k-2)}{k^2-1}A}.
$$

El numerador mide la separación de las medias, ponderada por su precisión. El denominador incorpora la corrección de Welch. Esta es la fórmula aplicada en la rama `equal_var=False` de SciPy revisada localmente.

### 4.3. Grados de libertad y valor p

$$
\nu_1=k-1,\qquad \nu_2=\frac{k^2-1}{3A}.
$$

$$
p=\Pr\left(F_{\nu_1,\nu_2}\geq F_W\mid H_0\right).
$$

$\nu_2$ puede ser fraccionario. El valor p es la probabilidad de obtener un estadístico al menos tan grande como el observado bajo la hipótesis nula y los supuestos del modelo. **No es la probabilidad de que las regiones sean iguales.**

## 5. Comparación de una región contra Tacaná

Para cada región, los scripts ejecutan una prueba t bilateral de Welch:

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

El valor p bilateral es $2\Pr(T_\nu\geq |t|)$. El intervalo de confianza calculado en los scripts es:

$$
IC_{95\%}(\Delta)=\Delta\pm t_{0.975,\nu}\,SE.
$$

Los intervalos guardados **no están ajustados por comparaciones múltiples**. Una diferencia positiva indica que la media regional es mayor; la interfaz muestra $|\Delta|$, la magnitud de esa diferencia.

## 6. Corrección de Holm

Realizar varias pruebas aumenta la posibilidad de encontrar resultados significativos por azar. La función `holm()` ajusta sus valores p.

Ordenamos los $m$ valores: $p_{(1)}\leq\cdots\leq p_{(m)}$. Para la posición $i$:

$$
p^{\mathrm{Holm}}_{(i)}=
\min\left(1,\max_{1\leq j\leq i}\left[(m-j+1)p_{(j)}\right]\right).
$$

Después se devuelve cada valor ajustado a su prueba original. El máximo acumulado mantiene el orden de los valores ajustados.

Las familias de pruebas se ajustan por separado:

| Análisis | Familia |
|---|---|
| Relieve global contra Tacaná | 4 ANOVA: 2 medidas × 2 escalas |
| Relieve por pares | 12 pruebas: 3 regiones × 2 medidas × 2 escalas |
| Temperatura global contra Tacaná | 4 ANOVA: 2 cuerpos × 2 horarios |
| Temperatura por pares | Todas las comparaciones generadas en esa ejecución; 84 en los archivos actuales |
| Muestreo regional inicial | 6 ANOVA de Welch: 2 cuerpos × 3 medidas |

Holm controla el error familiar cuando los valores p individuales son válidos. No corrige la dependencia espacial que pueda invalidar esos valores de partida.

## 7. Cómo se calcula el parecido mostrado en la interfaz

La ordenación usa la distancia de Wasserstein de orden 1:

$$
D_W(R,T)=\int_{-\infty}^{+\infty}|G_R(x)-G_T(x)|\,dx,
$$

donde $G_R$ y $G_T$ son las funciones de distribución acumulada empíricas. Cada observación tiene el mismo peso dentro de su muestra. Una distancia menor indica distribuciones más próximas; conserva la unidad de la medida: grados, metros o grados Celsius. [Documentación de SciPy: wasserstein_distance](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.wasserstein_distance.html).

```python
distance = stats.wasserstein_distance(values, ref)
```

En `resultados-python.js`, la tarjeta selecciona la región de cada cuerpo con menor distancia en **pendiente para bloques de 1 km**, y presenta también el relieve de esa misma región. No calcula una puntuación conjunta de pendiente, relieve y temperatura.

Actualmente Shackleton tiene la menor distancia lunar en ambas medidas. Cerberus Tholi es la única región marciana del análisis local de relieve; por ello no existe una búsqueda comparativa entre varias regiones de Marte en esa selección.

## 8. Ejemplo con los resultados guardados

En `anova.json`, para pendiente con bloques de 1 km:

- Grupos: 4.
- Observaciones totales: 584 bloques.
- $F_W=1675.038021$.
- $p=6.88345\times10^{-187}$.
- $p_{\mathrm{Holm}}=2.75338\times10^{-186}$.

Con un umbral de referencia de 0.05, el resultado indica diferencias entre al menos dos medias, condicionado a los supuestos. No significa que ninguna región pueda parecerse a Tacaná.

Para Shackleton frente a Tacaná, en la misma escala:

| Medida | Media Tacaná | Media Shackleton | Diferencia Shackleton − Tacaná | Wasserstein | p de Welch por pares, ajustado con Holm |
|---|---:|---:|---:|---:|---:|
| Pendiente (°) | 24.411 | 21.349 | −3.062 | 4.901 | 0.0004581 |
| Relieve local (m) | 363.917 | 367.380 | +3.463 | 81.762 | 0.8248323 |

Las medias del relieve son cercanas, pero las distribuciones no son idénticas: su distancia es 81.762 m. El p alto del relieve no demuestra equivalencia. La pendiente presenta una diferencia estadística aun siendo la región lunar más cercana entre las disponibles. Los valores de esta tabla proceden de `comparaciones.json` y se muestran redondeados.

## 9. ANOVA clásico del análisis regional inicial

`anova_regiones.py` también calculó el ANOVA clásico, separado para cada cuerpo, con 36 sectores y 80 muestras por sector. Ese análisis inicial no incluía Tacaná como grupo y no debe confundirse con la comparación local posterior.

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

Aquí se compara variación entre grupos con variación dentro de los grupos. El ANOVA clásico supone una varianza poblacional común. En ese script también se calcularon Welch y diagnósticos de varianzas y normalidad; estos diagnósticos no convierten automáticamente el muestreo espacial en independiente.

## 10. Tamaño del efecto adicional: g de Hedges

El análisis de relieve guarda un tamaño del efecto estandarizado, separado del ANOVA y de Wasserstein:

$$
s_p=\sqrt{\frac{(n_R-1)s_R^2+(n_T-1)s_T^2}{n_R+n_T-2}},
$$

$$
g=\left(1-\frac{3}{4(n_R+n_T)-9}\right)\frac{\Delta}{s_p}.
$$

Es la corrección aproximada implementada en el script. El signo sigue el de $\Delta$ y su magnitud expresa la diferencia en unidades de desviación estándar combinada. Se guarda como `hedges_g`; no se usa para seleccionar la región de la tarjeta.

## 11. Alcance de las conclusiones

- Welch permite varianzas diferentes, pero no elimina los supuestos sobre independencia ni los problemas causados por distribuciones muy alejadas del modelo.
- Los bloques vecinos pueden estar correlacionados. Los resultados son exploratorios; la independencia espacial no está demostrada.
- Usar bloques de 2 km comprueba sensibilidad a la escala, pero no prueba independencia.
- Un p guardado como `0.0` puede deberse a límites de precisión numérica: no es una probabilidad matemáticamente nula.
- Las temperaturas provienen de sensores, períodos y soportes espaciales distintos. No equivalen a un experimento controlado.
- No se comparan altitudes absolutas entre cuerpos con referencias verticales diferentes.
- El análisis no permite concluir habitabilidad, disponibilidad de oxígeno ni equivalencia física global.

## 12. Archivos y trazabilidad

| Archivo del proyecto | Contenido |
|---|---|
| `recursos/scripts/comparar_tacana.py` | Bloques, Welch, comparaciones por pares, Holm, Hedges y Wasserstein para relieve |
| `recursos/scripts/comparar_temperatura_tacana.py` | Filtrado y comparación de temperatura superficial |
| `recursos/scripts/anova_regiones.py` | Muestreo inicial de sectores, ANOVA clásico y Welch |
| `recursos/comparacion_tacana/bloques.json` | Observaciones del ANOVA local de relieve |
| `recursos/comparacion_tacana/anova.json` | Resultados globales de relieve |
| `recursos/comparacion_tacana/comparaciones.json` | Resultados por pares y distancias |
| `recursos/comparacion_tacana/metodologia.json` | Fuentes, escalas, archivos originales y limitaciones del relieve |
| `recursos/comparacion_tacana/temperatura_metodologia.json` | Procedencia y limitaciones de temperatura |
| `resultados-python.js` | Lectura y presentación de resultados; selección automática de región |

Las ecuaciones son métodos estadísticos establecidos, no fórmulas de similitud publicadas por NASA. NASA y los demás proveedores aportan los datos; el procesamiento y las comparaciones son cálculos locales del proyecto.

## 13. Referencias de las ecuaciones

### Fuentes gratuitas para consultar las fórmulas

No es necesario comprar los artículos originales para revisar el cálculo. Estos recursos se consultaron sin suscripción ni registro:

| Método | Recurso abierto | Dónde consultar |
|---|---|---|
| ANOVA de Welch | [Documentación oficial de SciPy](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.f_oneway.html) y [código de SciPy 1.18.0](https://github.com/scipy/scipy/blob/v1.18.0/scipy/stats/_stats_py.py) | Buscar `def f_oneway`, después `w_t = n_t / s_t2`, `numerator`, `denominator` y `hat_f2`; es la implementación de las ecuaciones de la sección 4. La documentación describe el método; el código muestra las operaciones completas. |
| Prueba t de Welch | [NIST: Two-Sample t-Test for Equal Means](https://www.itl.nist.gov/div898/handbook/eda/section3/eda353.htm) | Las secciones *Test Statistic* y *Critical Region* presentan el estadístico y los grados de libertad de Welch–Satterthwaite. |
| ANOVA clásico | [NIST: The ANOVA table and tests of hypotheses about means](https://www.itl.nist.gov/div898/handbook/prc/section4/prc433.htm) | Cuadrados medios, grados de libertad y cociente F. |
| Holm | [Manual oficial de R: p.adjust](https://stat.ethz.ch/R-manual/R-devel/library/stats/html/p.adjust.html) y [código de p.adjust](https://raw.githubusercontent.com/wch/r-source/trunk/src/library/stats/R/p.adjust.R) | El manual explica el procedimiento; la rama `holm` del código expresa el ajuste mediante `pmin` y `cummax`, equivalente a la ecuación de la sección 6. |
| Wasserstein | [Documentación oficial de SciPy](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.wasserstein_distance.html) | La sección *Notes* muestra la integral entre distribuciones acumuladas. |
| Hedges | [Artículo completo alojado en University of California, Merced](https://faculty.ucmerced.edu/jvevea/classes/290_21/readings/week%2010/Hedges%201981.pdf) | Texto de 1981 sobre el estimador y la corrección de sesgo. |

También está disponible una [copia abierta del artículo de Welch de 1947](https://www.dcscience.net/welch-1947.pdf). Los DOI que siguen se conservan como identificación bibliográfica; las páginas de los editores pueden solicitar pago. Para consultar el cálculo sin pagar, utiliza los recursos de esta tabla.

### Procedencia y verificación

Para redactar las ecuaciones se revisaron los scripts del proyecto y el código de `scipy.stats.f_oneway` instalado, además de la documentación oficial de SciPy. Las referencias originales siguientes identifican el fundamento bibliográfico de los métodos; no implican que NASA haya validado esta aplicación a regiones planetarias.

Se evaluó de forma independiente la fórmula de Welch escrita en este documento usando `bloques.json`: reprodujo los cuatro estadísticos F guardados con tolerancia relativa de 1e-12 y sus valores p con tolerancia relativa de 1e-10. Esto verifica la correspondencia matemática con el cálculo, no la independencia del muestreo.

1. **ANOVA de Welch, sección 4.** Welch, B. L. (1951). *On the Comparison of Several Mean Values: An Alternative Approach*. Biometrika, 38(3–4), 330–336. [DOI de la publicación](https://doi.org/10.1093/biomet/38.3-4.330). La implementación revisada de SciPy identifica sus ecuaciones 29 y 30 como base del estadístico y los grados de libertad. [Documentación e identificación de la referencia en SciPy](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.f_oneway.html). La consulta web al texto completo del editor no estuvo disponible; la verificación de las fórmulas se hizo contra el código instalado.

2. **Prueba t de Welch y aproximación de grados de libertad, sección 5.** Welch, B. L. (1947). *The Generalization of “Student’s” Problem when Several Different Population Variances are Involved*. Biometrika, 34(1–2), 28–35. [DOI](https://doi.org/10.1093/biomet/34.1-2.28). [Implementación utilizada: scipy.stats.ttest_ind](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.ttest_ind.html). El intervalo mostrado se construye invirtiendo la prueba t bilateral con esos grados de libertad.

3. **Corrección de Holm, sección 6.** Holm, S. (1979). *A Simple Sequentially Rejective Multiple Test Procedure*. Scandinavian Journal of Statistics, 6(2), 65–70. [Copia de la publicación alojada en la Universidad de São Paulo](https://www.ime.usp.br/~abe/lista/pdf4R8xPVzCnX.pdf). La fórmula del documento expresa el procedimiento mediante valores p ajustados y coincide con la función `holm()` del proyecto. La descarga completa de esta copia devolvió acceso restringido durante la consulta.

4. **Distancia de Wasserstein, sección 7.** [SciPy: scipy.stats.wasserstein_distance](https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.wasserstein_distance.html). Su sección *Notes* presenta la distancia como integral de la diferencia absoluta entre funciones acumuladas. Es una medida descriptiva separada del ANOVA.

5. **ANOVA clásico, sección 9.** NIST/SEMATECH. *e-Handbook of Statistical Methods*, sección 7.4.3.3, *The ANOVA table and tests of hypotheses about means*. [Referencia institucional y ecuaciones](https://www.itl.nist.gov/div898/handbook/prc/section4/prc433.htm). Presenta la razón entre cuadrados medios y los grados de libertad $k-1$ y $N-k$.

6. **Tamaño del efecto, sección 10.** Hedges, L. V. (1981). *Distribution Theory for Glass’s Estimator of Effect Size and Related Estimators*. Journal of Educational Statistics, 6(2), 107–128. [DOI](https://doi.org/10.3102/10769986006002107). El factor usado en el proyecto es una aproximación a la corrección de sesgo, no la expresión exacta mediante funciones gamma. La estandarización combinada debe interpretarse con cautela cuando las varianzas son muy diferentes.

### Validez matemática y validez del estudio

Las ecuaciones corresponden a métodos reconocidos. Para que sus valores p e intervalos tengan la interpretación inferencial indicada, el modelo debe ser adecuado para los datos. En este proyecto no se ha demostrado independencia espacial y, en temperatura, existen diferencias de sensor y período. Por eso se mantiene la interpretación exploratoria: fórmulas correctas no bastan para demostrar equivalencia entre Tacaná y una región lunar o marciana.
