# Project Log

Registro cronologico del proyecto. Mantener append-only.

## [2026-07-05] Estructura inicial de trabajo

### Objetivo

Crear una estructura minima y fiel al second brain para empezar el proyecto sin modificar datasets.

### Cambios realizados

- Se creo `README.md`.
- Se creo `AGENTS.md`.
- Se creo `PROJECT_LOG.md`.
- Se creo `requirements.txt`.
- Se creo `notebooks/01_main_analysis.ipynb` como notebook principal inicial.
- Se crearon `data/processed/` y `reports/figures/` para salidas futuras.

### Decisiones

- Los datasets recibidos permanecen intactos en la raiz del proyecto.
- No se cargo, limpio, movio ni transformo ningun dataset.
- La primera fase sera exploratoria y lineal, centrada en entender columnas, claves, fechas, granularidad y calidad.

### Siguiente paso

Revisar `DescriptionDataCoSupplyChain.csv` y empezar el inventario de fuentes en `notebooks/01_main_analysis.ipynb`.
## [2026-07-05] Resumen inicial de datasets

### Objetivo

Crear un script en `proyecto.py` para inspeccionar los dos CSV principales sin usar el diccionario y sin modificar datos originales.

### Cambios realizados

- Se actualizo `proyecto.py` con funciones de lectura e inspeccion de CSV.
- Se genero `reports/data_overview_report.md` con resumen de `DataCoSupplyChainDataset.csv` y `tokenized_access_logs.csv`.
- El reporte incluye `head`, `info`, `describe`, tipos de datos, nulos, cardinalidad, duplicados, columnas posiblemente de fecha y valores frecuentes.

### Decisiones

- `DescriptionDataCoSupplyChain.csv` se excluyo del resumen porque funciona como diccionario de datos.
- Los CSV originales se leyeron en modo analitico y no se modificaron, movieron ni sobrescribieron.

### Siguiente paso

Leer el reporte y decidir la primera pregunta de analisis antes de limpiar o modelar.

## [2026-07-05] Head humano y lectura guiada

### Objetivo

Hacer que el resumen inicial sea legible para una persona, no solo una salida tecnica de pandas.

### Cambios realizados

- Se cambio `proyecto.py` para que el reporte agrupe columnas por tema.
- Se agrego una seccion de lectura del CSV: que representa cada fila y como interpretar los bloques principales.
- Se reemplazo el `.head()` gigante como lectura principal por un head compacto y un head vertical en formato ficha.
- Cada fila de muestra ahora se lee como campo, valor y explicacion inicial.

### Decision

Las explicaciones son una guia inicial basada en nombres de columnas y valores visibles. El diccionario puede usarse despues para confirmar significados concretos si hace falta.

## [2026-07-05] Limpieza inicial para modelado

### Objetivo

Crear datos procesados para poder trabajar mejor con modelos sin modificar los CSV originales.

### Cambios realizados

- Se convirtio `Type` en columnas booleanas one-hot: `payment_type_cash`, `payment_type_debit`, `payment_type_payment` y `payment_type_transfer`.
- Se parsearon `order date (DateOrders)` y `shipping date (DateOrders)` a datetime.
- Se crearon variables derivadas de entrega: `shipping_hours_from_dates`, `shipping_days_from_dates_exact` y `shipping_days_from_dates_floor`.
- Se crearon targets booleanos: `is_late_delivery`, `is_shipping_canceled`, `is_order_canceled`, `is_suspected_fraud`, `is_payment_problem` e `is_order_problem`.
- Se generaron `data/processed/dataco_supply_chain_processed.csv` y `data/processed/tokenized_access_logs_processed.csv`.
- Se genero `reports/cleaning_and_targets_report.md`.

### Hallazgos

- `Days for shipping (real)` y `Days for shipment (scheduled)` ya venian como enteros.
- Las fechas de pedido y envio venian como texto parseable a datetime, sin valores no parseados.
- No hay variable explicita de devoluciones, quejas, reclamaciones o refunds en los dos CSV analizados.
- `Late_delivery_risk` es el objetivo mas claro para un modelo de prediccion de pedidos problematicos.
- Hay 4.657 filas donde una diferencia real de 12 horas aparece como 1 dia en `Days for shipping (real)`; otras 5.080 filas de 12 horas aparecen como 0 dias. Conviene usar `shipping_hours_from_dates` para mayor precision.

### Cuidado de leakage

Para predecir retrasos antes del envio no usar como features `Delivery Status`, `shipping date (DateOrders)`, `shipping_datetime`, `Days for shipping (real)`, `shipping_hours_from_dates`, `shipping_days_from_dates_exact`, `shipping_days_from_dates_floor` ni `is_late_delivery`.

## [2026-07-05] Graficos EDA basicos para variables de modelo

### Objetivo

Crear graficos simples para identificar variables candidatas para modelos de ventas y de pedidos problematicos.

### Cambios realizados

- Se actualizo `proyecto.py` con una fase `basic_eda_charts()`.
- Se genero `reports/basic_eda_charts.md` como informe navegable de graficos.
- Se generaron graficos PNG en `reports/figures/basic_eda/`.
- Se creo `data/processed/product_sales_vs_web_views.csv` para comparar ventas por producto con visitas web por producto.

### Graficos creados

- Ventas por pais, producto, categoria, segmento, mercado, metodo de pago, modo de envio y mes.
- Beneficio por categoria.
- Distribucion de `Sales`.
- Descuento vs ventas.
- Correlaciones simples con `Sales` y con `is_late_delivery`.
- Tasa de retraso por modo de envio y por pais.
- Visitas web por departamento, categoria y hora.
- Comparacion entre share de ventas y share de visitas web por producto.

### Lectura inicial

- Para ventas parecen relevantes: pais, producto, categoria, segmento, mercado, mes, metodo de pago y senales web.
- Para retrasos parecen relevantes: modo de envio, pais/mercado y variables temporales disponibles antes del envio.
- Hay que evitar leakage en el modelo de retraso: no usar variables posteriores como `Delivery Status`, fecha real de envio ni duracion real de envio.

## [2026-07-05] Informe del problema de envio

### Objetivo

Analizar el problema de pedidos con retraso sin empezar todavia un modelo, porque la senal principal parece lineal y concentrada en la forma de envio.

### Cambios realizados

- Se creo `shipping_problem_report.py` como script reproducible para el informe logistico.
- Se genero `reports/shipping_problem_report.md`.
- Se generaron graficos criticos en `reports/figures/shipping_problem/`.

### Graficos creados

- Tasa de retraso por modo de envio.
- Error medio del sistema actual: dias reales menos dias prometidos.
- Distribucion del error por modo de envio.
- Paises criticos dentro de `First Class` y `Second Class`.
- Ciudades criticas dentro de `First Class` y `Second Class`.
- Tasa mensual de retraso en `First Class` y `Second Class`.

### Hallazgos

- `First Class` promete 1 dia y tarda 2 dias de media; el 95.32% aparece como retrasado y el sistema subestima el tiempo en el 100% de pedidos.
- `Second Class` promete 2 dias y tarda 3.99 dias de media; el 76.63% aparece como retrasado.
- El problema se mantiene por pais, ciudad y mes; no parece un caso aislado de una region o temporada.
- El sistema actual de dias prometidos parece deficiente, especialmente para `First Class` y `Second Class`.

### Siguiente paso

Evaluar si conviene crear un modelo de prediccion de llegada mas eficiente que use solo informacion disponible en el momento del pedido y evite leakage.

## [2026-07-05] Auditoria y formato presentacion del informe de envio

### Objetivo

Revisar graficos sospechosos del informe de envio y convertir el Markdown en un documento mas presentable, con graficos embebidos y secciones claras.

### Cambios realizados

- Se audito la diferencia entre retraso oficial (`Late_delivery_risk`) y promesa subestimada (`Days for shipping (real) > Days for shipment (scheduled)`).
- Se agrego el grafico `shipping_late_definition_comparison.png` para comparar ambas definiciones.
- Se explico por que la distribucion de error por modo de envio parece demasiado perfecta: el dataset tiene dias prometidos fijos por `Shipping Mode` y dias reales muy discretos.
- Se reescribio `reports/shipping_problem_report.md` como informe tipo presentacion, con portada, separadores, titulos grandes e imagenes embebidas.
- Se guardo el Markdown con UTF-8 BOM para mejorar compatibilidad con editores de Windows.

### Conclusion de auditoria

El grafico de distribucion no estaba mal calculado. La aparente perfeccion es una senal del propio dataset y del sistema actual: `First Class`, `Second Class`, `Same Day` y `Standard Class` usan promesas de dias muy rigidas. La diferencia entre 38.07% y 39.77% en `Standard Class` se debe a que una cifra usa la etiqueta oficial y la otra compara dias reales contra dias prometidos.

## [2026-07-05] Informe de envio convertido a R Markdown

### Objetivo

Convertir el informe principal de envio de `.md` a `.Rmd` para que pueda renderizarse como documento de proyecto con YAML, tabla de contenidos y graficos embebidos.

### Cambios realizados

- Se actualizo `shipping_problem_report.py` para generar `reports/shipping_problem_report.Rmd`.
- Se agrego cabecera YAML de R Markdown con salida `html_document`.
- Se agrego chunk `setup` de knitr.
- Se conservaron los graficos embebidos desde `reports/figures/shipping_problem/`.
- Se mantiene el `.md` anterior como copia historica, pero el informe principal pasa a ser `.Rmd`.

## [2026-07-05] Modelo de prediccion de llegada de paquetes

### Objetivo

Comparar el sistema actual de dias prometidos (`Days for shipment (scheduled)`) contra varios modelos para predecir `Days for shipping (real)`.

### Cambios realizados

- Se creo `shipping_arrival_model.py`.
- Se genero `reports/shipping_arrival_model_report.Rmd`.
- Se generaron metricas en `data/processed/shipping_arrival_model_metrics.csv`.
- Se guardaron predicciones de test en `data/processed/shipping_arrival_model_test_predictions.csv`.
- Se genero `data/processed/shipping_promise_compliance_test.csv`.
- Se generaron graficos en `reports/figures/shipping_model/`.

### Modelos probados

- Current system scheduled days.
- Baseline mean by Shipping Mode.
- Linear Regression.
- Ridge Regression.
- Lasso Regression.
- Random Forest.
- Extra Trees.
- Hist Gradient Boosting.
- Gradient Boosting.

`xgboost` no estaba instalado, asi que se usaron alternativas de gradient boosting de scikit-learn.

### Hallazgos

- El mejor modelo realista fue `Random Forest` con MAE 0.9615 dias.
- El sistema actual tiene MAE 1.2848 dias.
- La regla simple por `Shipping Mode` tiene MAE 0.9771 dias, casi igual que el mejor modelo.
- Esto confirma que el problema principal esta en la promesa base por tipo de envio, no necesariamente en falta de un modelo complejo.
- En test, `First Class` cumple 0.0% de su promesa, `Same Day` 46.71%, `Second Class` 20.35% y `Standard Class` 60.33%.

### Cuidado de leakage

Se retiro del modelo realista la fecha real de envio/llegada (`shipping_*`), porque esta ligada al target. El informe final usa fecha del pedido (`order_*`) y variables disponibles antes del resultado.

## [2026-07-05] Tuning Random Forest para llegada de paquetes

Se creo `random_forest_arrival_tuning.py` para centrarse solo en Random Forest y comparar varias configuraciones de hiperparametros contra el sistema actual y contra la media por `Shipping Mode`.

Cambios principales:

- Se reincorporo la fecha del pedido como variables `order_*`: ano, mes, dia, dia de semana, dia del ano, semana, trimestre, hora, fin de semana y codificacion ciclica.
- Se excluyo cualquier informacion posterior al pedido para evitar leakage: `shipping_*`, `shipping date (DateOrders)`, `Days for shipping (real)`, `Delivery Status`, `Late_delivery_risk` e `is_late_delivery`.
- Se evaluaron MAE, MSE, RMSE, R2, WAPE, MAPE y residuos.
- Se guardaron metricas, predicciones, residuos, importancia de variables y graficos en `data/processed/` y `reports/figures/random_forest_arrival/`.
- Se genero `reports/random_forest_arrival_tuning_report.Rmd`.

Resultados destacados:

- Mejor modelo: `RF_base_previous`.
- Test RF: MAE 0.9617, MSE 1.5866, RMSE 1.2596, R2 0.3923, WAPE 0.2751, MAPE 0.3073.
- Sistema actual: MAE 1.2848, MSE 2.5322, RMSE 1.5913, R2 0.0302, WAPE 0.3675, MAPE 0.4214.
- Baseline media por `Shipping Mode`: MAE 0.9771, MSE 1.5981, RMSE 1.2642, R2 0.3879, WAPE 0.2795, MAPE 0.3203.
- Los modelos mas profundos sobreaprenden train pero no mejoran test. `RF_deep_leaf2` baja a MAE 0.3517 en train, pero queda en MAE 0.9686 en test.
- `Shipping Mode` domina la importancia de variables (~0.736), seguido por hora del pedido, ciudad, dia, estado y dia del ano.

Siguiente propuesta:

- Probar lags y rollings historicos sin leakage usando `shift(1)`, por ejemplo media movil de dias reales por `Shipping Mode`, pais, ciudad, categoria y combinaciones modo-pais o modo-ciudad.

## [2026-07-05] Random Forest con lags y rollings por tipo de envio

Se creo `random_forest_arrival_lag_rolling.py` para volver a probar el mejor Random Forest anterior agregando historicos por `Shipping Mode`.

Cuidado de leakage:

- Los historicos no usan el resultado del pedido actual.
- Para cada pedido se usan solo envios del mismo `Shipping Mode` con `shipping_datetime` anterior al `order_datetime` del pedido actual.
- Esto evita usar pedidos que fueron ordenados antes pero que todavia no habrian terminado en el momento de hacer la prediccion.

Variables historicas probadas:

- lag del ultimo envio completado del mismo tipo.
- medias rolling de los ultimos 7, 30 y 100 envios completados.
- desviacion de los ultimos 30 envios completados.
- tasa historica de promesa subestimada.
- medias y volumenes de envios completados en los ultimos 7/30 dias.
- volumen de pedidos recibidos del mismo tipo en los ultimos 7/30/90 dias.

Artefactos generados:

- `reports/random_forest_arrival_lag_rolling_report.Rmd`.
- `data/processed/random_forest_arrival_lag_rolling_metrics.csv`.
- `data/processed/random_forest_arrival_lag_rolling_predictions.csv`.
- `data/processed/random_forest_arrival_lag_rolling_residuals.csv`.
- `data/processed/random_forest_arrival_lag_rolling_feature_importance.csv`.
- `data/processed/random_forest_arrival_lag_rolling_feature_coverage.csv`.
- Graficos en `reports/figures/random_forest_arrival_lag_rolling/`.

Resultados:

- RF con lags/rollings: MAE 0.9338, MSE 1.5601, RMSE 1.2491, R2 0.4025, WAPE 0.2671, MAPE 0.2932.
- RF sin historico anterior: MAE 0.9617, RMSE 1.2596, R2 0.3923.
- Baseline media por `Shipping Mode`: MAE 0.9771, RMSE 1.2642, R2 0.3879.
- Sistema actual: MAE 1.2848, RMSE 1.5913, R2 0.0302.

Conclusion:

Los lags y rollings si aportan senal, pero la mejora frente al baseline simple por tipo de envio es pequena: alrededor de 0.0433 dias de MAE, aproximadamente 1 hora de error medio por pedido. El resultado apoya que, con estos datos, la recomendacion principal sea actualizar la promesa/base por `Shipping Mode`. El modelo queda como mejora secundaria, no como necesidad principal.

## [2026-07-05] Informe empresarial de recomendacion de envios

Se edito `reports/random_forest_arrival_lag_rolling_report.Rmd` para convertirlo en un informe de exposicion empresarial.

Cambios principales:

- Se retiro la explicacion tecnica extensa sobre lags, rollings y leakage del cuerpo principal del informe.
- Se centro la narrativa en la decision de negocio: el modelo no vale la pena como primera solucion y lo mejor es actualizar un baseline por `Shipping Mode`.
- Se agrego una comparacion comercial entre sistema actual, baseline por tipo de envio y Random Forest con historicos.
- Se calculo que el baseline reduce el MAE de 1.2848 a 0.9771 dias, una mejora aproximada del 24% frente al sistema actual.
- Se calculo que las promesas incumplidas bajarian de 103.400 a 56.886 pedidos, es decir 46.514 pedidos dejarian de incumplir la promesa comunicada.
- Se aclaro que esto no hace que los paquetes lleguen antes: reduce sobrepromesa. El foco real debe ser arreglar los envios, especialmente First Class, Second Class y la dispersion de Standard Class.

Artefactos nuevos:

- `shipping_business_recommendation.py`.
- `data/processed/shipping_business_baseline_comparison.csv`.
- `reports/figures/shipping_business/shipping_business_mae_comparison.png`.
- `reports/figures/shipping_business/shipping_business_broken_promises_total.png`.
- `reports/figures/shipping_business/shipping_business_broken_promises_by_mode.png`.

## [2026-07-05] Pulido del informe empresarial de envios

Se reviso `reports/random_forest_arrival_lag_rolling_report.Rmd` para eliminar frases meta orientadas a explicar como presentar el informe.

Cambios:

- El informe habla directamente a la empresa y presenta recomendaciones operativas.
- Se elimino lenguaje como "vender este problema", "historia correcta" o formulas similares.
- Se retiro del informe la aclaracion didactica de baseline para mantener el documento centrado en la recomendacion empresarial.
- Se mantuvo la conclusion: la promesa base por tipo de envio es la accion inicial recomendada; el modelo queda como opcion secundaria.


## [2026-07-05] EDA de variables para modelo de ventas

Se creo `sales_feature_eda.py` para volver al problema principal del proyecto: preparar variables candidatas para un futuro modelo de ventas.

Objetivo:

- Revisar variables reales disponibles antes de modelar `Sales`.
- Crear variables derivadas utiles sin modificar los CSV raw.
- Generar graficos de barras en un informe R Markdown.

Variables revisadas:

- ventas por comprador: `Customer Id`, `Order Customer Id`, `Customer Segment`.
- geografia: `Order Country`, `Order City`, `Order Region`, `Order State`, `Market`, `Customer Country`, `Customer City`.
- fecha: `order_datetime`, mes cronologico, mes del anio, dia de la semana, fin de semana.
- festivos: marca derivada aproximada desde fecha de pedido; no existe calendario oficial por pais en el dataset.
- ofertas/descuentos: `Order Item Discount`, `Order Item Discount Rate`, `has_discount`, rangos de descuento.
- producto: `Product Name`, `Category Name`, `Department Name`.
- precio/cantidad/margen: `Order Item Product Price`, `Order Item Quantity`, `Order Item Profit Ratio`.
- metodo de pago: variables `payment_type_*` convertidas a etiqueta legible.
- visitas web por producto: tabla agregada `product_sales_vs_web_views.csv`.

Variables no disponibles:

- No hay columna explicita de campanas de marketing, por lo que no se uso como variable del modelo.
- No hay festivos oficiales por pais, stock, inventario, coste publicitario, distancia de envio ni canal real de adquisicion.

Artefactos generados:

- `reports/sales_feature_eda_report.Rmd`.
- `reports/figures/sales_feature_eda/` con 28 graficos de barras.
- `data/processed/sales_feature_eda_dataset.csv`.
- `data/processed/sales_variable_availability_audit.csv`.
- `data/processed/sales_feature_eda_aggregates.csv`.

Notas:

- Los graficos temporales se corrigieron para aparecer en orden natural/cronologico, no ordenados por ventas.
- Los datasets raw originales permanecen intactos.

## [2026-07-06] Comparacion inicial de modelos de ventas sin lags

Se creo `sales_model_comparison.py` para entrenar modelos de prediccion de `Sales` sin lags ni rollings.

Modelos comparados:

- Baseline global mean.
- Baseline mean by Product.
- Linear Regression.
- Lasso.
- Decision Tree.
- Random Forest.
- Hist Gradient Boosting.

Variables usadas:

- geografia: pais, region, estado, ciudad, mercado y geografia de cliente;
- comprador: `Customer Id`, `Customer Segment`;
- producto: `Product Name`, `Category Name`, `Department Name`;
- precio/cantidad: `Order Item Product Price`, `Order Item Quantity`;
- descuentos/ofertas: `Order Item Discount`, `Order Item Discount Rate`, `has_discount`;
- calendario: fecha de pedido, mes, dia de semana, hora, fin de semana, festivo generico y periodo comercial derivado.

Cuidado de leakage:

- Se excluyeron `Sales per customer`, `Order Item Total`, beneficios/profit, estados posteriores, targets de retraso/cancelacion/fraude y metodo de pago.
- El metodo de pago queda fuera porque no se conoce antes de completar la compra.
- No se usaron lags ni rollings.

Resultados en test:

- Mejor modelo: Linear Regression.
- Linear Regression: MAE 20.0734, MSE 1239.1250, RMSE 35.2012, R2 0.9665, WAPE 0.0869, MAPE 0.1485.
- Lasso: MAE 20.0857, RMSE 35.2042, R2 0.9665.
- Random Forest: MAE 29.4710, RMSE 139.8455, R2 0.4711.
- Hist Gradient Boosting: MAE 31.6392, RMSE 144.9575, R2 0.4317.
- Decision Tree: MAE 32.6908, RMSE 145.3411, R2 0.4287.
- Baseline por producto: MAE 81.6731.
- Baseline global: MAE 116.0065.

Conclusion:

La relacion dominante es casi lineal porque `Sales` depende directamente de precio, cantidad y descuento. Linear Regression y Lasso superan a los arboles. Los modelos de arbol aprenden casi perfecto en train pero generalizan peor, senal de sobreajuste. El siguiente paso razonable es probar lags/rollings historicos por producto, categoria, pais/ciudad y comprador, siempre comparando contra el baseline por producto.

Artefactos generados:

- `reports/sales_model_comparison_report.Rmd`.
- `reports/figures/sales_model/`.
- `data/processed/sales_model_comparison_metrics.csv`.
- `data/processed/sales_model_comparison_predictions.csv`.
- `data/processed/sales_model_comparison_residuals.csv`.
- `data/processed/sales_model_feature_importance.csv`.
- `data/processed/sales_model_feature_audit.csv`.
## [2026-07-06] Modelo de ventas con lags y rollings

Se creo `sales_model_lag_rolling.py` para comprobar leakage, tipos de variables y el impacto de lags/rollings sobre el modelo de prediccion de `Sales`.

Comprobaciones:

- `order_datetime` se parsea como datetime dentro del script.
- `Order Item Quantity` queda como entero y `Sales` como float.
- El metodo de pago esta como booleanos one-hot en el dataset procesado, pero queda excluido del modelo porque no se conoce antes de completar la compra.
- Se excluyen por leakage `Sales per customer`, `Order Item Total`, beneficios/profit, estados posteriores, targets de envio/problema, `Type` y `payment_type_*`.
- Las categoricas se codifican dentro del pipeline con `OrdinalEncoder`; no se modifican los CSV raw.

Features historicas:

- Lags diarios exactos de 1, 7, 30 y 365 dias, equivalentes a 24, 168, 720 y 8760 horas.
- Rollings de 7 dias y 30 dias con `shift(1)` para evitar que el dia actual entre en su propio historico.
- Historicos por ventas globales, producto, categoria, pais y comprador.

Resultados en test:

- Mejor modelo con historicos: Lasso with lags, MAE 22.7814, MSE 1508.1668, RMSE 38.8351, R2 0.9592, WAPE 0.0987 y MAPE 0.1425.
- Linear Regression with lags: MAE 22.7853, RMSE 38.8510 y R2 0.9592.
- Random Forest with lags: MAE 29.1814, RMSE 139.0730 y R2 0.4769.
- Mejor modelo anterior sin lags: Linear Regression, MAE 20.0734, RMSE 35.2012 y R2 0.9665.

Conclusion:

Los lags y rollings no mejoran el mejor modelo anterior; lo empeoran en 2.7080 MAE frente a Linear Regression sin lags. Para `Sales` por linea, lo mas solido sigue siendo Linear Regression/Lasso sin historicos.

Artefactos generados:

- `reports/sales_model_lag_rolling_report.Rmd`.
- `reports/figures/sales_model_lag_rolling/`.
- `data/processed/sales_model_lag_rolling_metrics.csv`.
- `data/processed/sales_model_lag_rolling_predictions.csv`.
- `data/processed/sales_model_lag_rolling_residuals.csv`.
- `data/processed/sales_model_lag_rolling_feature_importance.csv`.
- `data/processed/sales_model_lag_rolling_audit.csv`.
## [2026-07-06] Walk-forward validation del modelo lineal de ventas

Se creo `sales_linear_walk_forward.py` para validar `Linear Regression` con un esquema temporal mas cercano a produccion.

Esquema de validacion:

- Entrenamiento inicial con 12 meses: 2015-01 a 2015-12.
- Test mensual desde 2016-01 hasta 2018-01.
- Ventana expansiva: cada mes probado se incorpora al entrenamiento antes de predecir el siguiente mes.
- Total: 25 folds mensuales y 117.869 filas evaluadas fuera de muestra.

Modelo y variables:

- Modelo: `Linear Regression`.
- Variables: geografia, comprador, producto, precio/cantidad, descuentos/ofertas y calendario.
- Categoricas: `OneHotEncoder` dentro del pipeline, con categorias infrecuentes agrupadas y categorias nuevas controladas.
- Numericas: imputacion y escalado.
- Metodo de pago excluido porque no se conoce antes de completar compra.
- Excluidas por leakage: `Sales per customer`, `Order Item Total`, beneficios/profit, estados posteriores, targets de envio/problema, `Type` y `payment_type_*`.

Resultados globales fuera de muestra:

- MAE ponderado: 11.4120.
- MSE ponderado: 434.4888.
- RMSE global: 20.8444.
- R2 global: 0.9785.
- WAPE global: 0.0550.
- MAPE global: 0.0955.

Lectura:

- El modelo mantiene buen rendimiento al avanzar mes a mes con informacion historica disponible hasta cada corte.
- El peor mes fue 2017-10, con MAE 21.8736; coincide con la parte final del dataset, donde el volumen mensual cae bastante.
- La comparacion con el split anterior sirve como referencia, pero no es una comparacion de una sola variable: esta validacion usa OneHotEncoder, mas adecuado para categoricas en regresion lineal, mientras el primer pipeline usaba el encoding original.
- Para `Sales` por linea, el modelo depende principalmente de precio, cantidad y descuento.

Artefactos generados:

- `reports/sales_linear_walk_forward_report.Rmd`.
- `reports/figures/sales_linear_walk_forward/`.
- `data/processed/sales_linear_walk_forward_metrics.csv`.
- `data/processed/sales_linear_walk_forward_summary.csv`.
- `data/processed/sales_linear_walk_forward_predictions.csv`.
- `data/processed/sales_linear_walk_forward_residuals.csv`.
- `data/processed/sales_linear_walk_forward_audit.csv`.
- `data/processed/sales_linear_walk_forward_coefficients.csv`.
## [2026-07-06] Degradacion temporal del modelo lineal sin reentrenar

Aclaracion: en la walk-forward validation anterior el modelo si se reentrenaba en cada mes. Cada fold hacia un nuevo `fit()` con una ventana expansiva: 2015, luego 2015 + 2016-01, luego 2015 + 2016-01 + 2016-02, y asi sucesivamente.

Para probar el caso contrario, se creo `sales_linear_static_temporal_decay.py`.

Esquema:

- Entrenamiento unico con 2015-01 a 2015-12.
- Prediccion mensual de 2016-01 a 2018-01 sin volver a entrenar.
- Mismo pipeline que la walk-forward validation: `Linear Regression`, `OneHotEncoder` para categoricas, imputacion/escalado de numericas y mismas exclusiones por leakage.
- Comparacion directa contra `sales_linear_walk_forward_metrics.csv`.

Resultados globales fuera de muestra:

- Modelo congelado: MAE 12.6116, MSE 551.7390, RMSE 23.4891, R2 0.9727, WAPE 0.0608 y MAPE 0.1085.
- Modelo reentrenado mensual: MAE 11.4120, MSE 434.4888, RMSE 20.8444, R2 0.9785, WAPE 0.0550 y MAPE 0.0955.
- Ejecucion sin reentrenar: alrededor de 13 segundos.
- Walk-forward con reentrenamiento mensual: alrededor de 214 segundos.

Degradacion:

- El modelo congelado aguanta 16 meses sin degradacion clara frente al reentrenamiento mensual.
- La primera degradacion clara aparece en 2017-05, 17 meses despues del corte de entrenamiento, con gap de MAE 2.3029 y ratio 1.1969 frente al reentrenado.
- Desde 2017-10 la separacion se vuelve fuerte.
- El peor gap aparece en 2017-12, con 11.7257 puntos de MAE por encima del modelo reentrenado.

Lectura operativa:

No parece necesario reentrenar cada mes para `Sales` por linea, porque el modelo aguanta bastante mientras la relacion precio-cantidad-descuento no cambie. Pero dejarlo congelado indefinidamente si degrada. Con estos datos, tiene mas sentido proponer reentrenamiento periodico anual o activado por cambios de volumen/mix que reentrenamiento mensual obligatorio.

Artefactos generados:

- `reports/sales_linear_static_decay_report.Rmd`.
- `reports/figures/sales_linear_static_decay/`.
- `data/processed/sales_linear_static_decay_metrics.csv`.
- `data/processed/sales_linear_static_decay_summary.csv`.
- `data/processed/sales_linear_static_decay_predictions.csv`.
- `data/processed/sales_linear_static_decay_residuals.csv`.
- `data/processed/sales_linear_static_vs_walk_forward.csv`.
- `data/processed/sales_linear_static_decay_audit.csv`.
## [2026-07-06] Forecast de demanda diaria por producto

Objetivo:

- Target: `quantity_sold`.
- Definicion: suma diaria de `Order Item Quantity` por `Product Name`.
- Unidad de analisis: producto-dia.
- Se incluyen todos los productos en todos los dias del rango historico; si no hubo venta, el target es `0`.

Validez temporal:

- Excluidas como variables directas: `Sales`, `Order Item Product Price`, `Order Item Quantity`, `Order Item Discount`, `Order Item Discount Rate`, `Order Item Total` y derivados de la linea actual.
- Precio, ventas, descuentos y cantidad solo entran como lags o rollings historicos desplazados.
- Los rollings usan `shift(1)`, por lo que el dia actual no entra en su propio historico.
- Split temporal: train antes de 2017-01-01 y test desde 2017-01-01.
- Los CSV raw permanecen intactos.

Modelos comparados:

- Baseline global train mean.
- Baseline product train mean.
- Baseline lag 1d by Product.
- Baseline rolling 7d by Product.
- Baseline rolling 30d by Product.
- Linear Regression.
- Lasso.
- Decision Tree.
- Random Forest.
- Hist Gradient Boosting.

Resultados en test:

- Mejor resultado global: `Baseline rolling 7d by Product`, MAE 0.9972, RMSE 4.3736, R2 0.8207 y WAPE 0.4305.
- `Baseline lag 1d by Product`: MAE 1.0017, RMSE 4.3578, R2 0.8220 y WAPE 0.4324.
- `Baseline rolling 30d by Product`: MAE 1.1305, RMSE 4.6521, R2 0.7971 y WAPE 0.4880.
- Mejor modelo ML: `Decision Tree`, MAE 1.4122, RMSE 4.8393, R2 0.7805 y WAPE 0.6096.
- Random Forest: MAE 1.5462, RMSE 4.4716, R2 0.8126 y WAPE 0.6674.
- Hist Gradient Boosting: MAE 1.5045, RMSE 4.4824, R2 0.8117 y WAPE 0.6495.

Conclusion:

Los modelos complejos no superan al baseline historico. Para demanda diaria producto-dia, la referencia principal debe ser `Baseline rolling 7d by Product`. El siguiente paso recomendable es probar agregacion semanal, forecast por categoria/producto importante o incorporar senales externas/planificadas como stock, campanas o promociones reales.

Correccion pendiente completada:

- Se pulio `reports/daily_product_quantity_forecast_report.Rmd` para dejar claro que el ganador global es el baseline historico y que el mejor modelo ML queda por detras.
- El script `daily_product_quantity_forecast.py` tambien quedo actualizado para regenerar esa lectura correctamente en futuras ejecuciones.

Artefactos generados:

- `daily_product_quantity_forecast.py`.
- `reports/daily_product_quantity_forecast_report.Rmd`.
- `reports/figures/daily_product_quantity_forecast/`.
- `data/processed/daily_product_quantity_forecast_dataset.csv`.
- `data/processed/daily_product_quantity_forecast_metrics.csv`.
- `data/processed/daily_product_quantity_forecast_predictions.csv`.
- `data/processed/daily_product_quantity_forecast_residuals.csv`.
- `data/processed/daily_product_quantity_forecast_feature_audit.csv`.
- `data/processed/daily_product_quantity_forecast_feature_importance.csv`.
## [2026-07-06] Informe empresarial final de demanda

Se creo `demand_business_recommendation.py` para generar el informe final de demanda en formato R Markdown.

Objetivo:

- Presentar a la empresa una recomendacion clara sobre forecast diario de unidades vendidas por producto.
- Mantener la misma estructura del informe empresarial de envios/retrasos.
- Evitar graficos y explicaciones innecesarias.
- Hablar directamente en terminos comerciales y operativos.

Informe generado:

- `reports/demand_business_recommendation_report.Rmd`.
- Graficos en `reports/figures/demand_business/`.

Graficos incluidos:

- `demand_business_mae.png`: error medio por producto-dia.
- `demand_business_wape.png`: error relativo total sobre unidades vendidas.
- `demand_business_monthly_demand.png`: demanda mensual real vs referencia recomendada.

Decision principal:

- Usar `Baseline rolling 7d by Product` como referencia inicial para planificar demanda diaria.
- No presentar los modelos ML como solucion principal, porque no superan al baseline historico.

Resultados usados:

- Baseline rolling 7d por producto: MAE 0.9972, RMSE 4.3736, R2 0.8207 y WAPE 0.4305.
- Mejor modelo ML: Decision Tree, MAE 1.4122, RMSE 4.8393, R2 0.7805 y WAPE 0.6096.
- El mejor modelo ML queda 0.4149 unidades de MAE por encima del baseline, alrededor de 41.6% mas error.

Conclusion empresarial:

La referencia historica de 7 dias por producto es la mejor opcion actual por precision, simplicidad y mantenimiento. Para justificar modelos mas complejos hacen falta senales adicionales de negocio: stock, promociones planificadas, campanas, precio futuro, trafico web futuro o calendario comercial detallado.

## [2026-07-06] Cierre y preparacion para GitHub

Se ordeno el proyecto para subirlo a GitHub sin modificar ni mover los datasets originales.

Cambios realizados:

- `README.md` actualizado como README final del proyecto.
- `.gitignore` creado para excluir CSV raw, CSV procesados pesados, HTML renderizados, caches y entornos locales.
- `data/README.md`, `data/processed/README.md` y `reports/README.md` actualizados para explicar la estructura.
- Los informes `.Rmd` quedan como entregables principales.
- Los archivos `.html` y los CSV derivados se consideran regenerables.

Decision de versionado:

- No subir los CSV originales por tamano y buenas practicas.
- No subir `data/processed/*.csv` porque se regeneran desde los scripts.
- Mantener scripts, informes `.Rmd`, figuras y documentacion como base del repositorio.

