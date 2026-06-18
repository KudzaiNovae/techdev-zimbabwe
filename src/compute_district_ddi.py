"""
Compute the district-level Digital Desert Index for Zimbabwe (reproducible).

This is the transparent, geopandas-free replacement for the previously
hand-committed ``data/processed/zwe_districts_ddi_census.csv``. It computes the
district DDI entirely from committed inputs so that running this script
reproduces the numbers exactly.

Why this script exists
----------------------
The original district pipeline (``build_district_table.py``) apportioned
population by GADM polygon area. The committed GADM file is a stub: it has 66
features but every geometry is an identical 133-byte placeholder, so every
district received a near-identical area (~1,050 km^2; the country total came
out at 69k vs the real 390,757 km^2) and therefore a near-identical population
(~250k each). With population, coverage and electricity all constant within an
urban/rural class, the "district" DDI collapsed to just two values.

The later hand-built census file fixed the populations (real 2022 Census
totals) but its headline ``ddi`` column was produced by an undocumented
adjustment that did not match its own visible pillar columns. For example
Mudzi listed pillars averaging 52.4 but a ``ddi`` of 39.7. That made the
flagship Stage-2 output non-reproducible and internally inconsistent.

This script computes the four-pillar DDI cleanly and consistently from:
  * real 2022 Census district populations (committed roster)
  * POTRAZ Q4 2025 rural/urban LTE coverage
  * World Bank national internet use and rural/urban electricity access
  * ITU mobile data+voice basket affordability (% of GNI)

OpenCellID tower density is attached for context only. Because that source is
~99% NetOne-biased AND its district assignment depends on the GADM stub's
spatial join, it is deliberately NOT folded into the index.

Run:
    python src/compute_district_ddi.py

Inputs (all committed):
    data/raw/zimstat/zwe_district_population_2022_census.csv   <- district roster
    data/processed/potraz_q4_2025_coverage.csv                 <- extract_potraz.py
    data/raw/worldbank/wb_indicators_wide.csv                  <- extract_worldbank.py
    data/processed/itu_indicators_wide.csv                     <- extract_itu.py
    data/processed/opencellid_district_towers.csv              <- optional, context only

Outputs:
    data/processed/zwe_districts_ddi_census.csv
    data/processed/zwe_districts_ddi_summary.txt
    outputs/figures/district_ddi_refined.png                   <- if matplotlib present
"""
import sys
from pathlib import Path
import pandas as pd
import numpy as np

ROSTER_PATH   = Path("data/raw/zimstat/zwe_district_population_2022_census.csv")
POTRAZ_COV    = Path("data/processed/potraz_q4_2025_coverage.csv")
WB_PATH       = Path("data/raw/worldbank/wb_indicators_wide.csv")
ITU_PATH      = Path("data/processed/itu_indicators_wide.csv")
OPENCELLID    = Path("data/processed/opencellid_district_towers.csv")

OUT_DIR = Path("data/processed")
FIG_DIR = Path("outputs/figures")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# POTRAZ Q4 2025 reports national urban/rural base-station totals (Table 9).
URBAN_BS_TOTAL = 8423
RURAL_BS_TOTAL = 4681


def clip01(x):
    return np.clip(x, 0.0, 100.0)


def wb_latest(wb: pd.DataFrame, col: str) -> float:
    """Latest non-null Zimbabwe value for a World Bank column."""
    z = wb[wb["country_iso3"] == "ZWE"][["year", col]].dropna()
    if not len(z):
        sys.exit(f"World Bank column '{col}' has no Zimbabwe value.")
    return float(z.sort_values("year").iloc[-1][col])


# --- 1. District roster (real 2022 Census populations) ---------------------
if not ROSTER_PATH.exists():
    sys.exit(f"Missing {ROSTER_PATH}. This roster of 2022 Census district "
             "populations is a committed input for the district DDI.")
d = pd.read_csv(ROSTER_PATH)
print(f"Loaded {len(d)} districts "
      f"(total population {d['population'].sum():,}) from {ROSTER_PATH}")

# --- 2. POTRAZ rural/urban coverage ----------------------------------------
if not POTRAZ_COV.exists():
    sys.exit(f"Missing {POTRAZ_COV}. Run src/extract_potraz.py first.")
cov = pd.read_csv(POTRAZ_COV).set_index("technology")
rural_4g = float(cov.loc["LTE", "pop_coverage_rural_pct"])   # 29.0
urban_4g = float(cov.loc["LTE", "pop_coverage_urban_pct"])   # 95.9
print(f"POTRAZ LTE coverage: rural {rural_4g}% / urban {urban_4g}%")

# --- 3. National indicators (World Bank + ITU) -----------------------------
if not WB_PATH.exists():
    sys.exit(f"Missing {WB_PATH}. Run src/extract_worldbank.py first.")
wb = pd.read_csv(WB_PATH)
internet_users   = wb_latest(wb, "wb_internet_users_pct")          # 41.64
rural_elec       = wb_latest(wb, "electricity_access_rural_pct")   # 51.4
urban_elec       = wb_latest(wb, "electricity_access_urban_pct")   # 84.0

# ITU affordability basket as % of GNI per capita. This is the SAME value used
# in the country-level DDI (3.15) — the old district build hard-coded 10.1,
# which capped every district's affordability pillar at 100.
basket_pct_gni = np.nan
if ITU_PATH.exists():
    itu = pd.read_csv(ITU_PATH)
    z = itu[itu["country_iso3"] == "ZWE"]
    if len(z) and pd.notna(z["basket_data_voice_low_pct_gni"].iloc[0]):
        basket_pct_gni = float(z["basket_data_voice_low_pct_gni"].iloc[0])
if pd.isna(basket_pct_gni):
    sys.exit("Could not read ITU basket_data_voice_low_pct_gni for Zimbabwe.")
print(f"National indicators: internet {internet_users}% | rural elec "
      f"{rural_elec}% | urban elec {urban_elec}% | basket {basket_pct_gni}% of GNI")

# --- 4. Per-district indicators --------------------------------------------
is_urban = d["urban_rural"].eq("urban")
d["pop_covered_4g_pct"]            = np.where(is_urban, urban_4g, rural_4g)
d["internet_users_pct"]           = internet_users
d["electricity_access_pct"]       = np.where(is_urban, urban_elec, rural_elec)
d["basket_data_voice_low_pct_gni"] = basket_pct_gni

# --- 5. Four-pillar gap scores (each 0-100, higher = worse) -----------------
d["coverage_gap"]      = clip01(100 - d["pop_covered_4g_pct"]).round(1)
d["adoption_gap"]      = clip01(100 - d["internet_users_pct"]).round(1)
d["affordability_gap"] = clip01(d["basket_data_voice_low_pct_gni"] * 10).round(1)
d["electricity_gap"]   = clip01(100 - d["electricity_access_pct"]).round(1)

PILLARS = ["coverage_gap", "adoption_gap", "affordability_gap", "electricity_gap"]
d["ddi"] = d[PILLARS].mean(axis=1).round(1)
d["ddi_rank"] = d["ddi"].rank(ascending=False, method="min").astype(int)

# Quintiles (DDI only takes a few distinct values, so drop duplicate edges and
# fall back to the urban/rural split if there are too few unique values).
try:
    d["ddi_quintile"] = pd.qcut(
        d["ddi"], q=5,
        labels=["Q1 (best)", "Q2", "Q3", "Q4", "Q5 (worst)"],
        duplicates="drop",
    ).astype(str)
except ValueError:
    d["ddi_quintile"] = np.where(is_urban, "Q1 (best)", "Q5 (worst)")

# --- 6. Base stations apportioned by population within each class -----------
urban_pop = d.loc[is_urban, "population"].sum()
rural_pop = d.loc[~is_urban, "population"].sum()
d["base_stations"] = np.where(
    is_urban,
    (d["population"] / urban_pop * URBAN_BS_TOTAL),
    (d["population"] / rural_pop * RURAL_BS_TOTAL),
).round().astype(int)
d["base_stations_per_10k"] = (d["base_stations"] / d["population"] * 10000).round(2)

# --- 7. OpenCellID tower density (context only, recomputed on real pop) -----
# NB: provisional — the tower->district assignment relies on the GADM stub's
# spatial join, so treat these values as indicative until a real GADM is used.
d["towers_per_10k"] = np.nan
if OPENCELLID.exists():
    oc = pd.read_csv(OPENCELLID)
    if {"district_name", "total_towers"}.issubset(oc.columns):
        towers = oc.groupby("district_name")["total_towers"].sum()
        d["_towers"] = d["district_name"].map(towers)
        d["towers_per_10k"] = (d["_towers"] / d["population"] * 10000).round(2)
        d = d.drop(columns="_towers")
        matched = d["towers_per_10k"].notna().sum()
        print(f"OpenCellID density attached for {matched}/{len(d)} districts "
              "(context only, excluded from the index)")

# --- 8. Save ---------------------------------------------------------------
cols = ["province", "district_name", "urban_rural", "population",
        "pop_covered_4g_pct", "internet_users_pct", "electricity_access_pct",
        "basket_data_voice_low_pct_gni",
        "coverage_gap", "adoption_gap", "affordability_gap", "electricity_gap",
        "ddi", "ddi_rank", "ddi_quintile",
        "base_stations", "base_stations_per_10k", "towers_per_10k"]
d = d.sort_values(["ddi", "population"], ascending=[False, False]).reset_index(drop=True)
out_csv = OUT_DIR / "zwe_districts_ddi_census.csv"
d[cols].to_csv(out_csv, index=False)
print(f"\nDistrict DDI -> {out_csv}")

# --- 9. Human-readable summary ---------------------------------------------
urban = d[d["urban_rural"] == "urban"]
rural = d[d["urban_rural"] == "rural"]
lines = []
lines.append("=" * 70)
lines.append("ZIMBABWE DISTRICT DIGITAL DESERT INDEX (higher = more excluded)")
lines.append("=" * 70)
lines.append("")
lines.append(f"Districts: {len(d)}  |  Population: {d['population'].sum():,} "
             "(2022 Census)")
lines.append(f"Urban districts: {len(urban)}  DDI {urban['ddi'].min():.1f}"
             f"-{urban['ddi'].max():.1f}  ({urban['population'].sum():,} people)")
lines.append(f"Rural districts: {len(rural)}  DDI {rural['ddi'].min():.1f}"
             f"-{rural['ddi'].max():.1f}  ({rural['population'].sum():,} people)")
pop = d['population'].sum()
rural_share = rural['population'].sum() / pop * 100
lines.append(f"Population in rural-council districts: {rural_share:.1f}% (these districts carry "
             "the 29% LTE coverage and 51.4% rural-electricity burden).")
lines.append("Note: this is the share in rural-council districts, not the census rural population")
lines.append("share. The 2022 Census / World Bank put the rural population at about 60%; the gap is")
lines.append("peri-urban wards (e.g. Harare Rural) that sit inside rural-council districts.")
lines.append("")
lines.append("Pillars (national where not district-resolved):")
lines.append(f"  coverage_gap     100 - LTE coverage (urban {urban_4g}, rural {rural_4g})")
lines.append(f"  adoption_gap     100 - internet users ({internet_users})")
lines.append(f"  affordability_gap basket {basket_pct_gni}% of GNI x 10")
lines.append(f"  electricity_gap  100 - electricity (urban {urban_elec}, rural {rural_elec})")
lines.append("")
lines.append("Worst 10 districts:")
for _, r in d.sort_values("ddi", ascending=False).head(10).iterrows():
    lines.append(f"  {r['ddi']:>5.1f}  {r['district_name']:<26} "
                 f"({r['province']}, {r['urban_rural']}, pop {r['population']:,})")
lines.append("")
lines.append("Best 10 districts:")
for _, r in d.sort_values("ddi", ascending=True).head(10).iterrows():
    lines.append(f"  {r['ddi']:>5.1f}  {r['district_name']:<26} "
                 f"({r['province']}, {r['urban_rural']}, pop {r['population']:,})")
summary = "\n".join(lines)
(OUT_DIR / "zwe_districts_ddi_summary.txt").write_text(summary, encoding="utf-8")
print("\n" + summary)

# --- 10. Figure (optional) -------------------------------------------------
try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt

    FIG_DIR.mkdir(parents=True, exist_ok=True)
    prov = (d.groupby("province")
              .apply(lambda g: np.average(g["ddi"], weights=g["population"]),
                     include_groups=False)
              .sort_values())
    fig, ax = plt.subplots(figsize=(9, 6))
    colors = ["#C00000" if v >= 45 else "#1F4E79" for v in prov.values]
    ax.barh(prov.index, prov.values, color=colors, edgecolor="white")
    for i, v in enumerate(prov.values):
        ax.text(v + 0.4, i, f"{v:.1f}", va="center", fontsize=9)
    ax.set_xlabel("Population-weighted Digital Desert Index (higher = worse)")
    ax.set_title("Zimbabwe — district Digital Desert Index by province\n"
                 "Population-weighted from 2022 Census + POTRAZ Q4 2025 + WB + ITU",
                 fontsize=12, fontweight="bold")
    ax.spines[["top", "right"]].set_visible(False)
    fig.text(0.01, 0.01,
             "Four-pillar DDI (coverage, adoption, affordability, electricity), "
             "equal weights. OpenCellID excluded (NetOne-biased).",
             fontsize=8, color="#555555")
    fig.tight_layout()
    out_png = FIG_DIR / "district_ddi_refined.png"
    fig.savefig(out_png, dpi=200, bbox_inches="tight")
    plt.close(fig)
    print(f"\nFigure -> {out_png}")
except ImportError:
    print("\n(matplotlib not installed — skipped district_ddi_refined.png)")
