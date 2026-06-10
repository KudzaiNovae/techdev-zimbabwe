"""
Extract World Bank indicators for Zimbabwe + SADC peers.

Run locally:
    pip install wbdata pandas
    python extract_worldbank.py

Output (in ./data/raw/worldbank/):
    wb_indicators_wide.csv   one row per country-year, indicators as columns
    wb_indicators_long.csv   one row per country-year-indicator (good for plotting)
    wb_zimbabwe_summary.csv  latest value per indicator for Zimbabwe (quick QA)
"""
import sys
from pathlib import Path
import pandas as pd

try:
    import wbdata
except ImportError:
    sys.exit("Install dependencies first:  pip install wbdata pandas")

# --- Config ----------------------------------------------------------------
OUT_DIR = Path("data/raw/worldbank")
OUT_DIR.mkdir(parents=True, exist_ok=True)

COUNTRIES = ["ZWE", "ZMB", "MOZ", "MWI", "BWA", "ZAF"]
COUNTRY_NAMES = {
    "ZWE": "Zimbabwe", "ZMB": "Zambia", "MOZ": "Mozambique",
    "MWI": "Malawi",   "BWA": "Botswana", "ZAF": "South Africa",
}

# Indicator code -> human-readable short name
INDICATORS = {
    # --- Tier 1: Core (income, poverty, population, electricity) ---
    "NY.GNP.PCAP.CD":     "gni_per_capita_usd",
    "NY.GNP.PCAP.PP.CD":  "gni_per_capita_ppp",
    "NY.GDP.PCAP.CD":     "gdp_per_capita_usd",
    "SI.POV.NAHC":        "poverty_headcount_natl_pct",
    "SI.POV.DDAY":        "poverty_215_ppp_pct",
    "SI.POV.GINI":        "gini_index",
    "SP.POP.TOTL":        "population_total",
    "SP.RUR.TOTL.ZS":     "rural_population_pct",
    "SP.URB.TOTL.IN.ZS":  "urban_population_pct",
    "EG.ELC.ACCS.ZS":     "electricity_access_pct",
    "EG.ELC.ACCS.RU.ZS":  "electricity_access_rural_pct",
    "EG.ELC.ACCS.UR.ZS":  "electricity_access_urban_pct",

    # --- Tier 2: Human impact (education, health, finance) ---
    "SE.ADT.LITR.ZS":     "literacy_adult_pct",
    "SE.SEC.ENRR":        "secondary_enrolment_gross_pct",
    "SE.XPD.TOTL.GD.ZS":  "gov_education_exp_pct_gdp",
    "SH.MED.PHYS.ZS":     "physicians_per_1000",
    "SH.XPD.CHEX.GD.ZS":  "health_exp_pct_gdp",
    "FX.OWN.TOTL.ZS":     "account_ownership_pct",
    "FX.OWN.TOTL.MA.ZS":  "account_ownership_male_pct",
    "FX.OWN.TOTL.FE.ZS":  "account_ownership_female_pct",
    "SL.TLF.CACT.FE.ZS":  "labour_force_female_pct",

    # --- Tier 3: Cross-check vs ITU + context ---
    "IT.CEL.SETS.P2":     "wb_mobile_subs_per_100",
    "IT.NET.USER.ZS":     "wb_internet_users_pct",
    "IT.NET.BBND.P2":     "wb_fixed_broadband_per_100",
    "NV.AGR.TOTL.ZS":     "agriculture_pct_gdp",
}

# --- Fetch -----------------------------------------------------------------
print(f"Fetching {len(INDICATORS)} indicators for {len(COUNTRIES)} countries...")
print(f"Countries: {', '.join(COUNTRIES)}")
print()

# Pull one indicator at a time so one failure doesn't kill the whole run.
frames = []
failed = []
for code, name in INDICATORS.items():
    try:
        s = wbdata.get_series(code, country=COUNTRIES)
        df = s.reset_index()
        df.columns = ["country_name", "year", name]
        frames.append(df)
        print(f"  OK   {code:25s} -> {name}")
    except Exception as e:
        failed.append((code, name, str(e)[:80]))
        print(f"  FAIL {code:25s} -> {e!s:.80}")

if not frames:
    sys.exit("No indicators fetched. Check your network and retry.")

# --- Merge -----------------------------------------------------------------
df = frames[0]
for f in frames[1:]:
    df = df.merge(f, on=["country_name", "year"], how="outer")

# Country name -> ISO3
name_to_iso = {v: k for k, v in COUNTRY_NAMES.items()}
df["country_iso3"] = df["country_name"].map(name_to_iso)

df["year"] = df["year"].astype(int)
df = df[df["year"] >= 2010].copy()

front = ["country_iso3", "country_name", "year"]
df = df[front + [c for c in df.columns if c not in front]]
df = df.sort_values(["country_iso3", "year"]).reset_index(drop=True)

# --- Save ------------------------------------------------------------------
wide_path = OUT_DIR / "wb_indicators_wide.csv"
df.to_csv(wide_path, index=False)
print(f"\nWIDE  -> {wide_path}  ({len(df)} rows x {len(df.columns)} cols)")

indicator_cols = [c for c in df.columns if c not in front]
long_df = (df.melt(id_vars=front, value_vars=indicator_cols,
                   var_name="indicator", value_name="value")
             .dropna(subset=["value"])
             .reset_index(drop=True))
long_path = OUT_DIR / "wb_indicators_long.csv"
long_df.to_csv(long_path, index=False)
print(f"LONG  -> {long_path}  ({len(long_df)} rows)")

# Zimbabwe quick summary
zwe = df[df["country_iso3"] == "ZWE"]
summary_rows = []
for col in indicator_cols:
    non_null = zwe.dropna(subset=[col])
    if len(non_null):
        latest = non_null.iloc[-1]
        summary_rows.append({"indicator": col, "latest_year": int(latest["year"]),
                             "latest_value": latest[col]})
    else:
        summary_rows.append({"indicator": col, "latest_year": None,
                             "latest_value": None})
summary_df = pd.DataFrame(summary_rows)
summary_path = OUT_DIR / "wb_zimbabwe_summary.csv"
summary_df.to_csv(summary_path, index=False)

print(f"\nZimbabwe latest values:")
print(summary_df.to_string(index=False))

if failed:
    print(f"\n{len(failed)} indicator(s) failed:")
    for code, name, err in failed:
        print(f"  {code} ({name}): {err}")
