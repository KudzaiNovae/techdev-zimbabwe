"""
Process ITU DataHub CSVs — auto-detects any CSV in data/raw/itu/.

Scans all CSV files in the ITU directory, identifies their indicator type
from the seriesCode/seriesName columns, extracts SADC country data, and
merges into a single wide table.

No renaming of downloaded files needed — drop them in data/raw/itu/ and run.
"""
import sys
from pathlib import Path
import pandas as pd
import numpy as np

RAW_DIR = Path("data/raw/itu")
OUT_DIR = Path("data/processed")
OUT_DIR.mkdir(parents=True, exist_ok=True)

COUNTRIES_KEEP = ["ZWE", "ZMB", "MOZ", "MWI", "BWA", "ZAF"]
GNI_MAP = {"ZWE": 2400, "ZMB": 1500, "MOZ": 600, "MWI": 640, "BWA": 7800, "ZAF": 7000}

# seriesCode prefix -> output column name
SERIES_MAP = {
    "i271GA":           "pop_covered_4g_pct",
    "i271G_":           "pop_covered_3g_pct",      # i271G but not i271GA
    "i271pop":          "pop_covered_2g_pct",
    "i271G5":           "pop_covered_5g_pct",
    "i271":             "mobile_subs_total",        # plain i271 = total subs
    "i911":             "mobile_subs_per_100",
    "i271mb_low_1GB":   "basket_data_voice_low_pct_gni",
    "i271mb_high_5GB":  "basket_data_voice_high_pct_gni",
    "i271mb_5GB":       "basket_data_only_pct_gni",
    "i154_FBB5":        "basket_fixed_bb_pct_gni",
    "i4214":            "intl_bandwidth_mbps",
    "i994":             "intl_bandwidth_per_user",
}


def identify_series(series_code):
    """Map a seriesCode to our output column name."""
    if pd.isna(series_code):
        return None
    sc = str(series_code).strip()
    # Try exact prefixes, longest first
    for prefix in sorted(SERIES_MAP.keys(), key=len, reverse=True):
        if sc.startswith(prefix):
            return SERIES_MAP[prefix]
    return None


def prefer_gni_series(df, iso):
    """For affordability, prefer _GNI series. Fallback to $ with conversion."""
    gni_rows = df[df["seriesCode"].str.contains("GNI", na=False)]
    if len(gni_rows):
        return float(gni_rows.sort_values("dataYear").iloc[-1]["dataValue"])
    usd_rows = df[df["seriesCode"].str.endswith("$", na=False)]
    if len(usd_rows) and iso in GNI_MAP:
        usd = float(usd_rows.sort_values("dataYear").iloc[-1]["dataValue"])
        return round(usd / (GNI_MAP[iso] / 12) * 100, 2)
    # Last resort: any row
    if len(df):
        return float(df.sort_values("dataYear").iloc[-1]["dataValue"])
    return np.nan


print(f"Scanning {RAW_DIR}/ for ITU CSV files...")

all_csvs = list(RAW_DIR.glob("*.csv"))
if not all_csvs:
    sys.exit(f"No CSV files found in {RAW_DIR}/. Download from datahub.itu.int.")

print(f"Found {len(all_csvs)} CSV files")

# Load and tag all rows
all_rows = []
for csv_path in all_csvs:
    try:
        df = pd.read_csv(csv_path)
    except Exception as e:
        print(f"  ✗ {csv_path.name}: {e}")
        continue
    if "entityIso" not in df.columns or "seriesCode" not in df.columns:
        print(f"  ⊘ {csv_path.name}: not an ITU format (missing entityIso/seriesCode)")
        continue
    df["dataValue"] = pd.to_numeric(df.get("dataValue"), errors="coerce")
    df["dataYear"] = pd.to_numeric(df.get("dataYear"), errors="coerce")
    sadc = df[df["entityIso"].isin(COUNTRIES_KEEP)].copy()
    if len(sadc):
        codes = sadc["seriesCode"].unique()
        print(f"  ✓ {csv_path.name}: {len(sadc)} SADC rows, codes={list(codes)[:3]}")
        all_rows.append(sadc)

if not all_rows:
    sys.exit("No SADC data found in any CSV.")

combined = pd.concat(all_rows, ignore_index=True)

# Build wide table: one row per country, latest value per indicator
result_rows = []
for iso in COUNTRIES_KEEP:
    country_data = combined[combined["entityIso"] == iso]
    row = {"country_iso3": iso, "country_name": country_data["entityName"].iloc[0] if len(country_data) else iso}
    
    for sc_prefix, col_name in SERIES_MAP.items():
        mask = country_data["seriesCode"].str.startswith(sc_prefix, na=False)
        sub = country_data[mask].dropna(subset=["dataValue"])
        if len(sub) == 0:
            continue
        
        if "basket" in col_name or "affordability" in col_name.lower():
            row[col_name] = prefer_gni_series(sub, iso)
        else:
            latest = sub.sort_values("dataYear").iloc[-1]
            row[col_name] = float(latest["dataValue"])
            row[f"{col_name}_year"] = int(latest["dataYear"])
    
    result_rows.append(row)

wide = pd.DataFrame(result_rows)
wide["year"] = 2024  # reference year

out_path = OUT_DIR / "itu_indicators_wide.csv"
wide.to_csv(out_path, index=False)
print(f"\nWrote {out_path} ({len(wide)} rows × {len(wide.columns)} cols)")

# Zimbabwe summary
zwe = wide[wide["country_iso3"] == "ZWE"]
if len(zwe):
    print("\nZimbabwe ITU indicators:")
    for col in [c for c in wide.columns if c not in ["country_iso3", "country_name", "year"] and not c.endswith("_year")]:
        val = zwe[col].iloc[0]
        if pd.notna(val):
            print(f"  {col:<40} {val:>10.2f}")
