from __future__ import annotations

from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd


PROJECT_DIR = Path(__file__).resolve().parent
DATA_PATH = PROJECT_DIR / "data" / "processed" / "dataco_supply_chain_processed.csv"
WEB_PRODUCT_PATH = PROJECT_DIR / "data" / "processed" / "product_sales_vs_web_views.csv"
REPORTS_DIR = PROJECT_DIR / "reports"
FIGURES_DIR = REPORTS_DIR / "figures" / "sales_feature_eda"
PROCESSED_DIR = PROJECT_DIR / "data" / "processed"
REPORT_PATH = REPORTS_DIR / "sales_feature_eda_report.Rmd"
FEATURE_DATASET_PATH = PROCESSED_DIR / "sales_feature_eda_dataset.csv"
VARIABLE_AUDIT_PATH = PROCESSED_DIR / "sales_variable_availability_audit.csv"
AGGREGATES_PATH = PROCESSED_DIR / "sales_feature_eda_aggregates.csv"

TARGET = "Sales"


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


def safe_filename(name: str) -> str:
    allowed = []
    for char in name.lower():
        if char.isalnum():
            allowed.append(char)
        elif char in {" ", "_", "-", "/"}:
            allowed.append("_")
    return "".join(allowed).strip("_")


def format_label(value: object, max_len: int = 42) -> str:
    text = "Sin dato" if pd.isna(value) else str(value)
    return text if len(text) <= max_len else text[: max_len - 3] + "..."


def add_sales_features(df: pd.DataFrame) -> pd.DataFrame:
    result = df.copy()
    result["order_datetime"] = pd.to_datetime(result["order_datetime"], errors="coerce")
    result = result.dropna(subset=["order_datetime", TARGET]).copy()

    result["order_date"] = result["order_datetime"].dt.date
    result["order_year"] = result["order_datetime"].dt.year
    result["order_month"] = result["order_datetime"].dt.month
    result["order_month_name"] = result["order_datetime"].dt.month_name()
    result["order_year_month"] = result["order_datetime"].dt.to_period("M").astype(str)
    result["order_quarter"] = "Q" + result["order_datetime"].dt.quarter.astype(str)
    result["order_weekofyear"] = result["order_datetime"].dt.isocalendar().week.astype(int)
    result["order_dayofweek"] = result["order_datetime"].dt.dayofweek
    result["order_day_name"] = result["order_datetime"].dt.day_name()
    result["is_weekend"] = result["order_dayofweek"].isin([5, 6])

    month_day = result["order_datetime"].dt.strftime("%m-%d")
    result["is_generic_fixed_holiday"] = month_day.isin(["01-01", "05-01", "12-25"])
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
    result.loc[result["is_generic_fixed_holiday"], "calendar_period"] = "Generic fixed holiday"

    result["has_discount"] = result["Order Item Discount"].fillna(0).gt(0)
    result["discount_rate_bin"] = pd.cut(
        result["Order Item Discount Rate"].fillna(0),
        bins=[-0.001, 0.0, 0.05, 0.10, 0.15, 0.20, np.inf],
        labels=["0%", "0-5%", "5-10%", "10-15%", "15-20%", ">20%"],
    )
    result["discount_amount_bin"] = pd.cut(
        result["Order Item Discount"].fillna(0),
        bins=[-0.001, 0.0, 5, 10, 20, 50, np.inf],
        labels=["0", "0-5", "5-10", "10-20", "20-50", ">50"],
    )
    result["quantity_bin"] = result["Order Item Quantity"].astype("Int64").astype(str)
    result["product_price_bin"] = pd.qcut(
        result["Order Item Product Price"].rank(method="first"),
        q=5,
        labels=["Precio muy bajo", "Precio bajo", "Precio medio", "Precio alto", "Precio muy alto"],
    )
    result["profit_ratio_bin"] = pd.cut(
        result["Order Item Profit Ratio"].replace([np.inf, -np.inf], np.nan),
        bins=[-np.inf, -0.2, 0, 0.1, 0.2, np.inf],
        labels=["Perdida alta", "Perdida baja", "Margen bajo", "Margen medio", "Margen alto"],
    )

    payment_cols = [col for col in result.columns if col.startswith("payment_type_")]
    if payment_cols:
        result["payment_type"] = (
            result[payment_cols]
            .idxmax(axis=1)
            .str.replace("payment_type_", "", regex=False)
            .str.title()
        )
        empty_payment = result[payment_cols].sum(axis=1).eq(0)
        result.loc[empty_payment, "payment_type"] = "Unknown"

    customer_sales = result.groupby("Customer Id")[TARGET].sum().rename("customer_total_sales")
    result["customer_total_sales"] = result["Customer Id"].map(customer_sales)
    result["customer_value_band"] = pd.qcut(
        result["customer_total_sales"].rank(method="first"),
        q=5,
        labels=["Comprador muy bajo", "Comprador bajo", "Comprador medio", "Comprador alto", "Comprador muy alto"],
    )
    return result


def aggregate_sales(
    df: pd.DataFrame,
    column: str,
    top_n: int | None = None,
    order_values: list[str] | None = None,
) -> pd.DataFrame:
    grouped = (
        df.groupby(column, dropna=False)
        .agg(
            sales=(TARGET, "sum"),
            orders=("Order Id", "nunique"),
            rows=("Order Id", "size"),
            avg_sale=(TARGET, "mean"),
            avg_quantity=("Order Item Quantity", "mean"),
            avg_discount_rate=("Order Item Discount Rate", "mean"),
        )
        .reset_index()
    )
    if order_values is None:
        grouped = grouped.sort_values("sales", ascending=False)
    else:
        order_map = {value: index for index, value in enumerate(order_values)}
        grouped["_sort_order"] = grouped[column].astype(str).map(order_map).fillna(len(order_map))
        grouped = grouped.sort_values("_sort_order").drop(columns="_sort_order")
    total_sales = grouped["sales"].sum()
    grouped[column] = grouped[column].map(format_label)
    if top_n is not None and order_values is None:
        grouped = grouped.head(top_n)
    grouped["feature"] = column
    grouped["sales_share"] = grouped["sales"] / total_sales
    return grouped


def plot_sales_bar(
    grouped: pd.DataFrame,
    label_column: str,
    title: str,
    output: Path,
    horizontal: bool = True,
    color: str = "#4C78A8",
) -> None:
    data = grouped.copy()
    if horizontal:
        data = data.sort_values("sales", ascending=True)
        fig, ax = plt.subplots(figsize=(11, max(5.2, len(data) * 0.36)))
        bars = ax.barh(data[label_column], data["sales"], color=color)
        ax.bar_label(bars, labels=[f"{v/1_000_000:.2f}M" for v in data["sales"]], padding=4, fontsize=8)
        ax.set_xlabel("Ventas")
    else:
        fig, ax = plt.subplots(figsize=(11, 5.5))
        bars = ax.bar(data[label_column], data["sales"], color=color)
        ax.bar_label(bars, labels=[f"{v/1_000_000:.2f}M" for v in data["sales"]], padding=4, fontsize=8)
        ax.set_ylabel("Ventas")
        ax.tick_params(axis="x", rotation=35)
    ax.set_title(title, fontsize=15, pad=12)
    ax.grid(axis="x" if horizontal else "y", alpha=0.25)
    ax.spines["top"].set_visible(False)
    ax.spines["right"].set_visible(False)
    fig.tight_layout()
    fig.savefig(output, dpi=150)
    plt.close(fig)


def image_block(title: str, path: str, reading: str) -> str:
    return f"""
## {title}

<img src="{path}" alt="{title}" width="920">

**Lectura:** {reading}
"""


def build_variable_audit(df: pd.DataFrame) -> pd.DataFrame:
    requested = [
        ("ventas_por_comprador", ["Customer Id", "Order Customer Id", "Customer Segment"], "Disponible"),
        ("pais_ciudad_pedido", ["Order Country", "Order City", "Order Region", "Market"], "Disponible"),
        ("pais_ciudad_cliente", ["Customer Country", "Customer City"], "Disponible"),
        ("fecha_pedido", ["order_datetime", "order date (DateOrders)"], "Disponible"),
        ("dia_semana", ["order_datetime"], "Derivada"),
        ("festivos", ["order_datetime"], "Derivada aproximada"),
        ("ofertas_descuentos", ["Order Item Discount", "Order Item Discount Rate"], "Disponible"),
        ("campanas_marketing", [], "No disponible"),
        ("producto_categoria", ["Product Name", "Category Name", "Department Name"], "Disponible"),
        ("precio_cantidad", ["Order Item Product Price", "Order Item Quantity"], "Disponible"),
        ("metodo_pago", ["payment_type_cash", "payment_type_debit", "payment_type_payment", "payment_type_transfer"], "Disponible"),
        ("visitas_web_producto", ["product_sales_vs_web_views.csv"], "Disponible como tabla agregada"),
    ]
    rows = []
    columns = set(df.columns)
    for variable, required_cols, status_hint in requested:
        present = [col for col in required_cols if col in columns or col.endswith(".csv")]
        missing = [col for col in required_cols if col not in columns and not col.endswith(".csv")]
        if variable == "campanas_marketing":
            status = "No disponible en los datasets revisados"
        elif missing:
            status = f"Parcial: faltan {', '.join(missing)}"
        else:
            status = status_hint
        rows.append(
            {
                "variable_solicitada": variable,
                "estado": status,
                "columnas_usadas": ", ".join(present) if present else "-",
            }
        )
    return pd.DataFrame(rows)


def main() -> None:
    REPORTS_DIR.mkdir(exist_ok=True)
    FIGURES_DIR.mkdir(parents=True, exist_ok=True)
    PROCESSED_DIR.mkdir(exist_ok=True)

    df = pd.read_csv(DATA_PATH, low_memory=False)
    sales_df = add_sales_features(df)
    variable_audit = build_variable_audit(sales_df)

    selected_output_columns = [
        "Order Id",
        "Order Item Id",
        "Customer Id",
        "Order Customer Id",
        "Customer Segment",
        "Order Country",
        "Order City",
        "Order Region",
        "Order State",
        "Customer Country",
        "Customer City",
        "Market",
        "Product Name",
        "Category Name",
        "Department Name",
        "Sales",
        "Order Item Quantity",
        "Order Item Product Price",
        "Order Item Discount",
        "Order Item Discount Rate",
        "Order Item Profit Ratio",
        "payment_type",
        "Shipping Mode",
        "Order Status",
        "order_datetime",
        "order_year_month",
        "order_month_name",
        "order_day_name",
        "order_quarter",
        "is_weekend",
        "is_generic_fixed_holiday",
        "calendar_period",
        "has_discount",
        "discount_rate_bin",
        "discount_amount_bin",
        "quantity_bin",
        "product_price_bin",
        "profit_ratio_bin",
        "customer_total_sales",
        "customer_value_band",
    ]
    selected_output_columns = [col for col in selected_output_columns if col in sales_df.columns]
    sales_df[selected_output_columns].to_csv(FEATURE_DATASET_PATH, index=False)
    variable_audit.to_csv(VARIABLE_AUDIT_PATH, index=False)

    month_order = [
        "January",
        "February",
        "March",
        "April",
        "May",
        "June",
        "July",
        "August",
        "September",
        "October",
        "November",
        "December",
    ]
    weekday_order = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday", "Saturday", "Sunday"]
    year_month_order = sorted(sales_df["order_year_month"].dropna().unique().tolist())

    chart_specs = [
        ("Order Country", "Ventas por pais de pedido", 20, True, None, "Donde se concentra la facturacion por mercado geografico de destino."),
        ("Order City", "Ventas por ciudad de pedido", 20, True, None, "Ciudades con mayor peso comercial; candidatas para variables geograficas del modelo."),
        ("Order Region", "Ventas por region de pedido", 15, True, None, "Agrupa paises/ciudades en regiones con diferencias claras de volumen."),
        ("Market", "Ventas por mercado", None, False, None, "Mercado es una variable compacta y util para capturar diferencias regionales."),
        ("Customer Segment", "Ventas por segmento de comprador", None, False, None, "Permite ver si Consumer, Corporate o Home Office tienen patrones distintos de ventas."),
        ("Customer Country", "Ventas por pais del comprador", 15, True, None, "Pais del cliente puede aportar senal distinta al pais de entrega."),
        ("Customer City", "Ventas por ciudad del comprador", 15, True, None, "Ciudades de cliente con mas volumen de compra."),
        ("Customer Id", "Ventas por comprador", 20, True, None, "Compradores de mayor valor historico; util para variables agregadas por cliente."),
        ("customer_value_band", "Ventas por banda de valor del comprador", None, False, None, "Resume clientes segun su valor historico total sin usar miles de IDs directamente."),
        ("Department Name", "Ventas por departamento", None, False, None, "Departamento de producto como senal comercial de alto nivel."),
        ("Category Name", "Ventas por categoria", 20, True, None, "Categorias con mas peso en ventas."),
        ("Product Name", "Ventas por producto", 20, True, None, "Productos top; si hay pocos productos dominantes, el modelo debe capturarlo."),
        ("order_year_month", "Ventas por mes cronologico", None, False, year_month_order, "Evolucion mensual en orden temporal, util para tendencia y estacionalidad."),
        ("order_month_name", "Ventas por mes del anio", None, False, month_order, "Estacionalidad por mes sin depender del anio concreto."),
        ("order_day_name", "Ventas por dia de la semana", None, False, weekday_order, "Patron semanal de compra en orden natural de lunes a domingo."),
        ("is_weekend", "Ventas en fin de semana vs laborable", None, False, None, "Diferencia entre compras de fin de semana y dias laborables."),
        ("is_generic_fixed_holiday", "Ventas en festivos genericos", None, False, None, "Festivos derivados del calendario; no son una columna original del dataset."),
        ("calendar_period", "Ventas por periodo comercial de calendario", None, False, None, "Periodos derivados de fecha como Navidad o Black Friday; no equivalen a campanas reales."),
        ("has_discount", "Ventas con descuento vs sin descuento", None, False, None, "Evalua si las ofertas/descuentos concentran ventas."),
        ("discount_rate_bin", "Ventas por rango de descuento", None, False, None, "Rangos de descuento como proxy de ofertas."),
        ("discount_amount_bin", "Ventas por descuento absoluto", None, False, None, "Importe descontado por linea de pedido."),
        ("quantity_bin", "Ventas por cantidad de producto", None, False, None, "Cantidad comprada por linea, clave para ventas."),
        ("product_price_bin", "Ventas por banda de precio", None, False, None, "Banda de precio del producto."),
        ("profit_ratio_bin", "Ventas por banda de margen", None, False, None, "Relacion entre ventas y rentabilidad."),
        ("payment_type", "Ventas por metodo de pago", None, False, None, "Metodo de pago ya codificado sin sesgo ordinal."),
        ("Shipping Mode", "Ventas por tipo de envio", None, False, None, "El tipo de envio puede estar asociado al valor del pedido."),
        ("Order Status", "Ventas por estado del pedido", 12, True, None, "Estados de pedido y posibles cancelaciones/fraude pueden afectar ventas netas."),
    ]

    chart_rows = []
    aggregate_frames = []
    palette = ["#4C78A8", "#59A14F", "#F28E2B", "#B07AA1", "#E15759", "#76B7B2"]
    for index, (column, title, top_n, horizontal, order_values, reading) in enumerate(chart_specs, start=1):
        if column not in sales_df.columns:
            continue
        grouped = aggregate_sales(sales_df, column, top_n=top_n, order_values=order_values)
        aggregate_frames.append(grouped)
        filename = f"{index:02d}_{safe_filename(title)}.png"
        output = FIGURES_DIR / filename
        plot_sales_bar(grouped, column, title, output, horizontal=horizontal, color=palette[index % len(palette)])
        chart_rows.append(
            {
                "title": title,
                "relative_path": f"figures/sales_feature_eda/{filename}",
                "reading": reading,
            }
        )

    if WEB_PRODUCT_PATH.exists():
        web_df = pd.read_csv(WEB_PRODUCT_PATH)
        product_col = web_df.columns[0]
        web_df = web_df.rename(columns={product_col: "Product Name"})
        web_top = web_df.sort_values("sales", ascending=False).head(15).copy()
        web_top["Product Name"] = web_top["Product Name"].map(format_label)
        fig, ax = plt.subplots(figsize=(11, 6.5))
        y = np.arange(len(web_top))
        ax.barh(y + 0.18, web_top["sales_share"] * 100, 0.36, label="Share ventas", color="#4C78A8")
        ax.barh(y - 0.18, web_top["views_share"] * 100, 0.36, label="Share visitas web", color="#F28E2B")
        ax.set_yticks(y)
        ax.set_yticklabels(web_top["Product Name"])
        ax.invert_yaxis()
        ax.set_xlabel("% del total")
        ax.set_title("Ventas vs visitas web por producto", fontsize=15, pad=12)
        ax.legend(frameon=False)
        ax.grid(axis="x", alpha=0.25)
        ax.spines["top"].set_visible(False)
        ax.spines["right"].set_visible(False)
        fig.tight_layout()
        web_chart_path = FIGURES_DIR / "28_ventas_vs_visitas_web_por_producto.png"
        fig.savefig(web_chart_path, dpi=150)
        plt.close(fig)
        chart_rows.append(
            {
                "title": "Ventas vs visitas web por producto",
                "relative_path": "figures/sales_feature_eda/28_ventas_vs_visitas_web_por_producto.png",
                "reading": "Las visitas web pueden aportar una senal de demanda, aunque no sustituyen las ventas reales.",
            }
        )

    if aggregate_frames:
        pd.concat(aggregate_frames, ignore_index=True).to_csv(AGGREGATES_PATH, index=False)

    sales_summary = pd.DataFrame(
        [
            {"metrica": "Filas analizadas", "valor": f"{len(sales_df):,}".replace(",", ".")},
            {"metrica": "Ventas totales", "valor": f"{sales_df[TARGET].sum():,.2f}".replace(",", "X").replace(".", ",").replace("X", ".")},
            {"metrica": "Pedidos unicos", "valor": f"{sales_df['Order Id'].nunique():,}".replace(",", ".")},
            {"metrica": "Compradores unicos", "valor": f"{sales_df['Customer Id'].nunique():,}".replace(",", ".")},
            {"metrica": "Productos unicos", "valor": f"{sales_df['Product Name'].nunique():,}".replace(",", ".")},
            {"metrica": "Paises de pedido", "valor": f"{sales_df['Order Country'].nunique():,}".replace(",", ".")},
            {"metrica": "Ciudades de pedido", "valor": f"{sales_df['Order City'].nunique():,}".replace(",", ".")},
        ]
    )

    chart_blocks = []
    for row in chart_rows:
        chart_blocks.append(image_block(row["title"], row["relative_path"], row["reading"]))

    report = f"""---
title: "EDA de Variables para Modelo de Ventas"
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

<div align="center">

# EDA de Variables para Modelo de Ventas

## DataCo Supply Chain

**Objetivo:** revisar variables candidatas antes de modelar ventas y visualizar su distribucion con graficos de barras.

</div>

---

# 1. Resumen

Este informe revisa variables disponibles para un futuro modelo de ventas. No se modificaron los CSV raw; las variables nuevas se guardaron como salidas derivadas en `data/processed/`.

Variable objetivo propuesta: `Sales`.

{markdown_table(sales_summary)}

---

# 2. Variables Revisadas

Se revisaron las variables solicitadas y solo se usaron las que existen o se pueden derivar de columnas reales.

{markdown_table(variable_audit)}

Notas importantes:

- No hay columna explicita de campana de marketing. Por tanto no se usa `campana` como variable del modelo.
- Los descuentos si existen y se usan como proxy de ofertas: `Order Item Discount` y `Order Item Discount Rate`.
- Los festivos se derivan de la fecha de pedido con una marca simple de festivos genericos. No sustituyen un calendario oficial por pais.
- Los periodos tipo Black Friday o Navidad son periodos de calendario derivados, no campanas reales.

---

# 3. Graficos de Variables Candidatas

{''.join(chart_blocks)}

---

# 4. Lectura para el Modelo

Variables con pinta de aportar senal:

- geografia: `Order Country`, `Order City`, `Order Region`, `Market`;
- comprador: `Customer Id`, `Customer Segment`, banda de valor historico del comprador;
- producto: `Product Name`, `Category Name`, `Department Name`;
- precio y cantidad: `Order Item Product Price`, `Order Item Quantity`;
- descuentos/ofertas: `Order Item Discount`, `Order Item Discount Rate`, `has_discount`;
- calendario: mes, dia de semana, fin de semana, periodos comerciales derivados;
- metodo de pago y tipo de envio como variables auxiliares.

Variables no disponibles para usar directamente:

- campanas de marketing;
- festivos oficiales por pais;
- stock, inventario o disponibilidad;
- costes publicitarios;
- distancia de envio;
- canal real de adquisicion del cliente.

Siguiente paso recomendado: construir un primer baseline de ventas con variables disponibles y comparar si las agregaciones por cliente, producto, geografia y calendario mejoran frente a una media historica simple.
"""

    REPORT_PATH.write_text(report, encoding="utf-8-sig")
    print(f"Informe generado: {REPORT_PATH}")
    print(f"Dataset derivado: {FEATURE_DATASET_PATH}")
    print(f"Auditoria de variables: {VARIABLE_AUDIT_PATH}")
    print(f"Agregados: {AGGREGATES_PATH}")
    print(f"Graficos: {FIGURES_DIR}")


if __name__ == "__main__":
    main()
