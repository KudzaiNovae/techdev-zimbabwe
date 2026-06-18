"""
Generate a themed ETL pipeline diagram for the slide deck.

Run:
    python src/gen_etl_diagram.py

Output:
    outputs/figures/etl_pipeline.png
"""
from pathlib import Path
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
from matplotlib.patches import FancyBboxPatch, FancyArrowPatch

OUT_DIR = Path("outputs/figures")
OUT_DIR.mkdir(parents=True, exist_ok=True)

NAVY = "#1F4E79"
MIDBLUE = "#2E74B5"
RED = "#C00000"
GREY = "#6B7280"

fig, ax = plt.subplots(figsize=(13, 6.2))
ax.set_xlim(0, 13)
ax.set_ylim(0, 6.2)
ax.axis("off")


def box(x, y, w, h, text, color, fs=11, tc="white"):
    ax.add_patch(FancyBboxPatch(
        (x, y), w, h, boxstyle="round,pad=0.02,rounding_size=0.12",
        linewidth=0, facecolor=color))
    ax.text(x + w / 2, y + h / 2, text, ha="center", va="center",
            color=tc, fontsize=fs, fontweight="bold", linespacing=1.3)


def arrow(x1, y1, x2, y2):
    ax.add_patch(FancyArrowPatch(
        (x1, y1), (x2, y2), arrowstyle="-|>", mutation_scale=18,
        linewidth=2.2, color=GREY))


# Column headers
ax.text(1.95, 5.95, "DATA SOURCES", ha="center", fontsize=14, fontweight="bold", color=NAVY)
ax.text(6.5, 5.95, "PROCESSING", ha="center", fontsize=14, fontweight="bold", color=MIDBLUE)
ax.text(11.0, 5.95, "OUTPUTS", ha="center", fontsize=14, fontweight="bold", color=RED)

# Source boxes
sources = [
    "ITU DataHub\n(7 CSVs)",
    "World Bank\n(25 indicators)",
    "POTRAZ Q4 2025\n(7 tables)",
    "ZimStat Census\n(91 districts)",
    "OpenCellID\n(8,587 towers)",
]
sy = [4.75, 3.75, 2.75, 1.75, 0.75]
for t, y in zip(sources, sy):
    box(0.4, y, 3.1, 0.78, t, NAVY, fs=10.5)

# Processing boxes
proc = [
    ("extract_*.py\nclean & standardise", 4.55),
    ("compute_ddi.py\n4-pillar DDI", 2.65),
    ("build_district_table.py\nCensus + GADM join", 0.95),
]
for t, y in proc:
    box(5.0, y, 3.0, 0.95, t, MIDBLUE, fs=10.5)

# Output boxes
outs = [
    ("DDI country ranking\n6 SADC countries", 4.55),
    ("District DDI\n91 districts, real pop", 2.65),
    ("7 themed charts\n+ 12 policy actions", 0.95),
]
for t, y in outs:
    box(9.5, y, 3.1, 0.95, t, RED, fs=10.5)

# Arrows sources -> processing (fan into the middle compute box, staggered endpoints)
import numpy as np
targets = np.linspace(3.45, 2.85, len(sy))
for y, ty in zip(sy, targets):
    arrow(3.55, y + 0.39, 4.95, ty)
# processing chain -> outputs
arrow(8.05, 5.02, 9.45, 5.02)
arrow(8.05, 3.12, 9.45, 3.12)
arrow(8.05, 1.42, 9.45, 1.42)

ax.text(6.5, 0.12, "Orchestrated by run_all.py   .   single-command reproducibility",
        ha="center", fontsize=11, style="italic", color=GREY)

fig.savefig(OUT_DIR / "etl_pipeline.png", dpi=200, bbox_inches="tight",
            facecolor="white")
plt.close(fig)
print("Wrote", OUT_DIR / "etl_pipeline.png")
