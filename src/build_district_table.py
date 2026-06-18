"""
Attach district geometry to the Zimbabwe district Digital Desert Index.

This builds the spatial layer used by the choropleth maps. The DDI *numbers*
are computed (reproducibly, without geopandas) by ``compute_district_ddi.py``;
this script only joins those numbers to GADM admin-2 polygons so they can be
drawn on a map.

IMPORTANT — read this before trusting the maps
----------------------------------------------
The earlier version of this script apportioned population by GADM polygon
*area*. The committed ``gadm41_ZWE.gpkg`` is a STUB: it has 66 features but
every geometry is an identical 133-byte placeholder, so all "areas" came out
~1,050 km^2 (country total 69k vs the real 390,757 km^2) and every district
received ~250k people. That collapsed the whole map to one colour band.

This rewrite:
  * never apportions population by area — it uses the real 2022 Census
    populations and the clean four-pillar DDI from compute_district_ddi.py;
  * detects the stub GADM and refuses to pretend the map is meaningful;
  * aggregates the 91 census districts up to the ~63 GADM admin-2 polygons
    (population-weighted DDI) via a normalised name match.

To get real maps, download the genuine GADM file (several MB, NOT the stub):
    wget https://geodata.ucdavis.edu/gadm/gadm4.1/gpkg/gadm41_ZWE.gpkg -P data/raw/geo/

Run (after compute_district_ddi.py):
    python src/build_district_table.py

Output:
    data/processed/zwe_districts_master.gpkg   geometry + DDI (for the maps)
    data/processed/zwe_districts_master.csv    flat table
"""
import sys
import re
from pathlib import Path
import pandas as pd
import numpy as np

try:
    import geopandas as gpd
except ImportError:
    sys.exit("Install geopandas:  pip install geopandas")

GADM_PATH    = Path("data/raw/geo/gadm41_ZWE.gpkg")
DISTRICT_DDI = Path("data/processed/zwe_districts_ddi_census.csv")
OUT_DIR      = Path("data/processed")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Equal-area CRS for Zimbabwe so polygon areas are trustworthy.
EQUAL_AREA_EPSG = 102022  # Africa Albers Equal Area Conic
ZWE_AREA_KM2 = 390_757    # ground truth, for the stub check


def normalise(name: str) -> str:
    """Collapse 'Chipinge Urban' / 'Chipinge Rural' / 'Harare Urban' -> 'chipinge'/'harare'."""
    s = str(name).lower().strip()
    s = re.sub(r"\((ump|ump)\)", "", s)
    s = re.sub(r"\b(urban|rural|local board|centre|center|municipality|town|city)\b", "", s)
    s = re.sub(r"[^a-z]+", " ", s).strip()
    return s


# --- 1. District DDI numbers (authoritative, real populations) -------------
if not DISTRICT_DDI.exists():
    sys.exit(f"Missing {DISTRICT_DDI}. Run src/compute_district_ddi.py first.")
ddi = pd.read_csv(DISTRICT_DDI)
ddi["key"] = ddi["district_name"].map(normalise)
print(f"Loaded {len(ddi)} census districts (pop {ddi['population'].sum():,})")

# --- 2. District boundaries -------------------------------------------------
if not GADM_PATH.exists():
    sys.exit(f"Missing {GADM_PATH}. Download from "
             "https://geodata.ucdavis.edu/gadm/gadm4.1/gpkg/gadm41_ZWE.gpkg")
districts = gpd.read_file(GADM_PATH, layer="ADM_ADM_2").rename(columns={
    "NAME_2": "district_name", "NAME_1": "province", "GID_2": "district_id",
})
districts = districts[["district_id", "district_name", "province", "geometry"]].copy()
print(f"Loaded {len(districts)} GADM admin-2 polygons")

# --- 3. Stub-geometry guard -------------------------------------------------
try:
    areas = districts.to_crs(epsg=EQUAL_AREA_EPSG).geometry.area / 1e6
except Exception:
    areas = districts.to_crs(epsg=32735).geometry.area / 1e6  # UTM 35S fallback
total_area = float(areas.sum())
districts["area_km2"] = areas.round(1).values
spread = (areas.max() - areas.min()) / max(areas.mean(), 1e-9)
if total_area < 0.5 * ZWE_AREA_KM2 or spread < 0.2:
    print("\n" + "!" * 70)
    print(f"WARNING: GADM geometry looks like a STUB (total area {total_area:,.0f} km^2 "
          f"vs real {ZWE_AREA_KM2:,}; area spread {spread:.2f}).")
    print("The output table will carry correct DDI VALUES, but the geometry — and")
    print("therefore any rendered map — is meaningless until you download the real")
    print("GADM file. See the module docstring.")
    print("!" * 70 + "\n")

# --- 4. Aggregate census districts -> GADM polygons (population-weighted) ----
def wmean(g, col):
    w = g["population"]
    return float(np.average(g[col], weights=w)) if w.sum() else float(g[col].mean())

pillar_cols = ["coverage_gap", "adoption_gap", "affordability_gap", "electricity_gap", "ddi"]
agg = (ddi.groupby("key")
          .apply(lambda g: pd.Series(
              {**{c: round(wmean(g, c), 1) for c in pillar_cols},
               "district_population": int(g["population"].sum()),
               "base_stations": int(g["base_stations"].sum())}),
              include_groups=False)
          .reset_index())

districts["key"] = districts["district_name"].map(normalise)
districts = districts.merge(agg, on="key", how="left")
matched = districts["ddi"].notna().sum()
print(f"Matched {matched}/{len(districts)} GADM polygons to census DDI by name")
if matched < len(districts):
    miss = districts[districts["ddi"].isna()]["district_name"].tolist()
    print(f"  Unmatched GADM polygons (no DDI): {miss}")

# make_district_map.py expects *_score column names
districts["coverage_gap_score"]      = districts["coverage_gap"]
districts["adoption_gap_score"]      = districts["adoption_gap"]
districts["affordability_gap_score"] = districts["affordability_gap"]
districts["electricity_gap_score"]   = districts["electricity_gap"]
districts["ddi_rank"] = districts["ddi"].rank(ascending=False, method="min")

# --- 5. Save ---------------------------------------------------------------
gpkg_out = OUT_DIR / "zwe_districts_master.gpkg"
districts.to_file(gpkg_out, layer="districts", driver="GPKG")
csv_out = OUT_DIR / "zwe_districts_master.csv"
districts.drop(columns="geometry").to_csv(csv_out, index=False)
print(f"\nSpatial output -> {gpkg_out}")
print(f"Flat output    -> {csv_out}")

print("\nDDI by district (population-weighted, top 5 worst):")
for _, r in districts.dropna(subset=["ddi"]).sort_values("ddi", ascending=False).head(5).iterrows():
    print(f"  {r['ddi']:>5.1f}  {r['district_name']:<22} pop={int(r['district_population']):>9,}")
