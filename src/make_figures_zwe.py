"""
POTRAZ-specific figures for the Zimbabwe slide deck.

Produces:
    outputs/figures/zwe_rural_urban_coverage_gap.png
    outputs/figures/zwe_base_station_distribution.png
    outputs/figures/zwe_internet_tech_mix.png
"""
import sys
from pathlib import Path
import pandas as pd
import numpy as np

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
except ImportError:
    sys.exit("Install matplotlib: pip install matplotlib")

IN_DIR  = Path("data/processed")
OUT_DIR = Path("outputs/figures")
OUT_DIR.mkdir(parents=True, exist_ok=True)

URBAN_COLOR = "#1F4E79"
RURAL_COLOR = "#C00000"
ACCENT      = "#7F7F7F"


# === Figure 1: Rural vs Urban population coverage by technology ============
coverage = pd.read_csv(IN_DIR / "potraz_q4_2025_coverage.csv")

fig, ax = plt.subplots(figsize=(10, 5.5))
techs = coverage["technology"].tolist()
x = np.arange(len(techs))
width = 0.38

urban_vals = coverage["pop_coverage_urban_pct"].tolist()
rural_vals = coverage["pop_coverage_rural_pct"].tolist()

ax.bar(x - width/2, urban_vals, width, label="Urban", color=URBAN_COLOR, edgecolor="white")
ax.bar(x + width/2, rural_vals, width, label="Rural", color=RURAL_COLOR, edgecolor="white")

# Value labels
for i, (u, r) in enumerate(zip(urban_vals, rural_vals)):
    ax.text(i - width/2, u + 1.5, f"{u}%", ha="center", fontsize=10, color=URBAN_COLOR, fontweight="bold")
    ax.text(i + width/2, r + 1.5, f"{r}%", ha="center", fontsize=10, color=RURAL_COLOR, fontweight="bold")

# Gap callout for LTE (the most striking)
lte_idx = techs.index("LTE")
gap = urban_vals[lte_idx] - rural_vals[lte_idx]
ax.annotate(f"  {gap:.0f}-point gap", xy=(lte_idx, rural_vals[lte_idx] + 15),
            fontsize=11, color=RURAL_COLOR, fontweight="bold",
            xytext=(lte_idx + 0.5, 65),
            arrowprops=dict(arrowstyle="->", color=RURAL_COLOR, lw=1.5))

ax.set_xticks(x)
ax.set_xticklabels(techs, fontsize=11)
ax.set_ylabel("Population coverage (%)")
ax.set_ylim(0, 115)
ax.set_title("Zimbabwe — population coverage by technology, rural vs urban\n"
             "(POTRAZ Q4 2025)", fontsize=13, fontweight="bold", pad=12)
ax.legend(loc="upper right", frameon=False)
ax.spines[["top", "right"]].set_visible(False)
ax.grid(axis="y", alpha=0.3)

fig.text(0.02, -0.02,
         "Source: POTRAZ Postal & Telecommunications Sector Performance Report, Q4 2025. "
         "Coverage figures are operator-reported.",
         fontsize=8, color="#555555")

fig.tight_layout()
fig.savefig(OUT_DIR / "zwe_rural_urban_coverage_gap.png", dpi=200, bbox_inches="tight")
plt.close(fig)
print(f"Wrote {OUT_DIR / 'zwe_rural_urban_coverage_gap.png'}")


# === Figure 2: Base station distribution by operator and area =============
bs_area = pd.read_csv(IN_DIR / "potraz_q4_2025_base_stations_by_area.csv")
bs_area_no_total = bs_area[bs_area["operator"] != "Total"].copy()

fig, ax = plt.subplots(figsize=(10, 5.5))
operators = bs_area_no_total["operator"].tolist()
urban = bs_area_no_total["urban"].tolist()
rural = bs_area_no_total["rural"].tolist()

x = np.arange(len(operators))
width = 0.38

ax.bar(x - width/2, urban, width, label="Urban", color=URBAN_COLOR, edgecolor="white")
ax.bar(x + width/2, rural, width, label="Rural", color=RURAL_COLOR, edgecolor="white")

for i, (u, r) in enumerate(zip(urban, rural)):
    ax.text(i - width/2, u + 80, f"{u:,}", ha="center", fontsize=10)
    ax.text(i + width/2, r + 80, f"{r:,}", ha="center", fontsize=10)

ax.set_xticks(x)
ax.set_xticklabels(operators, fontsize=11)
ax.set_ylabel("Number of base stations")
ax.set_title("Zimbabwe — mobile base stations by operator and area\n"
             "(POTRAZ Q4 2025: 64% of all base stations are in urban areas)",
             fontsize=13, fontweight="bold", pad=12)
ax.legend(loc="upper right", frameon=False)
ax.spines[["top", "right"]].set_visible(False)
ax.grid(axis="y", alpha=0.3)

fig.text(0.02, -0.02,
         "Source: POTRAZ Q4 2025. Total Zimbabwe: 8,423 urban vs 4,681 rural base stations, "
         "despite ~60% of the population living rurally.",
         fontsize=8, color="#555555")

fig.tight_layout()
fig.savefig(OUT_DIR / "zwe_base_station_distribution.png", dpi=200, bbox_inches="tight")
plt.close(fig)
print(f"Wrote {OUT_DIR / 'zwe_base_station_distribution.png'}")


# === Figure 3: Internet subscriptions by technology (the Starlink story) ===
tech = pd.read_csv(IN_DIR / "potraz_q4_2025_internet_tech.csv")
tech_no_total = tech[tech["technology"] != "Total"].copy()
tech_no_total = tech_no_total.sort_values("change_pct", ascending=True)

fig, ax = plt.subplots(figsize=(10, 5.5))
colors = ["#C00000" if c < 0 else "#1F4E79" for c in tech_no_total["change_pct"]]
# Highlight Starlink/VSAT
labels = tech_no_total["technology"].tolist()
colors = ["#2E8B57" if "VSAT" in t or "Starlink" in t else c
          for t, c in zip(labels, colors)]

bars = ax.barh(labels, tech_no_total["change_pct"], color=colors, edgecolor="white")
for bar, val in zip(bars, tech_no_total["change_pct"]):
    offset = 1 if val >= 0 else -1
    ha = "left" if val >= 0 else "right"
    ax.text(val + offset, bar.get_y() + bar.get_height() / 2,
            f"{val:+.1f}%", va="center", ha=ha, fontsize=10)

ax.axvline(0, color="black", linewidth=0.8)
ax.set_xlabel("Quarter-on-quarter change (%) — Q3 2025 to Q4 2025")
ax.set_title("Zimbabwe internet subscriptions by technology — who's growing\n"
             "(Starlink VSAT +31.6% is the fastest-growing technology)",
             fontsize=13, fontweight="bold", pad=12)
ax.spines[["top", "right"]].set_visible(False)
ax.grid(axis="x", alpha=0.3)

fig.text(0.02, -0.02,
         "Source: POTRAZ Q4 2025. Starlink fills coverage gaps where terrestrial networks "
         "don't reach — a critical interim measure for digital deserts.",
         fontsize=8, color="#555555")

fig.tight_layout()
fig.savefig(OUT_DIR / "zwe_internet_tech_mix.png", dpi=200, bbox_inches="tight")
plt.close(fig)
print(f"Wrote {OUT_DIR / 'zwe_internet_tech_mix.png'}")

print("\nAll Zimbabwe-specific figures ready.")
