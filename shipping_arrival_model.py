from __future__ import annotations

from pathlib import Path
from time import perf_counter

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import ExtraTreesRegressor, GradientBoostingRegressor, HistGradientBoostingRegressor, RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Lasso, LinearRegression, Ridge
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, OrdinalEncoder, StandardScaler


PROJECT_DIR = Path(__file__).resolve().parent
DATA_PATH = PROJECT_DIR / "data" / "processed" / "dataco_supply_chain_processed.csv"
REPORTS_DIR = PROJECT_DIR / "reports"
FIGURES_DIR = REPORTS_DIR / "figures" / "shipping_model"
PROCESSED_DIR = PROJECT_DIR / "data" / "processed"
REPORT_PATH = REPORTS_DIR / "shipping_arrival_model_report.Rmd"
METRICS_PATH = PROCESSED_DIR / "shipping_arrival_model_metrics.csv"
PREDICTIONS_PATH = PROCESSED_DIR / "shipping_arrival_model_test_predictions.csv"
FEATURE_IMPORTANCE_PATH = PROCESSED_DIR / "shipping_arrival_feature_importance.csv"

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
    "order_month",
    "order_dayofweek",
    "order_hour",
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


def rmse(y_true: pd.Series, y_pred: np.ndarray) -> float:
    return float(np.sqrt(mean_squared_error(y_true, y_pred)))


def rounded_accuracy(y_true: pd.Series, y_pred: np.ndarray) -> float:
    rounded = np.rint(np.clip(y_pred, 0, None)).astype(int)
    return float((rounded == y_true.to_numpy()).mean())


def within_one_day(y_true: pd.Series, y_pred: np.ndarray) -> float:
    return float((np.abs(y_pred - y_true.to_numpy()) <= 1).mean())


def evaluate_predictions(model_name: str, y_true: pd.Series, y_pred: np.ndarray, train_seconds: float | None = None) -> dict[str, float | str | None]:
    return {
        "model": model_name,
        "mae": mean_absolute_error(y_true, y_pred),
        "rmse": rmse(y_true, y_pred),
        "r2": r2_score(y_true, y_pred),
        "exact_day_accuracy_rounded": rounded_accuracy(y_true, y_pred),
        "within_1_day_accuracy": within_one_day(y_true, y_pred),
        "train_seconds": train_seconds,
    }


def make_onehot_preprocessor() -> ColumnTransformer:
    try:
        encoder = OneHotEncoder(handle_unknown="ignore", sparse_output=True, min_frequency=20)
    except TypeError:
        encoder = OneHotEncoder(handle_unknown="ignore")

    return ColumnTransformer(
        transformers=[
            (
                "categorical",
                Pipeline(
                    steps=[
                        ("imputer", SimpleImputer(strategy="most_frequent")),
                        ("onehot", encoder),
                    ]
                ),
                CATEGORICAL_FEATURES,
            ),
            (
                "numeric",
                Pipeline(
                    steps=[
                        ("imputer", SimpleImputer(strategy="median")),
                        ("scaler", StandardScaler(with_mean=False)),
                    ]
                ),
                NUMERIC_FEATURES,
            ),
        ]
    )


def make_ordinal_preprocessor() -> ColumnTransformer:
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
                CATEGORICAL_FEATURES,
            ),
            (
                "numeric",
                Pipeline(steps=[("imputer", SimpleImputer(strategy="median"))]),
                NUMERIC_FEATURES,
            ),
        ]
    )


def temporal_train_test_split(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    sorted_df = df.sort_values("order_datetime").reset_index(drop=True)
    split_index = int(len(sorted_df) * (1 - TEST_SIZE))
    return sorted_df.iloc[:split_index].copy(), sorted_df.iloc[split_index:].copy()


def plot_metric(metrics: pd.DataFrame, metric: str, title: str, output: Path, lower_is_better: bool = True) -> None:
    data = metrics.sort_values(metric, ascending=lower_is_better)
    fig, ax = plt.subplots(figsize=(11, 5.8))
    bars = ax.barh(data["model"], data[metric], color="#4C78A8")
    ax.invert_yaxis()
    ax.bar_label(bars, fmt="%.3f", padding=4, fontsize=8)
    ax.set_title(title, fontsize=15, pad=12)
    ax.set_xlabel(metric)
    ax.grid(axis="x", alpha=0.25)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    fig.savefig(output, dpi=150)
    plt.close(fig)


def plot_promise_compliance(compliance: pd.DataFrame, output: Path) -> None:
    data = compliance.sort_values("promise_met_pct", ascending=True)
    fig, ax = plt.subplots(figsize=(10.5, 5.8))
    bars = ax.barh(data["Shipping Mode"], data["promise_met_pct"], color="#59A14F")
    ax.bar_label(bars, fmt="%.1f%%", padding=4)
    ax.set_title("Cumplimiento de promesa por tipo de envio", fontsize=15, pad=12)
    ax.set_xlabel("% pedidos que llegan en los dias prometidos o antes")
    ax.set_xlim(0, 105)
    ax.grid(axis="x", alpha=0.25)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    fig.savefig(output, dpi=150)
    plt.close(fig)


def plot_actual_vs_predicted(predictions: pd.DataFrame, model_name: str, output: Path) -> None:
    sample = predictions.sample(min(12000, len(predictions)), random_state=RANDOM_STATE)
    fig, ax = plt.subplots(figsize=(7, 6))
    ax.scatter(sample["actual_days"], sample[model_name], s=10, alpha=0.25, color="#E15759")
    max_value = max(sample["actual_days"].max(), sample[model_name].max())
    ax.plot([0, max_value], [0, max_value], color="black", linestyle="--", linewidth=1)
    ax.set_title(f"Real vs predicho - {model_name}", fontsize=15, pad=12)
    ax.set_xlabel("Dias reales")
    ax.set_ylabel("Dias predichos")
    ax.grid(alpha=0.2)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    fig.savefig(output, dpi=150)
    plt.close(fig)


def plot_residual_by_mode(predictions: pd.DataFrame, model_name: str, output: Path) -> None:
    tmp = predictions.copy()
    tmp["absolute_error"] = (tmp[model_name] - tmp["actual_days"]).abs()
    data = tmp.groupby("Shipping Mode")["absolute_error"].mean().sort_values(ascending=True)
    fig, ax = plt.subplots(figsize=(10, 5.5))
    bars = ax.barh(data.index, data.values, color="#F28E2B")
    ax.bar_label(bars, fmt="%.3f", padding=4)
    ax.set_title(f"Error absoluto medio por tipo de envio - {model_name}", fontsize=15, pad=12)
    ax.set_xlabel("MAE en dias")
    ax.grid(axis="x", alpha=0.25)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    fig.savefig(output, dpi=150)
    plt.close(fig)


def plot_feature_importance(importance: pd.DataFrame, output: Path) -> None:
    data = importance.head(18).sort_values("importance", ascending=True)
    fig, ax = plt.subplots(figsize=(10, 7))
    bars = ax.barh(data["feature"], data["importance"], color="#B07AA1")
    ax.bar_label(bars, fmt="%.3f", padding=4, fontsize=8)
    ax.set_title("Importancia aproximada de variables - mejor modelo de arboles", fontsize=15, pad=12)
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
    df = df.dropna(subset=[TARGET, CURRENT_SYSTEM_PREDICTION, "order_datetime"])
    df["order_datetime"] = pd.to_datetime(df["order_datetime"], errors="coerce")
    df = df.dropna(subset=["order_datetime"])

    available_features = [column for column in CATEGORICAL_FEATURES + NUMERIC_FEATURES if column in df.columns]
    missing_features = sorted(set(CATEGORICAL_FEATURES + NUMERIC_FEATURES) - set(available_features))

    train_df, test_df = temporal_train_test_split(df)
    X_train = train_df[available_features]
    y_train = train_df[TARGET].astype(float)
    X_test = test_df[available_features]
    y_test = test_df[TARGET].astype(float)

    metrics: list[dict[str, float | str | None]] = []
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

    current_pred = test_df[CURRENT_SYSTEM_PREDICTION].astype(float).to_numpy()
    metrics.append(evaluate_predictions("Current system scheduled days", y_test, current_pred, train_seconds=0.0))

    shipping_mode_mean = train_df.groupby("Shipping Mode")[TARGET].mean()
    global_mean = y_train.mean()
    mode_mean_pred = test_df["Shipping Mode"].map(shipping_mode_mean).fillna(global_mean).to_numpy()
    predictions["Baseline mean by Shipping Mode"] = mode_mean_pred
    metrics.append(evaluate_predictions("Baseline mean by Shipping Mode", y_test, mode_mean_pred, train_seconds=0.0))

    models = [
        (
            "Linear Regression",
            Pipeline(steps=[("preprocess", make_onehot_preprocessor()), ("model", LinearRegression())]),
        ),
        (
            "Ridge Regression",
            Pipeline(steps=[("preprocess", make_onehot_preprocessor()), ("model", Ridge(alpha=1.0, random_state=RANDOM_STATE))]),
        ),
        (
            "Lasso Regression",
            Pipeline(steps=[("preprocess", make_onehot_preprocessor()), ("model", Lasso(alpha=0.0005, max_iter=5000, random_state=RANDOM_STATE))]),
        ),
        (
            "Random Forest",
            Pipeline(
                steps=[
                    ("preprocess", make_ordinal_preprocessor()),
                    ("model", RandomForestRegressor(n_estimators=120, max_depth=18, min_samples_leaf=8, n_jobs=-1, random_state=RANDOM_STATE)),
                ]
            ),
        ),
        (
            "Extra Trees",
            Pipeline(
                steps=[
                    ("preprocess", make_ordinal_preprocessor()),
                    ("model", ExtraTreesRegressor(n_estimators=160, max_depth=20, min_samples_leaf=6, n_jobs=-1, random_state=RANDOM_STATE)),
                ]
            ),
        ),
        (
            "Hist Gradient Boosting",
            Pipeline(
                steps=[
                    ("preprocess", make_ordinal_preprocessor()),
                    ("model", HistGradientBoostingRegressor(max_iter=180, learning_rate=0.08, max_leaf_nodes=31, l2_regularization=0.05, random_state=RANDOM_STATE)),
                ]
            ),
        ),
        (
            "Gradient Boosting",
            Pipeline(
                steps=[
                    ("preprocess", make_ordinal_preprocessor()),
                    ("model", GradientBoostingRegressor(n_estimators=140, learning_rate=0.08, max_depth=4, random_state=RANDOM_STATE)),
                ]
            ),
        ),
    ]

    fitted_models: dict[str, Pipeline] = {}
    for model_name, pipeline in models:
        print(f"Entrenando {model_name}...")
        start = perf_counter()
        pipeline.fit(X_train, y_train)
        train_seconds = perf_counter() - start
        pred = pipeline.predict(X_test)
        pred = np.clip(pred, 0, None)
        predictions[model_name] = pred
        metrics.append(evaluate_predictions(model_name, y_test, pred, train_seconds=train_seconds))
        fitted_models[model_name] = pipeline

    metrics_df = pd.DataFrame(metrics).sort_values("mae")
    metrics_df.to_csv(METRICS_PATH, index=False)
    predictions.to_csv(PREDICTIONS_PATH, index=False)

    best_model_name = metrics_df.iloc[0]["model"]
    best_prediction_column = str(best_model_name)
    best_for_importance_name = "Random Forest" if "Random Forest" in fitted_models else str(best_model_name)

    if best_for_importance_name in fitted_models:
        model = fitted_models[best_for_importance_name].named_steps["model"]
        if hasattr(model, "feature_importances_"):
            importance = pd.DataFrame(
                {
                    "feature": available_features,
                    "importance": model.feature_importances_,
                }
            ).sort_values("importance", ascending=False)
            importance.to_csv(FEATURE_IMPORTANCE_PATH, index=False)
        else:
            importance = pd.DataFrame(columns=["feature", "importance"])
    else:
        importance = pd.DataFrame(columns=["feature", "importance"])

    test_eval = predictions.copy()
    test_eval["promise_met"] = test_eval["actual_days"].le(test_eval["current_system_scheduled_days"])
    compliance = (
        test_eval.groupby("Shipping Mode")
        .agg(
            orders=("Order Id", "count"),
            promise_met_pct=("promise_met", lambda s: round(s.mean() * 100, 2)),
            promised_days=("current_system_scheduled_days", "mean"),
            actual_days=("actual_days", "mean"),
        )
        .reset_index()
        .round(2)
    )

    compliance_path = PROCESSED_DIR / "shipping_promise_compliance_test.csv"
    compliance.to_csv(compliance_path, index=False)

    plot_metric(metrics_df, "mae", "Comparacion de modelos - MAE menor es mejor", FIGURES_DIR / "arrival_model_mae_comparison.png", lower_is_better=True)
    plot_metric(metrics_df, "rmse", "Comparacion de modelos - RMSE menor es mejor", FIGURES_DIR / "arrival_model_rmse_comparison.png", lower_is_better=True)
    plot_metric(metrics_df, "exact_day_accuracy_rounded", "Exactitud por dia redondeado - mayor es mejor", FIGURES_DIR / "arrival_model_exact_day_accuracy.png", lower_is_better=False)
    plot_promise_compliance(compliance, FIGURES_DIR / "arrival_promise_compliance_by_shipping_mode.png")
    plot_actual_vs_predicted(predictions, best_prediction_column, FIGURES_DIR / "arrival_actual_vs_predicted_best_model.png")
    plot_residual_by_mode(predictions, best_prediction_column, FIGURES_DIR / "arrival_mae_by_shipping_mode_best_model.png")
    if not importance.empty:
        plot_feature_importance(importance, FIGURES_DIR / "arrival_feature_importance_random_forest.png")

    metrics_table = metrics_df.copy()
    for column in ["mae", "rmse", "r2", "exact_day_accuracy_rounded", "within_1_day_accuracy", "train_seconds"]:
        metrics_table[column] = metrics_table[column].astype(float).round(4)

    compliance_table = compliance.copy()
    current_metrics = metrics_df[metrics_df["model"].eq("Current system scheduled days")].iloc[0]
    best_metrics = metrics_df.iloc[0]

    importance_table = importance.head(15).round(4) if not importance.empty else pd.DataFrame(columns=["feature", "importance"])

    report = f"""---
title: "Modelo de Prediccion de Llegada de Paquetes"
subtitle: "Experimento realista sin variables de llegada futuras"
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

# Modelo de Prediccion de Llegada de Paquetes

## DataCo Supply Chain

**Objetivo:** predecir cuantos dias tarda un pedido en llegar y comparar el resultado contra el sistema actual (`Days for shipment (scheduled)`).

</div>

---

# 1. Resumen Ejecutivo

Se entrenaron varios modelos para predecir `Days for shipping (real)` y se compararon contra la promesa actual del sistema (`Days for shipment (scheduled)`).

**Mejor resultado por MAE:** `{best_metrics['model']}` con MAE `{best_metrics['mae']:.4f}` dias.

**Sistema actual:** MAE `{current_metrics['mae']:.4f}` dias.

La comparacion responde una pregunta practica: si el sistema actual promete dias de llegada de forma demasiado rigida, un modelo con pais, ciudad, tipo de envio, comprador, producto, cantidad y fecha del pedido puede mejorar la estimacion. La fecha real de envio/llegada se excluye por leakage.

---

# 2. Variables Usadas

Target:

```text
Days for shipping (real)
```

Prediccion actual usada como comparacion:

```text
Days for shipment (scheduled)
```

Features usadas por los modelos:

{markdown_table(pd.DataFrame({'feature': available_features}))}

Features evitadas por leakage o porque solo se conocen despues del pedido:

{markdown_table(pd.DataFrame({'leakage_feature': LEAKAGE_COLUMNS}))}

Features esperadas pero no encontradas:

{markdown_table(pd.DataFrame({'missing_feature': missing_features}))}

---

# 3. Comparacion de Modelos

{markdown_table(metrics_table)}

{image_block('Grafico 1. MAE por modelo', 'figures/shipping_model/arrival_model_mae_comparison.png', 'MAE mide el error medio en dias. Cuanto menor, mejor. La barra del sistema actual muestra cuanto error tiene la promesa fija que ya trae el dataset.')}

---

{image_block('Grafico 2. RMSE por modelo', 'figures/shipping_model/arrival_model_rmse_comparison.png', 'RMSE penaliza mas los errores grandes. Sirve para ver si algun modelo falla fuerte en ciertos pedidos.')}

---

{image_block('Grafico 3. Exactitud por dia redondeado', 'figures/shipping_model/arrival_model_exact_day_accuracy.png', 'Mide cuantas veces el modelo acierta exactamente el numero entero de dias despues de redondear la prediccion.')}

---

# 4. La Promesa Actual de Envio Cumple lo que Dice?

Esta seccion responde la pregunta operativa: si `Same Day` promete mismo dia, `First Class` promete 1 dia, `Second Class` promete 2 dias y `Standard Class` promete 4 dias, cuantos pedidos llegan dentro de esa promesa?

{markdown_table(compliance_table)}

{image_block('Grafico 4. Cumplimiento de promesa por tipo de envio', 'figures/shipping_model/arrival_promise_compliance_by_shipping_mode.png', 'Aqui se ve si el problema es solo predictivo o tambien operativo. Si un tipo de envio casi nunca cumple su promesa, el problema no es solo el modelo: la promesa/logistica tambien esta mal calibrada.')}

Lectura clave:

- `First Class` no cumple su promesa en el conjunto de test: promete 1 dia, pero en estos datos llega en 2.
- `Same Day` no siempre significa mismo dia; una parte importante llega en 1 dia.
- `Second Class` promete 2 dias, pero muchas entregas tardan mas.
- `Standard Class` es el modo mejor calibrado en promedio, aunque no perfecto.

---

# 5. Mejor Modelo: Real vs Predicho

{image_block('Grafico 5. Dias reales vs dias predichos', 'figures/shipping_model/arrival_actual_vs_predicted_best_model.png', 'Cada punto compara dias reales contra dias predichos por el mejor modelo. La linea diagonal seria prediccion perfecta.')}

---

{image_block('Grafico 6. Error del mejor modelo por tipo de envio', 'figures/shipping_model/arrival_mae_by_shipping_mode_best_model.png', 'Este grafico muestra si el mejor modelo sigue fallando mas en algun modo de envio concreto.')}

---

# 6. Variables que Parecen Importantes

La tabla siguiente usa importancia aproximada del modelo `Random Forest`. En variables categoricas codificadas ordinalmente debe leerse como orientacion, no como explicacion causal definitiva.

{markdown_table(importance_table)}

{image_block('Grafico 7. Importancia aproximada de variables', 'figures/shipping_model/arrival_feature_importance_random_forest.png', 'Ayuda a ver que variables parecen aportar mas senal para estimar dias de llegada.')}

---

# 7. Decision para el Proyecto

El sistema actual de promesa de dias es demasiado simple. En los informes anteriores ya se veia que `First Class` y `Second Class` tienen promesas mal calibradas. Este experimento comprueba si modelos basados en informacion del pedido pueden mejorar esa estimacion.

Recomendacion:

1. El mejor modelo mejora claramente al sistema actual, pero solo mejora ligeramente a una regla simple por `Shipping Mode`.
2. Antes de complicar el modelo, conviene recalibrar la promesa base por tipo de envio.
3. Si se avanza, construir features historicas por pais/ciudad/modo de envio sin leakage y volver a evaluar contra el baseline simple.

---

# 8. Nota sobre XGBoost

`xgboost` no estaba instalado en el entorno local. Para cubrir esa familia de modelos se probaron alternativas de gradient boosting disponibles en scikit-learn:

- `HistGradientBoostingRegressor`
- `GradientBoostingRegressor`

Esto mantiene el experimento reproducible sin descargar dependencias nuevas.
"""

    REPORT_PATH.write_text(report, encoding="utf-8-sig")
    print(f"Reporte generado: {REPORT_PATH}")
    print(f"Metricas: {METRICS_PATH}")
    print(f"Predicciones test: {PREDICTIONS_PATH}")
    print(f"Graficos: {FIGURES_DIR}")


if __name__ == "__main__":
    main()