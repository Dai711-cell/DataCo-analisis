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
FIGURES_DIR = REPORTS_DIR / "figures" / "random_forest_arrival_lag_rolling"
PROCESSED_DIR = PROJECT_DIR / "data" / "processed"
REPORT_PATH = REPORTS_DIR / "random_forest_arrival_lag_rolling_report.Rmd"
METRICS_PATH = PROCESSED_DIR / "random_forest_arrival_lag_rolling_metrics.csv"
PREDICTIONS_PATH = PROCESSED_DIR / "random_forest_arrival_lag_rolling_predictions.csv"
RESIDUALS_PATH = PROCESSED_DIR / "random_forest_arrival_lag_rolling_residuals.csv"
IMPORTANCE_PATH = PROCESSED_DIR / "random_forest_arrival_lag_rolling_feature_importance.csv"
COVERAGE_PATH = PROCESSED_DIR / "random_forest_arrival_lag_rolling_feature_coverage.csv"

RANDOM_STATE = 42
TEST_SIZE = 0.2
TARGET = "Days for shipping (real)"
CURRENT_SYSTEM_PREDICTION = "Days for shipment (scheduled)"

BEST_RF_PARAMS = {
    "n_estimators": 120,
    "max_depth": 18,
    "min_samples_leaf": 8,
    "min_samples_split": 16,
    "max_features": 1.0,
    "bootstrap": True,
}

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

BASE_NUMERIC_FEATURES = [
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

HISTORY_FEATURES = [
    "mode_completed_lag1_days",
    "mode_completed_mean_last_7",
    "mode_completed_mean_last_30",
    "mode_completed_mean_last_100",
    "mode_completed_std_last_30",
    "mode_completed_expanding_mean",
    "mode_completed_late_rate_last_30",
    "mode_completed_mean_prev_7d",
    "mode_completed_mean_prev_30d",
    "mode_completed_late_rate_prev_30d",
    "mode_completed_count_prev_7d",
    "mode_completed_count_prev_30d",
    "mode_order_count_prev_7d",
    "mode_order_count_prev_30d",
    "mode_order_count_prev_90d",
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


def add_order_date_features(df: pd.DataFrame) -> pd.DataFrame:
    result = df.copy()
    result["order_datetime"] = pd.to_datetime(result["order_datetime"], errors="coerce")
    result["shipping_datetime"] = pd.to_datetime(result["shipping_datetime"], errors="coerce")
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


def safe_divide(numerator: np.ndarray, denominator: np.ndarray) -> np.ndarray:
    result = np.full(len(numerator), np.nan, dtype=float)
    mask = denominator > 0
    result[mask] = numerator[mask] / denominator[mask]
    return result


def window_mean(values: np.ndarray, cumsum: np.ndarray, start: np.ndarray, end: np.ndarray) -> np.ndarray:
    counts = end - start
    sums = cumsum[end] - cumsum[start]
    return safe_divide(sums, counts)


def window_std(values_sq_cumsum: np.ndarray, cumsum: np.ndarray, start: np.ndarray, end: np.ndarray) -> np.ndarray:
    counts = end - start
    sums = cumsum[end] - cumsum[start]
    sums_sq = values_sq_cumsum[end] - values_sq_cumsum[start]
    means = safe_divide(sums, counts)
    second_moments = safe_divide(sums_sq, counts)
    variance = second_moments - np.square(means)
    variance = np.where(np.isnan(variance), np.nan, np.maximum(variance, 0))
    return np.sqrt(variance)


def add_shipping_mode_history_features(df: pd.DataFrame) -> pd.DataFrame:
    result = df.copy()
    for feature in HISTORY_FEATURES:
        result[feature] = np.nan

    result["_underpromised_history"] = (result[TARGET] > result[CURRENT_SYSTEM_PREDICTION]).astype(float)
    one_day_ns = np.int64(24 * 60 * 60 * 1_000_000_000)

    for mode, current in result.groupby("Shipping Mode", sort=False):
        current = current.sort_values(["order_datetime", "Order Id"]).copy()
        current_idx = current.index
        current_times = current["order_datetime"].astype("int64").to_numpy()

        completed = result[
            result["Shipping Mode"].eq(mode)
            & result["shipping_datetime"].notna()
            & result[TARGET].notna()
        ].sort_values(["shipping_datetime", "Order Id"])

        if completed.empty:
            continue

        completed_times = completed["shipping_datetime"].astype("int64").to_numpy()
        completed_days = completed[TARGET].astype(float).to_numpy()
        completed_late = completed["_underpromised_history"].astype(float).to_numpy()
        cumsum_days = np.concatenate([[0.0], np.cumsum(completed_days)])
        cumsum_days_sq = np.concatenate([[0.0], np.cumsum(np.square(completed_days))])
        cumsum_late = np.concatenate([[0.0], np.cumsum(completed_late)])

        pos = np.searchsorted(completed_times, current_times, side="left")

        lag1 = np.full(len(current), np.nan, dtype=float)
        has_lag = pos > 0
        lag1[has_lag] = completed_days[pos[has_lag] - 1]
        result.loc[current_idx, "mode_completed_lag1_days"] = lag1

        for n in [7, 30, 100]:
            start_n = np.maximum(pos - n, 0)
            result.loc[current_idx, f"mode_completed_mean_last_{n}"] = window_mean(
                completed_days, cumsum_days, start_n, pos
            )

        start_30 = np.maximum(pos - 30, 0)
        result.loc[current_idx, "mode_completed_std_last_30"] = window_std(
            cumsum_days_sq, cumsum_days, start_30, pos
        )
        result.loc[current_idx, "mode_completed_late_rate_last_30"] = window_mean(
            completed_late, cumsum_late, start_30, pos
        )
        result.loc[current_idx, "mode_completed_expanding_mean"] = safe_divide(cumsum_days[pos], pos)

        for days in [7, 30]:
            start_time = np.searchsorted(completed_times, current_times - days * one_day_ns, side="left")
            result.loc[current_idx, f"mode_completed_mean_prev_{days}d"] = window_mean(
                completed_days, cumsum_days, start_time, pos
            )
            result.loc[current_idx, f"mode_completed_count_prev_{days}d"] = pos - start_time

        start_time_30 = np.searchsorted(completed_times, current_times - 30 * one_day_ns, side="left")
        result.loc[current_idx, "mode_completed_late_rate_prev_30d"] = window_mean(
            completed_late, cumsum_late, start_time_30, pos
        )

        order_times = current_times
        order_pos = np.searchsorted(order_times, current_times, side="left")
        for days in [7, 30, 90]:
            start_orders = np.searchsorted(order_times, current_times - days * one_day_ns, side="left")
            result.loc[current_idx, f"mode_order_count_prev_{days}d"] = order_pos - start_orders

    return result.drop(columns=["_underpromised_history"])


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
            ("numeric", Pipeline(steps=[("imputer", SimpleImputer(strategy="median"))]), numeric_features),
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


def train_rf(
    model_name: str,
    train_df: pd.DataFrame,
    test_df: pd.DataFrame,
    categorical_features: list[str],
    numeric_features: list[str],
) -> tuple[Pipeline, np.ndarray, np.ndarray, float]:
    features = categorical_features + numeric_features
    pipeline = Pipeline(
        steps=[
            ("preprocess", make_preprocessor(categorical_features, numeric_features)),
            ("model", RandomForestRegressor(**BEST_RF_PARAMS, n_jobs=-1, random_state=RANDOM_STATE)),
        ]
    )
    start = perf_counter()
    pipeline.fit(train_df[features], train_df[TARGET])
    train_seconds = perf_counter() - start
    train_pred = np.clip(pipeline.predict(train_df[features]), 0, None)
    test_pred = np.clip(pipeline.predict(test_df[features]), 0, None)
    print(f"{model_name}: entrenado en {train_seconds:.1f}s", flush=True)
    return pipeline, train_pred, test_pred, train_seconds


def markdown_table(df: pd.DataFrame) -> str:
    if df.empty:
        return "_Sin datos._"
    table = df.copy()
    table = table.where(pd.notna(table), "")
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


def plot_importance(importance: pd.DataFrame, output: Path, title: str) -> None:
    data = importance.head(20).sort_values("importance", ascending=True)
    fig, ax = plt.subplots(figsize=(10.5, 7))
    bars = ax.barh(data["feature"], data["importance"], color="#B07AA1")
    ax.bar_label(bars, fmt="%.3f", padding=4, fontsize=8)
    ax.set_title(title, fontsize=15, pad=12)
    ax.set_xlabel("Importancia")
    ax.grid(axis="x", alpha=0.25)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    fig.savefig(output, dpi=150)
    plt.close(fig)


def plot_residual_hist(residuals: pd.DataFrame, model: str, output: Path) -> None:
    data = residuals[residuals["model"].eq(model)]["residual"]
    fig, ax = plt.subplots(figsize=(10, 5.5))
    ax.hist(data, bins=35, color="#F28E2B", edgecolor="white")
    ax.axvline(0, color="black", linestyle="--", linewidth=1)
    ax.set_title(f"Distribucion de residuos - {model}", fontsize=15, pad=12)
    ax.set_xlabel("Residuo = real - predicho")
    ax.set_ylabel("Frecuencia")
    ax.grid(axis="y", alpha=0.25)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    fig.savefig(output, dpi=150)
    plt.close(fig)


def plot_mae_by_mode(residuals: pd.DataFrame, model: str, output: Path) -> None:
    data = residuals[residuals["model"].eq(model)].copy()
    grouped = data.groupby("Shipping Mode")["absolute_error"].mean().sort_values(ascending=True)
    fig, ax = plt.subplots(figsize=(10, 5.5))
    bars = ax.barh(grouped.index, grouped.values, color="#59A14F")
    ax.bar_label(bars, fmt="%.3f", padding=4)
    ax.set_title(f"MAE por tipo de envio - {model}", fontsize=15, pad=12)
    ax.set_xlabel("MAE en dias")
    ax.grid(axis="x", alpha=0.25)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    fig.savefig(output, dpi=150)
    plt.close(fig)


def main() -> None:
    REPORTS_DIR.mkdir(exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(exist_ok=True)

    print("Leyendo dataset procesado...", flush=True)
    df = pd.read_csv(DATA_PATH, low_memory=False)
    print("Creando variables de fecha del pedido...", flush=True)
    df = add_order_date_features(df)
    df = df.dropna(subset=["order_datetime", TARGET, CURRENT_SYSTEM_PREDICTION, "Shipping Mode"]).copy()
    print("Creando lags y rollings as-of por Shipping Mode...", flush=True)
    df = add_shipping_mode_history_features(df)

    available_categorical = [col for col in CATEGORICAL_FEATURES if col in df.columns]
    available_base_numeric = [col for col in BASE_NUMERIC_FEATURES if col in df.columns]
    available_history = [col for col in HISTORY_FEATURES if col in df.columns]
    base_features = available_categorical + available_base_numeric
    history_features = available_categorical + available_base_numeric + available_history

    train_df, test_df = temporal_train_test_split(df)
    y_train = train_df[TARGET]
    y_test = test_df[TARGET]

    metrics: list[dict[str, float | str | None]] = []
    residual_frames: list[pd.DataFrame] = []
    predictions = pd.DataFrame(
        {
            "Order Id": test_df["Order Id"].values,
            "order_datetime": test_df["order_datetime"].values,
            "Shipping Mode": test_df["Shipping Mode"].values,
            "actual_days": y_test.values,
        }
    )

    previous_metrics_path = PROCESSED_DIR / "random_forest_arrival_tuning_metrics.csv"
    if previous_metrics_path.exists():
        previous_metrics = pd.read_csv(previous_metrics_path)
        previous_rf = previous_metrics[previous_metrics["model"].eq("RF_base_previous")].copy()
        previous_rf["model"] = "RF_best_no_history_previous_run"
        metrics.extend(previous_rf.to_dict(orient="records"))

    current_test = test_df[CURRENT_SYSTEM_PREDICTION].astype(float).to_numpy()
    current_train = train_df[CURRENT_SYSTEM_PREDICTION].astype(float).to_numpy()
    metrics.append(evaluate_predictions("Current system scheduled days", "train", y_train, current_train, 0.0))
    metrics.append(evaluate_predictions("Current system scheduled days", "test", y_test, current_test, 0.0))

    mode_means = train_df.groupby("Shipping Mode")[TARGET].mean()
    global_mean = float(y_train.mean())
    mode_train = train_df["Shipping Mode"].map(mode_means).fillna(global_mean).to_numpy()
    mode_test = test_df["Shipping Mode"].map(mode_means).fillna(global_mean).to_numpy()
    metrics.append(evaluate_predictions("Baseline mean by Shipping Mode", "train", y_train, mode_train, 0.0))
    metrics.append(evaluate_predictions("Baseline mean by Shipping Mode", "test", y_test, mode_test, 0.0))

    historical_rule_train = train_df["mode_completed_expanding_mean"].fillna(global_mean).to_numpy()
    historical_rule_test = test_df["mode_completed_expanding_mean"].fillna(global_mean).to_numpy()
    metrics.append(evaluate_predictions("As-of mode historical mean", "train", y_train, historical_rule_train, 0.0))
    metrics.append(evaluate_predictions("As-of mode historical mean", "test", y_test, historical_rule_test, 0.0))

    print("Entrenando Random Forest ganador con historicos...", flush=True)
    rf_hist, rf_hist_train, rf_hist_test, rf_hist_seconds = train_rf(
        "RF_best_with_mode_lags_rollings",
        train_df,
        test_df,
        available_categorical,
        available_base_numeric + available_history,
    )
    metrics.append(evaluate_predictions("RF_best_with_mode_lags_rollings", "train", y_train, rf_hist_train, rf_hist_seconds))
    metrics.append(evaluate_predictions("RF_best_with_mode_lags_rollings", "test", y_test, rf_hist_test, rf_hist_seconds))
    predictions["RF_best_with_mode_lags_rollings"] = rf_hist_test

    for model_name, test_pred in {
        "Current system scheduled days": current_test,
        "Baseline mean by Shipping Mode": mode_test,
        "As-of mode historical mean": historical_rule_test,
        "RF_best_with_mode_lags_rollings": rf_hist_test,
    }.items():
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

    coverage = (
        df[available_history]
        .notna()
        .mean()
        .rename("non_null_share")
        .reset_index()
        .rename(columns={"index": "feature"})
    )
    coverage.to_csv(COVERAGE_PATH, index=False)

    best_model = str(metrics_df[metrics_df["split"].eq("test")].iloc[0]["model"])
    hist_importance = pd.DataFrame(
        {
            "feature": history_features,
            "importance": rf_hist.named_steps["model"].feature_importances_,
            "is_history_feature": [name in available_history for name in history_features],
        }
    ).sort_values("importance", ascending=False)
    hist_importance.to_csv(IMPORTANCE_PATH, index=False)

    plot_metric(metrics_df, "mae", "Comparacion con lags y rollings - MAE test", FIGURES_DIR / "rf_lag_rolling_mae.png")
    plot_metric(metrics_df, "rmse", "Comparacion con lags y rollings - RMSE test", FIGURES_DIR / "rf_lag_rolling_rmse.png")
    plot_metric(metrics_df, "wape", "Comparacion con lags y rollings - WAPE test", FIGURES_DIR / "rf_lag_rolling_wape.png")
    plot_importance(hist_importance, FIGURES_DIR / "rf_lag_rolling_feature_importance.png", "Importancia de variables con lags y rollings")
    history_importance = hist_importance[hist_importance["is_history_feature"]].copy()
    plot_importance(history_importance, FIGURES_DIR / "rf_lag_rolling_history_importance.png", "Importancia de historicos por tipo de envio")
    plot_residual_hist(residuals, "RF_best_with_mode_lags_rollings", FIGURES_DIR / "rf_lag_rolling_residual_histogram.png")
    plot_mae_by_mode(residuals, "RF_best_with_mode_lags_rollings", FIGURES_DIR / "rf_lag_rolling_mae_by_shipping_mode.png")

    metrics_table = metrics_df.copy()
    for column in ["mae", "mse", "rmse", "r2", "wape", "mape_nonzero_actual", "residual_mean", "residual_median", "residual_std", "train_seconds"]:
        metrics_table[column] = metrics_table[column].astype(float).round(4)

    test_metrics = metrics_df[metrics_df["split"].eq("test")].sort_values("mae")
    best_metrics = test_metrics.iloc[0]
    no_history_metrics = test_metrics[test_metrics["model"].eq("RF_best_no_history_previous_run")].iloc[0]
    history_metrics = test_metrics[test_metrics["model"].eq("RF_best_with_mode_lags_rollings")].iloc[0]
    current_metrics = test_metrics[test_metrics["model"].eq("Current system scheduled days")].iloc[0]
    mode_baseline_metrics = test_metrics[test_metrics["model"].eq("Baseline mean by Shipping Mode")].iloc[0]

    residual_summary = (
        residuals[residuals["model"].eq("RF_best_with_mode_lags_rollings")]
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

    feature_summary = hist_importance.head(20).copy()
    feature_summary["importance"] = feature_summary["importance"].round(4)
    coverage_table = coverage.copy()
    coverage_table["non_null_share"] = coverage_table["non_null_share"].round(4)

    improvement_vs_no_history = no_history_metrics["mae"] - history_metrics["mae"]
    improvement_vs_mode_baseline = mode_baseline_metrics["mae"] - history_metrics["mae"]

    conclusion = (
        "Los lags y rollings ayudan de forma material frente al Random Forest sin historico."
        if improvement_vs_no_history > 0.02
        else "Los lags y rollings no aportan una mejora material frente al Random Forest sin historico."
    )

    report = f"""---
title: "Random Forest con Lags y Rollings por Tipo de Envio"
subtitle: "Prueba de historicos sin leakage para prediccion de llegada"
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

# Random Forest con Lags y Rollings

## DataCo Supply Chain

**Objetivo:** comprobar si historicos por `Shipping Mode` capturan saturacion, cambios operativos o patrones temporales que mejoren el mejor Random Forest anterior.

</div>

---

# 1. Resumen Ejecutivo

El mejor modelo en test fue `{best_model}`.

| Comparacion | MAE | MSE | RMSE | R2 | WAPE | MAPE sin dias 0 |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| RF sin historico anterior | {no_history_metrics['mae']:.4f} | {no_history_metrics['mse']:.4f} | {no_history_metrics['rmse']:.4f} | {no_history_metrics['r2']:.4f} | {no_history_metrics['wape']:.4f} | {no_history_metrics['mape_nonzero_actual']:.4f} |
| RF con lags/rollings de Shipping Mode | {history_metrics['mae']:.4f} | {history_metrics['mse']:.4f} | {history_metrics['rmse']:.4f} | {history_metrics['r2']:.4f} | {history_metrics['wape']:.4f} | {history_metrics['mape_nonzero_actual']:.4f} |
| Baseline media por Shipping Mode | {mode_baseline_metrics['mae']:.4f} | {mode_baseline_metrics['mse']:.4f} | {mode_baseline_metrics['rmse']:.4f} | {mode_baseline_metrics['r2']:.4f} | {mode_baseline_metrics['wape']:.4f} | {mode_baseline_metrics['mape_nonzero_actual']:.4f} |
| Sistema actual | {current_metrics['mae']:.4f} | {current_metrics['mse']:.4f} | {current_metrics['rmse']:.4f} | {current_metrics['r2']:.4f} | {current_metrics['wape']:.4f} | {current_metrics['mape_nonzero_actual']:.4f} |

Mejora del RF con historicos frente al RF sin historico: **{improvement_vs_no_history:.4f} dias de MAE**.

Mejora del RF con historicos frente al baseline por `Shipping Mode`: **{improvement_vs_mode_baseline:.4f} dias de MAE**.

**Conclusion:** {conclusion}

Si la mejora frente al baseline simple sigue siendo pequena, la recomendacion mas defendible no es construir un modelo complejo, sino actualizar la promesa base por tipo de envio. Es facil de explicar, facil de mantener y casi igual de efectiva.

---

# 2. Como se Construyeron los Historicos

Para evitar leakage, los historicos no usan el resultado del pedido actual. Tampoco usan pedidos anteriores que aun no habrian terminado en el momento del pedido actual.

Regla usada:

```text
Para cada pedido actual:
usar solo envios del mismo Shipping Mode
con shipping_datetime anterior a order_datetime del pedido actual.
```

Esto simula informacion que la empresa si podria tener en produccion: desempeno de envios ya completados antes de recibir el nuevo pedido.

Features historicas creadas:

{markdown_table(pd.DataFrame({'feature': available_history}))}

Cobertura de estas variables:

{markdown_table(coverage_table)}

---

# 3. Parametros del Random Forest

Se mantuvo el mejor Random Forest anterior para aislar el efecto de los lags y rollings.

{markdown_table(pd.DataFrame([BEST_RF_PARAMS]))}

---

# 4. Resultados Completos

MAPE excluye filas con valor real 0 dias. WAPE se calcula como `sum(abs(error)) / sum(abs(real))`.

{markdown_table(metrics_table)}

{image_block('Grafico 1. MAE en test', 'figures/random_forest_arrival_lag_rolling/rf_lag_rolling_mae.png', 'Compara directamente el sistema actual, el baseline simple, el RF sin historico y el RF con historicos.') }

---

{image_block('Grafico 2. RMSE en test', 'figures/random_forest_arrival_lag_rolling/rf_lag_rolling_rmse.png', 'RMSE penaliza errores grandes. Si apenas cambia, los historicos no estan corrigiendo fallos fuertes.') }

---

{image_block('Grafico 3. WAPE en test', 'figures/random_forest_arrival_lag_rolling/rf_lag_rolling_wape.png', 'WAPE resume el error absoluto total frente al total de dias reales.') }

---

# 5. Residuos del RF con Historicos

Residuo:

```text
residuo = dias reales - dias predichos
```

Resumen por tipo de envio:

{markdown_table(residual_summary)}

{image_block('Grafico 4. Histograma de residuos', 'figures/random_forest_arrival_lag_rolling/rf_lag_rolling_residual_histogram.png', 'Muestra si el modelo con historicos tiende a subestimar o sobreestimar los dias de llegada.') }

---

{image_block('Grafico 5. MAE por tipo de envio', 'figures/random_forest_arrival_lag_rolling/rf_lag_rolling_mae_by_shipping_mode.png', 'Permite ver si los historicos ayudan justo donde estaba el problema: Second Class y Standard Class.') }

---

# 6. Importancia de Variables

Importancia general del RF con historicos:

{markdown_table(feature_summary)}

{image_block('Grafico 6. Importancia general', 'figures/random_forest_arrival_lag_rolling/rf_lag_rolling_feature_importance.png', 'Si `Shipping Mode` sigue dominando, el modelo sigue dependiendo casi todo de la promesa base del envio.') }

---

Importancia solo de variables historicas:

{markdown_table(history_importance.head(15).round(4))}

{image_block('Grafico 7. Importancia de historicos', 'figures/random_forest_arrival_lag_rolling/rf_lag_rolling_history_importance.png', 'Mide si los lags, rollings y volumen reciente por tipo de envio aportan senal real.') }

---

# 7. Decision

Esta prueba responde a la duda de saturacion o cambios recientes por tipo de envio.

Si el RF con lags/rollings no mejora de forma clara frente al baseline por `Shipping Mode`, entonces no hay suficiente informacion en estos datos para justificar un modelo operativo complejo. En ese caso la conclusion del proyecto queda muy limpia:

1. el sistema actual de promesa de dias esta mal calibrado;
2. actualizar a un baseline por `Shipping Mode` es facil, interpretable y casi igual de efectivo que el mejor modelo;
3. para justificar un modelo real harian falta datos operativos adicionales: capacidad logistica diaria, transportista, almacen, distancia, stock, incidencias, dias festivos y estado real de preparacion del pedido.
"""

    REPORT_PATH.write_text(report, encoding="utf-8-sig")
    print(f"Reporte generado: {REPORT_PATH}")
    print(f"Metricas: {METRICS_PATH}")
    print(f"Predicciones: {PREDICTIONS_PATH}")
    print(f"Residuos: {RESIDUALS_PATH}")
    print(f"Importancias: {IMPORTANCE_PATH}")
    print(f"Cobertura: {COVERAGE_PATH}")


if __name__ == "__main__":
    main()
