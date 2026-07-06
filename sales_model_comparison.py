from __future__ import annotations

from pathlib import Path
from time import perf_counter

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.ensemble import HistGradientBoostingRegressor, RandomForestRegressor
from sklearn.impute import SimpleImputer
from sklearn.linear_model import Lasso, LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OrdinalEncoder, StandardScaler
from sklearn.tree import DecisionTreeRegressor


PROJECT_DIR = Path(__file__).resolve().parent
DATA_PATH = PROJECT_DIR / "data" / "processed" / "dataco_supply_chain_processed.csv"
REPORTS_DIR = PROJECT_DIR / "reports"
FIGURES_DIR = REPORTS_DIR / "figures" / "sales_model"
PROCESSED_DIR = PROJECT_DIR / "data" / "processed"
REPORT_PATH = REPORTS_DIR / "sales_model_comparison_report.Rmd"
METRICS_PATH = PROCESSED_DIR / "sales_model_comparison_metrics.csv"
PREDICTIONS_PATH = PROCESSED_DIR / "sales_model_comparison_predictions.csv"
RESIDUALS_PATH = PROCESSED_DIR / "sales_model_comparison_residuals.csv"
IMPORTANCE_PATH = PROCESSED_DIR / "sales_model_feature_importance.csv"
FEATURE_AUDIT_PATH = PROCESSED_DIR / "sales_model_feature_audit.csv"

RANDOM_STATE = 42
TEST_SIZE = 0.2
TARGET = "Sales"

CATEGORICAL_FEATURES = [
    "Order Country",
    "Order Region",
    "Order State",
    "Order City",
    "Market",
    "Customer Country",
    "Customer City",
    "Customer Segment",
    "Customer Id",
    "Category Name",
    "Department Name",
    "Product Name",
    "calendar_period",
]

NUMERIC_FEATURES = [
    "Order Item Product Price",
    "Order Item Quantity",
    "Order Item Discount",
    "Order Item Discount Rate",
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
    "is_generic_fixed_holiday",
    "has_discount",
]

EXCLUDED_FOR_LEAKAGE = [
    "Sales",
    "Sales per customer",
    "Order Item Total",
    "Benefit per order",
    "Order Profit Per Order",
    "Order Item Profit Ratio",
    "Order Status",
    "Delivery Status",
    "Late_delivery_risk",
    "is_late_delivery",
    "is_shipping_canceled",
    "is_order_canceled",
    "is_suspected_fraud",
    "is_payment_problem",
    "is_order_problem",
    "Type",
    "payment_type_cash",
    "payment_type_debit",
    "payment_type_payment",
    "payment_type_transfer",
    "payment_type",
]


def markdown_table(df: pd.DataFrame) -> str:
    if df.empty:
        return "_Sin datos._"
    table = df.copy().where(pd.notna(df), "")
    columns = [str(column) for column in table.columns]
    header = "| " + " | ".join(columns) + " |"
    separator = "| " + " | ".join("---" for _ in columns) + " |"
    rows = []
    for row in table.astype(str).itertuples(index=False, name=None):
        cleaned = [value.replace("|", "/") for value in row]
        rows.append("| " + " | ".join(cleaned) + " |")
    return "\n".join([header, separator, *rows])


def image_block(title: str, path: str, reading: str) -> str:
    return f"""
## {title}

<img src="{path}" alt="{title}" width="920">

**Lectura:** {reading}
"""


def add_sales_features(df: pd.DataFrame) -> pd.DataFrame:
    result = df.copy()
    result["order_datetime"] = pd.to_datetime(result["order_datetime"], errors="coerce")
    result = result.dropna(subset=["order_datetime", TARGET]).copy()
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

    month_day = result["order_datetime"].dt.strftime("%m-%d")
    result["is_generic_fixed_holiday"] = month_day.isin(["01-01", "05-01", "12-25"]).astype(int)
    result["calendar_period"] = "Normal"
    result.loc[result["order_datetime"].dt.month.eq(12), "calendar_period"] = "Christmas season"
    result.loc[
        result["order_datetime"].dt.month.eq(11) & result["order_datetime"].dt.day.between(20, 30),
        "calendar_period",
    ] = "Black Friday period"
    result.loc[
        result["order_datetime"].dt.month.eq(9) & result["order_datetime"].dt.day.between(1, 15),
        "calendar_period",
    ] = "Back to school period"
    result.loc[result["is_generic_fixed_holiday"].eq(1), "calendar_period"] = "Generic fixed holiday"

    result["has_discount"] = result["Order Item Discount"].fillna(0).gt(0).astype(int)
    return result


def temporal_train_test_split(df: pd.DataFrame) -> tuple[pd.DataFrame, pd.DataFrame]:
    sorted_df = df.sort_values("order_datetime").reset_index(drop=True)
    split_index = int(len(sorted_df) * (1 - TEST_SIZE))
    return sorted_df.iloc[:split_index].copy(), sorted_df.iloc[split_index:].copy()


def make_tree_preprocessor(categorical_features: list[str], numeric_features: list[str]) -> ColumnTransformer:
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
            ("numeric", Pipeline(steps=[("imputer", SimpleImputer(strategy="median"))]), numeric_features),
        ]
    )


def make_linear_preprocessor(categorical_features: list[str], numeric_features: list[str]) -> ColumnTransformer:
    return ColumnTransformer(
        transformers=[
            (
                "categorical",
                Pipeline(
                    steps=[
                        ("imputer", SimpleImputer(strategy="most_frequent")),
                        ("ordinal", OrdinalEncoder(handle_unknown="use_encoded_value", unknown_value=-1)),
                        ("scaler", StandardScaler()),
                    ]
                ),
                categorical_features,
            ),
            (
                "numeric",
                Pipeline(steps=[("imputer", SimpleImputer(strategy="median")), ("scaler", StandardScaler())]),
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


def evaluate_predictions(
    model_name: str,
    split: str,
    y_true: pd.Series,
    y_pred: np.ndarray,
    train_seconds: float | None = None,
) -> dict[str, float | str | None]:
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
    fig, ax = plt.subplots(figsize=(11, 5.8))
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


def plot_residual_hist(residuals: pd.DataFrame, model_name: str, output: Path) -> None:
    data = residuals[residuals["model"].eq(model_name)]["residual"]
    fig, ax = plt.subplots(figsize=(10, 5.5))
    ax.hist(data, bins=45, color="#F28E2B", edgecolor="white")
    ax.axvline(0, color="black", linestyle="--", linewidth=1)
    ax.set_title(f"Distribucion de residuos - {model_name}", fontsize=15, pad=12)
    ax.set_xlabel("Residuo = real - predicho")
    ax.set_ylabel("Frecuencia")
    ax.grid(axis="y", alpha=0.25)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    fig.savefig(output, dpi=150)
    plt.close(fig)


def plot_residual_vs_predicted(residuals: pd.DataFrame, model_name: str, output: Path) -> None:
    data = residuals[residuals["model"].eq(model_name)].sample(frac=1, random_state=RANDOM_STATE).head(12000)
    fig, ax = plt.subplots(figsize=(8, 6))
    ax.scatter(data["predicted_sales"], data["residual"], s=10, alpha=0.22, color="#E15759")
    ax.axhline(0, color="black", linestyle="--", linewidth=1)
    ax.set_title(f"Residuos vs prediccion - {model_name}", fontsize=15, pad=12)
    ax.set_xlabel("Ventas predichas")
    ax.set_ylabel("Residuo = real - predicho")
    ax.grid(alpha=0.2)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    fig.savefig(output, dpi=150)
    plt.close(fig)


def plot_importance(importance: pd.DataFrame, output: Path, title: str) -> None:
    data = importance.head(25).sort_values("importance", ascending=True)
    fig, ax = plt.subplots(figsize=(10, 7))
    bars = ax.barh(data["feature"], data["importance"], color="#59A14F")
    ax.bar_label(bars, fmt="%.4f", padding=4, fontsize=8)
    ax.set_title(title, fontsize=15, pad=12)
    ax.set_xlabel("Importancia")
    ax.grid(axis="x", alpha=0.25)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    fig.savefig(output, dpi=150)
    plt.close(fig)


def get_tree_importance(model: Pipeline, feature_names: list[str]) -> pd.DataFrame:
    estimator = model.named_steps["model"]
    if not hasattr(estimator, "feature_importances_"):
        return pd.DataFrame(columns=["feature", "importance"])
    return (
        pd.DataFrame({"feature": feature_names, "importance": estimator.feature_importances_})
        .sort_values("importance", ascending=False)
        .reset_index(drop=True)
    )


def get_linear_importance(model: Pipeline, feature_names: list[str], model_name: str) -> pd.DataFrame:
    estimator = model.named_steps["model"]
    if not hasattr(estimator, "coef_"):
        return pd.DataFrame(columns=["model", "feature", "importance", "coefficient"])
    coefficients = np.ravel(estimator.coef_)
    return (
        pd.DataFrame(
            {
                "model": model_name,
                "feature": feature_names,
                "importance": np.abs(coefficients),
                "coefficient": coefficients,
            }
        )
        .sort_values("importance", ascending=False)
        .reset_index(drop=True)
    )


def build_feature_audit(available_features: list[str]) -> pd.DataFrame:
    rows = []
    groups = {
        "geografia": ["Order Country", "Order Region", "Order State", "Order City", "Market", "Customer Country", "Customer City"],
        "comprador": ["Customer Id", "Customer Segment"],
        "producto": ["Product Name", "Category Name", "Department Name"],
        "precio_cantidad": ["Order Item Product Price", "Order Item Quantity"],
        "descuentos_ofertas": ["Order Item Discount", "Order Item Discount Rate", "has_discount"],
        "calendario": [
            "order_year",
            "order_month",
            "order_day",
            "order_dayofweek",
            "order_dayofyear",
            "order_weekofyear",
            "order_quarter",
            "order_hour",
            "order_is_weekend",
            "calendar_period",
            "is_generic_fixed_holiday",
        ],
        "metodo_pago": ["payment_type_cash", "payment_type_debit", "payment_type_payment", "payment_type_transfer", "Type"],
    }
    for group, features in groups.items():
        used = [feature for feature in features if feature in available_features]
        excluded = [feature for feature in features if feature in EXCLUDED_FOR_LEAKAGE]
        status = "Usado" if used else "Excluido"
        reason = "Disponible antes/casi al formar la venta" if used else "No usado para evitar leakage o porque no esta disponible antes de la compra"
        rows.append(
            {
                "grupo": group,
                "estado": status,
                "features_usadas": ", ".join(used) if used else "-",
                "features_excluidas": ", ".join(excluded) if excluded else "-",
                "motivo": reason,
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    REPORTS_DIR.mkdir(exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(exist_ok=True)

    print("Leyendo datos...", flush=True)
    df = pd.read_csv(DATA_PATH, low_memory=False)
    df = add_sales_features(df)
    df = df[df[TARGET].notna()].copy()

    available_categorical = [col for col in CATEGORICAL_FEATURES if col in df.columns]
    available_numeric = [col for col in NUMERIC_FEATURES if col in df.columns]
    feature_names = available_categorical + available_numeric
    feature_audit = build_feature_audit(feature_names)
    feature_audit.to_csv(FEATURE_AUDIT_PATH, index=False)

    train_df, test_df = temporal_train_test_split(df)
    y_train = train_df[TARGET].astype(float)
    y_test = test_df[TARGET].astype(float)

    metrics: list[dict[str, float | str | None]] = []
    residual_frames: list[pd.DataFrame] = []
    predictions = pd.DataFrame(
        {
            "Order Id": test_df["Order Id"].values,
            "Order Item Id": test_df["Order Item Id"].values,
            "order_datetime": test_df["order_datetime"].values,
            "actual_sales": y_test.values,
        }
    )

    print("Calculando baselines...", flush=True)
    global_mean = float(y_train.mean())
    global_train_pred = np.full(len(train_df), global_mean)
    global_test_pred = np.full(len(test_df), global_mean)
    metrics.append(evaluate_predictions("Baseline global mean", "train", y_train, global_train_pred, 0.0))
    metrics.append(evaluate_predictions("Baseline global mean", "test", y_test, global_test_pred, 0.0))
    predictions["Baseline global mean"] = global_test_pred

    product_means = train_df.groupby("Product Name")[TARGET].mean()
    product_train_pred = train_df["Product Name"].map(product_means).fillna(global_mean).to_numpy()
    product_test_pred = test_df["Product Name"].map(product_means).fillna(global_mean).to_numpy()
    metrics.append(evaluate_predictions("Baseline mean by Product", "train", y_train, product_train_pred, 0.0))
    metrics.append(evaluate_predictions("Baseline mean by Product", "test", y_test, product_test_pred, 0.0))
    predictions["Baseline mean by Product"] = product_test_pred

    model_specs = [
        (
            "Linear Regression",
            Pipeline(
                steps=[
                    ("preprocess", make_linear_preprocessor(available_categorical, available_numeric)),
                    ("model", LinearRegression()),
                ]
            ),
        ),
        (
            "Lasso",
            Pipeline(
                steps=[
                    ("preprocess", make_linear_preprocessor(available_categorical, available_numeric)),
                    ("model", Lasso(alpha=0.001, max_iter=8000, random_state=RANDOM_STATE)),
                ]
            ),
        ),
        (
            "Decision Tree",
            Pipeline(
                steps=[
                    ("preprocess", make_tree_preprocessor(available_categorical, available_numeric)),
                    (
                        "model",
                        DecisionTreeRegressor(
                            max_depth=16,
                            min_samples_leaf=20,
                            random_state=RANDOM_STATE,
                        ),
                    ),
                ]
            ),
        ),
        (
            "Random Forest",
            Pipeline(
                steps=[
                    ("preprocess", make_tree_preprocessor(available_categorical, available_numeric)),
                    (
                        "model",
                        RandomForestRegressor(
                            n_estimators=120,
                            max_depth=18,
                            min_samples_leaf=8,
                            min_samples_split=16,
                            max_features=1.0,
                            bootstrap=True,
                            n_jobs=-1,
                            random_state=RANDOM_STATE,
                        ),
                    ),
                ]
            ),
        ),
        (
            "Hist Gradient Boosting",
            Pipeline(
                steps=[
                    ("preprocess", make_tree_preprocessor(available_categorical, available_numeric)),
                    (
                        "model",
                        HistGradientBoostingRegressor(
                            max_iter=260,
                            learning_rate=0.06,
                            max_leaf_nodes=31,
                            l2_regularization=0.01,
                            random_state=RANDOM_STATE,
                        ),
                    ),
                ]
            ),
        ),
    ]

    fitted_models: dict[str, Pipeline] = {}
    linear_importance_frames = []
    for model_name, pipeline in model_specs:
        print(f"Entrenando {model_name}...", flush=True)
        start = perf_counter()
        pipeline.fit(train_df[feature_names], y_train)
        train_seconds = perf_counter() - start
        train_pred = np.clip(pipeline.predict(train_df[feature_names]), 0, None)
        test_pred = np.clip(pipeline.predict(test_df[feature_names]), 0, None)

        metrics.append(evaluate_predictions(model_name, "train", y_train, train_pred, train_seconds))
        metrics.append(evaluate_predictions(model_name, "test", y_test, test_pred, train_seconds))
        predictions[model_name] = test_pred
        fitted_models[model_name] = pipeline
        residual_frames.append(
            pd.DataFrame(
                {
                    "model": model_name,
                    "Order Id": test_df["Order Id"].values,
                    "Order Item Id": test_df["Order Item Id"].values,
                    "actual_sales": y_test.values,
                    "predicted_sales": test_pred,
                    "residual": y_test.values - test_pred,
                    "absolute_error": np.abs(y_test.values - test_pred),
                    "Product Name": test_df["Product Name"].values,
                    "Category Name": test_df["Category Name"].values,
                    "Order Country": test_df["Order Country"].values,
                    "Customer Segment": test_df["Customer Segment"].values,
                }
            )
        )
        if model_name in {"Linear Regression", "Lasso"}:
            linear_importance_frames.append(get_linear_importance(pipeline, feature_names, model_name))

    for model_name, pred in {
        "Baseline global mean": global_test_pred,
        "Baseline mean by Product": product_test_pred,
    }.items():
        residual_frames.append(
            pd.DataFrame(
                {
                    "model": model_name,
                    "Order Id": test_df["Order Id"].values,
                    "Order Item Id": test_df["Order Item Id"].values,
                    "actual_sales": y_test.values,
                    "predicted_sales": pred,
                    "residual": y_test.values - pred,
                    "absolute_error": np.abs(y_test.values - pred),
                    "Product Name": test_df["Product Name"].values,
                    "Category Name": test_df["Category Name"].values,
                    "Order Country": test_df["Order Country"].values,
                    "Customer Segment": test_df["Customer Segment"].values,
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
        importance = get_tree_importance(best_pipeline, feature_names)
        if importance.empty and best_model in {"Linear Regression", "Lasso"}:
            importance = get_linear_importance(best_pipeline, feature_names, best_model)
    else:
        importance = pd.DataFrame(columns=["feature", "importance"])
    if not importance.empty and "model" not in importance.columns:
        importance.insert(0, "model", best_model)
    linear_importance = pd.concat(linear_importance_frames, ignore_index=True) if linear_importance_frames else pd.DataFrame()
    all_importance = pd.concat([importance, linear_importance], ignore_index=True, sort=False)
    all_importance.to_csv(IMPORTANCE_PATH, index=False)

    plot_metric(metrics_df, "mae", "Modelo de ventas - MAE test", FIGURES_DIR / "sales_model_mae.png")
    plot_metric(metrics_df, "rmse", "Modelo de ventas - RMSE test", FIGURES_DIR / "sales_model_rmse.png")
    plot_metric(metrics_df, "wape", "Modelo de ventas - WAPE test", FIGURES_DIR / "sales_model_wape.png")
    plot_residual_hist(residuals, best_model, FIGURES_DIR / "sales_model_best_residual_histogram.png")
    plot_residual_vs_predicted(residuals, best_model, FIGURES_DIR / "sales_model_best_residual_vs_predicted.png")
    if not importance.empty:
        plot_importance(importance, FIGURES_DIR / "sales_model_best_feature_importance.png", f"Importancia de variables - {best_model}")

    metrics_table = metrics_df.copy()
    for column in ["mae", "mse", "rmse", "r2", "wape", "mape_nonzero_actual", "residual_mean", "residual_median", "residual_std", "train_seconds"]:
        metrics_table[column] = metrics_table[column].astype(float).round(4)

    best_metrics = test_metrics.iloc[0]
    product_baseline = test_metrics[test_metrics["model"].eq("Baseline mean by Product")].iloc[0]
    global_baseline = test_metrics[test_metrics["model"].eq("Baseline global mean")].iloc[0]
    feature_audit_table = feature_audit.copy()
    importance_table = importance.head(25).copy()
    if not importance_table.empty:
        importance_table["importance"] = importance_table["importance"].astype(float).round(4)

    residual_summary = (
        residuals[residuals["model"].eq(best_model)]
        .agg(
            rows=("Order Id", "count"),
            mae=("absolute_error", "mean"),
            residual_mean=("residual", "mean"),
            residual_median=("residual", "median"),
            residual_std=("residual", "std"),
        )
        .reset_index()
        .round(4)
    )

    report = f"""---
title: "Comparacion de Modelos de Ventas"
subtitle: "Sin lags ni rollings"
author: "Proyecto DataCo"
date: "2026-07-06"
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

# Comparacion de Modelos de Ventas

## DataCo Supply Chain

**Objetivo:** comparar modelos para predecir `Sales` usando geografia, comprador, producto, precio/cantidad, descuentos/ofertas y calendario, sin lags ni rollings.

</div>

---

# 1. Resumen Ejecutivo

El mejor modelo en test fue `{best_model}`.

| Comparacion | MAE | MSE | RMSE | R2 | WAPE | MAPE sin ventas 0 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Mejor modelo | {best_metrics['mae']:.4f} | {best_metrics['mse']:.4f} | {best_metrics['rmse']:.4f} | {best_metrics['r2']:.4f} | {best_metrics['wape']:.4f} | {best_metrics['mape_nonzero_actual']:.4f} |
| Baseline por producto | {product_baseline['mae']:.4f} | {product_baseline['mse']:.4f} | {product_baseline['rmse']:.4f} | {product_baseline['r2']:.4f} | {product_baseline['wape']:.4f} | {product_baseline['mape_nonzero_actual']:.4f} |
| Baseline global | {global_baseline['mae']:.4f} | {global_baseline['mse']:.4f} | {global_baseline['rmse']:.4f} | {global_baseline['r2']:.4f} | {global_baseline['wape']:.4f} | {global_baseline['mape_nonzero_actual']:.4f} |

Nota importante: este modelo usa `Order Item Product Price` y `Order Item Quantity`. Estas variables explican gran parte de `Sales`, porque la venta por linea depende directamente de precio y cantidad. Por eso el modelo debe interpretarse como prediccion de importe de linea con informacion de carrito/pedido, no como forecast puro de demanda antes de que el cliente elija producto y cantidad.

Lectura principal:

- `Linear Regression` y `Lasso` funcionan mejor que los modelos de arbol en test.
- `Decision Tree`, `Random Forest` e `Hist Gradient Boosting` aprenden casi perfecto en train, pero generalizan peor en test. Esto indica sobreajuste.
- La senal dominante es lineal y viene de precio, cantidad y descuento.
- El metodo de pago queda fuera del modelo principal porque no se conoce antes de completar la compra.

---

# 2. Variables Usadas y Leakage

No se usaron lags ni rollings.

Se excluyeron variables que ya contienen resultado comercial, estado posterior o informacion no disponible antes/casi al cierre de compra:

- `Sales per customer`, `Order Item Total`, beneficios y profit;
- estados posteriores de pedido/envio;
- targets de retraso, cancelacion, fraude o problema;
- metodo de pago (`Type` y `payment_type_*`) para evitar leakage en prediccion antes de completar la compra.

Auditoria de grupos de variables:

{markdown_table(feature_audit_table)}

Features finales usadas:

{markdown_table(pd.DataFrame({'feature': feature_names}))}

---

# 3. Modelos Comparados

- `Baseline global mean`: media historica global de `Sales` en train.
- `Baseline mean by Product`: media historica de `Sales` por `Product Name` en train.
- `Linear Regression`.
- `Lasso`.
- `Decision Tree`.
- `Random Forest`.
- `Hist Gradient Boosting`.

El split fue temporal: el 80% inicial por fecha de pedido para train y el 20% final para test.

---

# 4. Resultados Completos

MAPE excluye ventas reales 0 para evitar division por cero. WAPE se calcula como `sum(abs(error)) / sum(abs(real))`.

{markdown_table(metrics_table)}

{image_block('Grafico 1. MAE en test', 'figures/sales_model/sales_model_mae.png', 'MAE es la metrica principal para comparar el error medio absoluto en importe de venta.') }

---

{image_block('Grafico 2. RMSE en test', 'figures/sales_model/sales_model_rmse.png', 'RMSE penaliza mas los errores grandes. Si sube mucho frente a MAE, hay ventas puntuales dificiles de predecir.') }

---

{image_block('Grafico 3. WAPE en test', 'figures/sales_model/sales_model_wape.png', 'WAPE resume el error absoluto frente al total de ventas reales.') }

---

# 5. Residuos del Mejor Modelo

Resumen global de residuos:

{markdown_table(residual_summary)}

{image_block('Grafico 4. Histograma de residuos', 'figures/sales_model/sales_model_best_residual_histogram.png', 'Permite ver si el modelo tiende a subestimar o sobreestimar ventas.') }

---

{image_block('Grafico 5. Residuos vs prediccion', 'figures/sales_model/sales_model_best_residual_vs_predicted.png', 'Busca patrones de error por tamano de venta predicha.') }

---

# 6. Importancia de Variables

Importancia del mejor modelo:

{markdown_table(importance_table)}

En `Linear Regression`, la importancia se interpreta como el valor absoluto del coeficiente estandarizado. Es especialmente fiable para comparar variables numericas como precio, cantidad y descuento; en variables categoricas codificadas de forma ordinal debe leerse como una aproximacion.

{image_block('Grafico 6. Importancia de variables', 'figures/sales_model/sales_model_best_feature_importance.png', 'Muestra que variables explican mas la prediccion del mejor modelo.') }

---

# 7. Decision

Esta primera comparacion es deliberadamente sin lags ni rollings. Sirve para establecer un punto de partida limpio.

Lecturas esperadas:

- si precio y cantidad dominan, el problema esta muy condicionado por la composicion de la linea de pedido;
- si producto/categoria aportan mucho, conviene crear historicos por producto en la siguiente iteracion;
- si geografia o calendario aportan poco, pueden quedar como variables auxiliares;
- el metodo de pago queda fuera del modelo principal por riesgo de leakage antes de que la compra se complete.

Siguiente paso natural: probar lags/rollings historicos por producto, categoria, pais/ciudad y comprador, comparando siempre contra el baseline por producto.
"""

    REPORT_PATH.write_text(report, encoding="utf-8-sig")
    print(f"Informe generado: {REPORT_PATH}")
    print(f"Metricas: {METRICS_PATH}")
    print(f"Predicciones: {PREDICTIONS_PATH}")
    print(f"Residuos: {RESIDUALS_PATH}")
    print(f"Importancia: {IMPORTANCE_PATH}")
    print(f"Auditoria features: {FEATURE_AUDIT_PATH}")


if __name__ == "__main__":
    main()
