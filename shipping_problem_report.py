from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


PROJECT_DIR = Path(__file__).resolve().parent
DATA_PATH = PROJECT_DIR / "data" / "processed" / "dataco_supply_chain_processed.csv"
REPORTS_DIR = PROJECT_DIR / "reports"
FIGURES_DIR = REPORTS_DIR / "figures" / "shipping_problem"
REPORT_PATH = REPORTS_DIR / "shipping_problem_report.Rmd"

CRITICAL_MODES = ["First Class", "Second Class"]
MODE_ORDER = ["Standard Class", "Same Day", "Second Class", "First Class"]


def pct(series: pd.Series) -> pd.Series:
    return (series * 100).round(2)


def markdown_table(df: pd.DataFrame) -> str:
    if df.empty:
        return "Sin datos."
    headers = [str(column) for column in df.columns]
    lines = ["| " + " | ".join(headers) + " |"]
    lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
    for _, row in df.iterrows():
        values = []
        for value in row:
            values.append(str(value).replace("|", "\\|"))
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines)


def save_horizontal_bar(data: pd.Series, title: str, xlabel: str, output: Path, color: str = "#E15759") -> None:
    data = data.sort_values(ascending=True)
    fig_height = max(4, min(9, len(data) * 0.42 + 1.6))
    fig, ax = plt.subplots(figsize=(11, fig_height))
    bars = ax.barh(data.index.astype(str), data.values, color=color)
    ax.bar_label(bars, fmt="%.1f", padding=4, fontsize=9)
    ax.set_title(title, fontsize=15, pad=12)
    ax.set_xlabel(xlabel)
    ax.grid(axis="x", alpha=0.25)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    fig.savefig(output, dpi=150)
    plt.close(fig)


def save_definition_comparison(mode_summary: pd.DataFrame, output: Path) -> None:
    data = mode_summary.set_index("Shipping Mode").reindex(MODE_ORDER)
    x = range(len(data))
    fig, ax = plt.subplots(figsize=(11.5, 5.8))
    bars1 = ax.bar([i - 0.2 for i in x], data["official_late_pct"], width=0.4, label="Retraso oficial (Late_delivery_risk)", color="#E15759")
    bars2 = ax.bar([i + 0.2 for i in x], data["underestimated_rate_pct"], width=0.4, label="Promesa subestimada (dias reales > prometidos)", color="#F28E2B")
    ax.bar_label(bars1, fmt="%.1f", padding=3, fontsize=8)
    ax.bar_label(bars2, fmt="%.1f", padding=3, fontsize=8)
    ax.set_xticks(list(x))
    ax.set_xticklabels(data.index, rotation=0)
    ax.set_title("Dos formas de medir el problema de envio", fontsize=15, pad=12)
    ax.set_ylabel("% de pedidos")
    ax.set_ylim(0, 112)
    ax.legend(loc="upper left")
    ax.grid(axis="y", alpha=0.25)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    fig.savefig(output, dpi=150)
    plt.close(fig)


def save_grouped_month_bars(month_summary: pd.DataFrame, output: Path) -> None:
    pivot = month_summary.pivot(index="order_month", columns="Shipping Mode", values="official_late_pct").fillna(0)
    fig, ax = plt.subplots(figsize=(12, 5.5))
    pivot[CRITICAL_MODES].plot(kind="bar", ax=ax, color=["#E15759", "#F28E2B"])
    ax.set_title("Retraso oficial por mes en First Class y Second Class", fontsize=15, pad=12)
    ax.set_xlabel("Mes del pedido")
    ax.set_ylabel("% pedidos con retraso oficial")
    ax.grid(axis="y", alpha=0.25)
    ax.legend(title="Modo de envio")
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    fig.savefig(output, dpi=150)
    plt.close(fig)


def save_delay_distribution(df: pd.DataFrame, output: Path) -> None:
    dist = pd.crosstab(df["Shipping Mode"], df["delay_days"], normalize="index") * 100
    dist = dist.reindex(MODE_ORDER)
    fig, ax = plt.subplots(figsize=(12, 6))
    bottom = None
    colors = ["#59A14F", "#8CD17D", "#BAB0AC", "#F28E2B", "#E15759", "#B07AA1", "#9C755F"]
    for idx, column in enumerate(dist.columns):
        values = dist[column]
        ax.bar(dist.index, values, bottom=bottom, label=f"{column:+.0f} dias", color=colors[idx % len(colors)])
        bottom = values if bottom is None else bottom + values
    ax.set_title("Auditoria del error: dias reales - dias prometidos", fontsize=15, pad=12)
    ax.set_xlabel("Modo de envio")
    ax.set_ylabel("% de pedidos")
    ax.legend(title="Error", bbox_to_anchor=(1.02, 1), loc="upper left")
    ax.grid(axis="y", alpha=0.25)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    fig.savefig(output, dpi=150)
    plt.close(fig)


def save_country_panels(country_summary: pd.DataFrame, output: Path) -> None:
    fig, axes = plt.subplots(1, 2, figsize=(14, 6), sharex=True)
    colors = {"First Class": "#E15759", "Second Class": "#F28E2B"}
    for ax, mode in zip(axes, CRITICAL_MODES):
        data = country_summary[country_summary["Shipping Mode"].eq(mode)].head(10).sort_values("official_late_pct")
        bars = ax.barh(data["Order Country"], data["official_late_pct"], color=colors[mode])
        ax.bar_label(bars, fmt="%.1f", padding=3, fontsize=8)
        ax.set_title(f"{mode}: paises con mas retraso")
        ax.set_xlabel("% pedidos con retraso oficial")
        ax.grid(axis="x", alpha=0.25)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
    fig.suptitle("Paises criticos por modo de envio, minimo 300 pedidos", y=1.02, fontsize=15)
    fig.tight_layout()
    fig.savefig(output, dpi=150, bbox_inches="tight")
    plt.close(fig)


def save_city_chart(city_summary: pd.DataFrame, output: Path) -> None:
    data = city_summary.head(15).copy().sort_values("official_late_pct")
    labels = data["Shipping Mode"] + " | " + data["Order City"]
    fig, ax = plt.subplots(figsize=(11.5, 7))
    colors = data["Shipping Mode"].map({"First Class": "#E15759", "Second Class": "#F28E2B"}).fillna("#4C78A8")
    bars = ax.barh(labels, data["official_late_pct"], color=colors)
    ax.bar_label(bars, fmt="%.1f", padding=3, fontsize=8)
    ax.set_title("Ciudades con retraso mas alto en First/Second Class, minimo 150 pedidos", fontsize=15, pad=12)
    ax.set_xlabel("% pedidos con retraso oficial")
    ax.grid(axis="x", alpha=0.25)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    fig.savefig(output, dpi=150)
    plt.close(fig)


def image_block(title: str, path: str, note: str) -> str:
    return f"""## {title}

<img src=\"{path}\" alt=\"{title}\" width=\"920\">

**Lectura:** {note}
"""


def main() -> None:
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    df = pd.read_csv(DATA_PATH, low_memory=False)
    df["delay_days"] = df["Days for shipping (real)"] - df["Days for shipment (scheduled)"]
    df["underestimated_delivery"] = df["delay_days"].gt(0)

    mode_summary = (
        df.groupby("Shipping Mode")
        .agg(
            orders=("Order Id", "count"),
            official_late_rate=("is_late_delivery", "mean"),
            promised_days=("Days for shipment (scheduled)", "mean"),
            actual_days=("Days for shipping (real)", "mean"),
            mean_error_days=("delay_days", "mean"),
            underestimated_rate=("underestimated_delivery", "mean"),
            canceled_rate=("is_shipping_canceled", "mean"),
        )
        .reset_index()
    )
    mode_summary["official_late_pct"] = pct(mode_summary["official_late_rate"])
    mode_summary["underestimated_rate_pct"] = pct(mode_summary["underestimated_rate"])
    mode_summary["canceled_pct"] = pct(mode_summary["canceled_rate"])
    mode_summary = mode_summary.sort_values("official_late_pct", ascending=False)

    country_summary = (
        df.groupby(["Shipping Mode", "Order Country"])
        .agg(
            orders=("Order Id", "count"),
            official_late_rate=("is_late_delivery", "mean"),
            mean_error_days=("delay_days", "mean"),
        )
        .reset_index()
    )
    country_summary = country_summary[country_summary["orders"].ge(300)].copy()
    country_summary["official_late_pct"] = pct(country_summary["official_late_rate"])
    country_summary = country_summary.sort_values(["Shipping Mode", "official_late_pct"], ascending=[True, False])

    city_summary = (
        df[df["Shipping Mode"].isin(CRITICAL_MODES)]
        .groupby(["Shipping Mode", "Order City"])
        .agg(
            orders=("Order Id", "count"),
            official_late_rate=("is_late_delivery", "mean"),
            mean_error_days=("delay_days", "mean"),
        )
        .reset_index()
    )
    city_summary = city_summary[city_summary["orders"].ge(150)].copy()
    city_summary["official_late_pct"] = pct(city_summary["official_late_rate"])
    city_summary = city_summary.sort_values("official_late_pct", ascending=False)

    month_summary = (
        df[df["Shipping Mode"].isin(CRITICAL_MODES)]
        .groupby(["Shipping Mode", "order_month"])
        .agg(orders=("Order Id", "count"), official_late_rate=("is_late_delivery", "mean"), mean_error_days=("delay_days", "mean"))
        .reset_index()
    )
    month_summary["official_late_pct"] = pct(month_summary["official_late_rate"])

    delay_counts = pd.crosstab(df["Shipping Mode"], df["delay_days"]).reindex(MODE_ORDER)
    status_vs_arithmetic = pd.crosstab(df["Delivery Status"], df["underestimated_delivery"], normalize="index").round(4) * 100

    save_horizontal_bar(
        mode_summary.set_index("Shipping Mode")["official_late_pct"],
        "Tasa de retraso oficial por modo de envio",
        "% pedidos con Late_delivery_risk = 1",
        FIGURES_DIR / "shipping_late_rate_by_mode.png",
    )
    save_horizontal_bar(
        mode_summary.set_index("Shipping Mode")["mean_error_days"],
        "Error medio del sistema actual: dias reales - dias prometidos",
        "Error medio en dias",
        FIGURES_DIR / "shipping_prediction_error_by_mode.png",
        color="#F28E2B",
    )
    save_definition_comparison(mode_summary, FIGURES_DIR / "shipping_late_definition_comparison.png")
    save_delay_distribution(df, FIGURES_DIR / "shipping_delay_distribution_by_mode.png")
    save_country_panels(country_summary, FIGURES_DIR / "shipping_country_late_rate_first_second_top.png")
    save_city_chart(city_summary, FIGURES_DIR / "shipping_city_late_rate_first_second_top.png")
    save_grouped_month_bars(month_summary, FIGURES_DIR / "shipping_month_late_rate_first_second.png")

    mode_table = mode_summary[
        [
            "Shipping Mode",
            "orders",
            "official_late_pct",
            "underestimated_rate_pct",
            "promised_days",
            "actual_days",
            "mean_error_days",
            "canceled_pct",
        ]
    ].round(2)
    country_table = country_summary[country_summary["Shipping Mode"].isin(CRITICAL_MODES)].groupby("Shipping Mode").head(8)[
        ["Shipping Mode", "Order Country", "orders", "official_late_pct", "mean_error_days"]
    ].round(2)
    city_table = city_summary.head(12)[["Shipping Mode", "Order City", "orders", "official_late_pct", "mean_error_days"]].round(2)

    first = mode_summary[mode_summary["Shipping Mode"].eq("First Class")].iloc[0]
    second = mode_summary[mode_summary["Shipping Mode"].eq("Second Class")].iloc[0]
    standard = mode_summary[mode_summary["Shipping Mode"].eq("Standard Class")].iloc[0]

    report = f"""---
title: "Informe del Problema de Envio"
subtitle: "DataCo Supply Chain"
author: "Proyecto DataCo"
date: "2026-07-05"
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

<div align=\"center\">

# Informe del Problema de Envio

## DataCo Supply Chain

**Objetivo:** explicar por que los pedidos llegan tarde y si el sistema actual de dias prometidos sirve como prediccion de llegada.

</div>

---

# 1. Resumen Ejecutivo

El problema de envio no parece necesitar primero un modelo complejo para detectarse. La senal principal es muy clara: **el retraso esta concentrado en la forma de envio**.

| Hallazgo | Lectura |
| --- | --- |
| `First Class` | Promete `{first['promised_days']:.1f}` dia, pero tarda `{first['actual_days']:.1f}` dias de media. Retraso oficial: `{first['official_late_pct']:.2f}%`. Promesa subestimada: `{first['underestimated_rate_pct']:.2f}%`. |
| `Second Class` | Promete `{second['promised_days']:.1f}` dias, pero tarda `{second['actual_days']:.2f}` dias de media. Retraso oficial: `{second['official_late_pct']:.2f}%`. |
| `Standard Class` | Esta mucho mejor calibrado en media: promete `{standard['promised_days']:.1f}` dias y tarda `{standard['actual_days']:.2f}` dias de media, aunque aun tiene retrasos oficiales en `{standard['official_late_pct']:.2f}%`. |

**Conclusion:** el sistema actual que estima cuantos dias tardara un pedido es deficiente, especialmente para `First Class` y `Second Class`. Parece una regla fija por modo de envio, no una prediccion adaptada al pais, ciudad, fecha o contexto del pedido.

---

# 2. Definiciones Usadas

Hay dos formas de medir el problema y conviene separarlas:

| Medida | Formula | Que responde |
| --- | --- | --- |
| Retraso oficial | `Late_delivery_risk == 1` / `is_late_delivery == True` | El dataset marca el pedido como entrega tardia. |
| Promesa subestimada | `Days for shipping (real) > Days for shipment (scheduled)` | El pedido tardo mas dias reales que los prometidos por el sistema. |

Estas dos medidas son muy parecidas, pero no identicas. La diferencia aparece sobre todo en pedidos con `Shipping canceled`: algunos tienen mas dias reales que prometidos, pero no siempre se etiquetan como `Late delivery`.

---

{image_block('Grafico 1. Retraso oficial por modo de envio', 'figures/shipping_problem/shipping_late_rate_by_mode.png', '`First Class` y `Second Class` son los modos claramente problematicos. `First Class` esta casi siempre tarde y `Second Class` llega tarde en la mayor parte de los pedidos.')}

---

{image_block('Grafico 2. Error medio del sistema actual', 'figures/shipping_problem/shipping_prediction_error_by_mode.png', 'El error medio confirma que la promesa de llegada esta mal calibrada: `First Class` se queda corto por 1 dia y `Second Class` por casi 2 dias.')}

---

{image_block('Grafico 3. Retraso oficial vs promesa subestimada', 'figures/shipping_problem/shipping_late_definition_comparison.png', 'Este grafico explica por que algunos porcentajes no coinciden exactamente. `Standard Class` tiene 38.07% de retraso oficial, pero 39.77% de promesa subestimada. No es contradiccion: son definiciones distintas.')}

---

# 3. Auditoria del Grafico “Demasiado Perfecto”

El grafico de distribucion de error parece demasiado perfecto porque el dataset trae valores muy discretos:

- `First Class`: todos los pedidos tienen 2 dias reales y 1 dia prometido, por eso todos quedan en `+1` dia.
- `Second Class`: todos prometen 2 dias y los dias reales se reparten entre 2, 3, 4, 5 y 6.
- `Standard Class`: todos prometen 4 dias y los dias reales se reparten entre 2, 3, 4, 5 y 6.
- `Same Day`: promete 0 dias y aparece con 0 o 1 dia real.

Esto **no indica que el grafico este mal**. Indica que el sistema actual de promesa de dias es muy simple y probablemente poco personalizado.

Distribucion exacta de `delay_days = dias reales - dias prometidos`:

{markdown_table(delay_counts.reset_index())}

---

{image_block('Grafico 4. Distribucion del error por modo de envio', 'figures/shipping_problem/shipping_delay_distribution_by_mode.png', 'Aqui se ve la estructura artificial/discreta del campo de dias. Es util como auditoria del sistema actual, pero no debe confundirse con una distribucion natural continua.')}

---

# 4. Paises y Ciudades Criticas

La geografia importa, pero no explica el problema principal tan bien como `Shipping Mode`. En `First Class`, muchos paises tienen tasas cercanas al 95-98%, asi que el problema parece sistemico. En `Second Class`, el patron tambien se repite en varios paises.

{image_block('Grafico 5. Paises criticos en First Class y Second Class', 'figures/shipping_problem/shipping_country_late_rate_first_second_top.png', 'Los paises mas problematicos refuerzan la conclusion, pero no sustituyen al factor principal: la forma de envio.')}

Paises con mayor retraso oficial y volumen suficiente:

{markdown_table(country_table)}

---

{image_block('Grafico 6. Ciudades criticas en First Class y Second Class', 'figures/shipping_problem/shipping_city_late_rate_first_second_top.png', 'Las ciudades criticas muestran tasas altas, sobre todo en `First Class`, pero el patron sigue pareciendo estructural del modo de envio.')}

Ciudades con mayor retraso oficial:

{markdown_table(city_table)}

---

# 5. Meses: No Parece un Pico Puntual

{image_block('Grafico 7. Retraso por mes en First Class y Second Class', 'figures/shipping_problem/shipping_month_late_rate_first_second.png', 'El problema persiste durante todos los meses. No parece una temporada aislada ni un pico puntual.')}

---

# 6. Tabla Resumen Final

{markdown_table(mode_table)}

---

# 7. Interpretacion para el Proyecto

El problema actual no es solo que haya pedidos tarde. El problema mas interesante es que **la promesa de dias de llegada no esta bien calibrada**.

- `First Class` deberia prometer 2 dias si se usa una regla simple, no 1.
- `Second Class` necesita una prediccion mas fina: muchas entregas tardan entre 3 y 6 dias.
- `Standard Class` esta mejor calibrado en promedio, pero aun puede mejorarse para casos concretos.
- Pais, ciudad, region, mercado, categoria/producto y fecha pueden ayudar a mejorar una prediccion personalizada.

---

# 8. Siguiente Paso: Modelo de Llegada

Tiene sentido construir un modelo de prediccion de llegada mas eficiente que el sistema actual.

El baseline minimo deberia comparar:

1. **Sistema actual:** `Days for shipment (scheduled)`.
2. **Baseline simple:** media historica por `Shipping Mode`.
3. **Modelo inicial:** prediccion de `Days for shipping (real)` usando variables disponibles en el momento del pedido.

Variables candidatas sin leakage:

- `Shipping Mode`
- `Order Country`, `Order Region`, `Order City`, `Market`
- `order_month`, `order_dayofweek`, `order_hour`
- `Category Name`, `Department Name`, `Product Name`
- `Customer Segment`
- metodo de pago one-hot (`payment_type_*`)

Variables que no deben entrar como features porque filtran el resultado:

- `Delivery Status`
- `Late_delivery_risk`
- `is_late_delivery`
- `shipping date (DateOrders)` / `shipping_datetime`
- `Days for shipping (real)` si se predice llegada
- `shipping_hours_from_dates`
- `shipping_days_from_dates_exact`
- `shipping_days_from_dates_floor`

---

# 9. Nota de Auditoria

La diferencia entre `Standard Class` con 38.07% de retraso oficial y 39.77% de promesa subestimada no es un error del informe. Es una diferencia de definicion. El retraso oficial viene de la etiqueta del dataset; la promesa subestimada sale de comparar dias reales contra dias prometidos.

Tabla de relacion entre `Delivery Status` y promesa subestimada:

{markdown_table(status_vs_arithmetic.reset_index())}
"""

    REPORT_PATH.write_text(report, encoding="utf-8-sig")
    print(f"Informe generado: {REPORT_PATH}")
    print(f"Graficos generados en: {FIGURES_DIR}")


if __name__ == "__main__":
    main()