# Graficos basicos para elegir variables


Estos graficos se generan desde `proyecto.py` usando los datos procesados. Son exploratorios: ayudan a elegir variables candidatas, no prueban causalidad.

## Reglas para leerlos

- Para modelo de ventas: mirar pais, producto, categoria, segmento, mercado, mes, metodo de pago y senales web.

- Para modelo de retraso/pedido problematico: mirar modo de envio, pais, mercado, fecha/hora y variables disponibles antes del envio.

- Evitar leakage: no usar variables que ocurren despues del resultado que se quiere predecir.

## Graficos

### Ventas por pais

Muestra si el pais tiene senal fuerte para ventas y demanda.

![Ventas por pais](figures/basic_eda/sales_by_order_country_top15.png)

### Ventas por producto

Ayuda a ver productos dominantes y posible concentracion de demanda.

![Ventas por producto](figures/basic_eda/sales_by_product_top15.png)

### Ventas por categoria

Las categorias suelen ser buenas features por capturar familias de producto.

![Ventas por categoria](figures/basic_eda/sales_by_category_top15.png)

### Ventas por segmento

Permite ver si Consumer, Corporate o Home Office tienen comportamientos diferentes.

![Ventas por segmento](figures/basic_eda/sales_by_customer_segment.png)

### Ventas por mercado

Resume diferencias regionales de demanda.

![Ventas por mercado](figures/basic_eda/sales_by_market.png)

### Ventas por metodo de pago

Sirve para ver si el metodo de pago acompana patrones de compra sin codificarlo ordinalmente.

![Ventas por metodo de pago](figures/basic_eda/sales_by_payment_type.png)

### Ventas por modo de envio

Puede aportar senal en demanda y en riesgo logistico.

![Ventas por modo de envio](figures/basic_eda/sales_by_shipping_mode.png)

### Retraso por modo de envio

Muy relevante para un modelo de retraso, siempre cuidando no usar variables posteriores al evento.

![Retraso por modo de envio](figures/basic_eda/late_rate_by_shipping_mode.png)

### Retraso por pais

Ayuda a detectar geografia con riesgo logistico alto.

![Retraso por pais](figures/basic_eda/late_rate_by_order_country_top15_volume.png)

### Beneficio por categoria

No todo lo que vende mucho es lo que mas aporta margen; este grafico separa volumen de valor.

![Beneficio por categoria](figures/basic_eda/profit_by_category_top15.png)

### Ventas por mes

Da una primera pista de estacionalidad.

![Ventas por mes](figures/basic_eda/sales_by_order_month.png)

### Distribucion de Sales

Permite ver escala, concentracion y posibles outliers para el modelo.

![Distribucion de Sales](figures/basic_eda/sales_distribution_p99.png)

### Descuento vs ventas

Busca si el descuento parece relacionarse con ventas; no implica causalidad.

![Descuento vs ventas](figures/basic_eda/discount_rate_vs_sales_sample.png)

### Correlacion con Sales

Ranking rapido de variables numericas potencialmente utiles para ventas; no reemplaza validacion.

![Correlacion con Sales](figures/basic_eda/corr_with_sales_top15.png)

### Correlacion con retraso

Ranking rapido para el target logistico, cuidando leakage.

![Correlacion con retraso](figures/basic_eda/corr_with_late_delivery_top15.png)

### Visitas por departamento

Los logs pueden aportar senal de interes/demanda por departamento.

![Visitas por departamento](figures/basic_eda/web_visits_by_department.png)

### Visitas por categoria

Compara interes web con categorias de venta.

![Visitas por categoria](figures/basic_eda/web_visits_by_category_top15.png)

### Visitas por hora

Puede aportar patrones temporales de demanda o actividad.

![Visitas por hora](figures/basic_eda/web_visits_by_hour.png)

### Ventas vs visitas web

Compara demanda comprada frente a interes web; util para features de demanda si se alinea temporalmente.

![Ventas vs visitas web](figures/basic_eda/sales_vs_web_views_top_products.png)