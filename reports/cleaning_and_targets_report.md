# Limpieza inicial DataCo Supply Chain


## Type a booleanos

Se convirtio `Type` a columnas booleanas one-hot para evitar codificacion ordinal artificial como 1, 2, 3 o 4.

Columnas creadas:

- `payment_type_cash`
- `payment_type_debit`
- `payment_type_payment`
- `payment_type_transfer`

## Fechas y dias de entrega

```text
                        field dtype_before                                                          interpretation
     Days for shipping (real)        int64                                    Ya viene como numero entero de dias.
Days for shipment (scheduled)        int64                                    Ya viene como numero entero de dias.
      order date (DateOrders)          str Viene como texto/fecha. Parseado a datetime con 0 valores no parseados.
   shipping date (DateOrders)          str Viene como texto/fecha. Parseado a datetime con 0 valores no parseados.
```

Columnas creadas desde las fechas: `order_datetime`, `shipping_datetime`, `shipping_hours_from_dates`, `shipping_days_from_dates_exact` y `shipping_days_from_dates_floor`.

Diferencias entre `shipping_days_from_dates_floor` y `Days for shipping (real)`: `4,657` filas.

Filas sin diferencia calculable por fechas no parseadas: `0`.

Distribucion especial cuando la diferencia real entre fechas es de 12 horas (`0.5` dias):

```text
 original_days_for_12_hours  count
                          0   5080
                          1   4657
```

## Targets derivados para pedidos problematicos

```text
                      positive_count  positive_pct
is_late_delivery               98977         54.83
is_shipping_canceled            7754          4.30
is_order_canceled               3692          2.05
is_suspected_fraud              4062          2.25
is_payment_problem             41725         23.11
is_order_problem              124452         68.94
```

## Nota de leakage

Para predecir retraso antes del envio, no usar como features `Delivery Status`, `shipping_datetime`, `shipping date (DateOrders)`, `Days for shipping (real)`, `shipping_hours_from_dates`, `shipping_days_from_dates_exact`, `shipping_days_from_dates_floor` ni `is_late_delivery`, porque contienen informacion posterior o directamente el target.

---

# Variables de devoluciones, quejas y objetivos posibles


## Variables explicitas encontradas

No se encontraron columnas explicitas de devoluciones, quejas, reclamaciones o refunds en los dos CSV analizados.

## Senales utiles que si existen

### Order Status

```text
   order_status  count   pct
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

### Delivery Status

```text
  delivery_status  count   pct
    Late delivery  98977 54.83
 Advance shipping  41592 23.04
 Shipping on time  32196 17.84
Shipping canceled   7754  4.30
```

### Late_delivery_risk

```text
 late_delivery_risk  count   pct
                  1  98977 54.83
                  0  81542 45.17
```

### Busqueda de palabras en URLs de logs

```text
return          0
refund          0
complaint       0
claim           0
devol           0
queja           0
cancel          0
fraud           0
hold         1048
pending         0
late            0
```

## Lectura practica

- Para devoluciones o quejas: no hay una variable directa en estos CSV.

- Para mejorar prediccion de pedidos problematicos: `Late_delivery_risk` es el objetivo mas claro.

- Tambien se pueden plantear objetivos separados como `is_order_canceled`, `is_suspected_fraud`, `is_payment_problem` o `is_shipping_canceled`.

- Cuidado: si se predice retraso antes de enviar, `Delivery Status`, `shipping date (DateOrders)` y `Days for shipping (real)` son leakage y no deberian usarse como features.