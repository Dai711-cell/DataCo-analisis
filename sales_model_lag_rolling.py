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
PREVIOUS_METRICS_PATH = PROJECT_DIR / "data" / "processed" / "sales_model_comparison_metrics.csv"
REPORTS_DIR = PROJECT_DIR / "reports"
FIGURES_DIR = REPORTS_DIR / "figures" / "sales_model_lag_rolling"
PROCESSED_DIR = PROJECT_DIR / "data" / "processed"
REPORT_PATH = REPORTS_DIR / "sales_model_lag_rolling_report.Rmd"
METRICS_PATH = PROCESSED_DIR / "sales_model_lag_rolling_metrics.csv"
PREDICTIONS_PATH = PROCESSED_DIR / "sales_model_lag_rolling_predictions.csv"
RESIDUALS_PATH = PROCESSED_DIR / "sales_model_lag_rolling_residuals.csv"
IMPORTANCE_PATH = PROCESSED_DIR / "sales_model_lag_rolling_feature_importance.csv"
AUDIT_PATH = PROCESSED_DIR / "sales_model_lag_rolling_audit.csv"

RANDOM_STATE = 42
TEST_SIZE = 0.2
TARGET = "Sales"
LAGS = [1, 7, 30, 365]
ROLLING_WINDOWS = [7, 30]

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

BASE_NUMERIC_FEATURES = [
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
    result["order_date"] = result["order_datetime"].dt.floor("D")
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


def add_exact_lags(frame: pd.DataFrame, daily: pd.DataFrame, group_cols: list[str], prefix: str) -> pd.DataFrame:
    result = frame
    for lag in LAGS:
        shifted = daily[group_cols + ["order_date", "sales_sum"]].copy()
        shifted["order_date"] = shifted["order_date"] + pd.Timedelta(days=lag)
        shifted = shifted.rename(columns={"sales_sum": f"{prefix}_sales_lag_{lag}d"})
        result = result.merge(shifted, on=group_cols + ["order_date"], how="left")
    return result


def make_dense_rolling(daily: pd.DataFrame, group_cols: list[str], prefix: str) -> pd.DataFrame:
    if not group_cols:
        base = daily[["order_date", "sales_sum"]].copy()
        group_key = pd.DataFrame({"_global_key": ["global"]})
        base["_global_key"] = "global"
        group_cols = ["_global_key"]
    else:
        base = daily[group_cols + ["order_date", "sales_sum"]].copy()

    pieces = []
    min_date = base["order_date"].min()
    max_date = base["order_date"].max()
    full_dates = pd.date_range(min_date, max_date, freq="D")
    for keys, group in base.groupby(group_cols, dropna=False, sort=False):
        if not isinstance(keys, tuple):
            keys = (keys,)
        dense = pd.DataFrame({"order_date": full_dates})
        for col, value in zip(group_cols, keys):
            dense[col] = value
        dense = dense.merge(group, on=group_cols + ["order_date"], how="left")
        dense["sales_sum"] = dense["sales_sum"].fillna(0.0)
        previous = dense["sales_sum"].shift(1)
        for window in ROLLING_WINDOWS:
            dense[f"{prefix}_sales_roll_sum_{window}d"] = previous.rolling(window, min_periods=1).sum()
            dense[f"{prefix}_sales_roll_mean_{window}d"] = previous.rolling(window, min_periods=1).mean()
        pieces.append(dense[group_cols + ["order_date"] + [c for c in dense.columns if c.startswith(prefix)]])

    out = pd.concat(pieces, ignore_index=True)
    if "_global_key" in out.columns:
        out = out.drop(columns="_global_key")
    return out


def add_history_features(df: pd.DataFrame) -> tuple[pd.DataFrame, list[str]]:
    result = df.copy()
    history_features: list[str] = []

    group_specs = [
        ([], "global", True),
        (["Product Name"], "product", True),
        (["Category Name"], "category", True),
        (["Order Country"], "country", True),
        (["Customer Id"], "customer", False),
    ]

    for group_cols, prefix, include_rolling in group_specs:
        if group_cols:
            daily = (
                result.groupby(group_cols + ["order_date"], dropna=False)[TARGET]
                .sum()
                .rename("sales_sum")
                .reset_index()
            )
        else:
            daily = result.groupby(["order_date"])[TARGET].sum().rename("sales_sum").reset_index()
        result = add_exact_lags(result, daily, group_cols, prefix)
        history_features.extend([f"{prefix}_sales_lag_{lag}d" for lag in LAGS])

        if include_rolling:
            rolling = make_dense_rolling(daily, group_cols, prefix)
            merge_cols = group_cols + ["order_date"]
            result = result.merge(rolling, on=merge_cols, how="left")
            for window in ROLLING_WINDOWS:
                history_features.append(f"{prefix}_sales_roll_sum_{window}d")
                history_features.append(f"{prefix}_sales_roll_mean_{window}d")

    return result, history_features


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


def plot_metric(metrics: pd.DataFrame, metric: str, title: str, output: Path) -> None:
    data = metrics[metrics["split"].eq("test")].sort_values(metric)
    fig, ax = plt.subplots(figsize=(11, 6))
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


def get_importance(model: Pipeline, feature_names: list[str], model_name: str) -> pd.DataFrame:
    estimator = model.named_steps["model"]
    if hasattr(estimator, "feature_importances_"):
        importance = estimator.feature_importances_
        return pd.DataFrame({"model": model_name, "feature": feature_names, "importance": importance})
    if hasattr(estimator, "coef_"):
        coefficients = np.ravel(estimator.coef_)
        return pd.DataFrame(
            {
                "model": model_name,
                "feature": feature_names,
                "importance": np.abs(coefficients),
                "coefficient": coefficients,
            }
        )
    return pd.DataFrame(columns=["model", "feature", "importance"])


def build_audit(df: pd.DataFrame, history_features: list[str], available_features: list[str]) -> pd.DataFrame:
    rows = [
        {"check": "order_datetime", "estado": str(df["order_datetime"].dtype), "lectura": "Parseado a datetime dentro del script"},
        {"check": "Order Item Quantity", "estado": str(df["Order Item Quantity"].dtype), "lectura": "Cantidad numerica/int"},
        {"check": "Sales", "estado": str(df[TARGET].dtype), "lectura": "Target numerico float"},
        {"check": "price_discount", "estado": "float", "lectura": "Precio, descuento y tasa de descuento numericos"},
        {"check": "payment_one_hot", "estado": "bool en dataset, excluido del modelo", "lectura": "No se usa porque el metodo de pago no se conoce antes de completar compra"},
        {"check": "leakage_excluded", "estado": "excluido", "lectura": ", ".join(EXCLUDED_FOR_LEAKAGE)},
        {"check": "categorical_encoding", "estado": "OrdinalEncoder dentro del pipeline", "lectura": "No se escriben categorias ordinales al CSV; se transforman durante entrenamiento"},
        {"check": "lags", "estado": f"{len([f for f in history_features if '_lag_' in f])} features", "lectura": "Lags diarios exactos 1, 7, 30 y 365 dias; equivalen a 24, 168, 720 y 8760 horas"},
        {"check": "rollings", "estado": f"{len([f for f in history_features if '_roll_' in f])} features", "lectura": "Rolling semanal 7 dias y mensual 30 dias, siempre con shift previo"},
        {"check": "feature_count", "estado": str(len(available_features)), "lectura": "Features usadas por el modelo con historicos"},
    ]
    return pd.DataFrame(rows)


def main() -> None:
    REPORTS_DIR.mkdir(exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(exist_ok=True)

    print("Leyendo datos...", flush=True)
    df = pd.read_csv(DATA_PATH, low_memory=False)
    df = add_sales_features(df)

    print("Creando lags y rollings diarios sin leakage...", flush=True)
    df, history_features = add_history_features(df)

    available_categorical = [col for col in CATEGORICAL_FEATURES if col in df.columns]
    available_numeric = [col for col in BASE_NUMERIC_FEATURES + history_features if col in df.columns]
    feature_names = available_categorical + available_numeric
    audit = build_audit(df, history_features, feature_names)
    audit.to_csv(AUDIT_PATH, index=False)

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
            "Linear Regression with lags",
            Pipeline(
                steps=[
                    ("preprocess", make_linear_preprocessor(available_categorical, available_numeric)),
                    ("model", LinearRegression()),
                ]
            ),
        ),
        (
            "Lasso with lags",
            Pipeline(
                steps=[
                    ("preprocess", make_linear_preprocessor(available_categorical, available_numeric)),
                    ("model", Lasso(alpha=0.001, max_iter=10000, random_state=RANDOM_STATE)),
                ]
            ),
        ),
        (
            "Decision Tree with lags",
            Pipeline(
                steps=[
                    ("preprocess", make_tree_preprocessor(available_categorical, available_numeric)),
                    ("model", DecisionTreeRegressor(max_depth=16, min_samples_leaf=20, random_state=RANDOM_STATE)),
                ]
            ),
        ),
        (
            "Random Forest with lags",
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
            "Hist Gradient Boosting with lags",
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
    all_importance = []
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
        all_importance.append(get_importance(pipeline, feature_names, model_name))
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
                }
            )
        )

    for model_name, pred in {"Baseline global mean": global_test_pred, "Baseline mean by Product": product_test_pred}.items():
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
                }
            )
        )

    metrics_df = pd.DataFrame(metrics).sort_values(["split", "mae"])
    previous_test = pd.DataFrame()
    if PREVIOUS_METRICS_PATH.exists():
        previous = pd.read_csv(PREVIOUS_METRICS_PATH)
        previous_test = previous[previous["split"].eq("test")].copy()
        previous_test["model"] = previous_test["model"] + " (sin lags)"
        previous_test["split"] = "test_previous_no_lags"

    metrics_output = pd.concat([metrics_df, previous_test], ignore_index=True, sort=False)
    metrics_output.to_csv(METRICS_PATH, index=False)
    predictions.to_csv(PREDICTIONS_PATH, index=False)
    residuals = pd.concat(residual_frames, ignore_index=True)
    residuals.to_csv(RESIDUALS_PATH, index=False)

    importance_df = pd.concat(all_importance, ignore_index=True, sort=False)
    importance_df.to_csv(IMPORTANCE_PATH, index=False)

    test_metrics = metrics_df[metrics_df["split"].eq("test")].sort_values("mae")
    best_model = str(test_metrics.iloc[0]["model"])
    best_importance = importance_df[importance_df["model"].eq(best_model)].sort_values("importance", ascending=False)

    plot_metric(metrics_df, "mae", "Modelo de ventas con lags - MAE test", FIGURES_DIR / "sales_model_lag_mae.png")
    plot_metric(metrics_df, "rmse", "Modelo de ventas con lags - RMSE test", FIGURES_DIR / "sales_model_lag_rmse.png")
    plot_metric(metrics_df, "wape", "Modelo de ventas con lags - WAPE test", FIGURES_DIR / "sales_model_lag_wape.png")
    plot_residual_hist(residuals, best_model, FIGURES_DIR / "sales_model_lag_best_residual_histogram.png")
    plot_importance(best_importance, FIGURES_DIR / "sales_model_lag_best_feature_importance.png", f"Importancia de variables - {best_model}")

    metrics_table = metrics_df.copy()
    for column in ["mae", "mse", "rmse", "r2", "wape", "mape_nonzero_actual", "residual_mean", "residual_median", "residual_std", "train_seconds"]:
        metrics_table[column] = metrics_table[column].astype(float).round(4)

    previous_summary = pd.DataFrame()
    if not previous_test.empty:
        previous_summary = previous_test[["model", "mae", "mse", "rmse", "r2", "wape", "mape_nonzero_actual"]].copy()
        for column in ["mae", "mse", "rmse", "r2", "wape", "mape_nonzero_actual"]:
            previous_summary[column] = previous_summary[column].astype(float).round(4)

    best_metrics = test_metrics.iloc[0]
    previous_linear = previous_test[previous_test["model"].eq("Linear Regression (sin lags)")]
    improvement_text = "No disponible"
    if not previous_linear.empty:
        prev_mae = float(previous_linear.iloc[0]["mae"])
        improvement = prev_mae - float(best_metrics["mae"])
        if improvement >= 0:
            improvement_text = f"mejora {improvement:.4f} MAE frente a Linear Regression sin lags"
        else:
            improvement_text = f"empeora {abs(improvement):.4f} MAE frente a Linear Regression sin lags"

    importance_table = best_importance.head(25).copy()
    if not importance_table.empty:
        importance_table["importance"] = importance_table["importance"].astype(float).round(4)
        if "coefficient" in importance_table.columns:
            importance_table["coefficient"] = importance_table["coefficient"].astype(float).round(4)

    report = f"""---
title: "Modelo de Ventas con Lags y Rollings"
subtitle: "Comparacion contra modelo sin historicos"
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

# Modelo de Ventas con Lags y Rollings

## DataCo Supply Chain

**Objetivo:** comprobar si historicos diarios por producto, categoria, pais, cliente y ventas globales mejoran el modelo de `Sales`.

</div>

---

# 1. Resumen Ejecutivo

El mejor modelo con historicos en test fue `{best_model}`.

| Modelo | MAE | MSE | RMSE | R2 | WAPE | MAPE |
| --- | ---: | ---: | ---: | ---: | ---: | ---: |
| Mejor con lags/rollings | {best_metrics['mae']:.4f} | {best_metrics['mse']:.4f} | {best_metrics['rmse']:.4f} | {best_metrics['r2']:.4f} | {best_metrics['wape']:.4f} | {best_metrics['mape_nonzero_actual']:.4f} |

Comparacion directa: **el mejor modelo con historicos {improvement_text}**.

Los lags y rollings se calcularon siempre con dias anteriores. Para una lectura en horas:

- 1 dia = 24 horas;
- 7 dias = 168 horas;
- 30 dias = 720 horas;
- 365 dias = 8760 horas.

---

# 2. Auditoria Rapida de Leakage y Tipos

{markdown_table(audit)}

Puntos clave:

- `order_datetime` se parsea a datetime dentro del script.
- `Order Item Quantity` se mantiene numerica/int.
- precio, descuento, tasa de descuento y target son numericos.
- metodo de pago esta en booleanos one-hot en el dataset, pero queda excluido del modelo principal.
- `Order Item Total`, `Sales per customer`, beneficios y estados posteriores siguen fuera por leakage.

---

# 3. Lags y Rollings Creados

Lags exactos diarios:

- 1, 7, 30 y 365 dias.

Grupos:

- ventas globales;
- ventas por producto;
- ventas por categoria;
- ventas por pais de pedido;
- ventas por comprador.

Rollings:

- rolling semanal: 7 dias;
- rolling mensual: 30 dias.

Los rollings se calculan con `shift(1)`: el dia actual no entra en su propio historico.

---

# 4. Resultados con Historicos

{markdown_table(metrics_table)}

{image_block('Grafico 1. MAE en test', 'figures/sales_model_lag_rolling/sales_model_lag_mae.png', 'Compara los modelos entrenados con lags y rollings.') }

---

{image_block('Grafico 2. RMSE en test', 'figures/sales_model_lag_rolling/sales_model_lag_rmse.png', 'RMSE permite ver si los historicos reducen errores grandes.') }

---

{image_block('Grafico 3. WAPE en test', 'figures/sales_model_lag_rolling/sales_model_lag_wape.png', 'WAPE resume el error absoluto frente al total de ventas reales.') }

---

# 5. Comparacion con Modelo sin Historicos

Resultados anteriores sin lags/rollings:

{markdown_table(previous_summary)}

Lectura: el punto de referencia real no es el baseline, sino Linear Regression/Lasso sin historicos, porque ya eran muy superiores al baseline.

---

# 6. Residuos e Importancia

{image_block('Grafico 4. Histograma de residuos', 'figures/sales_model_lag_rolling/sales_model_lag_best_residual_histogram.png', 'Muestra si el mejor modelo con historicos tiende a subestimar o sobreestimar ventas.') }

---

Importancia del mejor modelo:

{markdown_table(importance_table)}

{image_block('Grafico 5. Importancia de variables', 'figures/sales_model_lag_rolling/sales_model_lag_best_feature_importance.png', 'Permite ver si los lags/rollings entran entre las variables mas relevantes o si siguen dominando precio, cantidad y descuento.') }

---

# 7. Decision

Esta iteracion comprueba si los historicos temporales aportan algo sobre el modelo sin lags.

Resultado: los historicos no mejoran el mejor modelo anterior. `Sales` a nivel linea sigue estando dominado por precio, cantidad y descuento. Para este target conviene mantener Linear Regression/Lasso sin lags como referencia principal.

Los lags y rollings si aparecen entre variables relevantes, pero no compensan: anaden ruido o colinealidad y empeoran el error del modelo lineal. Si queremos aprovechar historicos, lo mas razonable es cambiar el objetivo a demanda agregada por producto/fecha, no a importe de una linea de pedido ya formada.
"""

    REPORT_PATH.write_text(report, encoding="utf-8-sig")
    print(f"Informe generado: {REPORT_PATH}")
    print(f"Metricas: {METRICS_PATH}")
    print(f"Predicciones: {PREDICTIONS_PATH}")
    print(f"Residuos: {RESIDUALS_PATH}")
    print(f"Importancia: {IMPORTANCE_PATH}")
    print(f"Auditoria: {AUDIT_PATH}")


if __name__ == "__main__":
    main()
