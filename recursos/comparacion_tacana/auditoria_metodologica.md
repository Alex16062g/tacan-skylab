# Verificación de cálculos y alcance de los resultados

Fecha: 15 de noviembre de 2026. El estado de la entrega es **análisis exploratorio con comprobaciones numéricas**, no validación científica integral ni certificación de NASA. No se dispone de una especificación de aceptación del destinatario. La procedencia oficial de los datos no implica aprobación de este procesamiento.

## Evidencia reproducible

Se ejecuta `python recursos/scripts/auditar_calculos.py` desde la raíz del proyecto. El resultado está en `auditoria_numerica.json`, con versiones de Python, NumPy y SciPy. Las 135 comprobaciones pasan. Se verifican las distancias, desviaciones estándar y puntuaciones almacenadas de 9,087 lugares lunares y 2,054 marcianos, tanto a 2 como a 3 km; los cuatro ANOVA de Welch locales; la corrección de Holm con un caso conocido; los operadores de terreno con superficies analíticas; y las huellas de los tres archivos de elevación usados en el catálogo.

La verificación de Wasserstein integra de forma independiente la diferencia absoluta entre las funciones de distribución empíricas. No llama a la función de distancia utilizada por el productor de resultados. El ANOVA de Welch se reproduce mediante sus sumas ponderadas y grados de libertad, usando la función de supervivencia F de SciPy únicamente para la cola. Por ello existe una comprobación independiente de la fórmula F, pero no una implementación independiente de la distribución F.

En un plano de elevación z = 0.1x + 0.2y se comprueba la pendiente arctan(sqrt(0.1² + 0.2²)), TPI cero y TRI igual a la raíz de la suma de los ocho desniveles al cuadrado. Un terreno plano produce cero en los cinco descriptores. Estas pruebas no demuestran por sí solas una georreferenciación correcta de todos los productos reales.

## Fórmulas y variables

Para k grupos, se definen n_i, media m_i y variancia muestral s_i². Los pesos de Welch son w_i = n_i/s_i²; W = suma(w_i); m_w = suma(w_i m_i)/W; C = suma[(1 − w_i/W)²/(n_i − 1)].

El estadístico es F = {suma[w_i(m_i − m_w)²]/(k − 1)} / {1 + 2(k − 2)C/(k² − 1)}. Los grados de libertad son k − 1 y (k² − 1)/(3C). Su hipótesis se refiere a medias poblacionales; no mide equivalencia ni semejanza porcentual.

Para las distribuciones empíricas A y B, W1 = integral |F_A(x) − F_B(x)| dx. En una variable j se define S_j = 100/(1 + W1_j/s_Tacaná,j). El índice general es S = 0.5 S_pendiente + 0.5 S_relieve. Pendiente se expresa en grados y relieve en metros; cada distancia se divide por la desviación de su propia variable. TPI, TRI y altura relativa son descriptores suplementarios con peso cero. Clima, oxígeno, presión e irradiancia no participan en este índice.

La transformación a 0–100, los pesos iguales y el umbral de 80 son decisiones del proyecto sin calibración externa. No proceden de una fórmula NASA. La normalización usa exclusivamente la dispersión del Tacaná: el índice es direccional respecto a esa referencia y no es una métrica simétrica universal. Un solapamiento de rangos no demuestra igualdad de distribuciones.

## Sensibilidad observada

| Resultado | Separación 2 km | Separación 3 km |
| --- | --- | --- |
| Primer lugar lunar | Neander C | Lacroix J |
| Lugares lunares por encima de 80 | 195 | 82 |
| Primer lugar marciano | Ophir Cavus | Tithonium Chasma |
| Lugares marcianos por encima de 80 | 1 | 0 |

La mediana del cambio absoluto es 2.50 puntos para Luna y 2.14 para Marte; el máximo es 27.82 y 23.66 puntos, respectivamente. La ventana sigue siendo de 12 km, pero cambian el suavizado, los vecindarios derivados y el número de muestras interiores: 25 frente a 9. Se trata de sensibilidad conjunta del procesamiento, no de un intervalo de confianza. El primer lugar no es estable entre estas dos configuraciones.

## Límites para la entrega

La auditoría no reproduce íntegramente la adquisición, el control de calidad ni el remuestreo de todos los datos originales. Las huellas demuestran coincidencia con archivos registrados, no exactitud instrumental. Se comprueban también los ANOVA térmicos, las comparaciones locales y térmicas por pares, sus intervalos de confianza y las cuatro familias de corrección de Holm. No se revisan todos los análisis históricos por sectores. La temperatura MODIS, la bolométrica Diviner y la de brillo MCS difieren en definición física, soporte espacial y periodo; no deben tratarse como observaciones intercambiables sin un modelo de armonización.

Los vecindarios se solapan y la independencia espacial no está demostrada. Welch permite variancias distintas; no corrige autocorrelación. Holm controla la multiplicidad bajo sus condiciones, pero no convierte p-valores inválidos en válidos. No se han propagado errores instrumentales ni definido márgenes científicos de equivalencia. Buscar el máximo entre miles de lugares exige validar posteriormente los candidatos; la puntuación máxima por sí sola no lo hace.

Para sustentar una conclusión confirmatoria se requiere especificar la pregunta y los criterios de aceptación del destinatario, fijar escalas y tolerancias antes de seleccionar candidatos, verificar georreferenciación y calidad extremo a extremo, modelar dependencia e incertidumbre, y contrastar candidatos con observaciones independientes. No se debe declarar una similitud global, habitabilidad ni equivalencia con Tacaná a partir del índice actual. Una entrega exploratoria puede exponer estos resultados y límites de forma explícita; no equivale a demostrar que satisface los requisitos de NASA.

## Referencias abiertas

- SciPy. (s. f.). *f_oneway*. https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.f_oneway.html . Documenta el contraste, sus supuestos y remite al trabajo de Welch (1951).
- SciPy. (s. f.). *wasserstein_distance*. https://docs.scipy.org/doc/scipy/reference/generated/scipy.stats.wasserstein_distance.html . Incluye la definición integral empleada en la verificación independiente.
- GDAL. (s. f.). *gdaldem*. https://gdal.org/en/stable/programs/gdaldem.html . Documenta TPI y las variantes de TRI. La pendiente del proyecto usa diferencias centrales; no se afirma que reproduce por defecto el algoritmo Horn de GDAL.


## Robustez numérica del código

La función de afinidad divide la magnitud menor entre la mayor cuando la distancia supera la dispersión de referencia. Así evita desbordamientos intermedios con entradas finitas extremas sin cambiar la fórmula matemática. Se rechazan distancias negativas, dispersiones no positivas y entradas no finitas.

Los descriptores comprueban que la cuadrícula tenga dimensiones correctas y datos finitos. La separación debe coincidir con la cuadrícula computacional, dividir la ventana y dejar soporte suficiente para el suavizado. Los controles evitan que una configuración incompatible produzca silenciosamente un resultado mal muestreado.

Las pruebas adicionales verifican continuidad periódica de longitud, ausencia de conexión artificial entre polos e invariancia de los descriptores ante un desplazamiento vertical constante. Los p-valores pequeños se comparan con tolerancia relativa y tolerancia absoluta cero, para evitar aceptar como equivalentes un valor pequeño y cero. Un cero por subdesbordamiento no representa una probabilidad matemáticamente nula.

Estas mejoras no añaden condiciones ambientales al índice de terreno: se verifica su cálculo por separado. Agregar variables incompatibles o contar repetidamente descriptores correlacionados no aumenta la calidad del cálculo. Los resultados históricos conservan su definición y los nuevos controles se aplican a las ejecuciones siguientes.
