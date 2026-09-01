# Data

Esta carpeta contiene salidas derivadas del analisis. Los datos originales deben mantenerse fuera de GitHub.

## Archivos raw esperados

Colocar en la raiz del proyecto, solo en local:

```text
DataCoSupplyChainDataset.csv
DescriptionDataCoSupplyChain.csv
tokenized_access_logs.csv
```

## `processed/`

Contiene tablas generadas por los scripts:

- datasets limpios;
- metricas de modelos;
- predicciones;
- residuos;
- auditorias de features;
- agregados para informes.

Estos archivos se excluyen del repo mediante `.gitignore` porque son regenerables y algunos son demasiado grandes para GitHub.

No sobrescribir nunca los CSV raw originales.

