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

Vista previa no incluida en la versión pública para evitar divulgar identificadores de clientes o direcciones IP.

## Head humano en formato ficha

Se omiten las muestras de registros completos en la versión pública porque pueden incluir datos identificativos.

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

Estadísticas descriptivas de columnas categóricas disponibles al ejecutar localmente el análisis; se omiten ejemplos de texto libre en la versión pública.

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

Los recuentos de categorías pueden reproducirse localmente; el informe público no incluye valores identificativos.

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

Vista previa no incluida en la versión pública para evitar divulgar identificadores de clientes o direcciones IP.

## Head humano en formato ficha

Se omiten las muestras de registros completos en la versión pública porque pueden incluir datos identificativos.

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

Estadísticas descriptivas de columnas categóricas disponibles al ejecutar localmente el análisis; se omiten ejemplos de texto libre en la versión pública.

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

Los recuentos de categorías pueden reproducirse localmente; el informe público no incluye valores identificativos.

## Primeras observaciones automaticas

- Revisar columnas con muchos nulos antes de usarlas en analisis o modelos.

- Revisar columnas con cardinalidad muy alta: pueden ser IDs, texto libre o claves tecnicas.

- Revisar columnas de fecha detectadas automaticamente antes de hacer splits temporales.

- Si se modela una variable de entrega, retraso, fraude, venta o conversion, comprobar leakage antes del baseline.