"""
Make a choropleth map of Zimbabwe districts coloured by Digital Desert Index.

Run locally:
    python src/make_district_map.py

Inputs:
    data/processed/zwe_districts_master.gpkg

Outputs (in ./outputs/figures/):
    zwe_district_ddi_map.png           Choropleth of overall DDI
    zwe_district_coverage_map.png      Choropleth of 4G coverage gap
"""
import sys
from pathlib import Path

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
    from matplotlib.colors import LinearSegmentedColormap
    import geopandas as gpd
except ImportError:
    sys.exit("Install dependencies: pip install matplotlib geopandas")

IN_PATH = Path("data/processed/zwe_districts_master.gpkg")
OUT_DIR = Path("outputs/figures")
OUT_DIR.mkdir(parents=True, exist_ok=True)

if not IN_PATH.exists():
    sys.exit(f"Missing {IN_PATH}. Run build_district_table.py first.")

districts = gpd.read_file(IN_PATH, layer="districts")
print(f"Loaded {len(districts)} districts")

# Custom red-blue colourmap: blue = low DDI (good), red = high DDI (bad)
ddi_cmap = LinearSegmentedColormap.from_list(
    "ddi", ["#1F4E79", "#FFC000", "#C00000"], N=256
)


def annotate_top_districts(ax, gdf, col, n=5, ascending=False, color="white"):
    """Label the N highest/lowest districts."""
    sub = gdf.sort_values(col, ascending=ascending).head(n)
    for _, r in sub.iterrows():
        pt = r["geometry"].representative_point()
        ax.annotate(r["district_name"], xy=(pt.x, pt.y),
                    fontsize=8, ha="center", va="center",
                    color=color, weight="bold",
                    path_effects=[])


# === Figure 1: Overall DDI choropleth ======================================
fig, ax = plt.subplots(figsize=(10, 8))

districts.plot(
    column="ddi",
    ax=ax,
    cmap=ddi_cmap,
    legend=True,
    edgecolor="white",
    linewidth=0.4,
    legend_kwds={
        "label": "Digital Desert Index (higher = more excluded)",
        "orientation": "horizontal",
        "shrink": 0.7,
        "pad": 0.04,
    },
)

# Provincial boundaries on top in a darker line
provs = districts.dissolve(by="province")
provs.boundary.plot(ax=ax, color="#333333", linewidth=0.9)

# Annotate worst districts
worst = districts.sort_values("ddi", ascending=False).head(5)
for _, r in worst.iterrows():
    pt = r["geometry"].representative_point()
    ax.annotate(r["district_name"], xy=(pt.x, pt.y),
                fontsize=7, ha="center", va="center", color="white", weight="bold")

ax.set_title("Zimbabwe — Digital Desert Index by district\n"
             "Pilot version using urban/rural classification + national indicators",
             fontsize=13, fontweight="bold", pad=12)
ax.set_axis_off()

fig.text(0.02, 0.02,
         "Sources: GADM 4.1, POTRAZ Q4 2025, World Bank 2024. "
         "Provincial boundaries shown in dark grey. "
         "District-level variance will increase once district-resolved POTRAZ "
         "and Ookla data are integrated.",
         fontsize=8, color="#555555", wrap=True)

fig.tight_layout()
out1 = OUT_DIR / "zwe_district_ddi_map.png"
fig.savefig(out1, dpi=200, bbox_inches="tight")
plt.close(fig)
print(f"Wrote {out1}")


# === Figure 2: 4G coverage gap choropleth =================================
fig, ax = plt.subplots(figsize=(10, 8))
districts.plot(
    column="coverage_gap_score",
    ax=ax,
    cmap=ddi_cmap,
    legend=True,
    edgecolor="white",
    linewidth=0.4,
    legend_kwds={
        "label": "4G coverage gap (100 = nobody covered, 0 = everyone covered)",
        "orientation": "horizontal",
        "shrink": 0.7,
        "pad": 0.04,
    },
)
provs.boundary.plot(ax=ax, color="#333333", linewidth=0.9)

ax.set_title("Zimbabwe — 4G/LTE coverage gap by district\n"
             "Rural districts (red): 71% of population without 4G. "
             "Urban districts (blue): 4% gap.",
             fontsize=13, fontweight="bold", pad=12)
ax.set_axis_off()

fig.text(0.02, 0.02,
         "Sources: GADM 4.1, POTRAZ Q4 2025. Coverage gap = 100 − population "
         "with at least 4G/LTE signal. Rural value: 71.0 (29% covered); "
         "urban value: 4.1 (95.9% covered).",
         fontsize=8, color="#555555", wrap=True)

fig.tight_layout()
out2 = OUT_DIR / "zwe_district_coverage_map.png"
fig.savefig(out2, dpi=200, bbox_inches="tight")
plt.close(fig)
print(f"Wrote {out2}")

print("\nMaps ready for the slide deck.")
