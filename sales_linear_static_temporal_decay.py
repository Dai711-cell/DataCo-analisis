from __future__ import annotations

from pathlib import Path
from time import perf_counter

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score

from sales_linear_walk_forward import (
    CATEGORICAL_FEATURES,
    DATA_PATH,
    EXCLUDED_FOR_LEAKAGE,
    INITIAL_TRAIN_MONTHS,
    NUMERIC_FEATURES,
    TARGET,
    add_sales_features,
    image_block,
    make_model,
    mape_nonzero,
    markdown_table,
    wape,
)


PROJECT_DIR = Path(__file__).resolve().parent
REPORTS_DIR = PROJECT_DIR / "reports"
FIGURES_DIR = REPORTS_DIR / "figures" / "sales_linear_static_decay"
PROCESSED_DIR = PROJECT_DIR / "data" / "processed"
WALK_FORWARD_METRICS_PATH = PROCESSED_DIR / "sales_linear_walk_forward_metrics.csv"
WALK_FORWARD_SUMMARY_PATH = PROCESSED_DIR / "sales_linear_walk_forward_summary.csv"
REPORT_PATH = REPORTS_DIR / "sales_linear_static_decay_report.Rmd"
METRICS_PATH = PROCESSED_DIR / "sales_linear_static_decay_metrics.csv"
SUMMARY_PATH = PROCESSED_DIR / "sales_linear_static_decay_summary.csv"
PREDICTIONS_PATH = PROCESSED_DIR / "sales_linear_static_decay_predictions.csv"
RESIDUALS_PATH = PROCESSED_DIR / "sales_linear_static_decay_residuals.csv"
COMPARISON_PATH = PROCESSED_DIR / "sales_linear_static_vs_walk_forward.csv"
AUDIT_PATH = PROCESSED_DIR / "sales_linear_static_decay_audit.csv"

DEGRADATION_RATIO_THRESHOLD = 0.10
DEGRADATION_ABS_MAE_THRESHOLD = 2.0


def evaluate_month(
    month_index_after_train: int,
    test_month: str,
    y_true: pd.Series,
    y_pred: np.ndarray,
    train_rows: int,
    test_rows: int,
) -> dict[str, float | int | str]:
    clipped_pred = np.clip(y_pred, 0, None)
    mse = mean_squared_error(y_true, clipped_pred)
    residuals = y_true.to_numpy(dtype=float) - clipped_pred
    return {
        "month_index_after_train": month_index_after_train,
        "model": "Linear Regression static 2015",
        "train_month_start": "2015-01",
        "train_month_end": "2015-12",
        "test_month": test_month,
        "train_rows": train_rows,
        "test_rows": test_rows,
        "mae": mean_absolute_error(y_true, clipped_pred),
        "mse": mse,
        "rmse": float(np.sqrt(mse)),
        "r2": r2_score(y_true, clipped_pred),
        "wape": wape(y_true, clipped_pred),
        "mape_nonzero_actual": mape_nonzero(y_true, clipped_pred),
        "residual_mean": float(np.mean(residuals)),
        "residual_median": float(np.median(residuals)),
        "residual_std": float(np.std(residuals)),
    }


def weighted_summary(metrics: pd.DataFrame, predictions: pd.DataFrame, train_seconds: float, runtime_seconds: float) -> pd.DataFrame:
    mse = mean_squared_error(predictions[TARGET], predictions["prediction"])
    return pd.DataFrame(
        [
            {
                "model": "Linear Regression static 2015",
                "initial_train_months": INITIAL_TRAIN_MONTHS,
                "fit_count": 1,
                "test_months": len(metrics),
                "test_rows": len(predictions),
                "first_train_month": "2015-01",
                "last_train_month": "2015-12",
                "first_test_month": metrics["test_month"].min(),
                "last_test_month": metrics["test_month"].max(),
                "weighted_mae": mean_absolute_error(predictions[TARGET], predictions["prediction"]),
                "weighted_mse": mse,
                "global_rmse": float(np.sqrt(mse)),
                "global_r2": r2_score(predictions[TARGET], predictions["prediction"]),
                "global_wape": wape(predictions[TARGET], predictions["prediction"]),
                "global_mape": mape_nonzero(predictions[TARGET], predictions["prediction"]),
                "mean_month_mae": metrics["mae"].mean(),
                "median_month_mae": metrics["mae"].median(),
                "mean_month_wape": metrics["wape"].mean(),
                "train_seconds": train_seconds,
                "total_runtime_seconds": runtime_seconds,
            }
        ]
    )


def plot_static_vs_walk(comparison: pd.DataFrame, metric: str, output: Path) -> None:
    fig, ax = plt.subplots(figsize=(12, 5.8))
    ax.plot(
        comparison["test_month"],
        comparison[f"static_{metric}"],
        marker="o",
        linewidth=2,
        label="Modelo congelado",
        color="#E45756",
    )
    ax.plot(
        comparison["test_month"],
        comparison[f"walk_forward_{metric}"],
        marker="o",
        linewidth=2,
        label="Reentrenado mensual",
        color="#4C78A8",
    )
    ax.set_title(f"Modelo congelado vs reentrenado - {metric.upper()} por mes", fontsize=15, pad=12)
    ax.set_xlabel("Mes probado")
    ax.set_ylabel(metric.upper())
    ax.grid(axis="y", alpha=0.25)
    ax.tick_params(axis="x", rotation=60)
    ax.legend()
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    fig.savefig(output, dpi=150)
    plt.close(fig)


def plot_gap(comparison: pd.DataFrame, output: Path) -> None:
    fig, ax = plt.subplots(figsize=(12, 5.8))
    bars = ax.bar(comparison["test_month"], comparison["mae_gap_static_minus_walk"], color="#F58518")
    ax.axhline(0, color="black", linewidth=1)
    ax.axhline(DEGRADATION_ABS_MAE_THRESHOLD, color="#E45756", linestyle="--", linewidth=1)
    ax.set_title("Degradacion del modelo congelado frente al reentrenado", fontsize=15, pad=12)
    ax.set_xlabel("Mes probado")
    ax.set_ylabel("Diferencia de MAE")
    ax.grid(axis="y", alpha=0.25)
    ax.tick_params(axis="x", rotation=60)
    ax.bar_label(bars, fmt="%.1f", padding=2, fontsize=7)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    fig.savefig(output, dpi=150)
    plt.close(fig)


def plot_monthly_sales(predictions: pd.DataFrame, output: Path) -> None:
    monthly = (
        predictions.groupby("order_month_period", as_index=False)
        .agg(actual_sales=(TARGET, "sum"), predicted_sales=("prediction", "sum"))
        .rename(columns={"order_month_period": "test_month"})
    )
    fig, ax = plt.subplots(figsize=(12, 5.8))
    ax.plot(monthly["test_month"], monthly["actual_sales"], marker="o", linewidth=2, label="Sales real", color="#4C78A8")
    ax.plot(monthly["test_month"], monthly["predicted_sales"], marker="o", linewidth=2, label="Sales predicho", color="#E45756")
    ax.set_title("Modelo congelado - ventas reales vs predichas por mes", fontsize=15, pad=12)
    ax.set_xlabel("Mes probado")
    ax.set_ylabel("Sales")
    ax.grid(axis="y", alpha=0.25)
    ax.tick_params(axis="x", rotation=60)
    ax.legend()
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    fig.savefig(output, dpi=150)
    plt.close(fig)


def plot_residuals(residuals: pd.DataFrame, output: Path) -> None:
    fig, ax = plt.subplots(figsize=(10, 5.8))
    ax.hist(residuals["residual"], bins=60, color="#E45756", edgecolor="white")
    ax.axvline(0, color="black", linestyle="--", linewidth=1)
    ax.set_title("Modelo congelado - distribucion de residuos", fontsize=15, pad=12)
    ax.set_xlabel("Residuo = real - predicho")
    ax.set_ylabel("Frecuencia")
    ax.grid(axis="y", alpha=0.25)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    fig.savefig(output, dpi=150)
    plt.close(fig)


def write_report(
    summary: pd.DataFrame,
    walk_summary: pd.DataFrame,
    metrics: pd.DataFrame,
    comparison: pd.DataFrame,
    audit: pd.DataFrame,
) -> None:
    summary_row = summary.iloc[0]
    walk_row = walk_summary.iloc[0]
    first_ratio = comparison[comparison["degraded_over_10pct"]].head(1)
    first_abs = comparison[comparison["degraded_over_abs_threshold"]].head(1)
    worst = comparison.sort_values("mae_gap_static_minus_walk", ascending=False).iloc[0]

    if first_ratio.empty:
        ratio_text = "No supera el umbral del 10% de empeoramiento frente al modelo reentrenado en ningun mes."
    else:
        row = first_ratio.iloc[0]
        ratio_text = (
            f"Primer mes con degradacion relativa mayor al 10%: `{row['test_month']}`, "
            f"{int(row['month_index_after_train'])} meses despues del entrenamiento inicial."
        )

    if first_abs.empty:
        abs_text = "No supera el umbral absoluto de 2.0 puntos de MAE frente al modelo reentrenado en ningun mes."
        stable_text = "Con este umbral, no se observa degradacion clara dentro del periodo evaluado."
    else:
        row = first_abs.iloc[0]
        stable_months = int(row["month_index_after_train"]) - 1
        abs_text = (
            f"Primer mes con degradacion absoluta mayor a 2.0 MAE: `{row['test_month']}`, "
            f"{int(row['month_index_after_train'])} meses despues del entrenamiento inicial."
        )
        stable_text = (
            f"Lectura practica: el modelo congelado aguanta {stable_months} meses sin degradacion clara. "
            f"La primera senal fuerte aparece en el mes {int(row['month_index_after_train'])}, `{row['test_month']}`."
        )

    report = f"""---
title: "Degradacion Temporal - Modelo de Ventas Congelado"
subtitle: "Linear Regression entrenado una sola vez vs reentrenamiento mensual"
author: "Proyecto DataCo"
date: "{pd.Timestamp.today().date()}"
output:
  html_document:
    toc: true
    toc_depth: 2
    theme: flatly
---

```{{r setup, include=FALSE}}
knitr::opts_chunk$set(echo = FALSE, warning = FALSE, message = FALSE)
```

# Modelo Congelado

## Pregunta

En la validacion walk-forward anterior el modelo se reentrenaba en cada mes con una ventana expansiva. Este informe prueba lo contrario:

- se entrena una sola vez con los datos de 2015;
- se deja el modelo congelado;
- se predicen todos los meses futuros, de 2016-01 a 2018-01, sin volver a entrenar.

El objetivo es ver cuanto tarda en degradarse el modelo si no se actualiza.

---

# 1. Resultado General

| metrica | modelo congelado | reentrenado mensual |
| --- | ---: | ---: |
| fits del modelo | {int(summary_row["fit_count"])} | {int(walk_row["folds"])} |
| meses evaluados | {int(summary_row["test_months"])} | {int(walk_row["folds"])} |
| filas fuera de muestra | {int(summary_row["test_rows"])} | {int(walk_row["test_rows"])} |
| MAE | {summary_row["weighted_mae"]:.4f} | {float(walk_row["weighted_mae"]):.4f} |
| RMSE | {summary_row["global_rmse"]:.4f} | {float(walk_row["global_rmse"]):.4f} |
| R2 | {summary_row["global_r2"]:.4f} | {float(walk_row["global_r2"]):.4f} |
| WAPE | {summary_row["global_wape"]:.4f} | {float(walk_row["global_wape"]):.4f} |
| MAPE | {summary_row["global_mape"]:.4f} | {float(walk_row["global_mape"]):.4f} |

{ratio_text}

{abs_text}

{stable_text}

El peor gap frente al reentrenamiento mensual ocurre en `{worst["test_month"]}`: el modelo congelado queda {worst["mae_gap_static_minus_walk"]:.4f} puntos de MAE por encima del modelo reentrenado.

---

# 2. Auditoria

{markdown_table(audit)}

Lectura: se usa el mismo criterio de variables y leakage que en la validacion temporal anterior. La diferencia es solo operacional: aqui no se reentrena despues de 2015.

---

# 3. Comparacion Mes a Mes

{markdown_table(comparison[["test_month", "month_index_after_train", "static_mae", "walk_forward_mae", "mae_gap_static_minus_walk", "mae_ratio_static_vs_walk", "static_wape", "walk_forward_wape"]].round(4))}

{image_block(
    "MAE: modelo congelado vs reentrenado",
    "figures/sales_linear_static_decay/sales_static_vs_walk_mae.png",
    "Si la linea roja se separa de la azul, el modelo congelado empieza a perder ventaja por no actualizarse."
)}

{image_block(
    "WAPE: modelo congelado vs reentrenado",
    "figures/sales_linear_static_decay/sales_static_vs_walk_wape.png",
    "Compara el error relativo mensual sobre el volumen de ventas real."
)}

{image_block(
    "Gap de MAE por no reentrenar",
    "figures/sales_linear_static_decay/sales_static_walk_mae_gap.png",
    "Las barras positivas indican meses donde el modelo congelado comete mas error que el reentrenado."
)}

{image_block(
    "Ventas reales vs predichas con modelo congelado",
    "figures/sales_linear_static_decay/sales_static_actual_vs_predicted.png",
    "Revisa si el modelo congelado sigue el volumen mensual total, aunque no haya aprendido los meses recientes."
)}

{image_block(
    "Residuos del modelo congelado",
    "figures/sales_linear_static_decay/sales_static_residuals.png",
    "Distribucion global de errores de todas las predicciones futuras hechas sin reentrenar."
)}

---

# 4. Conclusion

El modelo congelado permite comprobar la degradacion real por falta de actualizacion. Si la diferencia frente al reentrenamiento mensual es pequena, el modelo puede actualizarse con menos frecuencia. Si el gap aparece pronto o se concentra en meses concretos, conviene reentrenar periodicamente o revisar cambios en mix de productos, volumen y descuentos.

En este problema concreto, `Sales` por linea sigue dependiendo sobre todo de precio, cantidad y descuento. Por eso el modelo puede aguantar relativamente bien sin reentrenar mientras esas relaciones no cambien de forma estructural.
"""
    REPORT_PATH.write_text(report, encoding="utf-8")


def main() -> None:
    start = perf_counter()
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    raw = pd.read_csv(DATA_PATH, low_memory=False)
    data = add_sales_features(raw).sort_values("order_datetime").reset_index(drop=True)
    feature_columns = CATEGORICAL_FEATURES + NUMERIC_FEATURES
    months = sorted(data["order_month_period"].dropna().unique())
    train_months = months[:INITIAL_TRAIN_MONTHS]
    test_months = months[INITIAL_TRAIN_MONTHS:]
    train_df = data[data["order_month_period"].isin(train_months)].copy()

    model = make_model()
    fit_start = perf_counter()
    model.fit(train_df[feature_columns], train_df[TARGET])
    train_seconds = perf_counter() - fit_start

    metrics_rows = []
    prediction_frames = []
    residual_frames = []
    for month_index, month in enumerate(test_months, start=1):
        test_df = data[data["order_month_period"].eq(month)].copy()
        y_pred = np.clip(model.predict(test_df[feature_columns]), 0, None)
        metrics_rows.append(
            evaluate_month(
                month_index_after_train=month_index,
                test_month=month,
                y_true=test_df[TARGET],
                y_pred=y_pred,
                train_rows=len(train_df),
                test_rows=len(test_df),
            )
        )
        predictions = test_df[
            [
                "order_datetime",
                "order_month_period",
                "Order Id",
                "Order Item Id",
                "Customer Id",
                "Product Name",
                "Category Name",
                "Order Country",
                "Order City",
                "Order Item Product Price",
                "Order Item Quantity",
                "Order Item Discount",
                TARGET,
            ]
        ].copy()
        predictions["month_index_after_train"] = month_index
        predictions["prediction"] = y_pred
        predictions["residual"] = predictions[TARGET] - predictions["prediction"]
        prediction_frames.append(predictions)
        residual_frames.append(
            predictions[
                ["month_index_after_train", "order_datetime", "order_month_period", TARGET, "prediction", "residual"]
            ].copy()
        )

    metrics = pd.DataFrame(metrics_rows)
    predictions_all = pd.concat(prediction_frames, ignore_index=True)
    residuals_all = pd.concat(residual_frames, ignore_index=True)
    summary = weighted_summary(metrics, predictions_all, train_seconds, perf_counter() - start)

    walk_metrics = pd.read_csv(WALK_FORWARD_METRICS_PATH)
    walk_summary = pd.read_csv(WALK_FORWARD_SUMMARY_PATH)
    comparison = metrics.merge(
        walk_metrics[["test_month_start", "mae", "rmse", "r2", "wape", "mape_nonzero_actual"]],
        left_on="test_month",
        right_on="test_month_start",
        how="left",
        suffixes=("_static", "_walk_forward"),
    ).drop(columns=["test_month_start"])
    comparison = comparison.rename(
        columns={
            "mae_static": "static_mae",
            "rmse_static": "static_rmse",
            "r2_static": "static_r2",
            "wape_static": "static_wape",
            "mape_nonzero_actual_static": "static_mape_nonzero_actual",
            "mae_walk_forward": "walk_forward_mae",
            "rmse_walk_forward": "walk_forward_rmse",
            "r2_walk_forward": "walk_forward_r2",
            "wape_walk_forward": "walk_forward_wape",
            "mape_nonzero_actual_walk_forward": "walk_forward_mape_nonzero_actual",
        }
    )
    comparison["mae_gap_static_minus_walk"] = comparison["static_mae"] - comparison["walk_forward_mae"]
    comparison["mae_ratio_static_vs_walk"] = comparison["static_mae"] / comparison["walk_forward_mae"]
    comparison["degraded_over_10pct"] = comparison["mae_ratio_static_vs_walk"].gt(1 + DEGRADATION_RATIO_THRESHOLD)
    comparison["degraded_over_abs_threshold"] = comparison["mae_gap_static_minus_walk"].gt(DEGRADATION_ABS_MAE_THRESHOLD)

    audit = pd.DataFrame(
        [
            {"check": "fit_count", "estado": 1, "lectura": "El modelo solo se entrena una vez con 2015"},
            {
                "check": "test_period",
                "estado": f"{test_months[0]} a {test_months[-1]}",
                "lectura": "Prediccion mensual futura sin reentrenar",
            },
            {
                "check": "categorical_encoding",
                "estado": "OneHotEncoder dentro del pipeline",
                "lectura": "Mismo pipeline que walk-forward; categorias nuevas controladas por handle_unknown",
            },
            {
                "check": "payment_one_hot",
                "estado": "bool en dataset, excluido del modelo",
                "lectura": "No se usa porque el metodo de pago no se conoce antes de completar compra",
            },
            {
                "check": "leakage_excluded",
                "estado": "excluido",
                "lectura": ", ".join(EXCLUDED_FOR_LEAKAGE),
            },
        ]
    )

    plot_static_vs_walk(comparison, "mae", FIGURES_DIR / "sales_static_vs_walk_mae.png")
    plot_static_vs_walk(comparison, "wape", FIGURES_DIR / "sales_static_vs_walk_wape.png")
    plot_gap(comparison, FIGURES_DIR / "sales_static_walk_mae_gap.png")
    plot_monthly_sales(predictions_all, FIGURES_DIR / "sales_static_actual_vs_predicted.png")
    plot_residuals(residuals_all, FIGURES_DIR / "sales_static_residuals.png")

    metrics.round(6).to_csv(METRICS_PATH, index=False)
    summary.round(6).to_csv(SUMMARY_PATH, index=False)
    predictions_all.round(6).to_csv(PREDICTIONS_PATH, index=False)
    residuals_all.round(6).to_csv(RESIDUALS_PATH, index=False)
    comparison.round(6).to_csv(COMPARISON_PATH, index=False)
    audit.to_csv(AUDIT_PATH, index=False)
    write_report(summary, walk_summary, metrics, comparison, audit)

    print(f"Generated {REPORT_PATH}")
    print(f"Generated {SUMMARY_PATH}")
    print(summary.to_string(index=False))
    print(comparison[["test_month", "static_mae", "walk_forward_mae", "mae_gap_static_minus_walk"]].to_string(index=False))


if __name__ == "__main__":
    main()
