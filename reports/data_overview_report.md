# Resumen inicial de datasets


---

Este reporte se genera desde `proyecto.py`. Lee los CSV originales en modo solo lectura y no modifica los datasets. Se excluye `DescriptionDataCoSupplyChain.csv` como dataset resumido; las explicaciones de campos son una guia inicial basada en nombres de columnas y valores visibles.

---

# DataCoSupplyChainDataset


Archivo: `DataCoSupplyChainDataset.csv`

Filas: `180,519`

Columnas: `53`

Memoria aproximada en pandas: `298.92 MB`


## Como leer este CSV

Cada fila parece representar una linea de pedido: un producto vendido a un cliente, con datos de envio, venta, beneficio, geografia, producto y estado del pedido.

## Grupos de columnas

### Pedido y pago

- `Type`
- `Order Customer Id`
- `order date (DateOrders)`
- `Order Id`
- `Order Status`

### Envio y entrega

- `Days for shipping (real)`
- `Days for shipment (scheduled)`
- `Delivery Status`
- `Late_delivery_risk`
- `shipping date (DateOrders)`
- `Shipping Mode`

### Ventas, descuento y margen

- `Benefit per order`
- `Sales per customer`
- `Order Item Discount`
- `Order Item Discount Rate`
- `Order Item Product Price`
- `Order Item Profit Ratio`
- `Order Item Quantity`
- `Sales`
- `Order Item Total`
- `Order Profit Per Order`
- `Product Price`

### Cliente

- `Customer City`
- `Customer Country`
- `Customer Email`
- `Customer Fname`
- `Customer Id`
- `Customer Lname`
- `Customer Password`
- `Customer Segment`
- `Customer State`
- `Customer Street`
- `Customer Zipcode`

### Producto

- `Category Id`
- `Category Name`
- `Department Id`
- `Department Name`
- `Product Card Id`
- `Product Category Id`
- `Product Description`
- `Product Image`
- `Product Name`
- `Product Status`

### Geografia

- `Latitude`
- `Longitude`
- `Market`
- `Order City`
- `Order Country`
- `Order Region`
- `Order State`
- `Order Zipcode`

### Otras columnas

- `Order Item Cardprod Id`
- `Order Item Id`

## Head compacto con columnas clave

Esta es una version reducida del `.head()` para orientarse sin ver todas las columnas a la vez.

```text
 Order Id order date (DateOrders)    Order Status   Delivery Status  Late_delivery_risk  Shipping Mode Product Name  Order Item Quantity  Sales  Order Item Total  Order Profit Per Order Customer Segment Order Country       Market
    77202         1/31/2018 22:56        COMPLETE  Advance shipping                   0 Standard Class Smart watch                     1 327.75        314.640015               91.250000         Consumer     Indonesia Pacific Asia
    75939         1/13/2018 12:27         PENDING     Late delivery                   1 Standard Class Smart watch                     1 327.75        311.359985             -249.089996         Consumer         India Pacific Asia
    75938         1/13/2018 12:06          CLOSED  Shipping on time                   0 Standard Class Smart watch                     1 327.75        309.720001             -247.779999         Consumer         India Pacific Asia
    75937         1/13/2018 11:45        COMPLETE  Advance shipping                   0 Standard Class Smart watch                     1 327.75        304.809998               22.860001      Home Office     Australia Pacific Asia
    75936         1/13/2018 11:24 PENDING_PAYMENT  Advance shipping                   0 Standard Class Smart watch                     1 327.75        298.250000              134.210007        Corporate     Australia Pacific Asia
    75935         1/13/2018 11:03        CANCELED Shipping canceled                   0 Standard Class Smart watch                     1 327.75        294.980011               18.580000         Consumer     Australia Pacific Asia
    75934         1/13/2018 10:42        COMPLETE     Late delivery                   1    First Class Smart watch                     1 327.75        288.420013               95.180000      Home Office         China Pacific Asia
    75933         1/13/2018 10:21      PROCESSING     Late delivery                   1    First Class Smart watch                     1 327.75        285.140015               68.430000        Corporate         China Pacific Asia
```

## Head humano en formato ficha

### Fila 1

Lectura vertical: cada linea es una columna del CSV y su valor en esa fila.

#### Pedido y pago

| Campo | Valor | Como leerlo |
| --- | --- | --- |
| Type | DEBIT | Tipo de pago o transaccion del pedido, por ejemplo DEBIT, TRANSFER, CASH. |
| Order Customer Id | 20755 | Pendiente de interpretar; revisar con el diccionario o con analisis posterior. |
| order date (DateOrders) | 1/31/2018 22:56 | Fecha y hora en que se realizo el pedido. |
| Order Id | 77202 | Identificador del pedido. |
| Order Status | COMPLETE | Estado administrativo del pedido, por ejemplo COMPLETE, PENDING, CLOSED. |

#### Envio y entrega

| Campo | Valor | Como leerlo |
| --- | --- | --- |
| Days for shipping (real) | 3 | Dias reales que tardo el envio. |
| Days for shipment (scheduled) | 4 | Dias previstos o prometidos para el envio. |
| Delivery Status | Advance shipping | Estado logistico de la entrega, por ejemplo tarde, a tiempo o adelantada. |
| Late_delivery_risk | 0 | Indicador binario: 1 suele significar riesgo/entrega tardia; 0 sin riesgo/tardia segun ... |
| shipping date (DateOrders) | 2/3/2018 22:56 | Fecha y hora de envio. |
| Shipping Mode | Standard Class | Modo de envio, por ejemplo Standard Class o Second Class. |

#### Ventas, descuento y margen

| Campo | Valor | Como leerlo |
| --- | --- | --- |
| Benefit per order | 91.25 | Beneficio estimado del pedido o linea de pedido. |
| Sales per customer | 314.6400146 | Ventas asociadas al cliente en esa fila. |
| Order Item Discount | 13.10999966 | Importe de descuento aplicado a la linea. |
| Order Item Discount Rate | 0.039999999 | Porcentaje o tasa de descuento aplicada. |
| Order Item Product Price | 327.75 | Precio unitario del producto en la linea. |
| Order Item Profit Ratio | 0.289999992 | Ratio de beneficio de la linea. |
| Order Item Quantity | 1 | Cantidad de unidades compradas en la linea. |
| Sales | 327.75 | Venta bruta o importe de venta antes de algunos ajustes/descuentos, segun el dataset. |
| Order Item Total | 314.6400146 | Total de la linea despues de descuento u otros ajustes. |
| Order Profit Per Order | 91.25 | Beneficio asociado al pedido o linea. |
| Product Price | 327.75 | Precio del producto. |

#### Cliente

| Campo | Valor | Como leerlo |
| --- | --- | --- |
| Customer City | Caguas | Pendiente de interpretar; revisar con el diccionario o con analisis posterior. |
| Customer Country | Puerto Rico | Pendiente de interpretar; revisar con el diccionario o con analisis posterior. |
| Customer Email | XXXXXXXXX | Pendiente de interpretar; revisar con el diccionario o con analisis posterior. |
| Customer Fname | Cally | Pendiente de interpretar; revisar con el diccionario o con analisis posterior. |
| Customer Id | 20755 | Identificador del cliente. |
| Customer Lname | Holloway | Pendiente de interpretar; revisar con el diccionario o con analisis posterior. |
| Customer Password | XXXXXXXXX | Pendiente de interpretar; revisar con el diccionario o con analisis posterior. |
| Customer Segment | Consumer | Segmento comercial del cliente. |
| Customer State | PR | Pendiente de interpretar; revisar con el diccionario o con analisis posterior. |
| Customer Street | 5365 Noble Nectar Island | Pendiente de interpretar; revisar con el diccionario o con analisis posterior. |
| Customer Zipcode | 725.0 | Pendiente de interpretar; revisar con el diccionario o con analisis posterior. |

#### Producto

| Campo | Valor | Como leerlo |
| --- | --- | --- |
| Category Id | 73 | Identificador numerico de categoria de producto. |
| Category Name | Sporting Goods | Nombre de la categoria de producto. |
| Department Id | 2 | Identificador del departamento de producto. |
| Department Name | Fitness | Nombre del departamento de producto. |
| Product Card Id | 1360 | Identificador tecnico del producto. |
| Product Category Id | 73 | Identificador de la categoria del producto. |
| Product Description | NA | Descripcion del producto, si existe. |
| Product Image | http://images.acmesports.sports/Smart+watch | URL o referencia de imagen del producto. |
| Product Name | Smart watch | Nombre del producto. |
| Product Status | 0 | Estado del producto dentro del catalogo. |

#### Geografia

| Campo | Valor | Como leerlo |
| --- | --- | --- |
| Latitude | 18.2514534 | Latitud asociada al cliente o localizacion registrada. |
| Longitude | -66.03705597 | Longitud asociada al cliente o localizacion registrada. |
| Market | Pacific Asia | Mercado o macro-region comercial. |
| Order City | Bekasi | Ciudad destino o asociada al pedido. |
| Order Country | Indonesia | Pais destino o asociado al pedido. |
| Order Region | Southeast Asia | Region del pedido. |
| Order State | Java Occidental | Estado/provincia del pedido. |
| Order Zipcode | NA | Codigo postal del pedido, si existe. |

#### Otras columnas

| Campo | Valor | Como leerlo |
| --- | --- | --- |
| Order Item Cardprod Id | 1360 | Identificador tecnico del producto en la linea de pedido. |
| Order Item Id | 180517 | Identificador unico de la linea de pedido. |

### Fila 2

Lectura vertical: cada linea es una columna del CSV y su valor en esa fila.

#### Pedido y pago

| Campo | Valor | Como leerlo |
| --- | --- | --- |
| Type | TRANSFER | Tipo de pago o transaccion del pedido, por ejemplo DEBIT, TRANSFER, CASH. |
| Order Customer Id | 19492 | Pendiente de interpretar; revisar con el diccionario o con analisis posterior. |
| order date (DateOrders) | 1/13/2018 12:27 | Fecha y hora en que se realizo el pedido. |
| Order Id | 75939 | Identificador del pedido. |
| Order Status | PENDING | Estado administrativo del pedido, por ejemplo COMPLETE, PENDING, CLOSED. |

#### Envio y entrega

| Campo | Valor | Como leerlo |
| --- | --- | --- |
| Days for shipping (real) | 5 | Dias reales que tardo el envio. |
| Days for shipment (scheduled) | 4 | Dias previstos o prometidos para el envio. |
| Delivery Status | Late delivery | Estado logistico de la entrega, por ejemplo tarde, a tiempo o adelantada. |
| Late_delivery_risk | 1 | Indicador binario: 1 suele significar riesgo/entrega tardia; 0 sin riesgo/tardia segun ... |
| shipping date (DateOrders) | 1/18/2018 12:27 | Fecha y hora de envio. |
| Shipping Mode | Standard Class | Modo de envio, por ejemplo Standard Class o Second Class. |

#### Ventas, descuento y margen

| Campo | Valor | Como leerlo |
| --- | --- | --- |
| Benefit per order | -249.0899963 | Beneficio estimado del pedido o linea de pedido. |
| Sales per customer | 311.3599854 | Ventas asociadas al cliente en esa fila. |
| Order Item Discount | 16.38999939 | Importe de descuento aplicado a la linea. |
| Order Item Discount Rate | 0.050000001 | Porcentaje o tasa de descuento aplicada. |
| Order Item Product Price | 327.75 | Precio unitario del producto en la linea. |
| Order Item Profit Ratio | -0.800000012 | Ratio de beneficio de la linea. |
| Order Item Quantity | 1 | Cantidad de unidades compradas en la linea. |
| Sales | 327.75 | Venta bruta o importe de venta antes de algunos ajustes/descuentos, segun el dataset. |
| Order Item Total | 311.3599854 | Total de la linea despues de descuento u otros ajustes. |
| Order Profit Per Order | -249.0899963 | Beneficio asociado al pedido o linea. |
| Product Price | 327.75 | Precio del producto. |

#### Cliente

| Campo | Valor | Como leerlo |
| --- | --- | --- |
| Customer City | Caguas | Pendiente de interpretar; revisar con el diccionario o con analisis posterior. |
| Customer Country | Puerto Rico | Pendiente de interpretar; revisar con el diccionario o con analisis posterior. |
| Customer Email | XXXXXXXXX | Pendiente de interpretar; revisar con el diccionario o con analisis posterior. |
| Customer Fname | Irene | Pendiente de interpretar; revisar con el diccionario o con analisis posterior. |
| Customer Id | 19492 | Identificador del cliente. |
| Customer Lname | Luna | Pendiente de interpretar; revisar con el diccionario o con analisis posterior. |
| Customer Password | XXXXXXXXX | Pendiente de interpretar; revisar con el diccionario o con analisis posterior. |
| Customer Segment | Consumer | Segmento comercial del cliente. |
| Customer State | PR | Pendiente de interpretar; revisar con el diccionario o con analisis posterior. |
| Customer Street | 2679 Rustic Loop | Pendiente de interpretar; revisar con el diccionario o con analisis posterior. |
| Customer Zipcode | 725.0 | Pendiente de interpretar; revisar con el diccionario o con analisis posterior. |

#### Producto

| Campo | Valor | Como leerlo |
| --- | --- | --- |
| Category Id | 73 | Identificador numerico de categoria de producto. |
| Category Name | Sporting Goods | Nombre de la categoria de producto. |
| Department Id | 2 | Identificador del departamento de producto. |
| Department Name | Fitness | Nombre del departamento de producto. |
| Product Card Id | 1360 | Identificador tecnico del producto. |
| Product Category Id | 73 | Identificador de la categoria del producto. |
| Product Description | NA | Descripcion del producto, si existe. |
| Product Image | http://images.acmesports.sports/Smart+watch | URL o referencia de imagen del producto. |
| Product Name | Smart watch | Nombre del producto. |
| Product Status | 0 | Estado del producto dentro del catalogo. |

#### Geografia

| Campo | Valor | Como leerlo |
| --- | --- | --- |
| Latitude | 18.27945137 | Latitud asociada al cliente o localizacion registrada. |
| Longitude | -66.0370636 | Longitud asociada al cliente o localizacion registrada. |
| Market | Pacific Asia | Mercado o macro-region comercial. |
| Order City | Bikaner | Ciudad destino o asociada al pedido. |
| Order Country | India | Pais destino o asociado al pedido. |
| Order Region | South Asia | Region del pedido. |
| Order State | Rajastán | Estado/provincia del pedido. |
| Order Zipcode | NA | Codigo postal del pedido, si existe. |

#### Otras columnas

| Campo | Valor | Como leerlo |
| --- | --- | --- |
| Order Item Cardprod Id | 1360 | Identificador tecnico del producto en la linea de pedido. |
| Order Item Id | 179254 | Identificador unico de la linea de pedido. |

### Fila 3

Lectura vertical: cada linea es una columna del CSV y su valor en esa fila.

#### Pedido y pago

| Campo | Valor | Como leerlo |
| --- | --- | --- |
| Type | CASH | Tipo de pago o transaccion del pedido, por ejemplo DEBIT, TRANSFER, CASH. |
| Order Customer Id | 19491 | Pendiente de interpretar; revisar con el diccionario o con analisis posterior. |
| order date (DateOrders) | 1/13/2018 12:06 | Fecha y hora en que se realizo el pedido. |
| Order Id | 75938 | Identificador del pedido. |
| Order Status | CLOSED | Estado administrativo del pedido, por ejemplo COMPLETE, PENDING, CLOSED. |

#### Envio y entrega

| Campo | Valor | Como leerlo |
| --- | --- | --- |
| Days for shipping (real) | 4 | Dias reales que tardo el envio. |
| Days for shipment (scheduled) | 4 | Dias previstos o prometidos para el envio. |
| Delivery Status | Shipping on time | Estado logistico de la entrega, por ejemplo tarde, a tiempo o adelantada. |
| Late_delivery_risk | 0 | Indicador binario: 1 suele significar riesgo/entrega tardia; 0 sin riesgo/tardia segun ... |
| shipping date (DateOrders) | 1/17/2018 12:06 | Fecha y hora de envio. |
| Shipping Mode | Standard Class | Modo de envio, por ejemplo Standard Class o Second Class. |

#### Ventas, descuento y margen

| Campo | Valor | Como leerlo |
| --- | --- | --- |
| Benefit per order | -247.7799988 | Beneficio estimado del pedido o linea de pedido. |
| Sales per customer | 309.7200012 | Ventas asociadas al cliente en esa fila. |
| Order Item Discount | 18.03000069 | Importe de descuento aplicado a la linea. |
| Order Item Discount Rate | 0.059999999 | Porcentaje o tasa de descuento aplicada. |
| Order Item Product Price | 327.75 | Precio unitario del producto en la linea. |
| Order Item Profit Ratio | -0.800000012 | Ratio de beneficio de la linea. |
| Order Item Quantity | 1 | Cantidad de unidades compradas en la linea. |
| Sales | 327.75 | Venta bruta o importe de venta antes de algunos ajustes/descuentos, segun el dataset. |
| Order Item Total | 309.7200012 | Total de la linea despues de descuento u otros ajustes. |
| Order Profit Per Order | -247.7799988 | Beneficio asociado al pedido o linea. |
| Product Price | 327.75 | Precio del producto. |

#### Cliente

| Campo | Valor | Como leerlo |
| --- | --- | --- |
| Customer City | San Jose | Pendiente de interpretar; revisar con el diccionario o con analisis posterior. |
| Customer Country | EE. UU. | Pendiente de interpretar; revisar con el diccionario o con analisis posterior. |
| Customer Email | XXXXXXXXX | Pendiente de interpretar; revisar con el diccionario o con analisis posterior. |
| Customer Fname | Gillian | Pendiente de interpretar; revisar con el diccionario o con analisis posterior. |
| Customer Id | 19491 | Identificador del cliente. |
| Customer Lname | Maldonado | Pendiente de interpretar; revisar con el diccionario o con analisis posterior. |
| Customer Password | XXXXXXXXX | Pendiente de interpretar; revisar con el diccionario o con analisis posterior. |
| Customer Segment | Consumer | Segmento comercial del cliente. |
| Customer State | CA | Pendiente de interpretar; revisar con el diccionario o con analisis posterior. |
| Customer Street | 8510 Round Bear Gate | Pendiente de interpretar; revisar con el diccionario o con analisis posterior. |
| Customer Zipcode | 95125.0 | Pendiente de interpretar; revisar con el diccionario o con analisis posterior. |

#### Producto

| Campo | Valor | Como leerlo |
| --- | --- | --- |
| Category Id | 73 | Identificador numerico de categoria de producto. |
| Category Name | Sporting Goods | Nombre de la categoria de producto. |
| Department Id | 2 | Identificador del departamento de producto. |
| Department Name | Fitness | Nombre del departamento de producto. |
| Product Card Id | 1360 | Identificador tecnico del producto. |
| Product Category Id | 73 | Identificador de la categoria del producto. |
| Product Description | NA | Descripcion del producto, si existe. |
| Product Image | http://images.acmesports.sports/Smart+watch | URL o referencia de imagen del producto. |
| Product Name | Smart watch | Nombre del producto. |
| Product Status | 0 | Estado del producto dentro del catalogo. |

#### Geografia

| Campo | Valor | Como leerlo |
| --- | --- | --- |
| Latitude | 37.29223251 | Latitud asociada al cliente o localizacion registrada. |
| Longitude | -121.881279 | Longitud asociada al cliente o localizacion registrada. |
| Market | Pacific Asia | Mercado o macro-region comercial. |
| Order City | Bikaner | Ciudad destino o asociada al pedido. |
| Order Country | India | Pais destino o asociado al pedido. |
| Order Region | South Asia | Region del pedido. |
| Order State | Rajastán | Estado/provincia del pedido. |
| Order Zipcode | NA | Codigo postal del pedido, si existe. |

#### Otras columnas

| Campo | Valor | Como leerlo |
| --- | --- | --- |
| Order Item Cardprod Id | 1360 | Identificador tecnico del producto en la linea de pedido. |
| Order Item Id | 179253 | Identificador unico de la linea de pedido. |

## Info

```text
<class 'pandas.DataFrame'>
RangeIndex: 180519 entries, 0 to 180518
Data columns (total 53 columns):
 #   Column                         Non-Null Count   Dtype  
---  ------                         --------------   -----  
 0   Type                           180519 non-null  str    
 1   Days for shipping (real)       180519 non-null  int64  
 2   Days for shipment (scheduled)  180519 non-null  int64  
 3   Benefit per order              180519 non-null  float64
 4   Sales per customer             180519 non-null  float64
 5   Delivery Status                180519 non-null  str    
 6   Late_delivery_risk             180519 non-null  int64  
 7   Category Id                    180519 non-null  int64  
 8   Category Name                  180519 non-null  str    
 9   Customer City                  180519 non-null  str    
 10  Customer Country               180519 non-null  str    
 11  Customer Email                 180519 non-null  str    
 12  Customer Fname                 180519 non-null  str    
 13  Customer Id                    180519 non-null  int64  
 14  Customer Lname                 180511 non-null  str    
 15  Customer Password              180519 non-null  str    
 16  Customer Segment               180519 non-null  str    
 17  Customer State                 180519 non-null  str    
 18  Customer Street                180519 non-null  str    
 19  Customer Zipcode               180516 non-null  float64
 20  Department Id                  180519 non-null  int64  
 21  Department Name                180519 non-null  str    
 22  Latitude                       180519 non-null  float64
 23  Longitude                      180519 non-null  float64
 24  Market                         180519 non-null  str    
 25  Order City                     180519 non-null  str    
 26  Order Country                  180519 non-null  str    
 27  Order Customer Id              180519 non-null  int64  
 28  order date (DateOrders)        180519 non-null  str    
 29  Order Id                       180519 non-null  int64  
 30  Order Item Cardprod Id         180519 non-null  int64  
 31  Order Item Discount            180519 non-null  float64
 32  Order Item Discount Rate       180519 non-null  float64
 33  Order Item Id                  180519 non-null  int64  
 34  Order Item Product Price       180519 non-null  float64
 35  Order Item Profit Ratio        180519 non-null  float64
 36  Order Item Quantity            180519 non-null  int64  
 37  Sales                          180519 non-null  float64
 38  Order Item Total               180519 non-null  float64
 39  Order Profit Per Order         180519 non-null  float64
 40  Order Region                   180519 non-null  str    
 41  Order State                    180519 non-null  str    
 42  Order Status                   180519 non-null  str    
 43  Order Zipcode                  24840 non-null   float64
 44  Product Card Id                180519 non-null  int64  
 45  Product Category Id            180519 non-null  int64  
 46  Product Description            0 non-null       float64
 47  Product Image                  180519 non-null  str    
 48  Product Name                   180519 non-null  str    
 49  Product Price                  180519 non-null  float64
 50  Product Status                 180519 non-null  int64  
 51  shipping date (DateOrders)     180519 non-null  str    
 52  Shipping Mode                  180519 non-null  str    
dtypes: float64(15), int64(14), str(24)
memory usage: 73.0 MB
```

## Describe numerico

```text
                                  count          mean           std          min           25%           50%            75%            max
Days for shipping (real)       180519.0      3.497654      1.623722     0.000000      2.000000      3.000000       5.000000       6.000000
Days for shipment (scheduled)  180519.0      2.931847      1.374449     0.000000      2.000000      4.000000       4.000000       4.000000
Benefit per order              180519.0     21.974989    104.433526 -4274.979980      7.000000     31.520000      64.800003     911.799988
Sales per customer             180519.0    183.107609    120.043670     7.490000    104.379997    163.990005     247.399994    1939.989990
Late_delivery_risk             180519.0      0.548291      0.497664     0.000000      0.000000      1.000000       1.000000       1.000000
Category Id                    180519.0     31.851451     15.640064     2.000000     18.000000     29.000000      45.000000      76.000000
Customer Id                    180519.0   6691.379495   4162.918106     1.000000   3258.500000   6457.000000    9779.000000   20757.000000
Customer Zipcode               180516.0  35921.126914  37542.461122   603.000000    725.000000  19380.000000   78207.000000   99205.000000
Department Id                  180519.0      5.443460      1.629246     2.000000      4.000000      5.000000       7.000000      12.000000
Latitude                       180519.0     29.719955      9.813646   -33.937553     18.265432     33.144863      39.279617      48.781933
Longitude                      180519.0    -84.915675     21.433241  -158.025986    -98.446312    -76.847908     -66.370583     115.263077
Order Customer Id              180519.0   6691.379495   4162.918106     1.000000   3258.500000   6457.000000    9779.000000   20757.000000
Order Id                       180519.0  36221.894903  21045.379569     1.000000  18057.000000  36140.000000   54144.000000   77204.000000
Order Item Cardprod Id         180519.0    692.509764    336.446807    19.000000    403.000000    627.000000    1004.000000    1363.000000
Order Item Discount            180519.0     20.664741     21.800901     0.000000      5.400000     14.000000      29.990000     500.000000
Order Item Discount Rate       180519.0      0.101668      0.070415     0.000000      0.040000      0.100000       0.160000       0.250000
Order Item Id                  180519.0  90260.000000  52111.490959     1.000000  45130.500000  90260.000000  135389.500000  180519.000000
Order Item Product Price       180519.0    141.232550    139.732492     9.990000     50.000000     59.990002     199.990005    1999.989990
Order Item Profit Ratio        180519.0      0.120647      0.466796    -2.750000      0.080000      0.270000       0.360000       0.500000
Order Item Quantity            180519.0      2.127638      1.453451     1.000000      1.000000      1.000000       3.000000       5.000000
Sales                          180519.0    203.772096    132.273077     9.990000    119.980003    199.919998     299.950012    1999.989990
Order Item Total               180519.0    183.107609    120.043670     7.490000    104.379997    163.990005     247.399994    1939.989990
Order Profit Per Order         180519.0     21.974989    104.433526 -4274.979980      7.000000     31.520000      64.800003     911.799988
Order Zipcode                   24840.0  55426.132327  31919.279101  1040.000000  23464.000000  59405.000000   90008.000000   99301.000000
Product Card Id                180519.0    692.509764    336.446807    19.000000    403.000000    627.000000    1004.000000    1363.000000
Product Category Id            180519.0     31.851451     15.640064     2.000000     18.000000     29.000000      45.000000      76.000000
Product Description                 0.0           NaN           NaN          NaN           NaN           NaN            NaN            NaN
Product Price                  180519.0    141.232550    139.732492     9.990000     50.000000     59.990002     199.990005    1999.989990
Product Status                 180519.0      0.000000      0.000000     0.000000      0.000000      0.000000       0.000000       0.000000
```

## Describe categorico y general

```text
                                  count unique                                                               top    freq          mean           std         min         25%         50%         75%         max
Type                             180519      4                                                             DEBIT   69295           NaN           NaN         NaN         NaN         NaN         NaN         NaN
Days for shipping (real)       180519.0    NaN                                                               NaN     NaN      3.497654      1.623722         0.0         2.0         3.0         5.0         6.0
Days for shipment (scheduled)  180519.0    NaN                                                               NaN     NaN      2.931847      1.374449         0.0         2.0         4.0         4.0         4.0
Benefit per order              180519.0    NaN                                                               NaN     NaN     21.974989    104.433526 -4274.97998         7.0       31.52   64.800003  911.799988
Sales per customer             180519.0    NaN                                                               NaN     NaN    183.107609     120.04367        7.49  104.379997  163.990005  247.399994  1939.98999
Delivery Status                  180519      4                                                     Late delivery   98977           NaN           NaN         NaN         NaN         NaN         NaN         NaN
Late_delivery_risk             180519.0    NaN                                                               NaN     NaN      0.548291      0.497664         0.0         0.0         1.0         1.0         1.0
Category Id                    180519.0    NaN                                                               NaN     NaN     31.851451     15.640064         2.0        18.0        29.0        45.0        76.0
Category Name                    180519     50                                                            Cleats   24551           NaN           NaN         NaN         NaN         NaN         NaN         NaN
Customer City                    180519    563                                                            Caguas   66770           NaN           NaN         NaN         NaN         NaN         NaN         NaN
Customer Country                 180519      2                                                           EE. UU.  111146           NaN           NaN         NaN         NaN         NaN         NaN         NaN
Customer Email                   180519      1                                                         XXXXXXXXX  180519           NaN           NaN         NaN         NaN         NaN         NaN         NaN
Customer Fname                   180519    782                                                              Mary   65150           NaN           NaN         NaN         NaN         NaN         NaN         NaN
Customer Id                    180519.0    NaN                                                               NaN     NaN   6691.379495   4162.918106         1.0      3258.5      6457.0      9779.0     20757.0
Customer Lname                   180511   1109                                                             Smith   64104           NaN           NaN         NaN         NaN         NaN         NaN         NaN
Customer Password                180519      1                                                         XXXXXXXXX  180519           NaN           NaN         NaN         NaN         NaN         NaN         NaN
Customer Segment                 180519      3                                                          Consumer   93504           NaN           NaN         NaN         NaN         NaN         NaN         NaN
Customer State                   180519     46                                                                PR   69373           NaN           NaN         NaN         NaN         NaN         NaN         NaN
Customer Street                  180519   7458                                           9126 Wishing Expressway     122           NaN           NaN         NaN         NaN         NaN         NaN         NaN
Customer Zipcode               180516.0    NaN                                                               NaN     NaN  35921.126914  37542.461122       603.0       725.0     19380.0     78207.0     99205.0
Department Id                  180519.0    NaN                                                               NaN     NaN       5.44346      1.629246         2.0         4.0         5.0         7.0        12.0
Department Name                  180519     11                                                          Fan Shop   66861           NaN           NaN         NaN         NaN         NaN         NaN         NaN
Latitude                       180519.0    NaN                                                               NaN     NaN     29.719955      9.813646  -33.937553   18.265432   33.144863   39.279617   48.781933
Longitude                      180519.0    NaN                                                               NaN     NaN    -84.915675     21.433241 -158.025986  -98.446312  -76.847908  -66.370583  115.263077
Market                           180519      5                                                             LATAM   51594           NaN           NaN         NaN         NaN         NaN         NaN         NaN
Order City                       180519   3597                                                     Santo Domingo    2211           NaN           NaN         NaN         NaN         NaN         NaN         NaN
Order Country                    180519    164                                                    Estados Unidos   24840           NaN           NaN         NaN         NaN         NaN         NaN         NaN
Order Customer Id              180519.0    NaN                                                               NaN     NaN   6691.379495   4162.918106         1.0      3258.5      6457.0      9779.0     20757.0
order date (DateOrders)          180519  65752                                                  10/25/2016 14:39       5           NaN           NaN         NaN         NaN         NaN         NaN         NaN
Order Id                       180519.0    NaN                                                               NaN     NaN  36221.894903  21045.379569         1.0     18057.0     36140.0     54144.0     77204.0
Order Item Cardprod Id         180519.0    NaN                                                               NaN     NaN    692.509764    336.446807        19.0       403.0       627.0      1004.0      1363.0
Order Item Discount            180519.0    NaN                                                               NaN     NaN     20.664741     21.800901         0.0         5.4        14.0       29.99       500.0
Order Item Discount Rate       180519.0    NaN                                                               NaN     NaN      0.101668      0.070415         0.0        0.04         0.1        0.16        0.25
Order Item Id                  180519.0    NaN                                                               NaN     NaN       90260.0  52111.490959         1.0     45130.5     90260.0    135389.5    180519.0
Order Item Product Price       180519.0    NaN                                                               NaN     NaN     141.23255    139.732492        9.99        50.0   59.990002  199.990005  1999.98999
Order Item Profit Ratio        180519.0    NaN                                                               NaN     NaN      0.120647      0.466796       -2.75        0.08        0.27        0.36         0.5
Order Item Quantity            180519.0    NaN                                                               NaN     NaN      2.127638      1.453451         1.0         1.0         1.0         3.0         5.0
Sales                          180519.0    NaN                                                               NaN     NaN    203.772096    132.273077        9.99  119.980003  199.919998  299.950012  1999.98999
Order Item Total               180519.0    NaN                                                               NaN     NaN    183.107609     120.04367        7.49  104.379997  163.990005  247.399994  1939.98999
Order Profit Per Order         180519.0    NaN                                                               NaN     NaN     21.974989    104.433526 -4274.97998         7.0       31.52   64.800003  911.799988
Order Region                     180519     23                                                   Central America   28341           NaN           NaN         NaN         NaN         NaN         NaN         NaN
Order State                      180519   1089                                                        Inglaterra    6722           NaN           NaN         NaN         NaN         NaN         NaN         NaN
Order Status                     180519      9                                                          COMPLETE   59491           NaN           NaN         NaN         NaN         NaN         NaN         NaN
Order Zipcode                   24840.0    NaN                                                               NaN     NaN  55426.132327  31919.279101      1040.0     23464.0     59405.0     90008.0     99301.0
Product Card Id                180519.0    NaN                                                               NaN     NaN    692.509764    336.446807        19.0       403.0       627.0      1004.0      1363.0
Product Category Id            180519.0    NaN                                                               NaN     NaN     31.851451     15.640064         2.0        18.0        29.0        45.0        76.0
Product Description                 0.0    NaN                                                               NaN     NaN           NaN           NaN         NaN         NaN         NaN         NaN         NaN
Product Image                    180519    118  http://images.acmesports.sports/Perfect+Fitness+Perfect+Rip+Deck   24515           NaN           NaN         NaN         NaN         NaN         NaN         NaN
Product Name                     180519    118                                  Perfect Fitness Perfect Rip Deck   24515           NaN           NaN         NaN         NaN         NaN         NaN         NaN
Product Price                  180519.0    NaN                                                               NaN     NaN     141.23255    139.732492        9.99        50.0   59.990002  199.990005  1999.98999
Product Status                 180519.0    NaN                                                               NaN     NaN           0.0           0.0         0.0         0.0         0.0         0.0         0.0
shipping date (DateOrders)       180519  63701                                                    5/9/2015 18:02      10           NaN           NaN         NaN         NaN         NaN         NaN         NaN
Shipping Mode                    180519      4                                                    Standard Class  107752           NaN           NaN         NaN         NaN         NaN         NaN         NaN
```

## Tipos de datos

```text
  dtype  column_count
    str            24
float64            15
  int64            14
```

## Nulos por columna

```text
                               missing_count  missing_pct
Product Description                   180519       100.00
Order Zipcode                         155679        86.24
Customer Lname                             8         0.00
Customer Zipcode                           3         0.00
Type                                       0         0.00
Days for shipping (real)                   0         0.00
Days for shipment (scheduled)              0         0.00
Benefit per order                          0         0.00
Sales per customer                         0         0.00
Delivery Status                            0         0.00
Late_delivery_risk                         0         0.00
Category Id                                0         0.00
Category Name                              0         0.00
Customer City                              0         0.00
Customer Country                           0         0.00
Customer Email                             0         0.00
Customer Fname                             0         0.00
Customer Id                                0         0.00
Customer Password                          0         0.00
Customer Segment                           0         0.00
Customer State                             0         0.00
Customer Street                            0         0.00
Department Id                              0         0.00
Department Name                            0         0.00
Latitude                                   0         0.00
Longitude                                  0         0.00
Market                                     0         0.00
Order City                                 0         0.00
Order Country                              0         0.00
Order Customer Id                          0         0.00
order date (DateOrders)                    0         0.00
Order Id                                   0         0.00
Order Item Cardprod Id                     0         0.00
Order Item Discount                        0         0.00
Order Item Discount Rate                   0         0.00
Order Item Id                              0         0.00
Order Item Product Price                   0         0.00
Order Item Profit Ratio                    0         0.00
Order Item Quantity                        0         0.00
Sales                                      0         0.00
Order Item Total                           0         0.00
Order Profit Per Order                     0         0.00
Order Region                               0         0.00
Order State                                0         0.00
Order Status                               0         0.00
Product Card Id                            0         0.00
Product Category Id                        0         0.00
Product Image                              0         0.00
Product Name                               0         0.00
Product Price                              0         0.00
Product Status                             0         0.00
shipping date (DateOrders)                 0         0.00
Shipping Mode                              0         0.00
```

## Cardinalidad

```text
                               unique_values  unique_pct    dtype
Order Item Id                         180519      100.00    int64
order date (DateOrders)                65752       36.42      str
Order Id                               65752       36.42    int64
shipping date (DateOrders)             63701       35.29      str
Benefit per order                      21998       12.19  float64
Order Profit Per Order                 21998       12.19  float64
Customer Id                            20652       11.44    int64
Order Customer Id                      20652       11.44    int64
Latitude                               11250        6.23  float64
Customer Street                         7458        4.13      str
Longitude                               4487        2.49  float64
Order City                              3597        1.99      str
Order Item Total                        2927        1.62  float64
Sales per customer                      2927        1.62  float64
Customer Lname                          1109        0.61      str
Order State                             1089        0.60      str
Order Item Discount                     1017        0.56  float64
Customer Zipcode                         995        0.55  float64
Customer Fname                           782        0.43      str
Order Zipcode                            609        0.34  float64
Customer City                            563        0.31      str
Sales                                    193        0.11  float64
Order Country                            164        0.09      str
Order Item Profit Ratio                  162        0.09  float64
Product Image                            118        0.07      str
Product Name                             118        0.07      str
Order Item Cardprod Id                   118        0.07    int64
Product Card Id                          118        0.07    int64
Order Item Product Price                  75        0.04  float64
Product Price                             75        0.04  float64
Category Id                               51        0.03    int64
Product Category Id                       51        0.03    int64
Category Name                             50        0.03      str
Customer State                            46        0.03      str
Order Region                              23        0.01      str
Order Item Discount Rate                  18        0.01  float64
Department Id                             11        0.01    int64
Department Name                           11        0.01      str
Order Status                               9        0.00      str
Days for shipping (real)                   7        0.00    int64
Market                                     5        0.00      str
Order Item Quantity                        5        0.00    int64
Delivery Status                            4        0.00      str
Type                                       4        0.00      str
Days for shipment (scheduled)              4        0.00    int64
Shipping Mode                              4        0.00      str
Customer Segment                           3        0.00      str
Customer Country                           2        0.00      str
Late_delivery_risk                         2        0.00    int64
Customer Password                          1        0.00      str
Customer Email                             1        0.00      str
Product Status                             1        0.00    int64
Product Description                        0        0.00  float64
```

## Duplicados

Filas duplicadas exactas: `0` (0.00%).

## Columnas posiblemente de fecha

```text
                           column  sample_parse_success_rate               min_sample_date               max_sample_date
0        Days for shipping (real)                        1.0 1970-01-01 00:00:00.000000000 1970-01-01 00:00:00.000000006
1   Days for shipment (scheduled)                        1.0 1970-01-01 00:00:00.000000000 1970-01-01 00:00:00.000000004
2               Benefit per order                        1.0 1969-12-31 23:59:59.999998860 1970-01-01 00:00:00.000000599
3              Sales per customer                        1.0 1970-01-01 00:00:00.000000009 1970-01-01 00:00:00.000001417
4              Late_delivery_risk                        1.0 1970-01-01 00:00:00.000000000 1970-01-01 00:00:00.000000001
5                     Category Id                        1.0 1970-01-01 00:00:00.000000002 1970-01-01 00:00:00.000000076
6                     Customer Id                        1.0 1970-01-01 00:00:00.000000006 1970-01-01 00:00:00.000020755
7                Customer Zipcode                        1.0 1970-01-01 00:00:00.000000603 1970-01-01 00:00:00.000098115
8                   Department Id                        1.0 1970-01-01 00:00:00.000000002 1970-01-01 00:00:00.000000012
9                        Latitude                        1.0 1970-01-01 00:00:00.000000017 1970-01-01 00:00:00.000000047
10                      Longitude                        1.0 1969-12-31 23:59:59.999999842 1970-01-01 00:00:00.000000115
11              Order Customer Id                        1.0 1970-01-01 00:00:00.000000006 1970-01-01 00:00:00.000020755
12        order date (DateOrders)                        1.0 2015-01-01 19:58:00.000000000 2018-01-31 22:56:00.000000000
13                       Order Id                        1.0 1970-01-01 00:00:00.000000058 1970-01-01 00:00:00.000077202
14         Order Item Cardprod Id                        1.0 1970-01-01 00:00:00.000000024 1970-01-01 00:00:00.000001363
15            Order Item Discount                        1.0 1970-01-01 00:00:00.000000000 1970-01-01 00:00:00.000000375
16       Order Item Discount Rate                        1.0 1970-01-01 00:00:00.000000000 1970-01-01 00:00:00.000000000
17                  Order Item Id                        1.0 1970-01-01 00:00:00.000000138 1970-01-01 00:00:00.000180517
18       Order Item Product Price                        1.0 1970-01-01 00:00:00.000000011 1970-01-01 00:00:00.000001500
19        Order Item Profit Ratio                        1.0 1969-12-31 23:59:59.999999998 1970-01-01 00:00:00.000000000
20            Order Item Quantity                        1.0 1970-01-01 00:00:00.000000001 1970-01-01 00:00:00.000000005
21                          Sales                        1.0 1970-01-01 00:00:00.000000011 1970-01-01 00:00:00.000001500
22               Order Item Total                        1.0 1970-01-01 00:00:00.000000009 1970-01-01 00:00:00.000001417
23         Order Profit Per Order                        1.0 1969-12-31 23:59:59.999998860 1970-01-01 00:00:00.000000599
24                  Order Zipcode                        1.0 1970-01-01 00:00:00.000001841 1970-01-01 00:00:00.000099301
25                Product Card Id                        1.0 1970-01-01 00:00:00.000000024 1970-01-01 00:00:00.000001363
26            Product Category Id                        1.0 1970-01-01 00:00:00.000000002 1970-01-01 00:00:00.000000076
27                  Product Price                        1.0 1970-01-01 00:00:00.000000011 1970-01-01 00:00:00.000001500
28                 Product Status                        1.0 1970-01-01 00:00:00.000000000 1970-01-01 00:00:00.000000000
29     shipping date (DateOrders)                        1.0 2015-01-04 16:17:00.000000000 2018-02-05 14:43:00.000000000
```

## Valores frecuentes en columnas categoricas

### Type

```text
    Type  count   pct
   DEBIT  69295 38.39
TRANSFER  49883 27.63
 PAYMENT  41725 23.11
    CASH  19616 10.87
```

### Delivery Status

```text
  Delivery Status  count   pct
    Late delivery  98977 54.83
 Advance shipping  41592 23.04
 Shipping on time  32196 17.84
Shipping canceled   7754  4.30
```

### Category Name

```text
       Category Name  count   pct
              Cleats  24551 13.60
      Men's Footwear  22246 12.32
     Women's Apparel  21035 11.65
Indoor/Outdoor Games  19298 10.69
             Fishing  17325  9.60
        Water Sports  15540  8.61
    Camping & Hiking  13729  7.61
    Cardio Equipment  12487  6.92
       Shop By Sport  10984  6.08
         Electronics   3156  1.75
```

### Customer City

```text
Customer City  count   pct
       Caguas  66770 36.99
      Chicago   3885  2.15
  Los Angeles   3417  1.89
     Brooklyn   3412  1.89
     New York   1816  1.01
 Philadelphia   1577  0.87
        Bronx   1500  0.83
    San Diego   1437  0.80
        Miami   1314  0.73
      Houston   1297  0.72
```

### Customer Country

```text
Customer Country  count   pct
         EE. UU. 111146 61.57
     Puerto Rico  69373 38.43
```

### Customer Email

```text
Customer Email  count   pct
     XXXXXXXXX 180519 100.0
```

### Customer Fname

```text
Customer Fname  count   pct
          Mary  65150 36.09
         James   1835  1.02
        Robert   1759  0.97
       Michael   1680  0.93
         David   1625  0.90
          John   1446  0.80
       William   1365  0.76
        Joseph   1117  0.62
      Jennifer   1033  0.57
       Richard   1032  0.57
```

### Customer Lname

```text
Customer Lname  count   pct
         Smith  64104 35.51
       Johnson    989  0.55
         Brown    909  0.50
      Williams    869  0.48
         Jones    859  0.48
        Garcia    724  0.40
        Wilson    675  0.37
        Taylor    661  0.37
         Davis    640  0.35
         Moore    599  0.33
```

### Customer Password

```text
Customer Password  count   pct
        XXXXXXXXX 180519 100.0
```

### Customer Segment

```text
Customer Segment  count   pct
        Consumer  93504 51.80
       Corporate  54789 30.35
     Home Office  32226 17.85
```

### Customer State

```text
Customer State  count   pct
            PR  69373 38.43
            CA  29223 16.19
            NY  11327  6.27
            TX   9103  5.04
            IL   7631  4.23
            FL   5456  3.02
            OH   4095  2.27
            PA   3824  2.12
            MI   3804  2.11
            NJ   3191  1.77
```

### Customer Street

```text
           Customer Street  count  pct
   9126 Wishing Expressway    122 0.07
  4388 Burning Goose Ridge    117 0.06
     4720 Noble Hills Wynd    116 0.06
  2878 Hazy Wagon  Thicket    113 0.06
         398 Emerald Grove    109 0.06
     3593 Blue Brook Acres    108 0.06
       2210 Merry Leaf Row    107 0.06
            6289 Rocky Way    107 0.06
2585 Silent Autumn Landing    105 0.06
     7694 Velvet Turnabout    103 0.06
```

### Department Name

```text
Department Name  count   pct
       Fan Shop  66861 37.04
        Apparel  48998 27.14
           Golf  33220 18.40
       Footwear  14525  8.05
       Outdoors   9686  5.37
        Fitness   2479  1.37
     Discs Shop   2026  1.12
     Technology   1465  0.81
       Pet Shop    492  0.27
      Book Shop    405  0.22
```

### Market

```text
      Market  count   pct
       LATAM  51594 28.58
      Europe  50252 27.84
Pacific Asia  41260 22.86
        USCA  25799 14.29
      Africa  11614  6.43
```

### Order City

```text
   Order City  count  pct
Santo Domingo   2211 1.22
New York City   2202 1.22
  Los Angeles   1845 1.02
  Tegucigalpa   1783 0.99
      Managua   1682 0.93
  Mexico City   1484 0.82
       Manila   1381 0.77
 Philadelphia   1302 0.72
San Francisco   1297 0.72
       London   1187 0.66
```

### Order Country

```text
 Order Country  count   pct
Estados Unidos  24840 13.76
       Francia  13222  7.32
        México  13172  7.30
      Alemania   9564  5.30
     Australia   8497  4.71
        Brasil   7987  4.42
   Reino Unido   7302  4.05
         China   5758  3.19
        Italia   4989  2.76
         India   4783  2.65
```

### order date (DateOrders)

```text
order date (DateOrders)  count  pct
       10/25/2016 14:39      5  0.0
         3/30/2016 4:37      5  0.0
        11/28/2016 1:18      5  0.0
         9/8/2015 12:15      5  0.0
          8/4/2017 2:31      5  0.0
         7/2/2015 19:42      5  0.0
         3/28/2015 0:55      5  0.0
         4/10/2015 0:02      5  0.0
        4/11/2017 15:49      5  0.0
        3/29/2015 10:33      5  0.0
```

### Order Region

```text
   Order Region  count   pct
Central America  28341 15.70
 Western Europe  27109 15.02
  South America  14935  8.27
        Oceania  10148  5.62
Northern Europe   9792  5.42
 Southeast Asia   9539  5.28
Southern Europe   9431  5.22
      Caribbean   8318  4.61
   West of USA    7993  4.43
     South Asia   7731  4.28
```

### Order State

```text
                Order State  count  pct
                 Inglaterra   6722 3.72
                 California   4966 2.75
            Isla de Francia   4580 2.54
Renania del Norte-Westfalia   3303 1.83
               San Salvador   3055 1.69
                 Nueva York   2753 1.53
           Distrito Federal   2559 1.42
                      Texas   2446 1.35
        Nueva Gales del Sur   2370 1.31
              Santo Domingo   2211 1.22
```

### Order Status

```text
   Order Status  count   pct
       COMPLETE  59491 32.96
PENDING_PAYMENT  39832 22.07
     PROCESSING  21902 12.13
        PENDING  20227 11.20
         CLOSED  19616 10.87
        ON_HOLD   9804  5.43
SUSPECTED_FRAUD   4062  2.25
       CANCELED   3692  2.05
 PAYMENT_REVIEW   1893  1.05
```

### Product Image

```text
                                                                         Product Image  count   pct
                      http://images.acmesports.sports/Perfect+Fitness+Perfect+Rip+Deck  24515 13.58
             http://images.acmesports.sports/Nike+Men%27s+CJ+Elite+2+TD+Football+Cleat  22246 12.32
                http://images.acmesports.sports/Nike+Men%27s+Dri-FIT+Victory+Golf+Polo  21035 11.65
                  http://images.acmesports.sports/O%27Brien+Men%27s+Neoprene+Life+Vest  19298 10.69
           http://images.acmesports.sports/Field+%26+Stream+Sportsman+16+Gun+Fire+Safe  17325  9.60
                           http://images.acmesports.sports/Pelican+Sunstream+100+Kayak  15500  8.59
http://images.acmesports.sports/Diamondback+Women%27s+Serene+Classic+Comfort+Bike+2014  13729  7.61
                 http://images.acmesports.sports/Nike+Men%27s+Free+5.0%2B+Running+Shoe  12169  6.74
http://images.acmesports.sports/Under+Armour+Girls%27+Toddler+Spine+Surge+Running+Shoe  10617  5.88
                                  http://images.acmesports.sports/Fighting+video+games    838  0.46
```

### Product Name

```text
                                 Product Name  count   pct
             Perfect Fitness Perfect Rip Deck  24515 13.58
      Nike Men's CJ Elite 2 TD Football Cleat  22246 12.32
         Nike Men's Dri-FIT Victory Golf Polo  21035 11.65
             O'Brien Men's Neoprene Life Vest  19298 10.69
    Field & Stream Sportsman 16 Gun Fire Safe  17325  9.60
                  Pelican Sunstream 100 Kayak  15500  8.59
Diamondback Women's Serene Classic Comfort Bi  13729  7.61
            Nike Men's Free 5.0+ Running Shoe  12169  6.74
Under Armour Girls' Toddler Spine Surge Runni  10617  5.88
                         Fighting video games    838  0.46
```

### shipping date (DateOrders)

```text
shipping date (DateOrders)  count  pct
            5/9/2015 18:02     10 0.01
           9/27/2015 20:28     10 0.01
           9/24/2015 23:48     10 0.01
            8/1/2015 18:37     10 0.01
          11/15/2016 13:45     10 0.01
           2/26/2017 23:36     10 0.01
            4/14/2017 4:26     10 0.01
             2/1/2015 2:35     10 0.01
            6/23/2017 4:20     10 0.01
            6/5/2017 12:25     10 0.01
```

### Shipping Mode

```text
 Shipping Mode  count   pct
Standard Class 107752 59.69
  Second Class  35216 19.51
   First Class  27814 15.41
      Same Day   9737  5.39
```

## Primeras observaciones automaticas

- Revisar columnas con muchos nulos antes de usarlas en analisis o modelos.

- Revisar columnas con cardinalidad muy alta: pueden ser IDs, texto libre o claves tecnicas.

- Revisar columnas de fecha detectadas automaticamente antes de hacer splits temporales.

- Si se modela una variable de entrega, retraso, fraude, venta o conversion, comprobar leakage antes del baseline.

---

# tokenized_access_logs


Archivo: `tokenized_access_logs.csv`

Filas: `469,977`

Columnas: `8`

Memoria aproximada en pandas: `243.52 MB`


## Como leer este CSV

Cada fila parece representar un evento de acceso web tokenizado: una visita o peticion registrada en logs, con campos tecnicos y de navegacion.

## Grupos de columnas

### Producto

- `Product`
- `Category`
- `Department`

### Logs y navegacion

- `Date`
- `ip`
- `url`

### Otras columnas

- `Month`
- `Hour`

## Head compacto con columnas clave

Esta es una version reducida del `.head()` para orientarse sin ver todas las columnas a la vez.

```text
                                      Product            Category          Date Month  Hour Department             ip                                                                                                                 url
      adidas Brazuca 2017 Official Match Ball baseball & softball 9/1/2017 6:00   Sep     6   fitness    37.97.182.65      /department/fitness/category/baseball%20&%20softball/product/adidas%20Brazuca%202017%20Official%20Match%20Ball
        The North Face Women's Recon Backpack  hunting & shooting 9/1/2017 6:00   Sep     6  fan shop    206.56.112.1      /department/fan%20shop/category/hunting%20&%20shooting/product/The%20North%20Face%20Women's%20Recon%20Backpack
       adidas Kids' RG III Mid Football Cleat      featured shops 9/1/2017 6:00   Sep     6   apparel   215.143.180.0            /department/apparel/category/featured%20shops/product/adidas%20Kids'%20RG%20III%20Mid%20Football%20Cleat
   Under Armour Men's Compression EV SL Slide         electronics 9/1/2017 6:00   Sep     6  footwear    206.56.112.1            /department/footwear/category/electronics/product/Under%20Armour%20Men's%20Compression%20EV%20SL%20Slide
                  Pelican Sunstream 100 Kayak        water sports 9/1/2017 6:01   Sep     6  fan shop  136.108.56.242                            /department/fan%20shop/category/water%20sports/product/Pelican%20Sunstream%20100%20Kayak
   Team Golf Tennessee Volunteers Putter Grip         accessories 9/1/2017 6:02   Sep     6  outdoors  116.202.25.156              /department/outdoors/category/accessories/product/Team%20Golf%20Tennessee%20Volunteers%20Putter%20Grip
        The North Face Women's Recon Backpack  hunting & shooting 9/1/2017 6:02   Sep     6  fan shop  131.132.236.70      /department/fan%20shop/category/hunting%20&%20shooting/product/The%20North%20Face%20Women's%20Recon%20Backpack
Diamondback Boys' Insight 24 Performance Hybr          basketball 9/1/2017 6:02   Sep     6   fitness  30.175.101.147 /department/fitness/category/basketball/product/Diamondback%20Boys'%20Insight%2024%20Performance%20Hybr/add_to_cart
```

## Head humano en formato ficha

### Fila 1

Lectura vertical: cada linea es una columna del CSV y su valor en esa fila.

#### Producto

| Campo | Valor | Como leerlo |
| --- | --- | --- |
| Product | adidas Brazuca 2017 Official Match Ball | Pendiente de interpretar; revisar con el diccionario o con analisis posterior. |
| Category | baseball & softball | Pendiente de interpretar; revisar con el diccionario o con analisis posterior. |
| Department | fitness | Pendiente de interpretar; revisar con el diccionario o con analisis posterior. |

#### Logs y navegacion

| Campo | Valor | Como leerlo |
| --- | --- | --- |
| Date | 9/1/2017 6:00 | Pendiente de interpretar; revisar con el diccionario o con analisis posterior. |
| ip | 37.97.182.65 | Pendiente de interpretar; revisar con el diccionario o con analisis posterior. |
| url | /department/fitness/category/baseball%20&%20softball/product/adidas%20Brazuca%202017%20... | Pendiente de interpretar; revisar con el diccionario o con analisis posterior. |

#### Otras columnas

| Campo | Valor | Como leerlo |
| --- | --- | --- |
| Month | Sep | Pendiente de interpretar; revisar con el diccionario o con analisis posterior. |
| Hour | 6 | Pendiente de interpretar; revisar con el diccionario o con analisis posterior. |

### Fila 2

Lectura vertical: cada linea es una columna del CSV y su valor en esa fila.

#### Producto

| Campo | Valor | Como leerlo |
| --- | --- | --- |
| Product | The North Face Women's Recon Backpack | Pendiente de interpretar; revisar con el diccionario o con analisis posterior. |
| Category | hunting & shooting | Pendiente de interpretar; revisar con el diccionario o con analisis posterior. |
| Department | fan shop | Pendiente de interpretar; revisar con el diccionario o con analisis posterior. |

#### Logs y navegacion

| Campo | Valor | Como leerlo |
| --- | --- | --- |
| Date | 9/1/2017 6:00 | Pendiente de interpretar; revisar con el diccionario o con analisis posterior. |
| ip | 206.56.112.1 | Pendiente de interpretar; revisar con el diccionario o con analisis posterior. |
| url | /department/fan%20shop/category/hunting%20&%20shooting/product/The%20North%20Face%20Wom... | Pendiente de interpretar; revisar con el diccionario o con analisis posterior. |

#### Otras columnas

| Campo | Valor | Como leerlo |
| --- | --- | --- |
| Month | Sep | Pendiente de interpretar; revisar con el diccionario o con analisis posterior. |
| Hour | 6 | Pendiente de interpretar; revisar con el diccionario o con analisis posterior. |

### Fila 3

Lectura vertical: cada linea es una columna del CSV y su valor en esa fila.

#### Producto

| Campo | Valor | Como leerlo |
| --- | --- | --- |
| Product | adidas Kids' RG III Mid Football Cleat | Pendiente de interpretar; revisar con el diccionario o con analisis posterior. |
| Category | featured shops | Pendiente de interpretar; revisar con el diccionario o con analisis posterior. |
| Department | apparel | Pendiente de interpretar; revisar con el diccionario o con analisis posterior. |

#### Logs y navegacion

| Campo | Valor | Como leerlo |
| --- | --- | --- |
| Date | 9/1/2017 6:00 | Pendiente de interpretar; revisar con el diccionario o con analisis posterior. |
| ip | 215.143.180.0 | Pendiente de interpretar; revisar con el diccionario o con analisis posterior. |
| url | /department/apparel/category/featured%20shops/product/adidas%20Kids'%20RG%20III%20Mid%2... | Pendiente de interpretar; revisar con el diccionario o con analisis posterior. |

#### Otras columnas

| Campo | Valor | Como leerlo |
| --- | --- | --- |
| Month | Sep | Pendiente de interpretar; revisar con el diccionario o con analisis posterior. |
| Hour | 6 | Pendiente de interpretar; revisar con el diccionario o con analisis posterior. |

## Info

```text
<class 'pandas.DataFrame'>
RangeIndex: 469977 entries, 0 to 469976
Data columns (total 8 columns):
 #   Column      Non-Null Count   Dtype
---  ------      --------------   -----
 0   Product     469977 non-null  str  
 1   Category    469977 non-null  str  
 2   Date        469977 non-null  str  
 3   Month       469977 non-null  str  
 4   Hour        469977 non-null  int64
 5   Department  469977 non-null  str  
 6   ip          469977 non-null  str  
 7   url         469977 non-null  str  
dtypes: int64(1), str(7)
memory usage: 28.7 MB
```

## Describe numerico

```text
         count       mean       std  min   25%   50%   75%   max
Hour  469977.0  14.591827  5.574014  0.0  10.0  15.0  20.0  23.0
```

## Describe categorico y general

```text
               count  unique                                                                                   top    freq       mean       std  min   25%   50%   75%   max
Product       469977      76                                                      Perfect Fitness Perfect Rip Deck   27878        NaN       NaN  NaN   NaN   NaN   NaN   NaN
Category      469977      33                                                                                cleats   27878        NaN       NaN  NaN   NaN   NaN   NaN   NaN
Date          469977  160815                                                                       9/14/2017 20:34     156        NaN       NaN  NaN   NaN   NaN   NaN   NaN
Month         469977       5                                                                                   Sep  137238        NaN       NaN  NaN   NaN   NaN   NaN   NaN
Hour        469977.0     NaN                                                                                   NaN     NaN  14.591827  5.574014  0.0  10.0  15.0  20.0  23.0
Department    469977       6                                                                             outdoors    79926        NaN       NaN  NaN   NaN   NaN   NaN   NaN
ip            469977    3340                                                                         157.21.93.193     566        NaN       NaN  NaN   NaN   NaN   NaN   NaN
url           469977     152  /department/apparel/category/cleats/product/Perfect%20Fitness%20Perfect%20Rip%20Deck   20258        NaN       NaN  NaN   NaN   NaN   NaN   NaN
```

## Tipos de datos

```text
dtype  column_count
  str             7
int64             1
```

## Nulos por columna

```text
            missing_count  missing_pct
Product                 0          0.0
Category                0          0.0
Date                    0          0.0
Month                   0          0.0
Hour                    0          0.0
Department              0          0.0
ip                      0          0.0
url                     0          0.0
```

## Cardinalidad

```text
            unique_values  unique_pct  dtype
Date               160815       34.22    str
ip                   3340        0.71    str
url                   152        0.03    str
Product                76        0.02    str
Category               33        0.01    str
Hour                   24        0.01  int64
Department              6        0.00    str
Month                   5        0.00    str
```

## Duplicados

Filas duplicadas exactas: `3,249` (0.69%).

## Columnas posiblemente de fecha

```text
  column  sample_parse_success_rate                min_sample_date                max_sample_date
0   Date                        1.0            2017-09-01 06:00:00            2017-10-10 15:56:00
1  Month                        1.0            0001-09-01 00:00:00            0001-10-01 00:00:00
2   Hour                        1.0  1970-01-01 00:00:00.000000005  1970-01-01 00:00:00.000000023
```

## Valores frecuentes en columnas categoricas

### Product

```text
                                      Product  count  pct
             Perfect Fitness Perfect Rip Deck  27878 5.93
       adidas Kids' RG III Mid Football Cleat  26200 5.57
         Nike Men's Dri-FIT Victory Golf Polo  25627 5.45
      Nike Men's CJ Elite 2 TD Football Cleat  25241 5.37
             O'Brien Men's Neoprene Life Vest  16194 3.45
                  Pelican Sunstream 100 Kayak  16186 3.44
Diamondback Women's Serene Classic Comfort Bi  15521 3.30
    Field & Stream Sportsman 16 Gun Fire Safe  15178 3.23
  Under Armour Hustle Storm Medium Duffle Bag  13752 2.93
      Columbia Men's PFG Anchor Tough T-Shirt  13716 2.92
```

### Category

```text
            Category  count  pct
              cleats  27878 5.93
       shop by sport  26227 5.58
      featured shops  26200 5.57
     women's apparel  25627 5.45
      men's footwear  25241 5.37
      girls' apparel  24581 5.23
         electronics  20845 4.44
indoor outdoor games  16194 3.45
        water sports  16186 3.44
  hunting & shooting  15645 3.33
```

### Date

```text
           Date  count  pct
9/14/2017 20:34    156 0.03
9/14/2017 20:37    152 0.03
9/14/2017 21:05    152 0.03
9/14/2017 20:44    150 0.03
9/14/2017 20:42    149 0.03
9/14/2017 21:14    147 0.03
9/14/2017 22:17    147 0.03
9/14/2017 20:59    146 0.03
9/14/2017 21:41    146 0.03
9/14/2017 21:24    145 0.03
```

### Month

```text
Month  count   pct
  Sep 137238 29.20
  Oct  84205 17.92
  Dec  84093 17.89
  Jan  83581 17.78
  Nov  80860 17.21
```

### Department

```text
Department  count   pct
 outdoors   79926 17.01
  apparel   79319 16.88
 footwear   79136 16.84
 fan shop   78724 16.75
  fitness   76437 16.26
     golf   76435 16.26
```

### ip

```text
             ip  count  pct
  157.21.93.193    566 0.12
 138.21.216.113    557 0.12
 77.137.114.147    516 0.11
   47.102.94.70    514 0.11
 83.234.215.133    514 0.11
 150.89.112.119    508 0.11
  211.122.14.29    505 0.11
 99.237.181.177    502 0.11
102.172.170.187    495 0.11
 69.214.176.127    493 0.10
```

### url

```text
                                                                                                                 url  count  pct
                                /department/apparel/category/cleats/product/Perfect%20Fitness%20Perfect%20Rip%20Deck  20258 4.31
            /department/apparel/category/featured%20shops/product/adidas%20Kids'%20RG%20III%20Mid%20Football%20Cleat  18643 3.97
                  /department/golf/category/women's%20apparel/product/Nike%20Men's%20Dri-FIT%20Victory%20Golf%20Polo  18372 3.91
         /department/apparel/category/men's%20footwear/product/Nike%20Men's%20CJ%20Elite%202%20TD%20Football%20Cleat  17963 3.82
             /department/fan%20shop/category/indoor/outdoor%20games/product/O'Brien%20Men's%20Neoprene%20Life%20Vest  11602 2.47
                            /department/fan%20shop/category/water%20sports/product/Pelican%20Sunstream%20100%20Kayak  11577 2.46
/department/fan%20shop/category/camping%20&%20hiking/product/Diamondback%20Women's%20Serene%20Classic%20Comfort%20Bi  11272 2.40
             /department/fan%20shop/category/fishing/product/Field%20&%20Stream%20Sportsman%2016%20Gun%20Fire%20Safe  10704 2.28
                /department/footwear/category/cardio%20equipment/product/Nike%20Men's%20Free%205.0+%20Running%20Shoe   9958 2.12
               /department/golf/category/shop%20by%20sport/product/Columbia%20Men's%20PFG%20Anchor%20Tough%20T-Shirt   9926 2.11
```

## Primeras observaciones automaticas

- Revisar columnas con muchos nulos antes de usarlas en analisis o modelos.

- Revisar columnas con cardinalidad muy alta: pueden ser IDs, texto libre o claves tecnicas.

- Revisar columnas de fecha detectadas automaticamente antes de hacer splits temporales.

- Si se modela una variable de entrega, retraso, fraude, venta o conversion, comprobar leakage antes del baseline.