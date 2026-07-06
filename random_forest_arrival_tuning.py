from __future__ import annotations

from pathlib import Path
from time import perf_counter

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OrdinalEncoder


PROJECT_DIR = Path(__file__).resolve().parent
DATA_PATH = PROJECT_DIR / "data" / "processed" / "dataco_supply_chain_processed.csv"
REPORTS_DIR = PROJECT_DIR / "reports"
FIGURES_DIR = REPORTS_DIR / "figures" / "random_forest_arrival"
PROCESSED_DIR = PROJECT_DIR / "data" / "processed"
REPORT_PATH = REPORTS_DIR / "random_forest_arrival_tuning_report.Rmd"
METRICS_PATH = PROCESSED_DIR / "random_forest_arrival_tuning_metrics.csv"
PREDICTIONS_PATH = PROCESSED_DIR / "random_forest_arrival_tuning_predictions.csv"
IMPORTANCE_PATH = PROCESSED_DIR / "random_forest_arrival_feature_importance.csv"
RESIDUALS_PATH = PROCESSED_DIR / "random_forest_arrival_residuals.csv"

RANDOM_STATE = 42
TEST_SIZE = 0.2
TARGET = "Days for shipping (real)"
CURRENT_SYSTEM_PREDICTION = "Days for shipment (scheduled)"

CATEGORICAL_FEATURES = [
    "Shipping Mode",
    "Order Country",
    "Order Region",
    "Order State",
    "Order City",
    "Market",
    "Customer Segment",
    "Category Name",
    "Department Name",
    "Product Name",
    "Type",
]

NUMERIC_FEATURES = [
    "Order Item Quantity",
    "order_year",
    "order_month",
    "order_day",
    "order_dayofweek",
    "order_dayofyear",
    "order_weekofyear",
    "order_quarter",
    "order_hour",
    "order_is_weekend",
    "order_month_sin",
    "order_month_cos",
    "order_dayofweek_sin",
    "order_dayofweek_cos",
    "payment_type_cash",
    "payment_type_debit",
    "payment_type_payment",
    "payment_type_transfer",
]

LEAKAGE_COLUMNS = [
    "Delivery Status",
    "Late_delivery_risk",
    "is_late_delivery",
    "shipping date (DateOrders)",
    "shipping_datetime",
    "shipping_month",
    "shipping_dayofweek",
    "shipping_hour",
    "Days for shipping (real)",
    "shipping_hours_from_dates",
    "shipping_days_from_dates_exact",
    "shipping_days_from_dates_floor",
]

RF_CONFIGS = [
    {
        "model": "RF_base_previous",
        "n_estimators": 120,
        "max_depth": 18,
        "min_samples_leaf": 8,
        "min_samples_split": 16,
        "max_features": 1.0,
        "bootstrap": True,
    },
    {
        "model": "RF_deeper_leaf4",
        "n_estimators": 180,
        "max_depth": 26,
        "min_samples_leaf": 4,
        "min_samples_split": 10,
        "max_features": 0.8,
        "bootstrap": True,
    },
    {
        "model": "RF_regularized_leaf12",
        "n_estimators": 180,
        "max_depth": 16,
        "min_samples_leaf": 12,
        "min_samples_split": 24,
        "max_features": "sqrt",
        "bootstrap": True,
    },
    {
        "model": "RF_deep_leaf2",
        "n_estimators": 220,
        "max_depth": 30,
        "min_samples_leaf": 2,
        "min_samples_split": 6,
        "max_features": 0.7,
        "bootstrap": True,
    },
]


def add_order_date_features(df: pd.DataFrame) -> pd.DataFrame:
    result = df.copy()
    result["order_datetime"] = pd.to_datetime(result["order_datetime"], errors="coerce")
    result["order_year"] = result["order_datetime"].dt.year
    result["order_month"] = result["order_datetime"].dt.month
    result["order_day"] = result["order_datetime"].dt.day
    result["order_dayofweek"] = result["order_datetime"].dt.dayofweek
    result["order_dayofyear"] = result["order_datetime"].dt.dayofyear
    result["order_weekofyear"] = result["order_datetime"].dt.isocalendar().week.astype(float)
    result["order_quarter"] = result["order_datetime"].dt.quarter
    result["order_hour"] = result["order_datetime"].dt.hour
    result["order_is_weekend"] = result["order_dayofweek"].isin([5, 6]).astype(int)
    result["order_month_sin"] = np.sin(2 * np.pi * result["order_month"] / 12)
    result["order_month_cos"] = np.cos(2 * np.pi * result["order_month"] / 12)
    result["order_dayofweek_sin"] = np.sin(2 * np.pi * result["order_dayofweek"] / 7)
    result["order_dayofweek_cos"] = np.cos(2 * np.pi * result["order_dayofweek"] / 7)
    return result


def temporal_train_test_split(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    sorted_df = df.sort_values("order_datetime").reset_index(drop=True)
    split_index = int(len(sorted_df) * (1 - TEST_SIZE))
    return sorted_df.iloc[:split_index].copy(), sorted_df.iloc[split_index:].copy()


def make_preprocessor(categorical_features: list[str], numeric_features: list[str]) -> ColumnTransformer:
    return ColumnTransformer(
        transformers=[
            (
                "categorical",
                Pipeline(
                    steps=[
                        ("imputer", SimpleImputer(strategy="most_frequent")),
                        ("ordinal", OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1)),
                    ]
                ),
                categorical_features,
            ),
            (
                "numeric",
                Pipeline(steps=[("imputer", SimpleImputer(strategy="median"))]),
                numeric_features,
            ),
        ]
    )


def wape(y_true: pd.Series, y_pred: np.ndarray) -> float:
    denominator = np.abs(y_true).sum()
    if denominator == 0:
        return np.nan
    return float(np.abs(y_true - y_pred).sum() / denominator)


def mape_nonzero(y_true: pd.Series, y_pred: np.ndarray) -> float:
    y_true_array = y_true.to_numpy(dtype=float)
    mask = y_true_array != 0
    if not mask.any():
        return np.nan
    return float(np.mean(np.abs((y_true_array[mask] - y_pred[mask]) / y_true_array[mask])))


def evaluate_predictions(model_name: str, split: str, y_true: pd.Series, y_pred: np.ndarray, train_seconds: float | None = None) -> dict[str, float | str | None]:
    y_pred = np.clip(y_pred, 0, None)
    mse = mean_squared_error(y_true, y_pred)
    residuals = y_true.to_numpy(dtype=float) - y_pred
    return {
        "model": model_name,
        "split": split,
        "mae": mean_absolute_error(y_true, y_pred),
        "mse": mse,
        "rmse": float(np.sqrt(mse)),
        "r2": r2_score(y_true, y_pred),
        "wape": wape(y_true, y_pred),
        "mape_nonzero_actual": mape_nonzero(y_true, y_pred),
        "residual_mean": float(np.mean(residuals)),
        "residual_median": float(np.median(residuals)),
        "residual_std": float(np.std(residuals)),
        "train_seconds": train_seconds,
    }


def plot_metric(metrics: pd.DataFrame, metric: str, title: str, output: Path, lower_is_better: bool = True) -> None:
    data = metrics[metrics["split"].eq("test")].sort_values(metric, ascending=lower_is_better)
    fig, ax = plt.subplots(figsize=(11, 5.5))
    bars = ax.barh(data["model"], data[metric], color="#4C78A8")
    ax.invert_yaxis()
    ax.bar_label(bars, fmt="%.4f", padding=4, fontsize=8)
    ax.set_title(title, fontsize=15, pad=12)
    ax.set_xlabel(metric)
    ax.grid(axis="x", alpha=0.25)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    fig.savefig(output, dpi=150)
    plt.close(fig)


def plot_residual_hist(residuals: pd.DataFrame, best_model: str, output: Path) -> None:
    data = residuals[residuals["model"].eq(best_model)]["residual"]
    fig, ax = plt.subplots(figsize=(10, 5.5))
    ax.hist(data, bins=35, color="#F28E2B", edgecolor="white")
    ax.axvline(0, color="black", linestyle="--", linewidth=1)
    ax.set_title(f"Distribucion de residuos - {best_model}", fontsize=15, pad=12)
    ax.set_xlabel("Residuo = real - predicho")
    ax.set_ylabel("Frecuencia")
    ax.grid(axis="y", alpha=0.25)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    fig.savefig(output, dpi=150)
    plt.close(fig)


def plot_residual_by_predicted(residuals: pd.DataFrame, best_model: str, output: Path) -> None:
    data = residuals[residuals["model"].eq(best_model)].sample(frac=1, random_state=RANDOM_STATE).head(12000)
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.scatter(data["predicted_days"], data["residual"], s=10, alpha=0.25, color="#E15759")
    ax.axhline(0, color="black", linestyle="--", linewidth=1)
    ax.set_title(f"Residuos vs prediccion - {best_model}", fontsize=15, pad=12)
    ax.set_xlabel("Dias predichos")
    ax.set_ylabel("Residuo = real - predicho")
    ax.grid(alpha=0.2)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    fig.savefig(output, dpi=150)
    plt.close(fig)


def plot_mae_by_mode(residuals: pd.DataFrame, best_model: str, output: Path) -> None:
    data = residuals[residuals["model"].eq(best_model)].copy()
    grouped = data.groupby("Shipping Mode")["absolute_error"].mean().sort_values(ascending=True)
    fig, ax = plt.subplots(figsize=(10, 5.5))
    bars = ax.barh(grouped.index, grouped.values, color="#59A14F")
    ax.bar_label(bars, fmt="%.3f", padding=4)
    ax.set_title(f"MAE por tipo de envio - {best_model}", fontsize=15, pad=12)
    ax.set_xlabel("MAE en dias")
    ax.grid(axis="x", alpha=0.25)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    fig.savefig(output, dpi=150)
    plt.close(fig)


def plot_importance(importance: pd.DataFrame, output: Path) -> None:
    data = importance.head(18).sort_values("importance", ascending=True)
    fig, ax = plt.subplots(figsize=(10, 7))
    bars = ax.barh(data["feature"], data["importance"], color="#B07AA1")
    ax.bar_label(bars, fmt="%.3f", padding=4, fontsize=8)
    ax.set_title("Importancia de variables - mejor Random Forest", fontsize=15, pad=12)
    ax.set_xlabel("Importancia")
    ax.grid(axis="x", alpha=0.25)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    fig.savefig(output, dpi=150)
    plt.close(fig)


def markdown_table(df: pd.DataFrame) -> str:
    if df.empty:
        return "Sin datos."
    headers = [str(column) for column in df.columns]
    lines = ["| " + " | ".join(headers) + " |"]
    lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
    for _, row in df.iterrows():
        values = [str(value).replace("|", "\\|") for value in row]
        lines.append("| " + " | ".join(values) + " |")
    return "\n".join(lines)


def image_block(title: str, path: str, note: str) -> str:
    return f"""## {title}

<img src=\"{path}\" alt=\"{title}\" width=\"920\">

**Lectura:** {note}
"""


def main() -> None:
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    df = pd.read_csv(DATA_PATH, low_memory=False)
    df = add_order_date_features(df)
    df = df.dropna(subset=[TARGET, CURRENT_SYSTEM_PREDICTION, "order_datetime"])

    available_categorical = [column for column in CATEGORICAL_FEATURES if column in df.columns]
    available_numeric = [column for column in NUMERIC_FEATURES if column in df.columns]
    available_features = available_categorical + available_numeric
    missing_features = sorted(set(CATEGORICAL_FEATURES + NUMERIC_FEATURES) - set(available_features))

    train_df, test_df = temporal_train_test_split(df)
    X_train = train_df[available_features]
    y_train = train_df[TARGET].astype(float)
    X_test = test_df[available_features]
    y_test = test_df[TARGET].astype(float)

    preprocessor = make_preprocessor(available_categorical, available_numeric)

    metrics: list[dict[str, float | str | None]] = []
    residual_frames: list[pd.DataFrame] = []
    predictions = pd.DataFrame(
        {
            "Order Id": test_df["Order Id"].values,
            "order_datetime": test_df["order_datetime"].astype(str).values,
            "Shipping Mode": test_df["Shipping Mode"].values,
            "Order Country": test_df["Order Country"].values,
            "Order City": test_df["Order City"].values,
            "actual_days": y_test.values,
            "current_system_scheduled_days": test_df[CURRENT_SYSTEM_PREDICTION].astype(float).values,
        }
    )

    baseline_predictions = {
        "Current system scheduled days": test_df[CURRENT_SYSTEM_PREDICTION].astype(float).to_numpy(),
        "Baseline mean by Shipping Mode": test_df["Shipping Mode"].map(train_df.groupby("Shipping Mode")[TARGET].mean()).fillna(y_train.mean()).to_numpy(),
    }

    for model_name, pred in baseline_predictions.items():
        predictions[model_name] = pred
        metrics.append(evaluate_predictions(model_name, "test", y_test, pred, train_seconds=0.0))
        residual_frames.append(
            pd.DataFrame(
                {
                    "model": model_name,
                    "Order Id": test_df["Order Id"].values,
                    "Shipping Mode": test_df["Shipping Mode"].values,
                    "actual_days": y_test.values,
                    "predicted_days": pred,
                    "residual": y_test.values - pred,
                    "absolute_error": np.abs(y_test.values - pred),
                }
            )
        )

    fitted_models: dict[str, Pipeline] = {}
    for config in RF_CONFIGS:
        model_name = str(config["model"])
        params = {key: value for key, value in config.items() if key != "model"}
        print(f"Entrenando {model_name} con {params}...")
        pipeline = Pipeline(
            steps=[
                ("preprocess", preprocessor),
                ("model", RandomForestRegressor(**params, n_jobs=-1, random_state=RANDOM_STATE)),
            ]
        )
        start = perf_counter()
        pipeline.fit(X_train, y_train)
        train_seconds = perf_counter() - start

        train_pred = np.clip(pipeline.predict(X_train), 0, None)
        test_pred = np.clip(pipeline.predict(X_test), 0, None)

        metrics.append(evaluate_predictions(model_name, "train", y_train, train_pred, train_seconds=train_seconds))
        metrics.append(evaluate_predictions(model_name, "test", y_test, test_pred, train_seconds=train_seconds))
        predictions[model_name] = test_pred
        fitted_models[model_name] = pipeline

        residual_frames.append(
            pd.DataFrame(
                {
                    "model": model_name,
                    "Order Id": test_df["Order Id"].values,
                    "Shipping Mode": test_df["Shipping Mode"].values,
                    "actual_days": y_test.values,
                    "predicted_days": test_pred,
                    "residual": y_test.values - test_pred,
                    "absolute_error": np.abs(y_test.values - test_pred),
                }
            )
        )

    metrics_df = pd.DataFrame(metrics).sort_values(["split", "mae"])
    metrics_df.to_csv(METRICS_PATH, index=False)
    predictions.to_csv(PREDICTIONS_PATH, index=False)

    residuals = pd.concat(residual_frames, ignore_index=True)
    residuals.to_csv(RESIDUALS_PATH, index=False)

    test_metrics = metrics_df[metrics_df["split"].eq("test")].sort_values("mae")
    best_model = str(test_metrics.iloc[0]["model"])
    best_pipeline = fitted_models.get(best_model)

    if best_pipeline is not None:
        rf_model = best_pipeline.named_steps["model"]
        importance = pd.DataFrame({"feature": available_features, "importance": rf_model.feature_importances_}).sort_values("importance", ascending=False)
    else:
        importance = pd.DataFrame(columns=["feature", "importance"])
    importance.to_csv(IMPORTANCE_PATH, index=False)

    plot_metric(metrics_df, "mae", "Random Forest tuning - MAE test", FIGURES_DIR / "rf_tuning_mae.png", lower_is_better=True)
    plot_metric(metrics_df, "rmse", "Random Forest tuning - RMSE test", FIGURES_DIR / "rf_tuning_rmse.png", lower_is_better=True)
    plot_metric(metrics_df, "wape", "Random Forest tuning - WAPE test", FIGURES_DIR / "rf_tuning_wape.png", lower_is_better=True)
    plot_residual_hist(residuals, best_model, FIGURES_DIR / "rf_best_residual_histogram.png")
    plot_residual_by_predicted(residuals, best_model, FIGURES_DIR / "rf_best_residual_vs_predicted.png")
    plot_mae_by_mode(residuals, best_model, FIGURES_DIR / "rf_best_mae_by_shipping_mode.png")
    if not importance.empty:
        plot_importance(importance, FIGURES_DIR / "rf_best_feature_importance.png")

    metrics_table = metrics_df.copy()
    for column in ["mae", "mse", "rmse", "r2", "wape", "mape_nonzero_actual", "residual_mean", "residual_median", "residual_std", "train_seconds"]:
        metrics_table[column] = metrics_table[column].astype(float).round(4)

    params_table = pd.DataFrame(RF_CONFIGS)
    importance_table = importance.head(18).round(4)
    residual_summary = (
        residuals[residuals["model"].eq(best_model)]
        .groupby("Shipping Mode")
        .agg(
            rows=("Order Id", "count"),
            mae=("absolute_error", "mean"),
            residual_mean=("residual", "mean"),
            residual_median=("residual", "median"),
        )
        .reset_index()
        .round(4)
    )

    best_metrics = test_metrics.iloc[0]
    current_metrics = test_metrics[test_metrics["model"].eq("Current system scheduled days")].iloc[0]
    baseline_metrics = test_metrics[test_metrics["model"].eq("Baseline mean by Shipping Mode")].iloc[0]

    report = f"""---
title: "Random Forest para Prediccion de Llegada"
subtitle: "Tuning, metricas completas y residuos"
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

<div align="center">

# Random Forest para Prediccion de Llegada

## DataCo Supply Chain

**Objetivo:** pulir Random Forest, comparar hiperparametros y analizar residuos sin usar fecha real de llegada/envio como leakage.

</div>

---

# 1. Resumen Ejecutivo

El mejor Random Forest en test fue `{best_model}`.

| Comparacion | MAE | RMSE | R2 | WAPE | MAPE sin dias 0 |
| --- | ---: | ---: | ---: | ---: | ---: |
| Mejor Random Forest | {best_metrics['mae']:.4f} | {best_metrics['rmse']:.4f} | {best_metrics['r2']:.4f} | {best_metrics['wape']:.4f} | {best_metrics['mape_nonzero_actual']:.4f} |
| Sistema actual | {current_metrics['mae']:.4f} | {current_metrics['rmse']:.4f} | {current_metrics['r2']:.4f} | {current_metrics['wape']:.4f} | {current_metrics['mape_nonzero_actual']:.4f} |
| Baseline por Shipping Mode | {baseline_metrics['mae']:.4f} | {baseline_metrics['rmse']:.4f} | {baseline_metrics['r2']:.4f} | {baseline_metrics['wape']:.4f} | {baseline_metrics['mape_nonzero_actual']:.4f} |

La mejora frente al sistema actual es clara, pero la mejora frente al baseline por `Shipping Mode` sigue siendo pequena. Esto confirma que gran parte de la senal esta en el tipo de envio.

---

# 2. Fecha Usada y Leakage

Se agregaron variables derivadas de la **fecha del pedido**:

- `order_year`, `order_month`, `order_day`, `order_dayofweek`, `order_dayofyear`, `order_weekofyear`, `order_quarter`, `order_hour`, `order_is_weekend`.
- variables ciclicas: `order_month_sin`, `order_month_cos`, `order_dayofweek_sin`, `order_dayofweek_cos`.

No se uso la fecha real de envio/llegada (`shipping_datetime`, `shipping_month`, `shipping_dayofweek`, `shipping_hour`) porque eso filtra el resultado.

Features usadas:

{markdown_table(pd.DataFrame({'feature': available_features}))}

Variables evitadas por leakage:

{markdown_table(pd.DataFrame({'leakage_feature': LEAKAGE_COLUMNS}))}

---

# 3. Hiperparametros Probados

{markdown_table(params_table)}

---

# 4. Resultados Completos

MAPE se calcula excluyendo filas donde el valor real es 0 dias, porque dividir entre 0 no es valido. WAPE se calcula como `sum(abs(error)) / sum(abs(real))`.

{markdown_table(metrics_table)}

{image_block('Grafico 1. MAE en test', 'figures/random_forest_arrival/rf_tuning_mae.png', 'MAE es la metrica principal: error medio absoluto en dias.')}

---

{image_block('Grafico 2. RMSE en test', 'figures/random_forest_arrival/rf_tuning_rmse.png', 'RMSE penaliza errores grandes. Si sube mucho frente a MAE, hay pedidos donde el modelo falla mas fuerte.')}

---

{image_block('Grafico 3. WAPE en test', 'figures/random_forest_arrival/rf_tuning_wape.png', 'WAPE expresa el error absoluto total frente al total de dias reales. Es util para resumir error relativo global.')}

---

# 5. Residuos del Mejor Random Forest

Residuo definido como:

```text
residuo = dias reales - dias predichos
```

Si el residuo es positivo, el modelo predijo menos dias de los reales. Si es negativo, predijo demasiados dias.

Resumen por tipo de envio:

{markdown_table(residual_summary)}

{image_block('Grafico 4. Histograma de residuos', 'figures/random_forest_arrival/rf_best_residual_histogram.png', 'Permite ver si el modelo tiende a equivocarse hacia arriba o hacia abajo.')}

---

{image_block('Grafico 5. Residuos vs prediccion', 'figures/random_forest_arrival/rf_best_residual_vs_predicted.png', 'Busca patrones: si los residuos no son aleatorios, todavia faltan variables o reglas por capturar.')}

---

{image_block('Grafico 6. MAE por tipo de envio', 'figures/random_forest_arrival/rf_best_mae_by_shipping_mode.png', 'Muestra donde el modelo sigue fallando mas despues del tuning.')}

---

# 6. Importancia de Variables

{markdown_table(importance_table)}

{image_block('Grafico 7. Importancia de variables', 'figures/random_forest_arrival/rf_best_feature_importance.png', 'La importancia confirma si `Shipping Mode` domina o si pais, ciudad y fecha del pedido aportan senal adicional.')}

---

# 7. Lags y Rollings Propuestos

Tiene sentido probar lags y rolling features, pero deben construirse con cuidado para evitar leakage. No deben usar informacion futura respecto al pedido que se quiere predecir.

Propuesta para una siguiente iteracion:

1. Ordenar pedidos por `order_datetime`.
2. Crear historicos por grupos como `Shipping Mode`, `Order Country`, `Order City`, `Order Region`, `Category Name`.
3. Para cada grupo, calcular features con `shift(1)` antes del rolling:
   - media historica de `Days for shipping (real)` ultimos 7/30/90 dias;
   - tasa historica de promesa incumplida;
   - volumen historico de pedidos;
   - desviacion historica de dias reales;
   - media historica por `Shipping Mode + Country`.
4. Evaluar si estas variables mejoran al baseline simple por `Shipping Mode`.

Ejemplo conceptual:

```python
df = df.sort_values('order_datetime')
df['lag_mean_days_mode_country'] = (
    df.groupby(['Shipping Mode', 'Order Country'])['Days for shipping (real)']
      .transform(lambda s: s.shift(1).rolling(100, min_periods=20).mean())
)
```

La clave es `shift(1)`: impide que el pedido actual se use para predecirse a si mismo.

---

# 8. Decision

Random Forest mejora al sistema actual, pero no cambia la conclusion de negocio: la promesa actual esta mal calibrada por tipo de envio. Antes de perseguir mucha complejidad, conviene:

1. recalibrar promesas por `Shipping Mode`;
2. probar lags/rollings historicos sin leakage;
3. volver a comparar contra el baseline por `Shipping Mode`.
"""

    REPORT_PATH.write_text(report, encoding="utf-8-sig")
    print(f"Reporte generado: {REPORT_PATH}")
    print(f"Metricas: {METRICS_PATH}")
    print(f"Predicciones: {PREDICTIONS_PATH}")
    print(f"Residuos: {RESIDUALS_PATH}")
    print(f"Importancias: {IMPORTANCE_PATH}")


if __name__ == "__main__":
    main()