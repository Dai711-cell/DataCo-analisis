from pathlib import Path

import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

PROJECT_DIR = Path(__file__).resolve().parent
DATA_PATH = PROJECT_DIR / "data" / "processed" / "dataco_supply_chain_processed.csv"
FIGURES_DIR = PROJECT_DIR / "reports" / "figures" / "shipping_business"
OUTPUT_PATH = PROJECT_DIR / "data" / "processed" / "shipping_business_baseline_comparison.csv"
FIGURES_DIR.mkdir(parents=True, exist_ok=True)

df = pd.read_csv(DATA_PATH, low_memory=False)
cols = ["Shipping Mode", "Days for shipping (real)", "Days for shipment (scheduled)", "Late_delivery_risk"]
df = df[cols].dropna().copy()
df["current_broken_promise"] = df["Days for shipping (real)"] > df["Days for shipment (scheduled)"]

summary = (
    df.groupby("Shipping Mode")
    .agg(
        orders=("Shipping Mode", "size"),
        current_promise_days=("Days for shipment (scheduled)", lambda s: s.mode().iloc[0]),
        actual_mean_days=("Days for shipping (real)", "mean"),
        actual_median_days=("Days for shipping (real)", "median"),
        current_broken_promises=("current_broken_promise", "sum"),
        official_late_orders=("Late_delivery_risk", "sum"),
    )
    .reset_index()
)
summary["recommended_baseline_days"] = np.ceil(summary["actual_mean_days"]).astype(int)
recommended_map = dict(zip(summary["Shipping Mode"], summary["recommended_baseline_days"]))
df["recommended_baseline_days"] = df["Shipping Mode"].map(recommended_map)
df["baseline_broken_promise"] = df["Days for shipping (real)"] > df["recommended_baseline_days"]
after = df.groupby("Shipping Mode").agg(baseline_broken_promises=("baseline_broken_promise", "sum")).reset_index()
summary = summary.merge(after, on="Shipping Mode")
summary["promises_fixed"] = summary["current_broken_promises"] - summary["baseline_broken_promises"]
summary["current_broken_rate"] = summary["current_broken_promises"] / summary["orders"]
summary["baseline_broken_rate"] = summary["baseline_broken_promises"] / summary["orders"]
summary["broken_rate_drop_pp"] = (summary["current_broken_rate"] - summary["baseline_broken_rate"]) * 100
summary.to_csv(OUTPUT_PATH, index=False)

metrics = pd.DataFrame(
    {
        "Sistema": ["Sistema actual", "Baseline por tipo de envio", "Random Forest con historicos"],
        "MAE": [1.2848, 0.9771, 0.9338],
    }
)
fig, ax = plt.subplots(figsize=(9, 5))
colors = ["#D95F02", "#1B9E77", "#7570B3"]
bars = ax.barh(metrics["Sistema"], metrics["MAE"], color=colors)
ax.invert_yaxis()
ax.bar_label(bars, fmt="%.4f", padding=5)
ax.set_title("Error medio de prediccion de dias de entrega", fontsize=15, pad=12)
ax.set_xlabel("MAE en dias")
ax.grid(axis="x", alpha=0.25)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
fig.tight_layout()
fig.savefig(FIGURES_DIR / "shipping_business_mae_comparison.png", dpi=150)
plt.close(fig)

totals = pd.DataFrame(
    {
        "Promesa": ["Promesa actual", "Promesa baseline"],
        "Pedidos con promesa incumplida": [int(df["current_broken_promise"].sum()), int(df["baseline_broken_promise"].sum())],
    }
)
fig, ax = plt.subplots(figsize=(8, 5))
bars = ax.bar(totals["Promesa"], totals["Pedidos con promesa incumplida"], color=["#D95F02", "#1B9E77"])
ax.bar_label(bars, fmt="%d", padding=5)
ax.set_title("Pedidos que incumplen la promesa comunicada", fontsize=15, pad=12)
ax.set_ylabel("Numero de pedidos")
ax.grid(axis="y", alpha=0.25)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
fig.tight_layout()
fig.savefig(FIGURES_DIR / "shipping_business_broken_promises_total.png", dpi=150)
plt.close(fig)

plot_data = summary.sort_values("current_broken_promises", ascending=True)
fig, ax = plt.subplots(figsize=(10, 5.5))
y = np.arange(len(plot_data))
height = 0.36
ax.barh(y + height / 2, plot_data["current_broken_rate"] * 100, height, label="Promesa actual", color="#D95F02")
ax.barh(y - height / 2, plot_data["baseline_broken_rate"] * 100, height, label="Promesa baseline", color="#1B9E77")
ax.set_yticks(y)
ax.set_yticklabels(plot_data["Shipping Mode"])
ax.set_xlabel("% de pedidos que incumplen promesa")
ax.set_title("Incumplimiento de promesa por tipo de envio", fontsize=15, pad=12)
ax.legend(frameon=False)
ax.grid(axis="x", alpha=0.25)
ax.spines["top"].set_visible(False)
ax.spines["right"].set_visible(False)
fig.tight_layout()
fig.savefig(FIGURES_DIR / "shipping_business_broken_promises_by_mode.png", dpi=150)
plt.close(fig)

print(summary.to_string(index=False))
