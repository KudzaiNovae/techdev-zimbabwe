"""
Compute the Digital Desert Index (DDI).

Stage 1: country-level DDI for Zimbabwe vs SADC peers (uses data we have today).
Stage 2: district-level DDI for Zimbabwe (needs ZimStat + POTRAZ + spatial join).

This script does Stage 1. Once you have a district-level master table with the
same column names, set INPUT_PATH to it and the same code computes district DDIs.

For Zimbabwe specifically, we override the coverage indicator with the latest
POTRAZ Q4 2025 figure (rural+urban population-weighted 4G coverage) since this
is far more current than the latest ITU value.

Run locally:
    python src/compute_ddi.py

Inputs (auto-located):
    data/raw/worldbank/wb_indicators_wide.csv     <- from extract_worldbank.py
    data/processed/itu_indicators_wide.csv        <- from extract_itu.py (optional)
    data/processed/potraz_q4_2025_headlines.csv   <- from extract_potraz.py (optional)

Outputs (in ./data/processed/):
    ddi_country.csv          DDI score per country, latest year
    ddi_country_long.csv     Sub-index breakdown for plotting
    ddi_summary.txt          Human-readable ranking
"""
import sys
from pathlib import Path
import pandas as pd
import numpy as np

# --- Config ----------------------------------------------------------------
WB_PATH      = Path("data/raw/worldbank/wb_indicators_wide.csv")
ITU_PATH     = Path("data/processed/itu_indicators_wide.csv")
POTRAZ_PATH  = Path("data/processed/potraz_q4_2025_headlines.csv")
OUT_DIR      = Path("data/processed")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Zimbabwe rural/urban population split (World Bank 2024):
#   Rural 60.11% | Urban 39.89%
ZWE_RURAL_SHARE = 0.6011
ZWE_URBAN_SHARE = 0.3989

# DDI configuration: equally-weighted four-pillar index
# Each pillar -> dict(value_col, transform, description)
# transform: how to map the raw value (0..) to a "gap score" (0..100, higher = worse)
PILLARS = {
    "coverage_gap": {
        # If we have ITU 4G coverage, use it. Else fall back to internet users as a coverage proxy.
        "primary_col":   "pop_covered_4g_pct",      # from ITU
        "fallback_col":  "wb_internet_users_pct",   # WB internet users %
        "transform":     "100_minus",               # gap = 100 - value
        "description":   "Population NOT covered by at least 4G (or proxy: not using internet)",
    },
    "adoption_gap": {
        "primary_col":   "internet_users_pct",      # ITU version
        "fallback_col":  "wb_internet_users_pct",   # WB version
        "transform":     "100_minus",
        "description":   "Population NOT using the internet",
    },
    "affordability_gap": {
        # Mobile data+voice basket as % of GNI per capita; UN target is 2%.
        # gap = min(100, value * 10)  ->  2% basket = 20 score; 10% basket = 100 score (max)
        "primary_col":   "basket_data_voice_low_pct_gni",
        "fallback_col":  None,    # no WB equivalent
        "transform":     "x10_cap100",
        "description":   "Mobile data+voice basket as % of GNI per capita, scaled (2% -> 20, >=10% -> 100)",
    },
    "electricity_gap": {
        # Unpowered towers don't transmit. Use rural electricity access.
        "primary_col":   "electricity_access_rural_pct",
        "fallback_col":  "electricity_access_pct",
        "transform":     "100_minus",
        "description":   "Rural population WITHOUT electricity access",
    },
}

COUNTRY_LABEL = {
    "ZWE": "Zimbabwe",  "ZMB": "Zambia",  "MOZ": "Mozambique",
    "MWI": "Malawi",    "BWA": "Botswana", "ZAF": "South Africa",
}


# --- Helpers ---------------------------------------------------------------
def apply_transform(value: float, transform: str) -> float:
    if pd.isna(value):
        return np.nan
    if transform == "100_minus":
        return max(0.0, min(100.0, 100.0 - float(value)))
    if transform == "x10_cap100":
        return max(0.0, min(100.0, float(value) * 10.0))
    raise ValueError(f"Unknown transform: {transform}")


def latest_value(df: pd.DataFrame, unit_col: str, value_col: str) -> pd.DataFrame:
    """Get the most recent non-null value per unit (country or district)."""
    if value_col not in df.columns:
        return pd.DataFrame(columns=[unit_col, "year", value_col])
    sub = df.dropna(subset=[value_col]).copy()
    if sub.empty:
        return pd.DataFrame(columns=[unit_col, "year", value_col])
    sub = sub.sort_values([unit_col, "year"])
    latest = sub.groupby(unit_col).tail(1)[[unit_col, "year", value_col]]
    return latest.rename(columns={"year": f"{value_col}_year"})


# --- Load -----------------------------------------------------------------
if not WB_PATH.exists():
    sys.exit(f"Missing {WB_PATH}. Run src/extract_worldbank.py first.")

print(f"Reading {WB_PATH} ...")
wb = pd.read_csv(WB_PATH)

unit_col = "country_iso3"

itu = None
if ITU_PATH.exists():
    print(f"Reading {ITU_PATH} ...")
    itu = pd.read_csv(ITU_PATH)
else:
    print(f"(ITU file not found at {ITU_PATH} - will use WB fallbacks where possible)")

# --- Build the indicator table (latest value per country per indicator) ----
needed_wb_cols = []
needed_itu_cols = []
for pillar, cfg in PILLARS.items():
    for c in (cfg["primary_col"], cfg["fallback_col"]):
        if c is None:
            continue
        if itu is not None and c in itu.columns:
            needed_itu_cols.append(c)
        elif c in wb.columns:
            needed_wb_cols.append(c)

needed_wb_cols  = sorted(set(needed_wb_cols))
needed_itu_cols = sorted(set(needed_itu_cols))

# Start with all countries present in WB data
countries = sorted(wb[unit_col].dropna().unique())
out = pd.DataFrame({unit_col: countries})

for col in needed_wb_cols:
    latest = latest_value(wb, unit_col, col)
    out = out.merge(latest, on=unit_col, how="left")

if itu is not None:
    for col in needed_itu_cols:
        latest = latest_value(itu, unit_col, col)
        out = out.merge(latest, on=unit_col, how="left")

# --- POTRAZ override for Zimbabwe coverage --------------------------------
# POTRAZ Q4 2025 reports rural 4G coverage at 29.0% and urban at 95.9%
# Compute population-weighted average using WB 2024 rural/urban shares
zwe_4g_potraz = None
zwe_3g_potraz = None
if POTRAZ_PATH.exists():
    potraz = pd.read_csv(POTRAZ_PATH)
    if not potraz.empty:
        r = potraz.iloc[0]
        rural_4g = r.get("rural_4g_population_coverage_pct", np.nan)
        urban_4g = r.get("urban_4g_population_coverage_pct", np.nan)
        if pd.notna(rural_4g) and pd.notna(urban_4g):
            zwe_4g_potraz = ZWE_RURAL_SHARE * rural_4g + ZWE_URBAN_SHARE * urban_4g
            print(f"\nPOTRAZ override: Zimbabwe 4G population coverage = "
                  f"{zwe_4g_potraz:.1f}%  "
                  f"(rural {rural_4g}% x {ZWE_RURAL_SHARE:.2f} + "
                  f"urban {urban_4g}% x {ZWE_URBAN_SHARE:.2f})")

# Inject into the indicator table for Zimbabwe
if zwe_4g_potraz is not None:
    col = "pop_covered_4g_pct"
    if col not in out.columns:
        out[col] = np.nan
        out[f"{col}_year"] = np.nan
    mask = out[unit_col] == "ZWE"
    out.loc[mask, col] = zwe_4g_potraz
    out.loc[mask, f"{col}_year"] = 2025

# --- Compute pillar scores -------------------------------------------------
pillar_rows = []
for unit in countries:
    row = out[out[unit_col] == unit].iloc[0]
    record = {unit_col: unit, "country_name": COUNTRY_LABEL.get(unit, unit)}
    for pillar, cfg in PILLARS.items():
        chosen_col = None
        chosen_year = None
        raw_val = np.nan
        # try primary, then fallback
        for candidate in (cfg["primary_col"], cfg["fallback_col"]):
            if candidate is None or candidate not in row.index:
                continue
            v = row.get(candidate, np.nan)
            if pd.notna(v):
                chosen_col = candidate
                chosen_year = row.get(f"{candidate}_year", np.nan)
                raw_val = v
                break
        gap = apply_transform(raw_val, cfg["transform"])
        record[f"{pillar}_raw"]     = raw_val
        record[f"{pillar}_source"]  = chosen_col
        record[f"{pillar}_year"]    = chosen_year
        record[f"{pillar}_score"]   = gap
    pillar_rows.append(record)

df = pd.DataFrame(pillar_rows)

# --- Composite DDI: average of available pillar scores --------------------
score_cols = [f"{p}_score" for p in PILLARS]
df["pillars_available"] = df[score_cols].notna().sum(axis=1)
df["ddi"] = df[score_cols].mean(axis=1, skipna=True).round(1)
df["ddi_rank"] = df["ddi"].rank(ascending=False, method="min").astype("Int64")

# --- Save ------------------------------------------------------------------
front = [unit_col, "country_name", "ddi", "ddi_rank", "pillars_available"]
df = df[front + [c for c in df.columns if c not in front]]
df = df.sort_values("ddi", ascending=False).reset_index(drop=True)

ddi_path = OUT_DIR / "ddi_country.csv"
df.to_csv(ddi_path, index=False)
print(f"\nDDI table -> {ddi_path}")

# Long format for charting (one row per country-pillar)
long_rows = []
for _, r in df.iterrows():
    for pillar in PILLARS:
        long_rows.append({
            "country_iso3": r[unit_col],
            "country_name": r["country_name"],
            "pillar":       pillar,
            "raw_value":    r[f"{pillar}_raw"],
            "score":        r[f"{pillar}_score"],
            "source":       r[f"{pillar}_source"],
            "year":         r[f"{pillar}_year"],
        })
long_df = pd.DataFrame(long_rows)
long_path = OUT_DIR / "ddi_country_long.csv"
long_df.to_csv(long_path, index=False)
print(f"Long table -> {long_path}")

# --- Human-readable summary ------------------------------------------------
lines = []
lines.append("=" * 72)
lines.append("DIGITAL DESERT INDEX - Country comparison (higher = worse)")
lines.append("=" * 72)
lines.append("")
lines.append(f"{'Rank':<5}{'Country':<18}{'DDI':>7}  {'Coverage':>9}{'Adoption':>10}{'Afford.':>9}{'Power':>8}")
lines.append("-" * 72)
for _, r in df.iterrows():
    name = r["country_name"]
    ddi = r["ddi"]
    cov = r["coverage_gap_score"]
    ado = r["adoption_gap_score"]
    aff = r["affordability_gap_score"]
    ele = r["electricity_gap_score"]
    def fmt(x):
        return f"{x:>8.1f}" if pd.notna(x) else f"{'  n/a':>8}"
    lines.append(f"{int(r['ddi_rank']):<5}{name:<18}{ddi:>7.1f}  "
                 f"{fmt(cov):>8}{fmt(ado):>10}{fmt(aff):>9}{fmt(ele):>8}")

lines.append("")
lines.append("Pillars (each 0-100, higher = worse gap):")
for pillar, cfg in PILLARS.items():
    lines.append(f"  - {pillar}: {cfg['description']}")
lines.append("")
lines.append("DDI = unweighted mean of available pillars.")
lines.append("")

# Per-country detail
lines.append("=" * 72)
lines.append("Per-country detail")
lines.append("=" * 72)
for _, r in df.iterrows():
    lines.append("")
    lines.append(f"  {r['country_name']} ({r[unit_col]})  -  DDI {r['ddi']}  (rank {int(r['ddi_rank'])})")
    for pillar in PILLARS:
        raw = r[f"{pillar}_raw"]
        score = r[f"{pillar}_score"]
        src = r[f"{pillar}_source"]
        yr  = r[f"{pillar}_year"]
        if pd.isna(raw):
            lines.append(f"    {pillar:<22} NO DATA")
        else:
            yr_str = "" if pd.isna(yr) else f", {int(yr)}"
            lines.append(f"    {pillar:<22} raw={raw:.2f}  score={score:.1f}  "
                         f"(source: {src}{yr_str})")

summary = "\n".join(lines)
summary_path = OUT_DIR / "ddi_summary.txt"
summary_path.write_text(summary, encoding="utf-8")

print("\n" + summary)
print(f"\nSummary -> {summary_path}")
