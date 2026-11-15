# Procedencia y reutilización de datos

Los datos NASA se consideran autorizados para este proyecto, conforme a lo declarado por su responsable. Sus referencias se conservan por trazabilidad; la revisión de permisos y apertura se centra en las fuentes ajenas a NASA.

La bibliografía de datos, métodos y herramientas está en [Referencias](../REFERENCIAS.md), en formato APA. Este documento conserva las condiciones de reutilización y los antecedentes de procesamiento. El ZIP inicial contiene datos NASA de Marte, según confirma el responsable del proyecto, y queda comprendido en la autorización NASA declarada. Las observaciones de permisos pendientes corresponden a fuentes ajenas a NASA, como SSN y los logos.

Revisión: 15 de noviembre de 2026. Este inventario distingue dominio público, autorización de uso gratuito y licencias abiertas con atribución. No atribuye una licencia CC0 a recursos cuyos proveedores no la declaran. Una licencia abierta tampoco garantiza ausencia de errores científicos.

## Imágenes del comparador

| Recurso activo | Procedencia | Reutilización y evidencia |
| --- | --- | --- |
| Tacaná | USGS/NASA, Landsat 8, Collection 2 Level-2; escena LC08_L2SP_021050_20251126_02_T1, adquirida el 26 de noviembre de 2025. Microsoft Planetary Computer distribuye los archivos. | Dominio público. USGS permite uso y redistribución sin restricciones: https://www.usgs.gov/faqs/are-there-any-restrictions-use-or-redistribution-landsat-data |
| Neander C, Luna | Producto WAC_GLOBAL_E300S0450_100M, versión 1.3, descargado directamente del archivo LROC PDS. | Los productos PDS son de dominio público. Esta condición no se extiende automáticamente a las imágenes editoriales o interfaces no PDS de LROC: https://www.lroc.im-ldi.com/about/terms |
| Ophir Cavus, Marte | CTX Murray Lab, servicio OnMars/CTX1, identificado por su descripción como Beta01. Esri distribuye este mosaico científico; no es World Imagery. | El servicio declara permiso de uso gratuito de Beta01 para cualquier finalidad y pide crédito NASA/JPL/MSSS/The Murray Lab: https://astro.arcgis.com/arcgis/rest/services/OnMars/CTX1/MapServer . Evidencia descargada: datos/imagenes_abiertas/ctx_service_metadata.json. La autorización V01 de https://murray-lab.caltech.edu/CTX/ es distinta y no se usa para atribuir una versión incorrecta al recorte. |

Los recortes y sus huellas SHA-256 están documentados en comparador_imagenes/fuentes.json. El script scripts/imagenes_abiertas.py conserva los recortes numéricos Landsat, el registro STAC, la cabecera PDS y los bytes de las filas lunares leídas. Las coordenadas definen ventanas de aproximadamente 12 km. Son imágenes de lugares distintos, no un registro espacial entre superficies equivalentes.

La imagen Landsat combina bandas B4, B3 y B2, aplica la escala y el desplazamiento de reflectancia de sus metadatos y ajusta el contraste para visualización. Su resolución nativa es 30 m; mostrarla a 1024 píxeles no añade resolución. El control QA_PIXEL marca aproximadamente 0.325 % del recorte como nube, sombra, cirro, nieve o relleno según los seis bits inferiores; esos píxeles no se reconstruyen. El recorte lunar tiene resolución nativa de 100 m y ajuste de contraste P1–P99. Los PNG/JPEG son derivados visuales, no los datos numéricos utilizados en el análisis estadístico.

## Cartografía de la página principal

- El fondo activo es Sentinel-2 cloudless **edición 2016**, EOX, con cobertura continua de México y resolución nominal de 10 m. Su capa WMTS `s2cloudless_3857` declara **CC BY 4.0**. No se emplean las ediciones 2018 o posteriores sujetas a restricciones no comerciales. Se conserva el crédito de EOX y Copernicus y el enlace a la licencia en el mapa.
- Fuente: https://tiles.maps.eox.at/wmts/1.0.0/WMTSCapabilities.xml . Condiciones del servicio público y confirmación de uso comercial del fondo 2016: https://cloudless.eox.at/documentation/faq . El servicio tiene política de uso razonable y no garantiza disponibilidad; su FAQ restringe revender/redistribuir las teselas del servicio como un conjunto independiente. Se usa para visualizar el mapa, sin descarga masiva ni redistribución del servicio. No se afirma que el endpoint carezca de condiciones por usar datos CC BY 4.0.
- Blue Marble y el parche Landsat de 60 km dejan de formar parte del mapa activo. Los recortes Landsat de dominio público siguen en el comparador y no se modifican los datos del análisis. Los archivos de contexto previos se conservan como históricos, pero no se solicitan al navegar por el mapa.
- Mapterhorn utiliza fuentes de elevación abiertas con condiciones específicas por proveedor; no se etiqueta todo el servicio como CC0. Se mantiene su atribución: https://mapterhorn.com/attribution/ .

## Datos científicos de relieve y condiciones

| Conjunto | Función | Condiciones y documentación |
| --- | --- | --- |
| NASA LOLA / SVS | Elevación lunar | Contenido SVS de dominio público salvo indicación contraria: https://svs.gsfc.nasa.gov/help/ . Producto: https://svs.gsfc.nasa.gov/4720/ |
| NASA PDS MOLA | Elevación de Marte | Archivo científico NASA PDS: https://pds-geosciences.wustl.edu/missions/mgs/megdr.html . Los archivos e identificadores descargados figuran en datos/nasa/manifest.json. |
| Copernicus DEM GLO-30 | Modelo de superficie del Tacaná | Licencia gratuita mundial con condiciones de atribución y de derivados; no es dominio público ni CC0. https://dataspace.copernicus.eu/explore-data/data-collections/copernicus-contributing-missions/collections-description/COP-DEM . Conservar el aviso de atribución completo de vista_previa/tacana_fuentes.json. |
| NASA MODIS | Temperatura superficial terrestre | Datos científicos abiertos; citar el producto MYD11A2 y su versión en los metadatos descargados. Guía de cita de LP DAAC: https://www.usgs.gov/centers/eros/data-citation |
| NASA Diviner y MCS | Temperatura y presión planetarias | Productos científicos PDS. Trazabilidad por producto en datos/nasa/ambiente/manifest.json; no confundir con fotografías editoriales de las misiones. |
| NASA POWER | Meteorología y energía solar terrestre | Servicio de datos gratuito NASA; origen, unidades y alcance: https://power.larc.nasa.gov/docs/faqs/data/ . Solicitud exacta conservada en datos/tacana_ambiente/source.json. Los datos de celda no son mediciones de la cumbre del Tacaná. |

Las licencias de los datos originales siguen siendo aplicables a sus derivados. Se conservan las referencias científicas, incluso en los recursos de dominio público. No se presenta el índice calculado por este proyecto como resultado avalado por NASA.

## Alcance y archivos anteriores

### Capa sísmica del Tacaná

El catálogo nacional SSN/UNAM aportado contiene 221,217 eventos entre el 1 de enero de 2020 y el 14 de noviembre de 2026. `filtrar_sismos_tacana.py` conserva únicamente los 42 epicentros situados dentro del rectángulo mostrado en el mapa: oeste −92.17388888888888, sur 15.069166666666664, este −92.04416666666667 y norte 15.195 grados, con límites inclusivos. No se aplica filtro de profundidad ni magnitud. Esta selección no demuestra origen volcánico y el rectángulo no es un límite geológico oficial del edificio volcánico.

El archivo `recursos/sismos/tacana.geojson` registra las coordenadas, fechas, magnitudes, profundidad, estado, fila original y SHA-256 del catálogo. La fecha mostrada es la publicada por SSN en tiempo local del centro de México, sin conversiones de zona horaria; se conservan también los valores UTC originales. La demo incluye solo esta capa filtrada, no los catálogos nacionales completos. Crédito visible: Servicio Sismológico Nacional (SSN), UNAM, DOI https://doi.org/10.21766/SSNMX/EC/MX . El aviso incluido en el CSV permite reproducción con fines no lucrativos y atribución; otros usos requieren permiso previo por escrito. No se presenta este catálogo como dominio público ni como licencia comercial irrestricta.

### Imágenes del catálogo completo

Para las imágenes lunares pendientes se utiliza también el servicio WMS oficial de USGS, capa `LROC_WAC`, documentado en https://stac.astrogeology.usgs.gov/docs/examples/to_qgis/ . La ficha específica https://astrogeology.usgs.gov/search/map/moon_lro_lroc_wac_global_morphology_mosaic_100m identifica el mosaico de junio de 2013, resolución original de 100 m/píxel, como «public domain» y solicita citar a los autores. Crédito: NASA/GSFC/Arizona State University; distribución USGS. Cada recorte conserva la solicitud WMS completa, sus coordenadas y la huella del archivo. Se reproyecta a una vista azimutal equidistante con el norte arriba. Las sombras y huecos de observación no se reconstruyen. La compresión WebP afecta únicamente a la imagen de visualización y no interviene en los cálculos científicos.

El enlace «Imagen» de cada fila permite solicitar un recorte para los 9,087 identificadores lunares y los 2,054 marcianos. Se genera al abrir la región y se guarda fuera del proyecto, en `%LOCALAPPDATA%/SpaceTerrainCache/<identificador-del-proyecto>/regiones_catalogo/`, para no activar la recarga automática de Live Server; no implica que las 11,141 imágenes estén descargadas ni que todas tengan observaciones completas. El servidor se inicia desde la raíz con `python recursos/scripts/servir_resultados.py --puerto 8000`. Live Server en el puerto 5500 consulta ese servicio en el mismo equipo, puerto 8000. Para acceso desde otra máquina se añade `--host 0.0.0.0`.

`imagenes_catalogo.py` valida el identificador contra el catálogo. La vista regional abarca el diámetro publicado más un 25 % de margen, con un mínimo de 12 km. Es una aproximación al encuadre, no un polígono oficial de límites: 4 lugares lunares y 127 marcianos no tienen diámetro y muestran un entorno de 12 km. La opción «Área de 12 km» permite comparar la misma extensión que la imagen del Tacaná.

Los recortes lunares proceden de los GeoTIFF de consulta del mosaico WAC de 100 m del archivo PDS, servido actualmente en `pds.mcp.nasa.gov`. Los de Marte proceden de las teselas CTX Beta01 del servicio USGS indicado arriba. Se mantienen las licencias y créditos de esas fuentes. No se utilizan imágenes generadas artificialmente. Cada PNG tiene un JSON con coordenadas, extensión, proyección, URLs de origen, resolución del nivel utilizado, licencia y SHA-256.

El procesamiento contempla los cambios de longitud 0/360 y −180/180, las teselas polares lunares y una proyección azimutal equidistante centrada en cada lugar. La salida de consulta es de 512 × 512 píxeles. Las regiones extensas usan niveles de menor detalle del mosaico; ampliar esa vista no agrega resolución. En los polos marcianos se reduce el nivel de detalle para abarcar la extensión sin truncarla.

La cobertura registrada corresponde a la máscara del ráster reproyectado, no certifica observaciones válidas de cada punto: los mosaicos pueden contener sombras o huecos originales. Para CTX se consideran ausentes los píxeles negros, lo cual también puede excluir sombras profundas. Los huecos detectados quedan transparentes y se muestra el porcentaje disponible; si no hay cobertura, aparece un aviso. La referencia y los créditos se conservan aunque la descarga sea local. Las imágenes no intervienen en el cálculo del índice de similitud ni modifican los resultados del ANOVA.

Esta revisión elimina las dos fuentes visuales que no tenían permiso claro para reutilización general: la fotografía terrestre de World Imagery y el recorte lunar obtenido por WMS. Sus reemplazos se integran en el comparador y en el proceso de actualización. No se han recalculado los índices de relieve, porque sus modelos de elevación no cambian.

No constituye una certificación de licencia de cada archivo histórico de temporal. Los CSV sísmicos de terceros, documentos previos y recursos ajenos a los conjuntos enumerados requieren revisión individual antes de redistribuir todo el directorio. La interfaz activa y las imágenes sustituidas deben distinguirse de ese archivo de trabajo. Tampoco se confunden las licencias de los datos con las licencias de las bibliotecas de software.

El servidor Python mantiene las URL públicas de las imágenes y reutiliza la caché histórica de `recursos/comparador_imagenes/regiones_catalogo/` en modo de lectura. Las nuevas teselas, imágenes y metadatos se escriben únicamente en la caché externa.


## Evaluación de reutilización y avisos conservados

Revisión documental: 15 de noviembre de 2026. Referencias presentadas según APA, 7.ª edición.

### Alcance y autorización de los datos NASA

Los datos NASA se consideran **autorizados para su uso en este proyecto**, conforme a lo declarado por su responsable. No constituyen un permiso pendiente de esta revisión. Se conservan sus referencias, identificadores y créditos para documentar la procedencia de los datos y reproducir los análisis.

La revisión de datos abiertos y condiciones de reutilización se centra en las fuentes ajenas a NASA. La autorización declarada para el proyecto no se extiende a materiales de terceros ni supone conceder una licencia abierta de redistribución sobre todos los archivos del repositorio.

### Resultado de la revisión

**El proyecto no puede describirse todavía como un conjunto íntegramente libre para cualquier uso y redistribución.** La mayor parte de los datos planetarios y las bibliotecas permiten reutilización, pero hay restricciones en el catálogo sísmico, condiciones específicas en los servicios cartográficos y archivos sin procedencia jurídica documentada.

En este documento, «libre» supone permiso para usar, modificar y redistribuir, incluido el uso comercial, sujeto a las condiciones de la licencia. Acceso gratuito, consulta pública y ausencia de una marca de copyright no bastan para establecer esos permisos. Una referencia APA reconoce la fuente, pero no sustituye una licencia.

La revisión comprende la aplicación, los datos y metadatos locales, los recursos históricos, las dependencias directas y la exportación de GitHub Pages. Se contrastan los avisos conservados con políticas oficiales. No constituye una certificación de cada píxel ni un análisis exhaustivo de todas las dependencias transitivas de los paquetes binarios.

### Datos, imágenes y cartografía

| Recurso y ubicación | Evaluación | Evidencia y condiciones |
| --- | --- | --- |
| LOLA, MOLA, Diviner, MCS y MODIS; manifiestos en `recursos/datos/nasa/` y `recursos/datos/tacana_temperatura/` | Autorizados para este proyecto | Autorización declarada por el responsable del proyecto. Se conservan identificadores de productos, etiquetas, fuentes y citas para trazabilidad científica. La política general NASA se incluye como referencia documental (NASA, s. f.). |
| Mapas derivados de NASA SVS, en `img/` | Dominio público salvo excepciones del producto | SVS permite descargar, utilizar y redistribuir su contenido, salvo indicación específica. Los derivados del proyecto conservan su procedencia en `img/mapas-fuentes.json` (NASA Scientific Visualization Studio, 2024). |
| Recortes lunares LROC PDS y mosaico WAC distribuido por USGS | Dominio público documentado | LROC distingue los productos del archivo PDS de las imágenes editoriales de su sitio. USGS identifica el mosaico WAC de junio de 2013 como dominio público y solicita citar a los autores. No se generaliza este permiso a todas las interfaces LROC (LROC Science Operations Center, s. f.; USGS, 2013). |
| Landsat 8 Collection 2 Level-2; `recursos/comparador_imagenes/tacana.jpg` y bandas originales | Reutilización y redistribución permitidas | USGS declara que sus datos Landsat pueden usarse y redistribuirse. Conservar el crédito USGS/NASA y el identificador de escena `LC08_L2SP_021050_20251126_02_T1`. Microsoft Planetary Computer actúa como distribuidor, no como autor de las observaciones (USGS, s. f.). |
| CTX Beta01; imágenes marcianas del servicio `OnMars/CTX1` | Permiso expreso de uso gratuito para todos los fines | Los metadatos del servicio conceden ese permiso para **Beta01** y piden crédito NASA/JPL/MSSS/The Murray Lab. El permiso del mosaico no garantiza disponibilidad ilimitada del servicio Esri ni se extrapola a otras versiones (Murray Lab, s. f.). |
| Copernicus DEM GLO-30; `recursos/datos/tacana_copernicus_glo30.tif` y derivados | Licencia gratuita amplia con obligaciones | La licencia GLO-30-F permite reproducción, distribución, comunicación y adaptación, sin una exclusión general del uso comercial. Exige atribución, aviso para derivados, exención de responsabilidad y ausencia de respaldo institucional implícito. No es CC0. La colección de Planetary Computer aparece como `proprietary`, remitiendo a una licencia específica; eso no significa que haya que pagar por estos usos (Copernicus Data Space Ecosystem, s. f.; European Space Agency, s. f.). |
| Sentinel-2 cloudless 2016, fondo del mapa | CC BY 4.0 para esa edición; servicio sujeto a condiciones | EOX permite aplicaciones comerciales con atribución para la edición 2016. Su endpoint público tiene uso razonable y restricciones de redistribución de teselas como conjunto independiente. Las ediciones posteriores tienen otras condiciones: no deben sustituirse como si compartieran la misma licencia (EOX IT Services, s. f.). |
| Mapterhorn, relieve servido al navegador | Datos abiertos con licencias por fuente | Su catálogo publica las atribuciones y licencias individuales; incluye GLO-30. La respuesta de una tesela no determina aquí qué fuentes contribuyen a cada píxel. Conservar la atribución Mapterhorn y el enlace a su catálogo; no etiquetar toda la cobertura como CC0 (Mapterhorn, s. f., s. f.). |
| Nombres y coordenadas IAU/USGS; `recursos/catalogo_regiones/` | Datos públicos de referencia | Conservar atribución IAU/USGS e identificadores. La política de USGS distingue sus datos de obras de terceros alojadas en sus páginas; no otorga permiso general sobre ilustraciones o publicaciones externas enlazadas por el catálogo (IAU & USGS, s. f.; USGS, s. f.). |
| NASA POWER y fichas planetarias NASA; `datos/luna_marte.json` y datos ambientales | Autorizados para este proyecto | Autorización declarada por el responsable del proyecto. Se conservan producto, fecha, unidades y documentación de las observaciones y valores de referencia (NASA, s. f.; NASA POWER Project, s. f.). |
| Catálogos SSN y `recursos/sismos/tacana.geojson` | **No libres para cualquier finalidad** | El pie del CSV autoriza reproducción con fines no lucrativos y atribución; para otros usos exige permiso previo por escrito. Filtrar 42 eventos no elimina esa condición. El aviso web no respondió durante esta revisión; la evidencia comprobada es el texto incluido en el archivo recibido (SSN, s. f.). |
| Ficha del Tacaná de Smithsonian/GVP; `datos/tacana.json` | **Tratamiento específico; no asumir CC0 para todo el sitio** | Los términos reconocen la base *Volcanoes of the World* como obra de empleados federales, pero contienen también reglas generales no comerciales y posibles derechos de terceros. Los hechos extraídos no equivalen a reutilizar fotografías o textos protegidos. Citar la base y distinguirla del contenido editorial; para una garantía de uso comercial irrestricto, documentar el alcance aplicable al extracto concreto (Global Volcanism Program, s. f.). |

#### Condiciones que deben acompañar al DEM del Tacaná

Los metadatos locales ya identifican el producto y su crédito. Para comunicar los derivados, conservar el aviso de atribución correspondiente:

> produced using Copernicus WorldDEM-30 © DLR e.V. 2010-2014 and © Airbus Defence and Space GmbH 2014-2018 provided under COPERNICUS by the European Union and ESA; all rights reserved

La licencia también exige informar a quienes reciban los datos de que las organizaciones responsables de Copernicus no asumen responsabilidad por el uso de Copernicus WorldDEM-30. No debe sugerirse aprobación de los resultados por esas organizaciones. Véanse los artículos 4 a 6 de la licencia citada.

### Archivos con documentación pendiente de derechos o procedencia

| Archivo o conjunto | Hallazgo | Qué falta |
| --- | --- | --- |
| `img/logo.png` | Imagen de identidad visual sin licencia o autor documentado en el proyecto | Identificar al titular y conservar autorización o licencia. |
| `img/pakal.png` | Logo de Pakal aportado como imagen; no se encontró una licencia de redistribución | La autorización para usarlo en esta web no equivale a una licencia abierta para cualquier tercero. Confirmar los derechos de autor y de marca pertinentes. |
| `recursos/datos/trekOBJ.zip`, su textura y derivados del visor inicial | Datos NASA de Marte, según la procedencia confirmada por el responsable del proyecto | Se aplica la autorización NASA declarada. El archivo contiene `model.obj`, `terrain.mtl` y `texture.png`; la URL e identificador de la exportación original no están registrados. Esta precisión documental no constituye un permiso pendiente. |
| JP2 iniciales `ldac_50s_3000m.jp2`, `ldec_80s_80m.jp2` y su duplicado; TIFF inicial `ldem_64.tif` | Pendiente de trazabilidad: los metadatos locales atribuyen el origen por coincidencia de nombre/formato o información aportada | Vincular cada archivo al producto oficial y a sus etiquetas o manifiestos. Para los productos NASA se aplica la autorización declarada; esta observación corresponde a la identificación del archivo, no a solicitar otra autorización. |
| `recursos/datos/ctx_source_page.html`, `recursos/lroc-wms.xml` y documentos de consulta guardados | Copias de documentación o catálogos de servicios | Conservar como evidencia local; la licencia del conjunto de datos no cubre necesariamente toda la página, sus imágenes o recursos enlazados. No están incluidos por defecto como páginas de la demo. |
| Código original de Tacaná Skylab | No hay una licencia de software propia declarada en la raíz | El titular debe elegir una licencia si desea conceder permisos abiertos sobre su código. Las licencias de las dependencias no licencian automáticamente el proyecto. No se asignó una licencia sin autorización. |

Los logos y los datos SSN sí forman parte de la aplicación activa. El ZIP y los insumos iniciales pertenecen al archivo de trabajo y al visor inicial; no son el origen de los recortes actuales del comparador de imágenes. Esta diferencia impide trasladar automáticamente una conclusión sobre la demo a todo el repositorio.

### Bibliotecas y herramientas

Se revisan las versiones enlazadas por la web, las licencias locales y los metadatos de los paquetes instalados. Las bibliotecas siguientes permiten usos comerciales y modificaciones bajo sus respectivas condiciones; deben conservarse sus avisos y los de los componentes que incorporan.

| Componente | Versión revisada | Licencia/evidencia |
| --- | --- | --- |
| Bootstrap | 6.0.0-alpha.1 | MIT; [licencia del paquete](https://cdn.jsdelivr.net/npm/bootstrap@6.0.0-alpha.1/LICENSE). |
| MapLibre GL JS | 6.18.0 | BSD-3-Clause; incluye avisos de componentes MIT/BSD; [licencias del paquete](https://unpkg.com/maplibre-gl@6.18.0/LICENSE.txt). |
| Three.js | 0.187.0 | MIT; `recursos/comparador_3d/vendor/LICENSE`. El visor inicial también incorpora Three.js. |
| Interestfor polyfill | 1.0.14, según la preparación del proyecto | BSD-3-Clause; `recursos/sismos/vendor/interestfor-LICENSE.txt`. |
| OddBird Popover polyfill | 0.7.3, según la preparación del proyecto | BSD-3-Clause; `recursos/sismos/vendor/popover-LICENSE.txt`. |
| NumPy | 2.5.1 | Metadatos instalados: BSD-3-Clause, 0BSD, MIT, Zlib y CC0-1.0 para los componentes incluidos. |
| SciPy | 1.18.0 | BSD; conservar también avisos de bibliotecas incluidas en su distribución binaria. |
| Pillow | 12.3.0 | MIT-CMU en los metadatos instalados. |
| Matplotlib | 3.11.2 | Licencia basada en PSF y avisos históricos. |
| Requests | 2.34.2 | Apache-2.0. |
| Rasterio | 1.5.2 | BSD-3-Clause; la distribución puede incorporar componentes nativos con avisos adicionales. |
| Tifffile | 2026.7.31 | BSD-3-Clause. |
| Beautiful Soup | 4.15.0 | MIT. |
| urllib3 | 2.7.0 | MIT. |
| Playwright | 1.65.2 | Apache-2.0 para el paquete; no constituye una licencia de redistribución de Microsoft Edge. |

Las herramientas Python se ejecutan localmente y no se incluyen en la demo estática. Los términos de alojamiento de jsDelivr, unpkg, Microsoft Planetary Computer o Esri son distintos de las licencias del código y de los datos que distribuyen. Microsoft Edge es una herramienta externa utilizada por las pruebas, no software libre redistribuido por el proyecto.

#### Ajustes efectuados en esta revisión

- El exportador conserva ahora los archivos sin extensión `LICENSE`, `COPYING` y `NOTICE`. Antes omitía la licencia de Three.js en el paquete estático.
- Se conserva una copia del permiso MIT junto al visor inicial: `recursos/vista_previa/THREE-LICENSE.txt`.
- Este documento se incluye en la exportación. No se han cambiado las mediciones, los resultados estadísticos ni las fuentes de los sismos.

### Condiciones pendientes para una distribución totalmente abierta

1. Sustituir el catálogo SSN por un conjunto que permita el uso previsto o conseguir autorización cuando el uso exceda el permiso no lucrativo.
2. Acreditar la licencia o autorización de los logos; si no puede acreditarse, excluirlos de una distribución presentada como completamente abierta.
3. Resolver la trazabilidad de los insumos iniciales sin etiqueta y documentar el alcance de uso de los datos GVP.
4. Conservar los créditos de EOX, Mapterhorn, Copernicus, USGS y las misiones NASA, además de las licencias del software distribuido.
5. Elegir una licencia para el código propio si se desea ofrecerlo como software de código abierto. Esa decisión no cambia las restricciones de datos de terceros.

La licencia regula permisos; no demuestra exactitud científica, cobertura completa, ausencia de errores ni aval institucional.

