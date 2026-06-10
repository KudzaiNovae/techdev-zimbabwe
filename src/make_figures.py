"""
Produce charts for the slide deck from the DDI output.

Run locally:
    pip install matplotlib
    python src/make_figures.py

Inputs:
    data/processed/ddi_country.csv
    data/processed/ddi_country_long.csv

Outputs (in ./outputs/figures/):
    ddi_country_ranking.png      Horizontal bar chart of overall DDI by country
    ddi_pillar_breakdown.png     Grouped bar chart showing each pillar per country
"""
import sys
from pathlib import Path
import pandas as pd

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
except ImportError:
    sys.exit("Install matplotlib: pip install matplotlib")

IN_DIR  = Path("data/processed")
OUT_DIR = Path("outputs/figures")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Color palette (colour-blind safe-ish)
ZIM_COLOR  = "#C00000"   # Zimbabwe highlighted in red
PEER_COLOR = "#4F81BD"   # Peers in muted blue
PILLAR_COLORS = {
    "coverage_gap":      "#1F4E79",
    "adoption_gap":      "#4F81BD",
    "affordability_gap": "#C00000",
    "electricity_gap":   "#7F7F7F",
}
PILLAR_LABELS = {
    "coverage_gap":      "Coverage gap",
    "adoption_gap":      "Adoption gap",
    "affordability_gap": "Affordability gap",
    "electricity_gap":   "Electricity gap",
}

ddi_path = IN_DIR / "ddi_country.csv"
long_path = IN_DIR / "ddi_country_long.csv"
if not ddi_path.exists():
    sys.exit(f"Missing {ddi_path}. Run src/compute_ddi.py first.")

df = pd.read_csv(ddi_path)
long_df = pd.read_csv(long_path)

# --- Figure 1: Country DDI ranking ----------------------------------------
fig, ax = plt.subplots(figsize=(9, 5))
plot_df = df.sort_values("ddi", ascending=True)  # so highest is on top
colors = [ZIM_COLOR if iso == "ZWE" else PEER_COLOR for iso in plot_df["country_iso3"]]
bars = ax.barh(plot_df["country_name"], plot_df["ddi"], color=colors, edgecolor="white")

for bar, val in zip(bars, plot_df["ddi"]):
    ax.text(val + 1, bar.get_y() + bar.get_height() / 2,
            f"{val:.0f}", va="center", fontsize=10)

ax.set_xlabel("Digital Desert Index (0–100, higher = more excluded)")
ax.set_title("Digital Desert Index — Zimbabwe vs SADC peers", fontsize=13, fontweight="bold", pad=12)
ax.set_xlim(0, max(plot_df["ddi"]) * 1.15)
ax.spines[["top", "right"]].set_visible(False)
ax.grid(axis="x", alpha=0.3)

# Footnote
fig.text(0.02, -0.02,
         "Source: World Bank, ITU DataHub. DDI = unweighted mean of coverage, adoption, "
         "affordability and electricity gap scores. Zimbabwe shown in red.",
         fontsize=8, color="#555555", wrap=True)

fig.tight_layout()
out1 = OUT_DIR / "ddi_country_ranking.png"
fig.savefig(out1, dpi=200, bbox_inches="tight")
plt.close(fig)
print(f"Wrote {out1}")

# --- Figure 2: Pillar breakdown -------------------------------------------
fig, ax = plt.subplots(figsize=(10, 5.5))

pillars = list(PILLAR_LABELS.keys())
countries_sorted = df.sort_values("ddi", ascending=False)["country_iso3"].tolist()
country_names = df.set_index("country_iso3").loc[countries_sorted, "country_name"].tolist()

import numpy as np
x = np.arange(len(countries_sorted))
width = 0.20

for i, pillar in enumerate(pillars):
    vals = []
    for iso in countries_sorted:
        row = long_df[(long_df["country_iso3"] == iso) & (long_df["pillar"] == pillar)]
        vals.append(row["score"].iloc[0] if len(row) and pd.notna(row["score"].iloc[0]) else 0)
    ax.bar(x + (i - 1.5) * width, vals, width,
           label=PILLAR_LABELS[pillar], color=PILLAR_COLORS[pillar], edgecolor="white")

ax.set_xticks(x)
ax.set_xticklabels(country_names, rotation=0, fontsize=10)
ax.set_ylabel("Pillar score (0–100, higher = worse)")
ax.set_title("DDI pillar breakdown — what's driving each country's score",
             fontsize=13, fontweight="bold", pad=12)
ax.set_ylim(0, 100)
ax.legend(loc="upper right", frameon=False, ncol=2)
ax.spines[["top", "right"]].set_visible(False)
ax.grid(axis="y", alpha=0.3)

fig.text(0.02, -0.02,
         "Source: World Bank, ITU DataHub. Missing bars = no data for that pillar in that country.",
         fontsize=8, color="#555555")

fig.tight_layout()
out2 = OUT_DIR / "ddi_pillar_breakdown.png"
fig.savefig(out2, dpi=200, bbox_inches="tight")
plt.close(fig)
print(f"Wrote {out2}")

print("\nFigures ready for the slide deck.")
