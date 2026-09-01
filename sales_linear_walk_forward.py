from __future__ import annotations

from pathlib import Path
from time import perf_counter

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from sklearn.compose import ColumnTransformer
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LinearRegression
from sklearn.metrics import mean_absolute_error, mean_squared_error, r2_score
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import OneHotEncoder, StandardScaler


PROJECT_DIR = Path(__file__).resolve().parent
DATA_PATH = PROJECT_DIR / "data" / "processed" / "dataco_supply_chain_processed.csv"
PREVIOUS_METRICS_PATH = PROJECT_DIR / "data" / "processed" / "sales_model_comparison_metrics.csv"
REPORTS_DIR = PROJECT_DIR / "reports"
FIGURES_DIR = REPORTS_DIR / "figures" / "sales_linear_walk_forward"
PROCESSED_DIR = PROJECT_DIR / "data" / "processed"
REPORT_PATH = REPORTS_DIR / "sales_linear_walk_forward_report.Rmd"
METRICS_PATH = PROCESSED_DIR / "sales_linear_walk_forward_metrics.csv"
SUMMARY_PATH = PROCESSED_DIR / "sales_linear_walk_forward_summary.csv"
PREDICTIONS_PATH = PROCESSED_DIR / "sales_linear_walk_forward_predictions.csv"
RESIDUALS_PATH = PROCESSED_DIR / "sales_linear_walk_forward_residuals.csv"
FEATURE_AUDIT_PATH = PROCESSED_DIR / "sales_linear_walk_forward_audit.csv"
COEFFICIENTS_PATH = PROCESSED_DIR / "sales_linear_walk_forward_coefficients.csv"

TARGET = "Sales"
INITIAL_TRAIN_MONTHS = 12
TEST_WINDOW_MONTHS = 1
MIN_CATEGORY_FREQUENCY = 20

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
    result["order_month_period"] = result["order_datetime"].dt.to_period("M").astype(str)
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


def make_preprocessor() -> ColumnTransformer:
    categorical_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="most_frequent")),
            (
                "onehot",
                OneHotEncoder(
                    handle_unknown="infrequent_if_exist",
                    min_frequency=MIN_CATEGORY_FREQUENCY,
                    sparse_output=True,
                ),
            ),
        ]
    )
    numeric_pipeline = Pipeline(
        steps=[
            ("imputer", SimpleImputer(strategy="median")),
            ("scaler", StandardScaler()),
        ]
    )
    return ColumnTransformer(
        transformers=[
            ("categorical", categorical_pipeline, CATEGORICAL_FEATURES),
            ("numeric", numeric_pipeline, NUMERIC_FEATURES),
        ],
        sparse_threshold=0.3,
    )


def make_model() -> Pipeline:
    return Pipeline(
        steps=[
            ("preprocess", make_preprocessor()),
            ("model", LinearRegression()),
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


def evaluate_fold(
    fold: int,
    train_month_start: str,
    train_month_end: str,
    test_month_start: str,
    test_month_end: str,
    y_true: pd.Series,
    y_pred: np.ndarray,
    train_rows: int,
    test_rows: int,
    train_seconds: float,
) -> dict[str, float | int | str]:
    clipped_pred = np.clip(y_pred, 0, None)
    mse = mean_squared_error(y_true, clipped_pred)
    residuals = y_true.to_numpy(dtype=float) - clipped_pred
    return {
        "fold": fold,
        "model": "Linear Regression walk-forward",
        "train_month_start": train_month_start,
        "train_month_end": train_month_end,
        "test_month_start": test_month_start,
        "test_month_end": test_month_end,
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
        "train_seconds": train_seconds,
    }


def plot_fold_metric(metrics: pd.DataFrame, metric: str, title: str, output: Path) -> None:
    fig, ax = plt.subplots(figsize=(12, 5.8))
    ax.plot(metrics["test_month_start"], metrics[metric], marker="o", linewidth=2, color="#4C78A8")
    ax.set_title(title, fontsize=15, pad=12)
    ax.set_xlabel("Mes probado")
    ax.set_ylabel(metric.upper())
    ax.grid(axis="y", alpha=0.25)
    ax.tick_params(axis="x", rotation=60)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    fig.savefig(output, dpi=150)
    plt.close(fig)


def plot_train_test_size(metrics: pd.DataFrame, output: Path) -> None:
    fig, ax = plt.subplots(figsize=(12, 5.8))
    ax.plot(metrics["test_month_start"], metrics["train_rows"], marker="o", label="train rows", color="#4C78A8")
    ax.bar(metrics["test_month_start"], metrics["test_rows"], label="test rows", color="#F58518", alpha=0.75)
    ax.set_title("Walk-forward: entrenamiento acumulado y test mensual", fontsize=15, pad=12)
    ax.set_xlabel("Mes probado")
    ax.set_ylabel("Filas")
    ax.grid(axis="y", alpha=0.25)
    ax.tick_params(axis="x", rotation=60)
    ax.legend()
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    fig.savefig(output, dpi=150)
    plt.close(fig)


def plot_actual_vs_pred(monthly: pd.DataFrame, output: Path) -> None:
    fig, ax = plt.subplots(figsize=(12, 5.8))
    ax.plot(monthly["test_month"], monthly["actual_sales"], marker="o", linewidth=2, label="Sales real", color="#4C78A8")
    ax.plot(
        monthly["test_month"],
        monthly["predicted_sales"],
        marker="o",
        linewidth=2,
        label="Sales predicho",
        color="#54A24B",
    )
    ax.set_title("Ventas reales vs predichas por mes de test", fontsize=15, pad=12)
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
    ax.hist(residuals["residual"], bins=60, color="#F58518", edgecolor="white")
    ax.axvline(0, color="black", linestyle="--", linewidth=1)
    ax.set_title("Distribucion de residuos walk-forward", fontsize=15, pad=12)
    ax.set_xlabel("Residuo = real - predicho")
    ax.set_ylabel("Frecuencia")
    ax.grid(axis="y", alpha=0.25)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    fig.savefig(output, dpi=150)
    plt.close(fig)


def get_coefficients(model: Pipeline) -> pd.DataFrame:
    preprocessor = model.named_steps["preprocess"]
    regressor = model.named_steps["model"]
    try:
        feature_names = preprocessor.get_feature_names_out()
    except Exception:
        feature_names = np.array([f"feature_{idx}" for idx in range(len(regressor.coef_))])
    coefs = pd.DataFrame(
        {
            "feature": feature_names,
            "coefficient": regressor.coef_,
        }
    )
    coefs["abs_coefficient"] = coefs["coefficient"].abs()
    return coefs.sort_values("abs_coefficient", ascending=False)


def write_report(
    summary: pd.DataFrame,
    metrics: pd.DataFrame,
    previous_linear: pd.DataFrame,
    audit: pd.DataFrame,
    coefficients: pd.DataFrame,
) -> None:
    best_month = metrics.sort_values("mae").iloc[0]
    worst_month = metrics.sort_values("mae", ascending=False).iloc[0]
    summary_row = summary.iloc[0]

    previous_text = "_No se encontro la metrica anterior._"
    if not previous_linear.empty:
        previous_text = markdown_table(previous_linear.round(4))

    report = f"""---
title: "Walk-Forward Validation - Modelo de Ventas"
subtitle: "Linear Regression con validacion temporal mensual"
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

# Walk-Forward Validation

## Modelo de ventas `Sales`

Esta validacion simula un uso real del modelo al pasar los meses:

1. Se entrena con los primeros {INITIAL_TRAIN_MONTHS} meses.
2. Se predice el mes siguiente, que el modelo no ha visto.
3. Ese mes se incorpora al entrenamiento.
4. Se repite el proceso hasta el ultimo mes disponible.

El modelo probado es `Linear Regression`, usando las mismas familias de variables del modelo de ventas sin lags: geografia, comprador, producto, precio/cantidad, descuentos/ofertas y calendario. En esta validacion las variables categoricas se codifican con `OneHotEncoder` dentro del pipeline para evitar imponer un orden artificial a paises, productos o compradores.

---

# 1. Resultado General

| metrica | valor |
| --- | ---: |
| folds mensuales | {int(summary_row["folds"])} |
| filas evaluadas fuera de muestra | {int(summary_row["test_rows"])} |
| MAE ponderado por filas | {summary_row["weighted_mae"]:.4f} |
| MSE ponderado por filas | {summary_row["weighted_mse"]:.4f} |
| RMSE global | {summary_row["global_rmse"]:.4f} |
| R2 global | {summary_row["global_r2"]:.4f} |
| WAPE global | {summary_row["global_wape"]:.4f} |
| MAPE global | {summary_row["global_mape"]:.4f} |

Mejor mes por MAE: `{best_month["test_month_start"]}`, con MAE {best_month["mae"]:.4f}.

Peor mes por MAE: `{worst_month["test_month_start"]}`, con MAE {worst_month["mae"]:.4f}.

---

# 2. Auditoria de Variables y Leakage

{markdown_table(audit)}

Lectura: el modelo no usa estados posteriores, beneficios, totales derivados directos ni metodo de pago. `Sales` es el target y queda fuera de las variables. `Order Item Product Price`, `Order Item Quantity` y descuentos se mantienen porque este modelo predice el importe de una linea de pedido ya formada; si el objetivo fuese forecast de demanda antes de la compra, esas variables no estarian disponibles y habria que redefinir el problema.

---

# 3. Metricas por Mes

{markdown_table(metrics[["fold", "train_month_start", "train_month_end", "test_month_start", "test_rows", "mae", "rmse", "r2", "wape", "mape_nonzero_actual"]].round(4))}

{image_block(
    "MAE por mes probado",
    "figures/sales_linear_walk_forward/sales_walk_forward_mae.png",
    "Muestra si el error se mantiene estable cuando el modelo avanza mes a mes con entrenamiento acumulado."
)}

{image_block(
    "WAPE por mes probado",
    "figures/sales_linear_walk_forward/sales_walk_forward_wape.png",
    "Permite comparar el error relativo sobre el volumen real de ventas de cada mes."
)}

{image_block(
    "Tamano de entrenamiento y test",
    "figures/sales_linear_walk_forward/sales_walk_forward_train_test_size.png",
    "El entrenamiento crece de forma acumulada y cada prueba corresponde al siguiente mes no visto."
)}

{image_block(
    "Ventas reales vs predichas por mes",
    "figures/sales_linear_walk_forward/sales_walk_forward_actual_vs_predicted.png",
    "Comprueba si el modelo sigue el nivel mensual total de ventas, no solo el error por linea."
)}

{image_block(
    "Distribucion de residuos",
    "figures/sales_linear_walk_forward/sales_walk_forward_residuals.png",
    "Los residuos se concentran cerca de cero, pero hay cola positiva/negativa en lineas donde la combinacion precio-cantidad-descuento se comporta peor."
)}

---

# 4. Comparacion con el Split Anterior

Resultado anterior de `Linear Regression` con split temporal fijo:

{previous_text}

Esta comparacion sirve como referencia, pero no debe leerse como un cambio de una sola variable: el primer modelo usaba el pipeline original y esta validacion usa `OneHotEncoder`, que es mas adecuado para variables categoricas en una regresion lineal. La conclusion principal aqui es temporal: el modelo lineal mantiene buen rendimiento cuando se entrena solo con meses pasados y se prueba sobre meses futuros no vistos.

---

# 5. Coeficientes Principales

{markdown_table(coefficients.head(25).round(4))}

Lectura: en un modelo lineal de `Sales` por linea, las variables de precio, cantidad y descuento deben dominar. Si las categorias aparecen con coeficientes altos, hay que interpretarlas como ajustes de contexto, no como causalidad directa.

---

# 6. Conclusion

La validacion walk-forward confirma si el modelo lineal aguanta el paso del tiempo con datos no vistos mes a mes. Este enfoque es mas cercano a produccion que un unico split, porque cada prediccion se hace solo con informacion historica disponible hasta ese momento.

Para `Sales` por linea, el modelo sigue siendo principalmente una lectura de precio, cantidad y descuento. Es util para estimar el importe de pedidos ya configurados. Para planificacion comercial o inventario, el siguiente problema deberia formularse como demanda agregada por producto/fecha, donde si tendrian mas valor los historicos, calendario y patrones temporales.
"""
    REPORT_PATH.write_text(report, encoding="utf-8")


def main() -> None:
    start = perf_counter()
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(parents=True, exist_ok=True)

    raw = pd.read_csv(DATA_PATH, low_memory=False)
    data = add_sales_features(raw)
    feature_columns = CATEGORICAL_FEATURES + NUMERIC_FEATURES
    missing = [column for column in feature_columns + [TARGET] if column not in data.columns]
    if missing:
        raise ValueError(f"Missing required columns: {missing}")

    data = data.sort_values("order_datetime").reset_index(drop=True)
    months = sorted(data["order_month_period"].dropna().unique())
    if len(months) <= INITIAL_TRAIN_MONTHS:
        raise ValueError("Not enough monthly periods for walk-forward validation.")

    metrics_rows = []
    prediction_frames = []
    residual_frames = []
    last_model: Pipeline | None = None

    for fold, test_start_index in enumerate(range(INITIAL_TRAIN_MONTHS, len(months), TEST_WINDOW_MONTHS), start=1):
        train_months = months[:test_start_index]
        test_months = months[test_start_index : test_start_index + TEST_WINDOW_MONTHS]
        if not test_months:
            continue

        train_df = data[data["order_month_period"].isin(train_months)].copy()
        test_df = data[data["order_month_period"].isin(test_months)].copy()
        if train_df.empty or test_df.empty:
            continue

        model = make_model()
        X_train = train_df[feature_columns]
        y_train = train_df[TARGET]
        X_test = test_df[feature_columns]
        y_test = test_df[TARGET]

        fit_start = perf_counter()
        model.fit(X_train, y_train)
        train_seconds = perf_counter() - fit_start
        y_pred = np.clip(model.predict(X_test), 0, None)
        last_model = model

        metrics_rows.append(
            evaluate_fold(
                fold=fold,
                train_month_start=train_months[0],
                train_month_end=train_months[-1],
                test_month_start=test_months[0],
                test_month_end=test_months[-1],
                y_true=y_test,
                y_pred=y_pred,
                train_rows=len(train_df),
                test_rows=len(test_df),
                train_seconds=train_seconds,
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
        predictions["fold"] = fold
        predictions["prediction"] = y_pred
        predictions["residual"] = predictions[TARGET] - predictions["prediction"]
        prediction_frames.append(predictions)
        residual_frames.append(
            predictions[["fold", "order_datetime", "order_month_period", TARGET, "prediction", "residual"]].copy()
        )

    metrics = pd.DataFrame(metrics_rows)
    predictions_all = pd.concat(prediction_frames, ignore_index=True)
    residuals_all = pd.concat(residual_frames, ignore_index=True)

    global_mse = mean_squared_error(predictions_all[TARGET], predictions_all["prediction"])
    summary = pd.DataFrame(
        [
            {
                "model": "Linear Regression walk-forward",
                "initial_train_months": INITIAL_TRAIN_MONTHS,
                "test_window_months": TEST_WINDOW_MONTHS,
                "folds": len(metrics),
                "test_rows": len(predictions_all),
                "first_train_month": months[0],
                "first_test_month": metrics["test_month_start"].min(),
                "last_test_month": metrics["test_month_end"].max(),
                "weighted_mae": mean_absolute_error(predictions_all[TARGET], predictions_all["prediction"]),
                "weighted_mse": global_mse,
                "global_rmse": float(np.sqrt(global_mse)),
                "global_r2": r2_score(predictions_all[TARGET], predictions_all["prediction"]),
                "global_wape": wape(predictions_all[TARGET], predictions_all["prediction"]),
                "global_mape": mape_nonzero(predictions_all[TARGET], predictions_all["prediction"]),
                "mean_fold_mae": metrics["mae"].mean(),
                "median_fold_mae": metrics["mae"].median(),
                "mean_fold_wape": metrics["wape"].mean(),
                "total_runtime_seconds": perf_counter() - start,
            }
        ]
    )

    monthly = (
        predictions_all.groupby("order_month_period", as_index=False)
        .agg(actual_sales=(TARGET, "sum"), predicted_sales=("prediction", "sum"), rows=(TARGET, "size"))
        .rename(columns={"order_month_period": "test_month"})
    )

    audit = pd.DataFrame(
        [
            {"check": "order_datetime", "estado": str(data["order_datetime"].dtype), "lectura": "Parseado a datetime dentro del script"},
            {"check": "Sales", "estado": str(data[TARGET].dtype), "lectura": "Target numerico float"},
            {
                "check": "Order Item Quantity",
                "estado": str(data["Order Item Quantity"].dtype),
                "lectura": "Cantidad numerica usada como feature",
            },
            {
                "check": "categorical_encoding",
                "estado": "OneHotEncoder dentro del pipeline",
                "lectura": f"handle_unknown=infrequent_if_exist, min_frequency={MIN_CATEGORY_FREQUENCY}",
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
            {
                "check": "walk_forward",
                "estado": f"{INITIAL_TRAIN_MONTHS} meses iniciales + {TEST_WINDOW_MONTHS} mes de test",
                "lectura": "Ventana expansiva: cada mes probado se suma al entrenamiento posterior",
            },
            {
                "check": "feature_count_before_encoding",
                "estado": len(feature_columns),
                "lectura": f"{len(CATEGORICAL_FEATURES)} categoricas y {len(NUMERIC_FEATURES)} numericas",
            },
        ]
    )

    if last_model is None:
        raise RuntimeError("No walk-forward folds were trained.")
    coefficients = get_coefficients(last_model)

    previous_linear = pd.DataFrame()
    if PREVIOUS_METRICS_PATH.exists():
        previous = pd.read_csv(PREVIOUS_METRICS_PATH)
        previous_linear = previous[
            previous["model"].eq("Linear Regression") & previous["split"].eq("test")
        ][["model", "split", "mae", "mse", "rmse", "r2", "wape", "mape_nonzero_actual"]]

    plot_fold_metric(metrics, "mae", "Linear Regression walk-forward - MAE por mes", FIGURES_DIR / "sales_walk_forward_mae.png")
    plot_fold_metric(metrics, "wape", "Linear Regression walk-forward - WAPE por mes", FIGURES_DIR / "sales_walk_forward_wape.png")
    plot_train_test_size(metrics, FIGURES_DIR / "sales_walk_forward_train_test_size.png")
    plot_actual_vs_pred(monthly, FIGURES_DIR / "sales_walk_forward_actual_vs_predicted.png")
    plot_residuals(residuals_all, FIGURES_DIR / "sales_walk_forward_residuals.png")

    metrics.round(6).to_csv(METRICS_PATH, index=False)
    summary.round(6).to_csv(SUMMARY_PATH, index=False)
    predictions_all.round(6).to_csv(PREDICTIONS_PATH, index=False)
    residuals_all.round(6).to_csv(RESIDUALS_PATH, index=False)
    audit.to_csv(FEATURE_AUDIT_PATH, index=False)
    coefficients.round(6).to_csv(COEFFICIENTS_PATH, index=False)
    write_report(summary, metrics, previous_linear, audit, coefficients)

    print(f"Generated {REPORT_PATH}")
    print(f"Generated {METRICS_PATH}")
    print(summary.to_string(index=False))


if __name__ == "__main__":
    main()
