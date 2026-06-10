"""
Build the Zimbabwe district-level master table.

This is the heart of the spatial pipeline. We start from GADM admin level 2
boundaries (~63 districts), and join:
    1. Province-level POTRAZ base station counts (Table 9, urban vs rural)
    2. World Bank national-level indicators (used as a baseline)
    3. ZimStat 2022 Census district populations (when available)
    4. WorldPop gridded population for rural/urban share (when available)

The output is one row per district with all indicators needed to compute the DDI.

Run locally:
    # Download GADM Zimbabwe data first:
    #   wget https://geodata.ucdavis.edu/gadm/gadm4.1/gpkg/gadm41_ZWE.gpkg -P data/raw/geo/
    # Then:
    python src/build_district_table.py

Output:
    data/processed/zwe_districts_master.gpkg   GeoPackage with geometry + indicators
    data/processed/zwe_districts_master.csv    Flat table (no geometry) for inspection
"""
import sys
from pathlib import Path
import pandas as pd
import numpy as np

try:
    import geopandas as gpd
except ImportError:
    sys.exit("Install geopandas:  pip install geopandas")

GADM_PATH      = Path("data/raw/geo/gadm41_ZWE.gpkg")
POTRAZ_PATH    = Path("data/processed/potraz_q4_2025_headlines.csv")
POTRAZ_COVERAGE_PATH = Path("data/processed/potraz_q4_2025_coverage.csv")
WB_PATH        = Path("data/raw/worldbank/wb_indicators_wide.csv")
ZIMSTAT_PATH   = Path("data/raw/zimstat/district_population_2022.csv")  # optional

OUT_DIR = Path("data/processed")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# --- 1. Load district boundaries ------------------------------------------
if not GADM_PATH.exists():
    sys.exit(f"Missing {GADM_PATH}. Download from "
             "https://geodata.ucdavis.edu/gadm/gadm4.1/gpkg/gadm41_ZWE.gpkg")

print(f"Reading {GADM_PATH} ...")
# GADM 4.1 ADM_2 layer in Zimbabwe contains districts
districts = gpd.read_file(GADM_PATH, layer="ADM_ADM_2")
print(f"  {len(districts)} districts loaded, columns: {list(districts.columns)[:6]}...")

# Standardise column names
districts = districts.rename(columns={
    "NAME_2": "district_name",
    "NAME_1": "province",
    "GID_2":  "district_id",
})

# Keep what we need
keep_cols = ["district_id", "district_name", "province", "geometry"]
districts = districts[keep_cols].copy()

# --- 2. Classify districts as urban vs rural ------------------------------
# Heuristic: cities and metro districts are urban; everything else rural
# (proper rural/urban classification would use ZimStat + WorldPop density)
URBAN_DISTRICTS = {
    "Bulawayo", "Harare Urban", "Chitungwiza", "Epworth", "Mutare",
    "Gweru", "Kwekwe", "Kadoma", "Masvingo", "Hwange",
    # Peri-urban districts often classified urban in census
}
districts["urban_rural"] = districts["district_name"].apply(
    lambda x: "urban" if x in URBAN_DISTRICTS else "rural"
)

# --- 3. Estimate district population --------------------------------------
# Priority: ZimStat processed file > raw ZimStat > area-based apportionment
total_pop = None
if WB_PATH.exists():
    wb = pd.read_csv(WB_PATH)
    zwe_pop = wb[wb["country_iso3"] == "ZWE"]["population_total"].dropna()
    if len(zwe_pop):
        total_pop = float(zwe_pop.iloc[-1])
        print(f"  National population (WB latest): {total_pop:,.0f}")

ZIMSTAT_PROCESSED = Path("data/processed/zimstat_district_population_2025.csv")
districts["district_population"] = np.nan

if ZIMSTAT_PROCESSED.exists():
    print(f"Reading {ZIMSTAT_PROCESSED} ...")
    zs = pd.read_csv(ZIMSTAT_PROCESSED)
    zs_lookup = zs.set_index("district_name")["population"].to_dict()
    districts["district_population"] = districts["district_name"].map(zs_lookup)
    matched = districts["district_population"].notna().sum()
    print(f"  Matched {matched}/{len(districts)} districts to ZimStat populations")
    # Also use ZimStat urban/rural classification where available
    zs_ur = zs.set_index("district_name")["urban_rural"].to_dict()
    zs_matched = districts["district_name"].map(zs_ur)
    districts.loc[zs_matched.notna(), "urban_rural"] = zs_matched[zs_matched.notna()]
elif ZIMSTAT_PATH.exists():
    print(f"Reading {ZIMSTAT_PATH} ...")
    zs = pd.read_csv(ZIMSTAT_PATH)
    districts = districts.merge(zs, on="district_name", how="left")
    if "population" in districts.columns:
        districts = districts.rename(columns={"population": "district_population"})

# For districts without ZimStat data, apportion remaining population by area
missing_pop = districts["district_population"].isna()
if missing_pop.any():
    n_missing = missing_pop.sum()
    print(f"  {n_missing} districts without ZimStat data — apportioning by area")
    # Apportion national population by area within each province
    print("  ZimStat district populations not available — apportioning by area")
    districts["area_km2"] = districts.to_crs(epsg=32735).geometry.area / 1e6
    # National population proportional to district area (very rough)
    if total_pop is None:
        total_pop = 16_634_370  # fallback to WB 2024 figure
    total_area = districts["area_km2"].sum()
    districts["district_population"] = (
        districts["area_km2"] / total_area * total_pop
    ).round().astype(int)

# --- 4. Apply POTRAZ Q4 2025 coverage figures ------------------------------
# We only have national rural/urban coverage from POTRAZ, not per-district.
# Apply national rural/urban values based on the district's classification.
if POTRAZ_COVERAGE_PATH.exists():
    cov = pd.read_csv(POTRAZ_COVERAGE_PATH).set_index("technology")
    rural_4g = float(cov.loc["LTE", "pop_coverage_rural_pct"])
    urban_4g = float(cov.loc["LTE", "pop_coverage_urban_pct"])
    rural_3g = float(cov.loc["3G",  "pop_coverage_rural_pct"])
    urban_3g = float(cov.loc["3G",  "pop_coverage_urban_pct"])
    rural_5g = float(cov.loc["5G",  "pop_coverage_rural_pct"])
    urban_5g = float(cov.loc["5G",  "pop_coverage_urban_pct"])
    print(f"  POTRAZ coverage applied: rural 4G {rural_4g}% / urban 4G {urban_4g}%")
else:
    sys.exit(f"Missing {POTRAZ_COVERAGE_PATH}. Run extract_potraz.py first.")

districts["pop_covered_4g_pct"] = districts["urban_rural"].map(
    {"urban": urban_4g, "rural": rural_4g}
)
districts["pop_covered_3g_pct"] = districts["urban_rural"].map(
    {"urban": urban_3g, "rural": rural_3g}
)
districts["pop_covered_5g_pct"] = districts["urban_rural"].map(
    {"urban": urban_5g, "rural": rural_5g}
)

# --- 5. Estimate base stations per district -------------------------------
# POTRAZ reports national urban/rural totals: 8,423 urban + 4,681 rural.
# Spread evenly across urban/rural districts (refinement: weight by population).
n_urban = (districts["urban_rural"] == "urban").sum()
n_rural = (districts["urban_rural"] == "rural").sum()
URBAN_BS_TOTAL = 8423
RURAL_BS_TOTAL = 4681

# Weight by population within each class
mask_urban = districts["urban_rural"] == "urban"
mask_rural = districts["urban_rural"] == "rural"
urban_pop_total = districts.loc[mask_urban, "district_population"].sum()
rural_pop_total = districts.loc[mask_rural, "district_population"].sum()

districts["base_stations"] = 0
districts.loc[mask_urban, "base_stations"] = (
    districts.loc[mask_urban, "district_population"] / urban_pop_total * URBAN_BS_TOTAL
).round().astype(int)
districts.loc[mask_rural, "base_stations"] = (
    districts.loc[mask_rural, "district_population"] / rural_pop_total * RURAL_BS_TOTAL
).round().astype(int)

districts["base_stations_per_1k"] = (
    districts["base_stations"] / districts["district_population"] * 1000
).round(3)

# --- 6. Bring in national WB indicators (broadcast to every district) -----
# Affordability, electricity, internet use don't vary at district level in our
# data, but we record them so the DDI computation has them.
if WB_PATH.exists():
    wb = pd.read_csv(WB_PATH)
    zwe = wb[wb["country_iso3"] == "ZWE"]
    def latest(col):
        s = zwe[["year", col]].dropna()
        return float(s.iloc[-1][col]) if len(s) else np.nan
    districts["internet_users_pct"]          = latest("wb_internet_users_pct")
    # Electricity: use rural rate for rural districts, urban rate for urban ones
    rural_elec = latest("electricity_access_rural_pct")
    urban_elec = latest("electricity_access_urban_pct")
    districts["electricity_access_pct"] = districts["urban_rural"].map(
        {"urban": urban_elec, "rural": rural_elec}
    )
    districts["gni_per_capita_usd"] = latest("gni_per_capita_usd")
else:
    # Fallback: known WB values for Zimbabwe (2024/2023)
    print("  WB data not found — using known fallback values for Zimbabwe")
    districts["internet_users_pct"] = 41.64       # WB 2024
    districts["electricity_access_pct"] = districts["urban_rural"].map(
        {"urban": 84.0, "rural": 51.4}            # WB 2023
    )
    districts["gni_per_capita_usd"] = 2400.0      # WB 2024

# Affordability: ~10.1% of GNI per capita for 1GB - national figure for now
districts["basket_data_voice_low_pct_gni"] = 10.1

# --- 7. Compute Digital Desert Index --------------------------------------
def clip01(x):
    return np.clip(x, 0, 100)

districts["coverage_gap_score"]     = clip01(100 - districts["pop_covered_4g_pct"])
districts["adoption_gap_score"]     = clip01(100 - districts["internet_users_pct"])
districts["affordability_gap_score"]= clip01(districts["basket_data_voice_low_pct_gni"] * 10)
districts["electricity_gap_score"]  = clip01(100 - districts["electricity_access_pct"])

pillar_cols = ["coverage_gap_score", "adoption_gap_score",
               "affordability_gap_score", "electricity_gap_score"]
districts["ddi"] = districts[pillar_cols].mean(axis=1).round(1)
districts["ddi_rank"] = districts["ddi"].rank(ascending=False, method="min").astype(int)
# With only urban/rural variation, many districts have identical DDI -
# use duplicates="drop" so qcut doesn't error
try:
    districts["ddi_quintile"] = pd.qcut(
        districts["ddi"], q=5,
        labels=["Q1 (best)", "Q2", "Q3", "Q4", "Q5 (worst)"],
        duplicates="drop"
    )
except ValueError:
    # If too few unique values, use the urban/rural classification as a proxy
    districts["ddi_quintile"] = districts["urban_rural"].map(
        {"urban": "Q1 (best)", "rural": "Q5 (worst)"}
    )

# --- 8. Save outputs ------------------------------------------------------
gpkg_out = OUT_DIR / "zwe_districts_master.gpkg"
districts.to_file(gpkg_out, layer="districts", driver="GPKG")
print(f"\nSpatial output -> {gpkg_out}")

csv_out = OUT_DIR / "zwe_districts_master.csv"
flat = districts.drop(columns="geometry")
flat.to_csv(csv_out, index=False)
print(f"Flat output    -> {csv_out}")

# --- 9. Print top/bottom districts ----------------------------------------
print("\nTop 10 districts by DDI (deepest digital deserts):")
top = districts.sort_values("ddi", ascending=False).head(10)
for _, r in top.iterrows():
    print(f"  #{r['ddi_rank']:>2}  {r['district_name']:<22} ({r['province']:<22})  "
          f"DDI {r['ddi']:>5.1f}  pop={r['district_population']:>9,}")

print("\nBottom 10 districts by DDI (best-served):")
bot = districts.sort_values("ddi", ascending=True).head(10)
for _, r in bot.iterrows():
    print(f"  #{r['ddi_rank']:>2}  {r['district_name']:<22} ({r['province']:<22})  "
          f"DDI {r['ddi']:>5.1f}  pop={r['district_population']:>9,}")

# Quintile summary
print("\nPopulation by DDI quintile:")
q = districts.groupby("ddi_quintile", observed=True).agg(
    districts=("district_name", "count"),
    population=("district_population", "sum"),
).reset_index()
q["pop_pct"] = (q["population"] / q["population"].sum() * 100).round(1)
print(q.to_string(index=False))
