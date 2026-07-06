# DataCo Supply Chain Analytics

Proyecto de analisis y modelado sobre el dataset DataCo Supply Chain. El trabajo se centra en dos decisiones de negocio:

- mejorar la promesa de entrega al cliente;
- estimar la demanda diaria por producto para apoyar la planificacion.

## Conclusiones Principales

### 1. Envios

El sistema actual promete plazos demasiado optimistas en algunos modos de envio.

La recomendacion empresarial es actualizar la promesa base por `Shipping Mode` antes de implantar un modelo complejo:

- el sistema actual tiene MAE de `1.2848` dias;
- una promesa base por tipo de envio baja a MAE `0.9771`;
- Random Forest con historicos baja a MAE `0.9338`, pero solo mejora unas 1 hora media frente al baseline;
- la prioridad real es corregir promesas y operacion logistica, no solo predecir mejor el retraso.

Informe principal:

- `reports/random_forest_arrival_lag_rolling_report.Rmd`

### 2. Ventas y Demanda

El analisis comercial se centra en anticipar las unidades que se venderan cada dia para cada producto:

```text
target = cantidad vendida diaria por producto
```

Resultado:

- el mejor resultado global fue `Baseline rolling 7d by Product`;
- MAE `0.9972`, RMSE `4.3736`, R2 `0.8207`, WAPE `0.4305`;
- el mejor modelo ML (`Decision Tree`) queda peor: MAE `1.4122`;
- con los datos actuales, una regla historica simple supera a los modelos complejos.

Informe principal:

- `reports/demand_business_recommendation_report.Rmd`

## Recomendacion Final

Para la empresa:

1. Actualizar promesas de entrega por tipo de envio.
2. Usar rolling 7 dias por producto como referencia inicial de demanda diaria.
3. No presentar modelos complejos como solucion principal si no superan al baseline.
4. Incorporar datos de negocio adicionales antes de volver a modelar demanda: stock, promociones planificadas, campanas, precio futuro, trafico web futuro, festivos por pais y eventos comerciales.

## Estructura

```text
.
|-- README.md
|-- AGENTS.md
|-- PROJECT_LOG.md
|-- requirements.txt
|-- proyecto.py
|-- shipping_problem_report.py
|-- shipping_arrival_model.py
|-- random_forest_arrival_tuning.py
|-- random_forest_arrival_lag_rolling.py
|-- shipping_business_recommendation.py
|-- sales_feature_eda.py
|-- sales_model_comparison.py
|-- sales_model_lag_rolling.py
|-- sales_linear_walk_forward.py
|-- sales_linear_static_temporal_decay.py
|-- daily_product_quantity_forecast.py
|-- demand_business_recommendation.py
|-- data/
|   |-- README.md
|   `-- processed/
|-- notebooks/
|   `-- 01_main_analysis.ipynb
`-- reports/
    |-- *.Rmd
    |-- README.md
    `-- figures/
```

## Datos

Los CSV originales no se incluyen en el repo por tamano y por buenas practicas de versionado.

Para reproducir el proyecto, coloca estos archivos en la raiz del proyecto:

```text
DataCoSupplyChainDataset.csv
DescriptionDataCoSupplyChain.csv
tokenized_access_logs.csv
```

Los archivos derivados de `data/processed/` tambien se excluyen de GitHub porque se pueden regenerar y varios pesan decenas o cientos de MB.

## Instalacion

```bash
python -m pip install -r requirements.txt
```

## Ejecucion Recomendada

Flujo principal:

```bash
python proyecto.py
python shipping_problem_report.py
python shipping_arrival_model.py
python random_forest_arrival_tuning.py
python random_forest_arrival_lag_rolling.py
python shipping_business_recommendation.py
python sales_feature_eda.py
python sales_model_comparison.py
python sales_model_lag_rolling.py
python sales_linear_walk_forward.py
python sales_linear_static_temporal_decay.py
python daily_product_quantity_forecast.py
python demand_business_recommendation.py
```

Los informes R Markdown (`.Rmd`) quedan en `reports/`.

## Informes Clave

- `reports/random_forest_arrival_lag_rolling_report.Rmd`: recomendacion empresarial de envios.
- `reports/demand_business_recommendation_report.Rmd`: recomendacion empresarial de demanda.
- `reports/daily_product_quantity_forecast_report.Rmd`: comparacion tecnica de modelos de demanda.

## Notas de Modelado

- Los CSV raw se tratan como inmutables.
- Los lags y rollings se calculan con informacion pasada (`shift(1)`), evitando que el dia actual entre en su propio historico.
- Las validaciones relevantes son temporales, no aleatorias.
- Los baselines se comparan siempre contra modelos complejos antes de recomendar ML.

## Estado del Proyecto

Proyecto cerrado como entrega analitica. La recomendacion final es operativa y conservadora: usar reglas simples cuando superan a modelos complejos, y solicitar mas datos de negocio antes de escalar a un sistema predictivo mas avanzado.
