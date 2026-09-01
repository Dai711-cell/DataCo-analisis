from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


PROJECT_DIR = Path(__file__).resolve().parent
PROCESSED_DIR = PROJECT_DIR / "data" / "processed"
REPORTS_DIR = PROJECT_DIR / "reports"
FIGURES_DIR = REPORTS_DIR / "figures" / "demand_business"

METRICS_PATH = PROCESSED_DIR / "daily_product_quantity_forecast_metrics.csv"
DATASET_PATH = PROCESSED_DIR / "daily_product_quantity_forecast_dataset.csv"
REPORT_PATH = REPORTS_DIR / "demand_business_recommendation_report.Rmd"


def fmt(value: float, digits: int = 4) -> str:
    return f"{value:.{digits}f}"


def pct(value: float) -> str:
    return f"{value:.1%}"


def markdown_table(df: pd.DataFrame) -> str:
    if df.empty:
        return "_Sin datos._"
    table = df.copy().where(pd.notna(df), "")
    columns = [str(column) for column in table.columns]
    header = "| " + " | ".join(columns) + " |"
    separator = "| " + " | ".join("---" for _ in columns) + " |"
    rows = []
    for row in table.astype(str).itertuples(index=False, name=None):
        rows.append("| " + " | ".join(value.replace("|", "/") for value in row) + " |")
    return "\n".join([header, separator, *rows])


def plot_bar(data: pd.DataFrame, metric: str, title: str, output: Path, color: str = "#4C78A8") -> None:
    plot_data = data.sort_values(metric, ascending=True)
    fig, ax = plt.subplots(figsize=(10, 5.6))
    bars = ax.barh(plot_data["Sistema"], plot_data[metric], color=color)
    ax.invert_yaxis()
    ax.bar_label(bars, fmt="%.4f", padding=4, fontsize=9)
    ax.set_title(title, fontsize=15, pad=12)
    ax.set_xlabel(metric.upper())
    ax.grid(axis="x", alpha=0.25)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    fig.savefig(output, dpi=150)
    plt.close(fig)


def plot_monthly_demand(dataset: pd.DataFrame, output: Path) -> pd.DataFrame:
    test = dataset[dataset["order_date"].ge(pd.Timestamp("2017-01-01"))].copy()
    test["recommended_prediction"] = test["product_quantity_sold_roll_mean_7d"].fillna(0)
    monthly = (
        test.groupby(test["order_date"].dt.to_period("M").astype(str), as_index=False)
        .agg(
            actual_quantity=("quantity_sold", "sum"),
            predicted_quantity=("recommended_prediction", "sum"),
        )
        .rename(columns={"order_date": "month"})
    )
    fig, ax = plt.subplots(figsize=(11, 5.8))
    ax.plot(monthly["month"], monthly["actual_quantity"], marker="o", linewidth=2, color="#4C78A8", label="Demanda real")
    ax.plot(
        monthly["month"],
        monthly["predicted_quantity"],
        marker="o",
        linewidth=2,
        color="#54A24B",
        label="Baseline rolling 7 dias",
    )
    ax.set_title("Demanda mensual real vs referencia recomendada", fontsize=15, pad=12)
    ax.set_xlabel("Mes")
    ax.set_ylabel("Unidades")
    ax.tick_params(axis="x", rotation=45)
    ax.grid(axis="y", alpha=0.25)
    ax.legend()
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    fig.savefig(output, dpi=150)
    plt.close(fig)
    return monthly


def main() -> None:
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    metrics = pd.read_csv(METRICS_PATH)
    test_metrics = metrics[metrics["split"].eq("test")].copy()
    selected_names = [
        "Baseline rolling 7d by Product",
        "Baseline lag 1d by Product",
        "Baseline rolling 30d by Product",
        "Decision Tree",
        "Hist Gradient Boosting",
        "Random Forest",
        "Baseline product train mean",
        "Baseline global train mean",
    ]
    selected = test_metrics[test_metrics["model"].isin(selected_names)].copy()
    selected["Sistema"] = selected["model"].replace(
        {
            "Baseline rolling 7d by Product": "Referencia 7 dias por producto",
            "Baseline lag 1d by Product": "Ultimo dia por producto",
            "Baseline rolling 30d by Product": "Referencia 30 dias por producto",
            "Decision Tree": "Decision Tree",
            "Hist Gradient Boosting": "Gradient Boosting",
            "Random Forest": "Random Forest",
            "Baseline product train mean": "Media historica por producto",
            "Baseline global train mean": "Media global",
        }
    )
    selected = selected.sort_values("mae")

    best = selected.iloc[0]
    best_ml = selected[~selected["model"].str.startswith("Baseline")].sort_values("mae").iloc[0]
    gap_mae = best_ml["mae"] - best["mae"]
    gap_pct = gap_mae / best["mae"]

    plot_bar(selected, "mae", "Error medio por producto-dia", FIGURES_DIR / "demand_business_mae.png")
    plot_bar(selected, "wape", "Error relativo total sobre unidades vendidas", FIGURES_DIR / "demand_business_wape.png", "#5F9E6E")

    dataset = pd.read_csv(DATASET_PATH, parse_dates=["order_date"])
    monthly = plot_monthly_demand(dataset, FIGURES_DIR / "demand_business_monthly_demand.png")
    total_actual = monthly["actual_quantity"].sum()
    total_pred = monthly["predicted_quantity"].sum()
    total_gap = total_pred - total_actual
    total_gap_pct = total_gap / total_actual if total_actual else np.nan

    business_table = pd.DataFrame(
        [
            {
                "Sistema": "Referencia 7 dias por producto",
                "MAE": fmt(float(best["mae"])),
                "RMSE": fmt(float(best["rmse"])),
                "R2": fmt(float(best["r2"])),
                "WAPE": fmt(float(best["wape"])),
                "Lectura comercial": "Mejor opcion: simple, estable y facil de mantener",
            },
            {
                "Sistema": "Mejor modelo ML",
                "MAE": fmt(float(best_ml["mae"])),
                "RMSE": fmt(float(best_ml["rmse"])),
                "R2": fmt(float(best_ml["r2"])),
                "WAPE": fmt(float(best_ml["wape"])),
                "Lectura comercial": "No mejora al baseline; agrega complejidad sin beneficio",
            },
            {
                "Sistema": "Media historica por producto",
                "MAE": fmt(float(selected[selected["model"].eq("Baseline product train mean")].iloc[0]["mae"])),
                "RMSE": fmt(float(selected[selected["model"].eq("Baseline product train mean")].iloc[0]["rmse"])),
                "R2": fmt(float(selected[selected["model"].eq("Baseline product train mean")].iloc[0]["r2"])),
                "WAPE": fmt(float(selected[selected["model"].eq("Baseline product train mean")].iloc[0]["wape"])),
                "Lectura comercial": "Demasiado lenta para cambios recientes de demanda",
            },
        ]
    )

    report = f"""---
title: "Recomendacion de Demanda DataCo"
subtitle: "Forecast diario de unidades vendidas por producto"
author: "Proyecto DataCo"
date: "{pd.Timestamp.today().date()}"
output:
  html_document:
    toc: true
    toc_depth: 2
    number_sections: true
    theme: readable
    df_print: paged
---

```{{r setup, include=FALSE}}
knitr::opts_chunk$set(echo = FALSE, warning = FALSE, message = FALSE)
```

<div align="center">

# Recomendacion de Demanda DataCo

## Usar una referencia historica simple por producto

**Recomendacion principal:** usar una referencia de demanda basada en el rolling de los ultimos 7 dias por producto como punto de partida operativo. Los modelos de machine learning probados no superan esta regla simple, por lo que no deberian ser la primera solucion para planificar unidades diarias.

</div>

---

# 1. Resumen Ejecutivo

El objetivo comercial es anticipar cuantas unidades se venderan por producto y dia para mejorar la planificacion.

La comparacion muestra que la mejor referencia actual no es un modelo complejo, sino una regla historica simple: el promedio movil de los ultimos 7 dias por producto.

La empresa deberia usar esta referencia como baseline operativo, medir su rendimiento por producto/categoria y solo avanzar a modelos mas complejos cuando existan senales adicionales que no estan hoy en el dataset: stock, promociones planificadas, campanas, precio futuro real, visitas web futuras o calendario comercial detallado.

---

# 2. Decision Comercial

Comparacion de alternativas principales:

{markdown_table(business_table)}

El mejor modelo ML queda **{fmt(float(gap_mae))} unidades de MAE** por encima del baseline recomendado. Esto equivale a **{pct(float(gap_pct))} mas error** por producto-dia.

## Grafico 1. Error medio por producto-dia

<img src="figures/demand_business/demand_business_mae.png" alt="Comparacion de MAE" width="920">

**Lectura:** la referencia historica de 7 dias por producto es la opcion con menor error. Los modelos complejos quedan por detras.

---

# 3. Error Relativo Sobre Unidades Vendidas

El WAPE permite ver el error total frente al volumen real de unidades vendidas. Tambien aqui gana la referencia de 7 dias por producto.

| Sistema | WAPE | Lectura comercial |
| --- | ---: | --- |
| Referencia 7 dias por producto | {fmt(float(best['wape']))} | Mejor equilibrio entre precision y simplicidad |
| Mejor modelo ML | {fmt(float(best_ml['wape']))} | Peor error relativo y mayor complejidad |
| Media historica por producto | {fmt(float(selected[selected['model'].eq('Baseline product train mean')].iloc[0]['wape']))} | No reacciona suficiente a cambios recientes |

## Grafico 2. Error relativo total

<img src="figures/demand_business/demand_business_wape.png" alt="Comparacion de WAPE" width="920">

**Lectura:** el baseline recomendado no solo gana en MAE; tambien gana al medir el error relativo total sobre unidades vendidas.

---

# 4. Comportamiento Mensual

En el periodo de test, la demanda real suma **{total_actual:,.0f} unidades**. La referencia rolling 7 dias estima **{total_pred:,.0f} unidades**, una diferencia agregada de **{total_gap:,.0f} unidades** ({pct(float(total_gap_pct))}).

## Grafico 3. Demanda mensual real vs referencia recomendada

<img src="figures/demand_business/demand_business_monthly_demand.png" alt="Demanda mensual real vs forecast" width="920">

**Lectura:** la referencia historica sigue el nivel general de demanda. La caida del final del dataset tambien aparece en la prediccion porque el rolling recoge cambios recientes.

---

# 5. Prioridad Operativa

La empresa deberia tratar este resultado como una decision de control y planificacion, no como una demostracion de que un modelo complejo ya aporta valor.

| Prioridad | Accion | Motivo |
| --- | --- | --- |
| 1 | Adoptar rolling 7 dias por producto como referencia base | Es la opcion mas precisa y facil de mantener |
| 2 | Medir errores por producto y categoria | La demanda no falla igual en todos los productos |
| 3 | Probar agregacion semanal | Puede reducir ruido diario y mejorar la utilidad operativa |
| 4 | Incorporar senales reales de negocio | Stock, promociones, campanas, precio futuro y trafico web futuro |
| 5 | Reentrenar modelos solo si superan al baseline | La complejidad debe justificarse con mejora medible |

---

# 6. Decision Final

La recomendacion final es usar **rolling 7 dias por producto** como referencia inicial para planificar demanda diaria.

Esta opcion permite:

- trabajar directamente con unidades vendidas por producto y dia;
- utilizar exclusivamente informacion disponible antes de cada prediccion;
- usar una regla transparente para operaciones y negocio;
- superar a los modelos ML probados en MAE y WAPE;
- mantener una base clara para futuras mejoras.

Los modelos complejos quedan como una segunda fase. Para que tengan sentido, el dataset necesita senales que expliquen cambios futuros de demanda, no solo historicos internos.
"""
    REPORT_PATH.write_text(report, encoding="utf-8")
    print(f"Generated {REPORT_PATH}")
    print(f"Generated {FIGURES_DIR}")


if __name__ == "__main__":
    main()
