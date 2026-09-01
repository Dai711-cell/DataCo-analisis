from __future__ import annotations

import warnings
from io import StringIO
from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


PROJECT_DIR = Path(__file__).resolve().parent
REPORTS_DIR = PROJECT_DIR / "reports"
OUTPUT_REPORT = REPORTS_DIR / "data_overview_report.md"
DATE_FORMAT = "%m/%d/%Y %H:%M"

DATASETS = {
    "DataCoSupplyChainDataset": PROJECT_DIR / "DataCoSupplyChainDataset.csv",
    "tokenized_access_logs": PROJECT_DIR / "tokenized_access_logs.csv",
}

DATASET_CONTEXT = {
    "DataCoSupplyChainDataset": {
        "row_meaning": "Cada fila parece representar una linea de pedido: un producto vendido a un cliente, con datos de envio, venta, beneficio, geografia, producto y estado del pedido.",
        "compact_columns": [
            "Order Id",
            "order date (DateOrders)",
            "Order Status",
            "Delivery Status",
            "Late_delivery_risk",
            "Shipping Mode",
            "Product Name",
            "Order Item Quantity",
            "Sales",
            "Order Item Total",
            "Order Profit Per Order",
            "Customer Segment",
            "Order Country",
            "Market",
        ],
    },
    "tokenized_access_logs": {
        "row_meaning": "Cada fila parece representar un evento de acceso web tokenizado: una visita o peticion registrada en logs, con campos tecnicos y de navegacion.",
        "compact_columns": [],
    },
}

COLUMN_HINTS = {
    "Type": "Tipo de pago o transaccion del pedido, por ejemplo DEBIT, TRANSFER, CASH.",
    "Days for shipping (real)": "Dias reales que tardo el envio.",
    "Days for shipment (scheduled)": "Dias previstos o prometidos para el envio.",
    "Benefit per order": "Beneficio estimado del pedido o linea de pedido.",
    "Sales per customer": "Ventas asociadas al cliente en esa fila.",
    "Delivery Status": "Estado logistico de la entrega, por ejemplo tarde, a tiempo o adelantada.",
    "Late_delivery_risk": "Indicador binario: 1 suele significar riesgo/entrega tardia; 0 sin riesgo/tardia segun el dataset.",
    "Category Id": "Identificador numerico de categoria de producto.",
    "Category Name": "Nombre de la categoria de producto.",
    "Customer Id": "Identificador del cliente.",
    "Customer Segment": "Segmento comercial del cliente.",
    "Department Id": "Identificador del departamento de producto.",
    "Department Name": "Nombre del departamento de producto.",
    "Latitude": "Latitud asociada al cliente o localizacion registrada.",
    "Longitude": "Longitud asociada al cliente o localizacion registrada.",
    "Market": "Mercado o macro-region comercial.",
    "Order City": "Ciudad destino o asociada al pedido.",
    "Order Country": "Pais destino o asociado al pedido.",
    "Order Id": "Identificador del pedido.",
    "order date (DateOrders)": "Fecha y hora en que se realizo el pedido.",
    "Order Item Cardprod Id": "Identificador tecnico del producto en la linea de pedido.",
    "Order Item Discount": "Importe de descuento aplicado a la linea.",
    "Order Item Discount Rate": "Porcentaje o tasa de descuento aplicada.",
    "Order Item Id": "Identificador unico de la linea de pedido.",
    "Order Item Product Price": "Precio unitario del producto en la linea.",
    "Order Item Profit Ratio": "Ratio de beneficio de la linea.",
    "Order Item Quantity": "Cantidad de unidades compradas en la linea.",
    "Sales": "Venta bruta o importe de venta antes de algunos ajustes/descuentos, segun el dataset.",
    "Order Item Total": "Total de la linea despues de descuento u otros ajustes.",
    "Order Profit Per Order": "Beneficio asociado al pedido o linea.",
    "Order Region": "Region del pedido.",
    "Order State": "Estado/provincia del pedido.",
    "Order Status": "Estado administrativo del pedido, por ejemplo COMPLETE, PENDING, CLOSED.",
    "Order Zipcode": "Codigo postal del pedido, si existe.",
    "Product Card Id": "Identificador tecnico del producto.",
    "Product Category Id": "Identificador de la categoria del producto.",
    "Product Description": "Descripcion del producto, si existe.",
    "Product Image": "URL o referencia de imagen del producto.",
    "Product Name": "Nombre del producto.",
    "Product Price": "Precio del producto.",
    "Product Status": "Estado del producto dentro del catalogo.",
    "shipping date (DateOrders)": "Fecha y hora de envio.",
    "Shipping Mode": "Modo de envio, por ejemplo Standard Class o Second Class.",
}

GROUP_RULES = [
    ("Pedido y pago", ["Order Id", "Order Status", "Type", "order date", "Order Customer Id"]),
    ("Envio y entrega", ["shipping date", "Shipping Mode", "Delivery Status", "Late_delivery_risk", "Days for shipping", "Days for shipment"]),
    ("Ventas, descuento y margen", ["Sales", "Benefit", "Profit", "Discount", "Price", "Quantity", "Order Item Total"]),
    ("Cliente", ["Customer"]),
    ("Producto", ["Product", "Category", "Department"]),
    ("Geografia", ["City", "Country", "State", "Region", "Market", "Latitude", "Longitude", "Zipcode", "Street"]),
    ("Logs y navegacion", ["ip", "url", "token", "log", "access", "time", "date", "method", "status", "request", "user", "session", "product"]),
]

pd.set_option("display.max_columns", 120)
pd.set_option("display.width", 220)
pd.set_option("display.max_colwidth", 80)


def read_csv_flexible(path: Path) -> pd.DataFrame:
    """Read a CSV trying common encodings without changing the original file."""
    encodings = ["utf-8", "utf-8-sig", "latin1"]
    last_error: Exception | None = None

    for encoding in encodings:
        try:
            return pd.read_csv(path, encoding=encoding, low_memory=False)
        except UnicodeDecodeError as error:
            last_error = error

    raise RuntimeError(f"Could not read {path.name} with common encodings") from last_error


def code_block(text: str) -> str:
    return f"```text\n{text}\n```"


def clean_text(value: object, max_length: int = 90) -> str:
    if pd.isna(value):
        return "NA"
    text = str(value).replace("\n", " ").replace("\r", " ").strip()
    if len(text) > max_length:
        return text[: max_length - 3] + "..."
    return text


def markdown_table(headers: list[str], rows: list[list[object]]) -> str:
    def escape(value: object) -> str:
        return clean_text(value).replace("|", "\\|")

    lines = ["| " + " | ".join(headers) + " |"]
    lines.append("| " + " | ".join(["---"] * len(headers)) + " |")
    for row in rows:
        lines.append("| " + " | ".join(escape(value) for value in row) + " |")
    return "\n".join(lines)


def dataframe_info(df: pd.DataFrame) -> str:
    buffer = StringIO()
    df.info(buf=buffer, show_counts=True)
    return buffer.getvalue().rstrip()


def dataframe_preview(df: pd.DataFrame, max_rows: int = 30) -> str:
    if df.empty:
        return "Sin datos."
    return code_block(df.head(max_rows).to_string(index=True))


def group_columns(columns: list[str]) -> dict[str, list[str]]:
    groups: dict[str, list[str]] = {name: [] for name, _ in GROUP_RULES}
    groups["Otras columnas"] = []

    for column in columns:
        column_lower = column.lower()
        assigned = False
        for group_name, keywords in GROUP_RULES:
            if any(keyword.lower() in column_lower for keyword in keywords):
                groups[group_name].append(column)
                assigned = True
                break
        if not assigned:
            groups["Otras columnas"].append(column)

    return {group: values for group, values in groups.items() if values}


def detect_date_like_columns(df: pd.DataFrame, sample_size: int = 5000) -> pd.DataFrame:
    results = []
    sample = df.head(sample_size)

    for column in sample.columns:
        series = sample[column].dropna()
        if series.empty:
            continue

        with warnings.catch_warnings():
            warnings.simplefilter("ignore")
            parsed = pd.to_datetime(series, errors="coerce")

        success_rate = parsed.notna().mean()
        if success_rate >= 0.80:
            results.append(
                {
                    "column": column,
                    "sample_parse_success_rate": round(success_rate, 3),
                    "min_sample_date": parsed.min(),
                    "max_sample_date": parsed.max(),
                }
            )

    return pd.DataFrame(results)


def categorical_columns(df: pd.DataFrame) -> list[str]:
    dtype_names = df.dtypes.astype(str)
    return [
        column
        for column, dtype_name in dtype_names.items()
        if dtype_name in {"object", "category", "bool", "string", "str"}
    ]


def compact_head(df: pd.DataFrame, dataset_name: str, rows: int = 8) -> str:
    configured = DATASET_CONTEXT.get(dataset_name, {}).get("compact_columns", [])
    selected_columns = [column for column in configured if column in df.columns]
    if not selected_columns:
        selected_columns = list(df.columns[: min(10, len(df.columns))])
    return code_block(df[selected_columns].head(rows).to_string(index=False))


def vertical_head(df: pd.DataFrame, rows: int = 3) -> str:
    grouped_columns = group_columns(list(df.columns))
    sections: list[str] = []

    for row_number, (_, row) in enumerate(df.head(rows).iterrows(), start=1):
        sections.append(f"### Fila {row_number}")
        sections.append("Lectura vertical: cada linea es una columna del CSV y su valor en esa fila.")
        for group_name, columns in grouped_columns.items():
            table_rows = []
            for column in columns:
                value = row[column]
                meaning = COLUMN_HINTS.get(column, "Pendiente de interpretar; revisar con el diccionario o con analisis posterior.")
                table_rows.append([column, value, meaning])
            sections.append(f"#### {group_name}")
            sections.append(markdown_table(["Campo", "Valor", "Como leerlo"], table_rows))

    return "\n\n".join(sections)


def column_groups_section(df: pd.DataFrame) -> str:
    groups = group_columns(list(df.columns))
    sections = []
    for group_name, columns in groups.items():
        sections.append(f"### {group_name}")
        sections.append("\n".join(f"- `{column}`" for column in columns))
    return "\n\n".join(sections)


def summarize_dataset(name: str, path: Path) -> str:
    df = read_csv_flexible(path)
    context = DATASET_CONTEXT.get(name, {})

    sections: list[str] = []
    sections.append(f"# {name}\n")
    sections.append(f"Archivo: `{path.name}`")
    sections.append(f"Filas: `{df.shape[0]:,}`")
    sections.append(f"Columnas: `{df.shape[1]:,}`")
    sections.append(f"Memoria aproximada en pandas: `{df.memory_usage(deep=True).sum() / 1024**2:,.2f} MB`\n")

    sections.append("## Como leer este CSV")
    sections.append(context.get("row_meaning", "Cada fila representa una observacion del dataset. La unidad exacta debe confirmarse con el analisis."))

    sections.append("## Grupos de columnas")
    sections.append(column_groups_section(df))

    sections.append("## Head compacto con columnas clave")
    sections.append("Esta es una version reducida del `.head()` para orientarse sin ver todas las columnas a la vez.")
    sections.append(compact_head(df, name))

    sections.append("## Head humano en formato ficha")
    sections.append(vertical_head(df, rows=3))

    sections.append("## Info")
    sections.append(code_block(dataframe_info(df)))

    sections.append("## Describe numerico")
    numeric_describe = df.describe(include="number").transpose()
    sections.append(dataframe_preview(numeric_describe, max_rows=80))

    sections.append("## Describe categorico y general")
    general_describe = df.describe(include="all").transpose()
    sections.append(dataframe_preview(general_describe, max_rows=80))

    sections.append("## Tipos de datos")
    dtype_summary = (
        df.dtypes.astype(str)
        .value_counts()
        .rename_axis("dtype")
        .reset_index(name="column_count")
    )
    sections.append(code_block(dtype_summary.to_string(index=False)))

    sections.append("## Nulos por columna")
    missing = pd.DataFrame(
        {
            "missing_count": df.isna().sum(),
            "missing_pct": (df.isna().mean() * 100).round(2),
        }
    ).sort_values(["missing_pct", "missing_count"], ascending=False)
    sections.append(dataframe_preview(missing, max_rows=80))

    sections.append("## Cardinalidad")
    cardinality = pd.DataFrame(
        {
            "unique_values": df.nunique(dropna=True),
            "unique_pct": (df.nunique(dropna=True) / len(df) * 100).round(2),
            "dtype": df.dtypes.astype(str),
        }
    ).sort_values("unique_values", ascending=False)
    sections.append(dataframe_preview(cardinality, max_rows=80))

    sections.append("## Duplicados")
    duplicate_count = int(df.duplicated().sum())
    duplicate_pct = duplicate_count / len(df) * 100 if len(df) else 0
    sections.append(f"Filas duplicadas exactas: `{duplicate_count:,}` ({duplicate_pct:.2f}%).")

    sections.append("## Columnas posiblemente de fecha")
    date_like = detect_date_like_columns(df)
    sections.append(dataframe_preview(date_like, max_rows=40))

    sections.append("## Valores frecuentes en columnas categoricas")
    cat_columns = categorical_columns(df)
    if not cat_columns:
        sections.append("No se detectaron columnas categoricas.")
    else:
        for column in cat_columns[:25]:
            top_values = df[column].value_counts(dropna=False).head(10).reset_index()
            top_values.columns = [column, "count"]
            top_values["pct"] = (top_values["count"] / len(df) * 100).round(2)
            sections.append(f"### {column}")
            sections.append(code_block(top_values.to_string(index=False)))

    sections.append("## Primeras observaciones automaticas")
    sections.append("- Revisar columnas con muchos nulos antes de usarlas en analisis o modelos.")
    sections.append("- Revisar columnas con cardinalidad muy alta: pueden ser IDs, texto libre o claves tecnicas.")
    sections.append("- Revisar columnas de fecha detectadas automaticamente antes de hacer splits temporales.")
    sections.append("- Si se modela una variable de entrega, retraso, fraude, venta o conversion, comprobar leakage antes del baseline.")

    return "\n\n".join(sections)


def normalize_column_name(column: str) -> str:
    cleaned = column.strip().lower()
    replacements = {
        " ": "_",
        "(": "",
        ")": "",
        "/": "_",
        "-": "_",
    }
    for old, new in replacements.items():
        cleaned = cleaned.replace(old, new)
    while "__" in cleaned:
        cleaned = cleaned.replace("__", "_")
    return cleaned.strip("_")


def inspect_outcome_signals(df: pd.DataFrame, logs_df: pd.DataFrame) -> str:
    keyword_list = ["return", "refund", "complaint", "claim", "devol", "queja"]
    status_keywords = ["cancel", "fraud", "hold", "pending", "late"]

    matching_columns = [
        column
        for column in list(df.columns) + list(logs_df.columns)
        if any(keyword in column.lower() for keyword in keyword_list)
    ]

    sections: list[str] = []
    sections.append("# Variables de devoluciones, quejas y objetivos posibles\n")

    if matching_columns:
        sections.append("## Variables explicitas encontradas")
        sections.append("\n".join(f"- `{column}`" for column in matching_columns))
    else:
        sections.append("## Variables explicitas encontradas")
        sections.append("No se encontraron columnas explicitas de devoluciones, quejas, reclamaciones o refunds en los dos CSV analizados.")

    sections.append("## Senales utiles que si existen")
    if "Order Status" in df.columns:
        order_status = df["Order Status"].value_counts(dropna=False).reset_index()
        order_status.columns = ["order_status", "count"]
        order_status["pct"] = (order_status["count"] / len(df) * 100).round(2)
        sections.append("### Order Status")
        sections.append(code_block(order_status.to_string(index=False)))

    if "Delivery Status" in df.columns:
        delivery_status = df["Delivery Status"].value_counts(dropna=False).reset_index()
        delivery_status.columns = ["delivery_status", "count"]
        delivery_status["pct"] = (delivery_status["count"] / len(df) * 100).round(2)
        sections.append("### Delivery Status")
        sections.append(code_block(delivery_status.to_string(index=False)))

    if "Late_delivery_risk" in df.columns:
        late_counts = df["Late_delivery_risk"].value_counts(dropna=False).reset_index()
        late_counts.columns = ["late_delivery_risk", "count"]
        late_counts["pct"] = (late_counts["count"] / len(df) * 100).round(2)
        sections.append("### Late_delivery_risk")
        sections.append(code_block(late_counts.to_string(index=False)))

    logs_url_matches = {}
    if "url" in logs_df.columns:
        lower_url = logs_df["url"].astype(str).str.lower()
        logs_url_matches = {keyword: int(lower_url.str.contains(keyword, regex=False).sum()) for keyword in keyword_list + status_keywords}
        sections.append("### Busqueda de palabras en URLs de logs")
        sections.append(code_block(pd.Series(logs_url_matches, name="count").to_string()))

    sections.append("## Lectura practica")
    sections.append("- Para devoluciones o quejas: no hay una variable directa en estos CSV.")
    sections.append("- Para mejorar prediccion de pedidos problematicos: `Late_delivery_risk` es el objetivo mas claro.")
    sections.append("- Tambien se pueden plantear objetivos separados como `is_order_canceled`, `is_suspected_fraud`, `is_payment_problem` o `is_shipping_canceled`.")
    sections.append("- Cuidado: si se predice retraso antes de enviar, `Delivery Status`, `shipping date (DateOrders)` y `Days for shipping (real)` son leakage y no deberian usarse como features.")

    return "\n\n".join(sections)


def process_supply_chain_dataset(df: pd.DataFrame) -> tuple[pd.DataFrame, str]:
    processed = df.copy()

    type_dummies = pd.get_dummies(processed["Type"], prefix="payment_type", dtype=bool)
    type_dummies.columns = [normalize_column_name(column) for column in type_dummies.columns]
    processed = pd.concat([processed, type_dummies], axis=1)

    processed["order_datetime"] = pd.to_datetime(processed["order date (DateOrders)"], format=DATE_FORMAT, errors="coerce")
    processed["shipping_datetime"] = pd.to_datetime(processed["shipping date (DateOrders)"], format=DATE_FORMAT, errors="coerce")
    shipping_delta = processed["shipping_datetime"] - processed["order_datetime"]
    processed["shipping_hours_from_dates"] = (shipping_delta.dt.total_seconds() / 3600).round().astype("Int64")
    processed["shipping_days_from_dates_exact"] = (processed["shipping_hours_from_dates"] / 24).round(3)
    processed["shipping_days_from_dates_floor"] = (processed["shipping_hours_from_dates"] // 24).astype("Int64")
    processed["shipping_days_floor_matches_original"] = processed["shipping_days_from_dates_floor"].eq(processed["Days for shipping (real)"])

    processed["order_year"] = processed["order_datetime"].dt.year.astype("Int64")
    processed["order_month"] = processed["order_datetime"].dt.month.astype("Int64")
    processed["order_dayofweek"] = processed["order_datetime"].dt.dayofweek.astype("Int64")
    processed["order_hour"] = processed["order_datetime"].dt.hour.astype("Int64")
    processed["shipping_year"] = processed["shipping_datetime"].dt.year.astype("Int64")
    processed["shipping_month"] = processed["shipping_datetime"].dt.month.astype("Int64")
    processed["shipping_dayofweek"] = processed["shipping_datetime"].dt.dayofweek.astype("Int64")
    processed["shipping_hour"] = processed["shipping_datetime"].dt.hour.astype("Int64")

    processed["is_late_delivery"] = processed["Late_delivery_risk"].eq(1)
    processed["is_shipping_canceled"] = processed["Delivery Status"].eq("Shipping canceled")
    processed["is_order_canceled"] = processed["Order Status"].eq("CANCELED")
    processed["is_suspected_fraud"] = processed["Order Status"].eq("SUSPECTED_FRAUD")
    processed["is_payment_problem"] = processed["Order Status"].isin(["PENDING_PAYMENT", "PAYMENT_REVIEW"])
    processed["is_order_problem"] = processed[["is_late_delivery", "is_shipping_canceled", "is_order_canceled", "is_suspected_fraud", "is_payment_problem"]].any(axis=1)

    date_report_rows = []
    for column in ["Days for shipping (real)", "Days for shipment (scheduled)"]:
        date_report_rows.append(
            {
                "field": column,
                "dtype_before": str(df[column].dtype),
                "interpretation": "Ya viene como numero entero de dias.",
            }
        )
    for column in ["order date (DateOrders)", "shipping date (DateOrders)"]:
        parsed = pd.to_datetime(df[column], format=DATE_FORMAT, errors="coerce")
        date_report_rows.append(
            {
                "field": column,
                "dtype_before": str(df[column].dtype),
                "interpretation": f"Viene como texto/fecha. Parseado a datetime con {parsed.isna().sum():,} valores no parseados.",
            }
        )

    mismatches = int((~processed["shipping_days_floor_matches_original"]).sum())
    missing_delta = int(processed["shipping_hours_from_dates"].isna().sum())
    half_day_distribution = (
        processed.loc[processed["shipping_days_from_dates_exact"].eq(0.5), "Days for shipping (real)"]
        .value_counts()
        .sort_index()
        .rename_axis("original_days_for_12_hours")
        .reset_index(name="count")
    )

    report_sections = ["# Limpieza inicial DataCo Supply Chain\n"]
    report_sections.append("## Type a booleanos")
    report_sections.append("Se convirtio `Type` a columnas booleanas one-hot para evitar codificacion ordinal artificial como 1, 2, 3 o 4.")
    report_sections.append("Columnas creadas:")
    report_sections.append("\n".join(f"- `{column}`" for column in type_dummies.columns))

    report_sections.append("## Fechas y dias de entrega")
    report_sections.append(code_block(pd.DataFrame(date_report_rows).to_string(index=False)))
    report_sections.append("Columnas creadas desde las fechas: `order_datetime`, `shipping_datetime`, `shipping_hours_from_dates`, `shipping_days_from_dates_exact` y `shipping_days_from_dates_floor`.")
    report_sections.append(f"Diferencias entre `shipping_days_from_dates_floor` y `Days for shipping (real)`: `{mismatches:,}` filas.")
    report_sections.append(f"Filas sin diferencia calculable por fechas no parseadas: `{missing_delta:,}`.")
    report_sections.append("Distribucion especial cuando la diferencia real entre fechas es de 12 horas (`0.5` dias):")
    report_sections.append(code_block(half_day_distribution.to_string(index=False)))

    report_sections.append("## Targets derivados para pedidos problematicos")
    targets = ["is_late_delivery", "is_shipping_canceled", "is_order_canceled", "is_suspected_fraud", "is_payment_problem", "is_order_problem"]
    target_summary = pd.DataFrame(
        {
            "positive_count": processed[targets].sum(),
            "positive_pct": (processed[targets].mean() * 100).round(2),
        }
    )
    report_sections.append(code_block(target_summary.to_string()))

    report_sections.append("## Nota de leakage")
    report_sections.append("Para predecir retraso antes del envio, no usar como features `Delivery Status`, `shipping_datetime`, `shipping date (DateOrders)`, `Days for shipping (real)`, `shipping_hours_from_dates`, `shipping_days_from_dates_exact`, `shipping_days_from_dates_floor` ni `is_late_delivery`, porque contienen informacion posterior o directamente el target.")

    return processed, "\n\n".join(report_sections)


def process_access_logs(logs_df: pd.DataFrame) -> pd.DataFrame:
    processed = logs_df.copy()
    processed["access_datetime"] = pd.to_datetime(processed["Date"], errors="coerce")
    processed["access_year"] = processed["access_datetime"].dt.year.astype("Int64")
    processed["access_month_number"] = processed["access_datetime"].dt.month.astype("Int64")
    processed["access_dayofweek"] = processed["access_datetime"].dt.dayofweek.astype("Int64")
    processed["access_hour_from_datetime"] = processed["access_datetime"].dt.hour.astype("Int64")
    processed["hour_matches_datetime"] = processed["access_hour_from_datetime"].eq(processed["Hour"])
    return processed


def create_processed_datasets() -> str:
    processed_dir = PROJECT_DIR / "data" / "processed"
    processed_dir.mkdir(parents=True, exist_ok=True)

    supply_df = read_csv_flexible(DATASETS["DataCoSupplyChainDataset"])
    logs_df = read_csv_flexible(DATASETS["tokenized_access_logs"])

    processed_supply, cleaning_report = process_supply_chain_dataset(supply_df)
    processed_logs = process_access_logs(logs_df)

    supply_output = processed_dir / "dataco_supply_chain_processed.csv"
    logs_output = processed_dir / "tokenized_access_logs_processed.csv"
    cleaning_report_output = REPORTS_DIR / "cleaning_and_targets_report.md"

    processed_supply.to_csv(supply_output, index=False)
    processed_logs.to_csv(logs_output, index=False)

    outcome_report = inspect_outcome_signals(supply_df, logs_df)
    full_report = cleaning_report + "\n\n---\n\n" + outcome_report
    cleaning_report_output.write_text(full_report, encoding="utf-8")

    return "\n".join(
        [
            "Datasets procesados generados:",
            f"- {supply_output}",
            f"- {logs_output}",
            f"Reporte de limpieza y targets: {cleaning_report_output}",
        ]
    )


def plot_horizontal_bar(series: pd.Series, title: str, xlabel: str, output_path: Path, color: str = "#4C78A8") -> None:
    data = series.dropna()
    if data.empty:
        return
    data = data.sort_values(ascending=True)
    fig_height = max(4, min(10, 0.35 * len(data) + 1.5))
    fig, ax = plt.subplots(figsize=(10, fig_height))
    ax.barh(data.index.astype(str), data.values, color=color)
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.grid(axis="x", alpha=0.25)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    fig.savefig(output_path, dpi=140)
    plt.close(fig)


def plot_vertical_bar(series: pd.Series, title: str, ylabel: str, output_path: Path, color: str = "#59A14F") -> None:
    data = series.dropna()
    if data.empty:
        return
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.bar(data.index.astype(str), data.values, color=color)
    ax.set_title(title)
    ax.set_ylabel(ylabel)
    ax.grid(axis="y", alpha=0.25)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    ax.tick_params(axis="x", rotation=35)
    fig.tight_layout()
    fig.savefig(output_path, dpi=140)
    plt.close(fig)


def plot_histogram(series: pd.Series, title: str, xlabel: str, output_path: Path, bins: int = 40) -> None:
    values = pd.to_numeric(series, errors="coerce").dropna()
    if values.empty:
        return
    upper = values.quantile(0.99)
    values = values[values <= upper]
    fig, ax = plt.subplots(figsize=(10, 5))
    ax.hist(values, bins=bins, color="#F28E2B", edgecolor="white")
    ax.set_title(title)
    ax.set_xlabel(xlabel)
    ax.set_ylabel("Frecuencia")
    ax.grid(axis="y", alpha=0.25)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    fig.savefig(output_path, dpi=140)
    plt.close(fig)


def plot_scatter_sample(df: pd.DataFrame, x: str, y: str, title: str, output_path: Path, sample_size: int = 12000) -> None:
    plot_df = df[[x, y]].dropna()
    if plot_df.empty:
        return
    if len(plot_df) > sample_size:
        plot_df = plot_df.sample(sample_size, random_state=42)
    fig, ax = plt.subplots(figsize=(8, 5))
    ax.scatter(plot_df[x], plot_df[y], s=8, alpha=0.25, color="#E15759")
    ax.set_title(title)
    ax.set_xlabel(x)
    ax.set_ylabel(y)
    ax.grid(alpha=0.2)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    fig.savefig(output_path, dpi=140)
    plt.close(fig)


def plot_grouped_bars(df: pd.DataFrame, title: str, output_path: Path) -> None:
    if df.empty:
        return
    fig, ax = plt.subplots(figsize=(11, 6))
    x = range(len(df))
    ax.bar([i - 0.2 for i in x], df["sales_share"], width=0.4, label="Share ventas", color="#4C78A8")
    ax.bar([i + 0.2 for i in x], df["views_share"], width=0.4, label="Share visitas", color="#F28E2B")
    ax.set_xticks(list(x))
    ax.set_xticklabels(df["product"], rotation=45, ha="right")
    ax.set_title(title)
    ax.set_ylabel("Proporcion")
    ax.legend()
    ax.grid(axis="y", alpha=0.25)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    fig.savefig(output_path, dpi=140)
    plt.close(fig)


def basic_eda_charts() -> str:
    processed_dir = PROJECT_DIR / "data" / "processed"
    figures_dir = REPORTS_DIR / "figures" / "basic_eda"
    figures_dir.mkdir(parents=True, exist_ok=True)

    supply_path = processed_dir / "dataco_supply_chain_processed.csv"
    logs_path = processed_dir / "tokenized_access_logs_processed.csv"
    if not supply_path.exists() or not logs_path.exists():
        create_processed_datasets()

    supply = pd.read_csv(supply_path, low_memory=False)
    logs = pd.read_csv(logs_path, low_memory=False)

    created: list[tuple[str, str, str]] = []

    def add_chart(filename: str, title: str, note: str) -> Path:
        created.append((filename, title, note))
        return figures_dir / filename

    plot_horizontal_bar(
        supply.groupby("Order Country")["Sales"].sum().sort_values(ascending=False).head(15),
        "Ventas totales por pais de pedido - top 15",
        "Ventas totales",
        add_chart("sales_by_order_country_top15.png", "Ventas por pais", "Muestra si el pais tiene senal fuerte para ventas y demanda."),
    )
    plot_horizontal_bar(
        supply.groupby("Product Name")["Sales"].sum().sort_values(ascending=False).head(15),
        "Ventas totales por producto - top 15",
        "Ventas totales",
        add_chart("sales_by_product_top15.png", "Ventas por producto", "Ayuda a ver productos dominantes y posible concentracion de demanda."),
    )
    plot_horizontal_bar(
        supply.groupby("Category Name")["Sales"].sum().sort_values(ascending=False).head(15),
        "Ventas totales por categoria - top 15",
        "Ventas totales",
        add_chart("sales_by_category_top15.png", "Ventas por categoria", "Las categorias suelen ser buenas features por capturar familias de producto."),
    )
    plot_horizontal_bar(
        supply.groupby("Customer Segment")["Sales"].sum().sort_values(ascending=False),
        "Ventas totales por segmento de cliente",
        "Ventas totales",
        add_chart("sales_by_customer_segment.png", "Ventas por segmento", "Permite ver si Consumer, Corporate o Home Office tienen comportamientos diferentes."),
    )
    plot_horizontal_bar(
        supply.groupby("Market")["Sales"].sum().sort_values(ascending=False),
        "Ventas totales por mercado",
        "Ventas totales",
        add_chart("sales_by_market.png", "Ventas por mercado", "Resume diferencias regionales de demanda."),
    )
    plot_horizontal_bar(
        supply.groupby("Type")["Sales"].sum().sort_values(ascending=False),
        "Ventas totales por metodo de pago",
        "Ventas totales",
        add_chart("sales_by_payment_type.png", "Ventas por metodo de pago", "Sirve para ver si el metodo de pago acompana patrones de compra sin codificarlo ordinalmente."),
    )
    plot_horizontal_bar(
        supply.groupby("Shipping Mode")["Sales"].sum().sort_values(ascending=False),
        "Ventas totales por modo de envio",
        "Ventas totales",
        add_chart("sales_by_shipping_mode.png", "Ventas por modo de envio", "Puede aportar senal en demanda y en riesgo logistico."),
    )
    plot_horizontal_bar(
        (supply.groupby("Shipping Mode")["is_late_delivery"].mean() * 100).sort_values(ascending=False),
        "Tasa de retraso por modo de envio",
        "% pedidos con retraso",
        add_chart("late_rate_by_shipping_mode.png", "Retraso por modo de envio", "Muy relevante para un modelo de retraso, siempre cuidando no usar variables posteriores al evento."),
        color="#E15759",
    )
    high_volume_countries = supply["Order Country"].value_counts().head(15).index
    plot_horizontal_bar(
        (supply[supply["Order Country"].isin(high_volume_countries)].groupby("Order Country")["is_late_delivery"].mean() * 100).sort_values(ascending=False),
        "Tasa de retraso por pais - top 15 por volumen",
        "% pedidos con retraso",
        add_chart("late_rate_by_order_country_top15_volume.png", "Retraso por pais", "Ayuda a detectar geografia con riesgo logistico alto."),
        color="#E15759",
    )
    plot_horizontal_bar(
        supply.groupby("Category Name")["Order Profit Per Order"].sum().sort_values(ascending=False).head(15),
        "Beneficio total por categoria - top 15",
        "Beneficio total",
        add_chart("profit_by_category_top15.png", "Beneficio por categoria", "No todo lo que vende mucho es lo que mas aporta margen; este grafico separa volumen de valor."),
        color="#59A14F",
    )
    monthly_sales = supply.groupby("order_month")["Sales"].sum().sort_index()
    plot_vertical_bar(
        monthly_sales,
        "Ventas totales por mes de pedido",
        "Ventas totales",
        add_chart("sales_by_order_month.png", "Ventas por mes", "Da una primera pista de estacionalidad."),
    )
    plot_histogram(
        supply["Sales"],
        "Distribucion de Sales - recortada al percentil 99",
        "Sales",
        add_chart("sales_distribution_p99.png", "Distribucion de Sales", "Permite ver escala, concentracion y posibles outliers para el modelo."),
    )
    plot_scatter_sample(
        supply,
        "Order Item Discount Rate",
        "Sales",
        "Relacion entre descuento y ventas - muestra aleatoria",
        add_chart("discount_rate_vs_sales_sample.png", "Descuento vs ventas", "Busca si el descuento parece relacionarse con ventas; no implica causalidad."),
    )

    numeric_columns = [
        "Days for shipment (scheduled)",
        "Order Item Discount Rate",
        "Order Item Product Price",
        "Order Item Quantity",
        "Product Price",
        "order_month",
        "order_dayofweek",
        "order_hour",
        "payment_type_cash",
        "payment_type_debit",
        "payment_type_payment",
        "payment_type_transfer",
    ]
    available_numeric = [column for column in numeric_columns if column in supply.columns]
    corr_sales = supply[available_numeric + ["Sales"]].corr(numeric_only=True)["Sales"].drop("Sales").sort_values(key=lambda s: s.abs(), ascending=False).head(15)
    plot_horizontal_bar(
        corr_sales,
        "Correlacion simple con Sales",
        "Correlacion Pearson",
        add_chart("corr_with_sales_top15.png", "Correlacion con Sales", "Ranking rapido de variables numericas potencialmente utiles para ventas; no reemplaza validacion."),
        color="#B07AA1",
    )
    corr_late = supply[available_numeric + ["is_late_delivery"]].corr(numeric_only=True)["is_late_delivery"].drop("is_late_delivery").sort_values(key=lambda s: s.abs(), ascending=False).head(15)
    plot_horizontal_bar(
        corr_late,
        "Correlacion simple con is_late_delivery",
        "Correlacion Pearson",
        add_chart("corr_with_late_delivery_top15.png", "Correlacion con retraso", "Ranking rapido para el target logistico, cuidando leakage."),
        color="#B07AA1",
    )

    plot_horizontal_bar(
        logs.groupby("Department").size().sort_values(ascending=False),
        "Visitas web por departamento",
        "Numero de visitas",
        add_chart("web_visits_by_department.png", "Visitas por departamento", "Los logs pueden aportar senal de interes/demanda por departamento."),
        color="#76B7B2",
    )
    plot_horizontal_bar(
        logs.groupby("Category").size().sort_values(ascending=False).head(15),
        "Visitas web por categoria - top 15",
        "Numero de visitas",
        add_chart("web_visits_by_category_top15.png", "Visitas por categoria", "Compara interes web con categorias de venta."),
        color="#76B7B2",
    )
    plot_vertical_bar(
        logs.groupby("Hour").size().sort_index(),
        "Visitas web por hora",
        "Numero de visitas",
        add_chart("web_visits_by_hour.png", "Visitas por hora", "Puede aportar patrones temporales de demanda o actividad."),
        color="#76B7B2",
    )

    sales_by_product = supply.groupby("Product Name")["Sales"].sum().rename("sales")
    views_by_product = logs.groupby("Product").size().rename("views")
    product_signal = pd.concat([sales_by_product, views_by_product], axis=1).fillna(0)
    product_signal = product_signal[(product_signal["sales"] > 0) | (product_signal["views"] > 0)].copy()
    if not product_signal.empty:
        product_signal["sales_share"] = product_signal["sales"] / product_signal["sales"].sum()
        product_signal["views_share"] = product_signal["views"] / product_signal["views"].sum()
        product_signal["share_gap_sales_minus_views"] = product_signal["sales_share"] - product_signal["views_share"]
        product_signal.sort_values("sales", ascending=False).to_csv(processed_dir / "product_sales_vs_web_views.csv")
        top_products = product_signal.sort_values("sales", ascending=False).head(12).reset_index().rename(columns={"index": "product", "Product Name": "product"})
        if "product" not in top_products.columns:
            top_products = top_products.rename(columns={top_products.columns[0]: "product"})
        plot_grouped_bars(
            top_products[["product", "sales_share", "views_share"]],
            "Share de ventas vs share de visitas web - top productos por ventas",
            add_chart("sales_vs_web_views_top_products.png", "Ventas vs visitas web", "Compara demanda comprada frente a interes web; util para features de demanda si se alinea temporalmente."),
        )

    report_lines = ["# Graficos basicos para elegir variables\n"]
    report_lines.append("Estos graficos se generan desde `proyecto.py` usando los datos procesados. Son exploratorios: ayudan a elegir variables candidatas, no prueban causalidad.")
    report_lines.append("## Reglas para leerlos")
    report_lines.append("- Para modelo de ventas: mirar pais, producto, categoria, segmento, mercado, mes, metodo de pago y senales web.")
    report_lines.append("- Para modelo de retraso/pedido problematico: mirar modo de envio, pais, mercado, fecha/hora y variables disponibles antes del envio.")
    report_lines.append("- Evitar leakage: no usar variables que ocurren despues del resultado que se quiere predecir.")

    report_lines.append("## Graficos")
    for filename, title, note in created:
        report_lines.append(f"### {title}")
        report_lines.append(note)
        report_lines.append(f"![{title}](figures/basic_eda/{filename})")

    report_path = REPORTS_DIR / "basic_eda_charts.md"
    report_path.write_text("\n\n".join(report_lines), encoding="utf-8")
    return f"Graficos EDA generados en: {figures_dir}\nInforme: {report_path}"

def main() -> None:
    REPORTS_DIR.mkdir(parents=True, exist_ok=True)

    report_sections = ["# Resumen inicial de datasets\n"]
    report_sections.append(
        "Este reporte se genera desde `proyecto.py`. Lee los CSV originales en modo solo lectura "
        "y no modifica los datasets. Se excluye `DescriptionDataCoSupplyChain.csv` como dataset resumido; "
        "las explicaciones de campos son una guia inicial basada en nombres de columnas y valores visibles."
    )

    for name, path in DATASETS.items():
        if not path.exists():
            report_sections.append(f"# {name}\n\nNo se encontro el archivo `{path}`.")
            continue
        print(f"Generando resumen de {path.name}...")
        report_sections.append(summarize_dataset(name, path))

    final_report = "\n\n---\n\n".join(report_sections)
    OUTPUT_REPORT.write_text(final_report, encoding="utf-8")

    print("\nResumen generado correctamente.")
    print(f"Reporte guardado en: {OUTPUT_REPORT}")
    print("\nVista previa:")
    print(final_report[:5000])

    print("\nPreparando datasets procesados...")
    print(create_processed_datasets())

    print("\nGenerando graficos EDA basicos...")
    print(basic_eda_charts())


if __name__ == "__main__":
    main()