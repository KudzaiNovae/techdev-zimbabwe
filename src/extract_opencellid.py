"""
Process OpenCellID cell tower data for Zimbabwe (MCC 648).

OpenCellID is a crowdsourced database of cell tower locations. The data
provides an independent cross-check on POTRAZ's operator-declared base
station counts and enables district-level tower density analysis.

Data source:
    Download from https://opencellid.org/downloads.php
    Filter: MCC 648 (Zimbabwe)
    Save as: data/raw/opencellid/648.csv

Run:
    python src/extract_opencellid.py

Output:
    data/processed/opencellid_district_towers.csv
    data/processed/opencellid_national_summary.csv
    outputs/figures/opencellid_tower_analysis.png

Caveats:
    - Crowdsourced: heavily biased toward NetOne (MNC 4 = 99% of entries).
      Econet (MNC 1) and Telecel (MNC 3) are severely under-represented.
    - Therefore: use for district-level RELATIVE density ranking, not
      absolute tower counts. Compare tower density ratios between districts,
      not raw counts vs POTRAZ totals.
    - LTE tower count (49) is far below POTRAZ's 3,585 because most LTE
      towers haven't been crowdsourced yet. The GSM/UMTS breakdown is
      more representative.
"""
import sys
from pathlib import Path
import pandas as pd
import numpy as np

try:
    import geopandas as gpd
    from shapely.geometry import Point
except ImportError:
    sys.exit("Install geopandas:  pip install geopandas")

try:
    import matplotlib
    matplotlib.use("Agg")
    import matplotlib.pyplot as plt
except ImportError:
    sys.exit("Install matplotlib:  pip install matplotlib")

# --- Config ----------------------------------------------------------------
RAW_PATH = Path("data/raw/opencellid/648.csv")
GADM_PATH = Path("data/raw/geo/gadm41_ZWE.gpkg")
MASTER_PATH = Path("data/processed/zwe_districts_master.csv")
OUT_DIR = Path("data/processed")
FIG_DIR = Path("outputs/figures")
OUT_DIR.mkdir(parents=True, exist_ok=True)
FIG_DIR.mkdir(parents=True, exist_ok=True)

if not RAW_PATH.exists():
    sys.exit(f"Missing {RAW_PATH}. Download MCC 648 from https://opencellid.org/downloads.php")
if not GADM_PATH.exists():
    sys.exit(f"Missing {GADM_PATH}. Download from https://geodata.ucdavis.edu/gadm/gadm4.1/gpkg/gadm41_ZWE.gpkg")

# --- Load ------------------------------------------------------------------
COLS = ['radio', 'mcc', 'net', 'area', 'cell', 'unit', 'lon', 'lat',
        'range_m', 'samples', 'changeable', 'created', 'updated', 'avg_signal']
towers = pd.read_csv(RAW_PATH, header=None, names=COLS)

NET_MAP = {4: 'NetOne', 1: 'Econet', 3: 'Telecel'}
towers['operator'] = towers['net'].map(NET_MAP).fillna('Other')

TECH_MAP = {'GSM': '2G', 'UMTS': '3G', 'LTE': '4G', 'NR': '5G', 'CDMA': '2G'}
towers['generation'] = towers['radio'].map(TECH_MAP).fillna('Unknown')

print(f"Loaded {len(towers):,} towers (MCC {towers['mcc'].iloc[0]})")
print(f"Technology: {towers['radio'].value_counts().to_dict()}")
print(f"Operator:   {towers['operator'].value_counts().to_dict()}")

# --- Spatial join to districts ---------------------------------------------
geometry = [Point(lon, lat) for lon, lat in zip(towers['lon'], towers['lat'])]
towers_gdf = gpd.GeoDataFrame(towers, geometry=geometry, crs="EPSG:4326")

districts = gpd.read_file(GADM_PATH, layer="ADM_ADM_2")
districts = districts.rename(columns={'NAME_2': 'district_name', 'NAME_1': 'province'})

joined = gpd.sjoin(towers_gdf, districts[['district_name', 'province', 'geometry']],
                   how='left', predicate='within')
matched = joined['district_name'].notna().sum()
print(f"Matched to districts: {matched:,} / {len(towers):,}")

# --- Aggregate per district ------------------------------------------------
agg = joined.dropna(subset=['district_name']).groupby('district_name').agg(
    total_towers=('cell', 'count'),
    towers_2g=('generation', lambda x: (x == '2G').sum()),
    towers_3g=('generation', lambda x: (x == '3G').sum()),
    towers_4g=('generation', lambda x: (x == '4G').sum()),
    econet=('operator', lambda x: (x == 'Econet').sum()),
    netone=('operator', lambda x: (x == 'NetOne').sum()),
    telecel=('operator', lambda x: (x == 'Telecel').sum()),
    avg_range_m=('range_m', 'mean'),
).reset_index()

# Merge population if available
if MASTER_PATH.exists():
    master = pd.read_csv(MASTER_PATH)
    agg = agg.merge(master[['district_name', 'province', 'district_population', 'urban_rural']],
                    on='district_name', how='left')
    agg['towers_per_10k'] = (agg['total_towers'] / agg['district_population'] * 10000).round(2)

agg = agg.sort_values('towers_per_10k' if 'towers_per_10k' in agg.columns else 'total_towers')

out_path = OUT_DIR / "opencellid_district_towers.csv"
agg.to_csv(out_path, index=False)
print(f"\nWrote {out_path}")

# --- National summary ------------------------------------------------------
summary = pd.DataFrame([{
    'total_towers': len(towers),
    'towers_gsm_2g': (towers['radio'] == 'GSM').sum(),
    'towers_umts_3g': (towers['radio'] == 'UMTS').sum(),
    'towers_lte_4g': (towers['radio'] == 'LTE').sum(),
    'pct_4g': round((towers['radio'] == 'LTE').sum() / len(towers) * 100, 2),
    'operators_econet': (towers['operator'] == 'Econet').sum(),
    'operators_netone': (towers['operator'] == 'NetOne').sum(),
    'operators_telecel': (towers['operator'] == 'Telecel').sum(),
    'districts_with_towers': agg['district_name'].nunique(),
}])
summary.to_csv(OUT_DIR / "opencellid_national_summary.csv", index=False)
print(f"Wrote {OUT_DIR / 'opencellid_national_summary.csv'}")

# --- Chart -----------------------------------------------------------------
fig, axes = plt.subplots(1, 2, figsize=(14, 6))

if 'towers_per_10k' in agg.columns and len(agg) > 0:
    plot_df = agg[agg['total_towers'] > 0].sort_values('towers_per_10k').tail(25)
    colors = ['#C00000' if ur == 'rural' else '#1F4E79'
              for ur in plot_df.get('urban_rural', ['?'] * len(plot_df))]
    axes[0].barh(plot_df['district_name'], plot_df['towers_per_10k'],
                 color=colors, edgecolor='white')
    axes[0].set_xlabel('Cell towers per 10,000 people')
    axes[0].set_title('Tower density by district\n(OpenCellID crowdsourced)', fontsize=11, fontweight='bold')
    axes[0].spines[['top', 'right']].set_visible(False)

tech_counts = towers['radio'].value_counts()
colors_pie = {'GSM': '#7F7F7F', 'UMTS': '#4F81BD', 'LTE': '#C00000'}
axes[1].pie(tech_counts.values, labels=[f"{t} ({TECH_MAP.get(t,t)})" for t in tech_counts.index],
            colors=[colors_pie.get(t, '#999') for t in tech_counts.index],
            autopct='%1.0f%%', startangle=90, textprops={'fontsize': 12})
axes[1].set_title(f'Zimbabwe towers by technology\n({len(towers):,} total)',
                  fontsize=11, fontweight='bold')

fig.text(0.02, -0.02,
         'Source: OpenCellID (MCC 648). Crowdsourced — biased toward NetOne. '
         'Use for relative density ranking, not absolute counts.',
         fontsize=8, color='#555555')
fig.tight_layout()
fig.savefig(FIG_DIR / "opencellid_tower_analysis.png", dpi=200, bbox_inches='tight')
plt.close()
print(f"Wrote {FIG_DIR / 'opencellid_tower_analysis.png'}")
