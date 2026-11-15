# Instrucciones de trabajo

## Objetivo general

Desarrollar una aplicación web que integre y compare datos geoespaciales del volcán Tacaná, la Luna y Marte para explorar el potencial del Tacaná como terreno análogo para investigaciones relacionadas con la exploración espacial.

## Objetivos específicos

1. Recopilar y organizar datos geoespaciales del volcán Tacaná y de regiones de la Luna y Marte provenientes de fuentes oficiales.
2. Analizar la compatibilidad de los datos considerando su disponibilidad, resolución y variables.
3. Comparar las características de los terrenos mediante variables como elevación, pendiente y rugosidad superficial.
4. Estimar índices porcentuales de similitud que permitan identificar regiones con características comparables a las del Tacaná.
5. Presentar las semejanzas y diferencias mediante una interfaz web visual e interactiva que facilite su consulta por investigadores e ingenieros aeroespaciales.
6. Ampliar la información disponible del Tacaná y evaluar la consistencia de los resultados para fortalecer las comparaciones.

## Alcance y decisiones

- Comprender el objetivo, los requisitos y el comportamiento esperado antes de proponer cambios.
- Revisar el código, los datos y la documentación existentes antes de implementar una solución.
- Preguntar antes de realizar cambios no autorizados que afecten la lógica, las fórmulas, los criterios de selección, la interpretación de resultados o el comportamiento funcional. Explicar el efecto previsto y las alternativas.
- Continuar sin pedir otra confirmación cuando el cambio y su efecto ya estén autorizados. Resolver de forma autónoma ajustes de presentación que no alteren la lógica.
- Mantener los cambios dentro del alcance solicitado y señalar los supuestos que puedan afectar el resultado.

## Investigación y recopilación de información

- Utilizar datos abiertos y fuentes primarias confiables, preferentemente oficiales o académicas.
- Verificar las condiciones de uso y redistribución; distinguir acceso gratuito, licencia abierta y autorización específica. Respetar las autorizaciones ya establecidas para el proyecto.
- Registrar autor o institución, producto, versión, fecha, enlace, licencia y cobertura de cada fuente utilizada.
- Comprobar que la información responda a la pregunta de investigación y tenga resolución, actualidad y calidad suficientes.
- Contrastar afirmaciones relevantes y documentar discrepancias entre fuentes.
- Conservar los datos originales y registrar las transformaciones necesarias para reproducir su procesamiento.
- No inventar datos, referencias, permisos ni información que una fuente no proporciona.

## Análisis e interpretación de datos

- Definir las variables, unidades, población, muestras y criterios de inclusión antes de realizar el análisis.
- Revisar valores faltantes, duplicados, valores atípicos y errores de medición. No reemplazarlos ni excluirlos sin justificar el criterio.
- Comprobar la compatibilidad de escalas, períodos, resolución y referencias espaciales antes de comparar conjuntos.
- Elegir métodos adecuados a la pregunta y verificar sus supuestos, incluida la independencia de las observaciones cuando corresponda.
- Documentar las ecuaciones, parámetros, ponderaciones y decisiones metodológicas utilizadas.
- Distinguir observaciones, estimaciones, valores de referencia e indicadores elaborados por el proyecto.
- Interpretar los resultados considerando incertidumbre, tamaño del efecto, cobertura y limitaciones; no confundir asociación con causalidad ni significación estadística con relevancia práctica.
- Evaluar la sensibilidad a decisiones metodológicas relevantes y conservar la precisión durante los cálculos.
- Verificar resultados con casos conocidos o cálculos independientes cuando la complejidad o el impacto lo justifiquen.

## Codificación y diseño

- Preferir soluciones simples, legibles y coherentes con la arquitectura existente.
- Separar adquisición de datos, procesamiento, almacenamiento y presentación para facilitar mantenimiento y verificación.
- Usar nombres descriptivos, unidades explícitas y contratos claros entre funciones y módulos.
- Validar entradas y manejar errores sin ocultarlos ni sustituir resultados fallidos por valores aparentemente válidos.
- Evitar duplicación y dependencias innecesarias. Revisar mantenimiento, compatibilidad y licencia antes de incorporar una dependencia.
- Mantener accesibilidad, claridad visual y adaptación a distintos tamaños de pantalla.
- Proteger credenciales y datos sensibles; no incluir secretos en código, registros ni archivos publicados.

## Depuración y resolución de problemas

- Reproducir el fallo y distinguir el comportamiento observado del esperado antes de modificar el código.
- Revisar mensajes de error, entradas, estado de la aplicación y cambios relacionados para localizar la causa.
- Corregir la causa del problema con el menor cambio suficiente, evitando soluciones que solo oculten el síntoma.
- Si la corrección requiere cambiar el comportamiento esperado o la lógica del análisis, explicar el impacto y consultar cuando no esté autorizado.
- Verificar el caso que falla y los flujos relacionados; añadir una prueba de regresión cuando ayude a evitar que el problema reaparezca.
- Distinguir fallos del código, problemas de datos y limitaciones de servicios externos.
- Comunicar qué se corrigió, cómo se comprobó y qué limitaciones permanecen. No declarar resuelto un problema sin evidencia.

## Documentación y mantenimiento

- Documentar el propósito, el método, los requisitos y los pasos necesarios para reproducir el trabajo.
- Mantener las referencias en formato APA con enlaces a las fuentes originales y los avisos exigidos por sus licencias.
- Actualizar la documentación cuando cambien algoritmos, formatos de datos, dependencias o procedimientos de ejecución.
- Retirar código y archivos sin uso solo después de comprobar sus dependencias y referencias; preservar originales y evidencias necesarios para reproducibilidad.
- Comprobar las rutas, la carga de recursos y los resultados después de reorganizar archivos o preparar una publicación.
- Distinguir claramente lo implementado, lo verificado y lo pendiente.

## Reescritura de documentación

- Redactar y mantener el README únicamente en español, sin duplicar su contenido en otro idioma.
- Conservar los nombres oficiales de productos, los identificadores de código y los títulos originales de las obras citadas cuando sean necesarios para identificarlos correctamente.
- Al reescribir, preservar el significado técnico, las ecuaciones, los comandos y las referencias. No modificar la lógica del proyecto como parte de un ajuste de redacción.
- Mantener una estructura clara, eliminar repeticiones y comprobar que los enlaces internos correspondan a los encabezados actualizados.
