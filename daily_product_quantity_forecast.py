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
from sklearn.preprocessing import OneHotEncoder, OrdinalEncoder, StandardScaler
from sklearn.tree import DecisionTreeRegressor


PROJECT_DIR = Path(__file__).resolve().parent
DATA_PATH = PROJECT_DIR / "data" / "processed" / "dataco_supply_chain_processed.csv"
REPORTS_DIR = PROJECT_DIR / "reports"
FIGURES_DIR = REPORTS_DIR / "figures" / "daily_product_quantity_forecast"
PROCESSED_DIR = PROJECT_DIR / "data" / "processed"

REPORT_PATH = REPORTS_DIR / "daily_product_quantity_forecast_report.Rmd"
DATASET_PATH = PROCESSED_DIR / "daily_product_quantity_forecast_dataset.csv"
METRICS_PATH = PROCESSED_DIR / "daily_product_quantity_forecast_metrics.csv"
PREDICTIONS_PATH = PROCESSED_DIR / "daily_product_quantity_forecast_predictions.csv"
RESIDUALS_PATH = PROCESSED_DIR / "daily_product_quantity_forecast_residuals.csv"
FEATURE_AUDIT_PATH = PROCESSED_DIR / "daily_product_quantity_forecast_feature_audit.csv"
FEATURE_IMPORTANCE_PATH = PROCESSED_DIR / "daily_product_quantity_forecast_feature_importance.csv"

TARGET = "quantity_sold"
RANDOM_STATE = 42
TEST_START_DATE = pd.Timestamp("2017-01-01")
LAGS = [1, 7, 30, 365]
ROLLING_WINDOWS = [7, 30]

CATEGORICAL_FEATURES = [
    "Product Name",
    "Category Name",
    "Department Name",
    "calendar_period",
]

NUMERIC_BASE_FEATURES = [
    "order_year",
    "order_month",
    "order_day",
    "order_dayofweek",
    "order_dayofyear",
    "order_weekofyear",
    "order_quarter",
    "order_is_weekend",
    "order_month_sin",
    "order_month_cos",
    "order_dayofweek_sin",
    "order_dayofweek_cos",
    "is_generic_fixed_holiday",
    "days_since_product_first_seen",
]

LEAKAGE_EXCLUDED = [
    "Sales",
    "Order Item Product Price",
    "Order Item Quantity",
    "Order Item Discount",
    "Order Item Discount Rate",
    "Order Item Total",
    "Sales per customer",
    "Benefit per order",
    "Order Profit Per Order",
    "Order Item Profit Ratio",
    "Order Status",
    "Delivery Status",
    "Late_delivery_risk",
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
        rows.append("| " + " | ".join(str(value).replace("|", "/") for value in row) + " |")
    return "\n".join([header, separator, *rows])


def image_block(title: str, path: str, reading: str) -> str:
    return f"""
## {title}

<img src="{path}" alt="{title}" width="920">

**Lectura:** {reading}
"""


def add_calendar_features(df: pd.DataFrame) -> pd.DataFrame:
    result = df.copy()
    result["order_year"] = result["order_date"].dt.year
    result["order_month"] = result["order_date"].dt.month
    result["order_day"] = result["order_date"].dt.day
    result["order_dayofweek"] = result["order_date"].dt.dayofweek
    result["order_dayofyear"] = result["order_date"].dt.dayofyear
    result["order_weekofyear"] = result["order_date"].dt.isocalendar().week.astype(float)
    result["order_quarter"] = result["order_date"].dt.quarter
    result["order_is_weekend"] = result["order_dayofweek"].isin([5, 6]).astype(int)
    result["order_month_sin"] = np.sin(2 * np.pi * result["order_month"] / 12)
    result["order_month_cos"] = np.cos(2 * np.pi * result["order_month"] / 12)
    result["order_dayofweek_sin"] = np.sin(2 * np.pi * result["order_dayofweek"] / 7)
    result["order_dayofweek_cos"] = np.cos(2 * np.pi * result["order_dayofweek"] / 7)

    month_day = result["order_date"].dt.strftime("%m-%d")
    result["is_generic_fixed_holiday"] = month_day.isin(["01-01", "05-01", "12-25"]).astype(int)
    result["calendar_period"] = "Normal"
    result.loc[result["order_date"].dt.month.eq(12), "calendar_period"] = "Christmas season"
    result.loc[
        result["order_date"].dt.month.eq(11) & result["order_date"].dt.day.between(20, 30),
        "calendar_period",
    ] = "Black Friday period"
    result.loc[
        result["order_date"].dt.month.eq(9) & result["order_date"].dt.day.between(1, 15),
        "calendar_period",
    ] = "Back to school period"
    result.loc[result["is_generic_fixed_holiday"].eq(1), "calendar_period"] = "Generic fixed holiday"
    return result


def build_daily_dataset(raw: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    data = raw.copy()
    data["order_datetime"] = pd.to_datetime(data["order_datetime"], errors="coerce")
    data = data.dropna(subset=["order_datetime", "Product Name"]).copy()
    data["order_date"] = data["order_datetime"].dt.floor("D")

    product_meta = (
        data.sort_values("order_datetime")
        .groupby("Product Name", as_index=False)
        .agg(
            **{
                "Category Name": ("Category Name", lambda s: s.dropna().mode().iloc[0] if not s.dropna().empty else "Unknown"),
                "Department Name": ("Department Name", lambda s: s.dropna().mode().iloc[0] if not s.dropna().empty else "Unknown"),
                "product_first_seen": ("order_date", "min"),
            }
        )
    )

    daily_observed = (
        data.groupby(["Product Name", "order_date"], as_index=False)
        .agg(
            quantity_sold=("Order Item Quantity", "sum"),
            sales_sum=("Sales", "sum"),
            order_lines=("Sales", "size"),
            avg_price=("Order Item Product Price", "mean"),
            avg_discount=("Order Item Discount", "mean"),
            avg_discount_rate=("Order Item Discount Rate", "mean"),
        )
    )

    all_dates = pd.date_range(data["order_date"].min(), data["order_date"].max(), freq="D")
    full_index = pd.MultiIndex.from_product(
        [product_meta["Product Name"].sort_values(), all_dates],
        names=["Product Name", "order_date"],
    )
    daily = full_index.to_frame(index=False)
    daily = daily.merge(product_meta, on="Product Name", how="left")
    daily = daily.merge(daily_observed, on=["Product Name", "order_date"], how="left")
    daily[["quantity_sold", "sales_sum", "order_lines"]] = daily[
        ["quantity_sold", "sales_sum", "order_lines"]
    ].fillna(0.0)
    daily["had_sale"] = daily["order_lines"].gt(0).astype(int)
    daily["days_since_product_first_seen"] = (daily["order_date"] - daily["product_first_seen"]).dt.days.clip(lower=0)
    daily = add_calendar_features(daily)

    history_features: list[str] = []
    daily = daily.sort_values(["Product Name", "order_date"]).reset_index(drop=True)
    for source_col in ["quantity_sold", "sales_sum", "order_lines", "avg_price", "avg_discount", "avg_discount_rate"]:
        for lag in LAGS:
            col = f"product_{source_col}_lag_{lag}d"
            daily[col] = daily.groupby("Product Name")[source_col].shift(lag)
            history_features.append(col)
        for window in ROLLING_WINDOWS:
            shifted = daily.groupby("Product Name")[source_col].shift(1)
            mean_col = f"product_{source_col}_roll_mean_{window}d"
            sum_col = f"product_{source_col}_roll_sum_{window}d"
            daily[mean_col] = shifted.groupby(daily["Product Name"]).rolling(window, min_periods=1).mean().reset_index(level=0, drop=True)
            daily[sum_col] = shifted.groupby(daily["Product Name"]).rolling(window, min_periods=1).sum().reset_index(level=0, drop=True)
            history_features.extend([mean_col, sum_col])

    category_daily = (
        daily.groupby(["Category Name", "order_date"], as_index=False)
        .agg(category_quantity_sold=("quantity_sold", "sum"), category_sales_sum=("sales_sum", "sum"))
        .sort_values(["Category Name", "order_date"])
    )
    for source_col in ["category_quantity_sold", "category_sales_sum"]:
        for lag in [1, 7, 30]:
            shifted = category_daily[["Category Name", "order_date", source_col]].copy()
            shifted["order_date"] = shifted["order_date"] + pd.Timedelta(days=lag)
            col = f"{source_col}_lag_{lag}d"
            shifted = shifted.rename(columns={source_col: col})
            daily = daily.merge(shifted, on=["Category Name", "order_date"], how="left")
            history_features.append(col)
        for window in ROLLING_WINDOWS:
            col = f"{source_col}_roll_mean_{window}d"
            category_daily[col] = category_daily.groupby("Category Name")[source_col].transform(
                lambda s: s.shift(1).rolling(window, min_periods=1).mean()
            )
            daily = daily.merge(category_daily[["Category Name", "order_date", col]], on=["Category Name", "order_date"], how="left")
            history_features.append(col)

    global_daily = daily.groupby("order_date", as_index=False).agg(global_quantity_sold=("quantity_sold", "sum"))
    for lag in [1, 7, 30]:
        shifted = global_daily.copy()
        shifted["order_date"] = shifted["order_date"] + pd.Timedelta(days=lag)
        col = f"global_quantity_sold_lag_{lag}d"
        shifted = shifted.rename(columns={"global_quantity_sold": col})
        daily = daily.merge(shifted, on="order_date", how="left")
        history_features.append(col)
    for window in ROLLING_WINDOWS:
        col = f"global_quantity_sold_roll_mean_{window}d"
        global_daily[col] = global_daily["global_quantity_sold"].shift(1).rolling(window, min_periods=1).mean()
        daily = daily.merge(global_daily[["order_date", col]], on="order_date", how="left")
        history_features.append(col)

    return daily, history_features


def make_linear_preprocessor(categorical_features: list[str], numeric_features: list[str]) -> ColumnTransformer:
    return ColumnTransformer(
        transformers=[
            (
                "categorical",
                Pipeline(
                    steps=[
                        ("imputer", SimpleImputer(strategy="most_frequent")),
                        ("onehot", OneHotEncoder(handle_unknown="infrequent_if_exist", min_frequency=20, sparse_output=True)),
                    ]
                ),
                categorical_features,
            ),
            (
                "numeric",
                Pipeline(steps=[("imputer", SimpleImputer(strategy="median")), ("scaler", StandardScaler())]),
                numeric_features,
            ),
        ],
        sparse_threshold=0.3,
    )


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


def wape(y_true: pd.Series, y_pred: np.ndarray) -> float:
    denominator = np.abs(y_true).sum()
    if denominator == 0:
        return np.nan
    return float(np.abs(y_true - y_pred).sum() / denominator)


def mape_nonzero(y_true: pd.Series, y_pred: np.ndarray) -> float:
    arr = y_true.to_numpy(dtype=float)
    mask = arr != 0
    if not mask.any():
        return np.nan
    return float(np.mean(np.abs((arr[mask] - y_pred[mask]) / arr[mask])))


def evaluate(model_name: str, split: str, y_true: pd.Series, y_pred: np.ndarray, train_seconds: float | None = None) -> dict:
    pred = np.clip(np.asarray(y_pred, dtype=float), 0, None)
    mse = mean_squared_error(y_true, pred)
    residuals = y_true.to_numpy(dtype=float) - pred
    return {
        "model": model_name,
        "split": split,
        "mae": mean_absolute_error(y_true, pred),
        "mse": mse,
        "rmse": float(np.sqrt(mse)),
        "r2": r2_score(y_true, pred),
        "wape": wape(y_true, pred),
        "mape_nonzero_actual": mape_nonzero(y_true, pred),
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


def plot_predictions_by_month(predictions: pd.DataFrame, output: Path) -> None:
    monthly = predictions.groupby(predictions["order_date"].dt.to_period("M").astype(str), as_index=False).agg(
        actual=(TARGET, "sum"), predicted=("prediction", "sum")
    )
    monthly = monthly.rename(columns={"order_date": "month"})
    fig, ax = plt.subplots(figsize=(12, 5.8))
    ax.plot(monthly["month"], monthly["actual"], marker="o", label="Cantidad real", color="#4C78A8")
    ax.plot(monthly["month"], monthly["predicted"], marker="o", label="Cantidad predicha", color="#54A24B")
    ax.set_title("Cantidad diaria agregada: real vs predicha por mes", fontsize=15, pad=12)
    ax.set_xlabel("Mes de test")
    ax.set_ylabel("Cantidad")
    ax.tick_params(axis="x", rotation=60)
    ax.grid(axis="y", alpha=0.25)
    ax.legend()
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    fig.savefig(output, dpi=150)
    plt.close(fig)


def plot_residuals(residuals: pd.DataFrame, output: Path) -> None:
    fig, ax = plt.subplots(figsize=(10, 5.8))
    ax.hist(residuals["residual"], bins=60, color="#F58518", edgecolor="white")
    ax.axvline(0, color="black", linestyle="--", linewidth=1)
    ax.set_title("Residuos - mejor modelo demanda producto-dia", fontsize=15, pad=12)
    ax.set_xlabel("Residuo = real - predicho")
    ax.set_ylabel("Frecuencia")
    ax.grid(axis="y", alpha=0.25)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    fig.savefig(output, dpi=150)
    plt.close(fig)


def feature_importance(model_name: str, pipeline: Pipeline, categorical: list[str], numeric: list[str]) -> pd.DataFrame:
    preprocessor = pipeline.named_steps["preprocess"]
    estimator = pipeline.named_steps["model"]
    try:
        names = preprocessor.get_feature_names_out()
    except Exception:
        names = np.array(categorical + numeric)

    if hasattr(estimator, "coef_"):
        values = estimator.coef_
        out = pd.DataFrame({"model": model_name, "feature": names, "importance": np.abs(values), "raw_value": values})
    elif hasattr(estimator, "feature_importances_"):
        values = estimator.feature_importances_
        out = pd.DataFrame({"model": model_name, "feature": names, "importance": values, "raw_value": values})
    else:
        out = pd.DataFrame(columns=["model", "feature", "importance", "raw_value"])
    return out.sort_values("importance", ascending=False)


def write_report(metrics: pd.DataFrame, audit: pd.DataFrame, importance: pd.DataFrame, best_model_name: str) -> None:
    test_metrics = metrics[metrics["split"].eq("test")].sort_values("mae")
    best_overall = test_metrics.iloc[0]
    best_baseline = test_metrics[test_metrics["model"].str.startswith("Baseline")].iloc[0]
    best_ml = test_metrics[~test_metrics["model"].str.startswith("Baseline")].iloc[0]
    ml_gap = best_ml["mae"] - best_baseline["mae"]
    ml_gap_pct = ml_gap / best_baseline["mae"] if best_baseline["mae"] else np.nan

    report = f"""---
title: "Forecast de Demanda Diaria por Producto"
subtitle: "Prediccion de Order Item Quantity agregada producto-dia"
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

# Forecast de Cantidad Vendida

## Objetivo

El objetivo es predecir `Order Item Quantity` agregada por `Product Name` y dia para apoyar la planificacion diaria de demanda.

El dataset de modelado incluye todos los productos en todos los dias del rango historico. Si un producto no vendio en un dia, su target es `0`. Esto hace que el problema sea demanda diaria real, no solo prediccion sobre dias donde ya sabemos que hubo venta.

---

# 1. Validez Temporal

{markdown_table(audit)}

Lectura: las variables del dia predicho quedan fuera. El modelo utiliza historicos desplazados y datos disponibles antes de la fecha de estimacion.

---

# 2. Resultado General

Mejor resultado global en test: `{best_overall['model']}`.

Mejor modelo ML en test: `{best_ml['model']}`.

| metrica | valor |
| --- | ---: |
| MAE ganador global | {best_overall['mae']:.4f} |
| RMSE ganador global | {best_overall['rmse']:.4f} |
| R2 ganador global | {best_overall['r2']:.4f} |
| WAPE ganador global | {best_overall['wape']:.4f} |
| MAE mejor ML | {best_ml['mae']:.4f} |
| RMSE mejor ML | {best_ml['rmse']:.4f} |
| R2 mejor ML | {best_ml['r2']:.4f} |
| WAPE mejor ML | {best_ml['wape']:.4f} |

El mejor modelo ML queda {ml_gap:.4f} puntos de MAE por encima del mejor baseline historico, equivalente a {ml_gap_pct:.2%} mas error. Por tanto, en esta primera version los modelos complejos no superan a una regla historica simple.

---

# 3. Comparacion de Modelos

{markdown_table(test_metrics[['model', 'mae', 'mse', 'rmse', 'r2', 'wape', 'mape_nonzero_actual', 'train_seconds']].round(4))}

{image_block(
    "MAE en test",
    "figures/daily_product_quantity_forecast/daily_quantity_mae.png",
    "Compara el error absoluto medio por producto-dia. Menor es mejor."
)}

{image_block(
    "WAPE en test",
    "figures/daily_product_quantity_forecast/daily_quantity_wape.png",
    "Mide el error total relativo a la cantidad real vendida."
)}

{image_block(
    "Cantidad real vs predicha por mes",
    "figures/daily_product_quantity_forecast/daily_quantity_actual_vs_predicted_month.png",
    "Comprueba si el mejor modelo ML sigue el volumen agregado mensual de unidades. El ganador global por MAE sigue siendo el baseline rolling 7d."
)}

{image_block(
    "Residuos del mejor modelo ML",
    "figures/daily_product_quantity_forecast/daily_quantity_residuals.png",
    "Permite ver sesgo y dispersion de errores producto-dia."
)}

---

# 4. Importancia de Variables

{markdown_table(importance[importance['model'].eq(best_model_name)].head(25).round(4))}

Lectura: las variables relevantes son historicos de demanda, calendario y atributos de producto o categoria disponibles antes de la fecha de estimacion.

---

# 5. Conclusion

La conclusion honesta de esta prueba es que los modelos complejos no superan al baseline rolling 7d por producto. Con los datos actuales, la regla historica simple es la referencia a usar. El siguiente paso no es vender un modelo complejo, sino mejorar el planteamiento: probar agregacion semanal, forecast por categoria/producto importante, variables externas o senales comerciales planificadas.
"""
    REPORT_PATH.write_text(report, encoding="utf-8")


def main() -> None:
    start = perf_counter()
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    raw_cols = [
        "order_datetime",
        "Product Name",
        "Category Name",
        "Department Name",
        "Order Item Quantity",
        "Sales",
        "Order Item Product Price",
        "Order Item Discount",
        "Order Item Discount Rate",
    ]
    raw = pd.read_csv(DATA_PATH, usecols=raw_cols, low_memory=False)
    daily, history_features = build_daily_dataset(raw)
    feature_columns = CATEGORICAL_FEATURES + NUMERIC_BASE_FEATURES + history_features

    train = daily[daily["order_date"].lt(TEST_START_DATE)].copy()
    test = daily[daily["order_date"].ge(TEST_START_DATE)].copy()
    X_train, y_train = train[feature_columns], train[TARGET]
    X_test, y_test = test[feature_columns], test[TARGET]

    metrics_rows = []
    prediction_frames = []
    residual_frames = []
    importances = []

    baseline_predictions = {
        "Baseline global train mean": np.full(len(test), y_train.mean()),
        "Baseline product train mean": test["Product Name"].map(train.groupby("Product Name")[TARGET].mean()).fillna(y_train.mean()).to_numpy(),
        "Baseline lag 1d by Product": test["product_quantity_sold_lag_1d"].fillna(y_train.mean()).to_numpy(),
        "Baseline rolling 7d by Product": test["product_quantity_sold_roll_mean_7d"].fillna(y_train.mean()).to_numpy(),
        "Baseline rolling 30d by Product": test["product_quantity_sold_roll_mean_30d"].fillna(y_train.mean()).to_numpy(),
    }
    for name, pred in baseline_predictions.items():
        metrics_rows.append(evaluate(name, "test", y_test, pred, None))

    models = {
        "Linear Regression": Pipeline(
            steps=[
                ("preprocess", make_linear_preprocessor(CATEGORICAL_FEATURES, NUMERIC_BASE_FEATURES + history_features)),
                ("model", LinearRegression()),
            ]
        ),
        "Lasso": Pipeline(
            steps=[
                ("preprocess", make_linear_preprocessor(CATEGORICAL_FEATURES, NUMERIC_BASE_FEATURES + history_features)),
                ("model", Lasso(alpha=0.001, max_iter=10000, random_state=RANDOM_STATE)),
            ]
        ),
        "Decision Tree": Pipeline(
            steps=[
                ("preprocess", make_tree_preprocessor(CATEGORICAL_FEATURES, NUMERIC_BASE_FEATURES + history_features)),
                ("model", DecisionTreeRegressor(random_state=RANDOM_STATE, min_samples_leaf=10, max_depth=18)),
            ]
        ),
        "Random Forest": Pipeline(
            steps=[
                ("preprocess", make_tree_preprocessor(CATEGORICAL_FEATURES, NUMERIC_BASE_FEATURES + history_features)),
                ("model", RandomForestRegressor(n_estimators=120, random_state=RANDOM_STATE, min_samples_leaf=5, max_features="sqrt", n_jobs=-1)),
            ]
        ),
        "Hist Gradient Boosting": Pipeline(
            steps=[
                ("preprocess", make_tree_preprocessor(CATEGORICAL_FEATURES, NUMERIC_BASE_FEATURES + history_features)),
                ("model", HistGradientBoostingRegressor(random_state=RANDOM_STATE, max_iter=200, learning_rate=0.06, l2_regularization=0.05)),
            ]
        ),
    }

    for name, model in models.items():
        fit_start = perf_counter()
        model.fit(X_train, y_train)
        train_seconds = perf_counter() - fit_start
        pred_train = np.clip(model.predict(X_train), 0, None)
        pred_test = np.clip(model.predict(X_test), 0, None)
        metrics_rows.append(evaluate(name, "train", y_train, pred_train, train_seconds))
        metrics_rows.append(evaluate(name, "test", y_test, pred_test, train_seconds))
        importances.append(feature_importance(name, model, CATEGORICAL_FEATURES, NUMERIC_BASE_FEATURES + history_features))

        predictions = test[["Product Name", "Category Name", "Department Name", "order_date", TARGET]].copy()
        predictions["model"] = name
        predictions["prediction"] = pred_test
        predictions["residual"] = predictions[TARGET] - predictions["prediction"]
        prediction_frames.append(predictions)
        residual_frames.append(predictions[["model", "Product Name", "order_date", TARGET, "prediction", "residual"]].copy())

    metrics = pd.DataFrame(metrics_rows)
    test_metrics = metrics[metrics["split"].eq("test")].sort_values("mae")
    best_model_name = test_metrics[~test_metrics["model"].str.startswith("Baseline")].iloc[0]["model"]
    best_predictions = pd.concat(prediction_frames, ignore_index=True)
    best_predictions = best_predictions[best_predictions["model"].eq(best_model_name)].copy()
    all_predictions = pd.concat(prediction_frames, ignore_index=True)
    residuals = pd.concat(residual_frames, ignore_index=True)
    importance_df = pd.concat(importances, ignore_index=True) if importances else pd.DataFrame()

    audit = pd.DataFrame(
        [
            {"check": "target", "estado": TARGET, "lectura": "Cantidad diaria por producto; incluye ceros producto-dia"},
            {"check": "split", "estado": f"train < {TEST_START_DATE.date()}, test >= {TEST_START_DATE.date()}", "lectura": "Temporal, sin mezcla aleatoria"},
            {"check": "same_day_quantity", "estado": "excluida", "lectura": "El target no entra como feature contemporanea"},
            {"check": "same_day_price_discount_sales", "estado": "excluidas", "lectura": "Precio, descuento y Sales del mismo dia no se usan"},
            {"check": "history_features", "estado": len(history_features), "lectura": "Lags/rollings desplazados por producto, categoria y global"},
            {"check": "rolling_shift", "estado": "shift(1)", "lectura": "Los rollings usan informacion anterior al dia predicho"},
            {"check": "raw_data", "estado": "intactos", "lectura": "Solo se generan salidas derivadas en data/processed y reports"},
        ]
    )

    plot_metric(metrics, "mae", "Forecast cantidad producto-dia - MAE test", FIGURES_DIR / "daily_quantity_mae.png")
    plot_metric(metrics, "wape", "Forecast cantidad producto-dia - WAPE test", FIGURES_DIR / "daily_quantity_wape.png")
    plot_predictions_by_month(best_predictions, FIGURES_DIR / "daily_quantity_actual_vs_predicted_month.png")
    plot_residuals(best_predictions.rename(columns={TARGET: "actual_quantity"}), FIGURES_DIR / "daily_quantity_residuals.png")

    daily.to_csv(DATASET_PATH, index=False)
    metrics.round(6).to_csv(METRICS_PATH, index=False)
    all_predictions.round(6).to_csv(PREDICTIONS_PATH, index=False)
    residuals.round(6).to_csv(RESIDUALS_PATH, index=False)
    audit.to_csv(FEATURE_AUDIT_PATH, index=False)
    importance_df.round(6).to_csv(FEATURE_IMPORTANCE_PATH, index=False)
    write_report(metrics, audit, importance_df, best_model_name)

    print(f"Generated {REPORT_PATH}")
    print(f"Generated {METRICS_PATH}")
    print(test_metrics[["model", "mae", "rmse", "r2", "wape", "mape_nonzero_actual", "train_seconds"]].to_string(index=False))
    print(f"Runtime seconds: {perf_counter() - start:.2f}")


if __name__ == "__main__":
    main()
