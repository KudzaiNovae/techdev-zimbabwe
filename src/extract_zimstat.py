"""
Extract district-level population projections from ZimStat.

Data source:
    ZimStat Population Projection by Districts
    Download from: https://www.zimstat.co.zw/ (SDMX data portal)
    Save as: data/raw/zimstat/Population_Projection_by_districts.csv

Run:
    python src/extract_zimstat.py

Output:
    data/processed/zimstat_district_population_2025.csv
    data/processed/zimstat_district_population_trend.csv

Coverage:
    The publicly available ZimStat SDMX dataset covers 42 districts across
    4 provinces (Manicaland, Mashonaland Central, Mashonaland East,
    Mashonaland West). The remaining provinces (Bulawayo, Harare,
    Masvingo, Matabeleland North, Matabeleland South, Midlands) are not
    included in this extract. For those districts the pipeline falls back
    to area-based population apportionment.
"""
import sys
from pathlib import Path
import pandas as pd

RAW_DIR = Path("data/raw/zimstat")
OUT_DIR = Path("data/processed")
OUT_DIR.mkdir(parents=True, exist_ok=True)

# Find the ZimStat CSV
candidates = list(RAW_DIR.glob("*opulation*roject*.csv")) + list(RAW_DIR.glob("*POP_PROJ*.csv"))
if not candidates:
    sys.exit(f"No ZimStat population CSV found in {RAW_DIR}/. "
             "Download from https://www.zimstat.co.zw/ and save there.")

path = candidates[0]
print(f"Reading {path} ...")
df = pd.read_csv(path)

# Province mapping from district codes
PROVINCE_MAP = {
    '1': 'Manicaland',
    '2': 'Mashonaland Central',
    '3': 'Mashonaland East',
    '4': 'Mashonaland West',
    '5': 'Matabeleland South',
    '6': 'Midlands',
    '7': 'Masvingo',
    '8': 'Matabeleland North',
    '9': 'Harare',
    '0': 'Bulawayo',
}

URBAN_KEYWORDS = [
    'Urban', 'Ruwa', 'Norton', 'Chinhoyi', 'Kadoma Urban',
    'Karoi', 'Mvurwi', 'Rusape', 'Bindura Urban', 'Marondera Urban',
    'Chegutu Urban', 'Kariba Urban', 'Chipinge Urban', 'Mutare Urban',
]

# === Total population by district, 2025 ===
total = df[
    (df['Age group'] == 'Total') &
    (df['Sex (DESC)'] == 'Total') &
    (df['TIME_PERIOD'] == 2025)
][['REF_AREA', 'Reference Area', 'Observation']].copy()
total.columns = ['district_code', 'district_name', 'population']
total['population'] = total['population'].round().astype(int)

# Sex breakdown
sex = df[
    (df['Age group'] == 'Total') &
    (df['TIME_PERIOD'] == 2025) &
    (df['Sex (DESC)'] != 'Total')
].pivot_table(index=['REF_AREA', 'Reference Area'],
              columns='Sex (DESC)', values='Observation', aggfunc='first').reset_index()
sex.columns = ['district_code', 'district_name', 'female_pop', 'male_pop']
sex[['female_pop', 'male_pop']] = sex[['female_pop', 'male_pop']].round().astype(int)

result = total.merge(sex, on=['district_code', 'district_name'])
result['female_pct'] = (result['female_pop'] / result['population'] * 100).round(1)

# Classify
result['urban_rural'] = result['district_name'].apply(
    lambda x: 'urban' if any(kw in x for kw in URBAN_KEYWORDS) else 'rural'
)
result['province_code'] = result['district_code'].str[3]
result['province'] = result['province_code'].map(PROVINCE_MAP)

result = result.sort_values('population', ascending=False).reset_index(drop=True)
out1 = OUT_DIR / 'zimstat_district_population_2025.csv'
result.to_csv(out1, index=False)
print(f"Wrote {out1}  ({len(result)} districts, total pop {result['population'].sum():,})")

# === Time series ===
trend = df[
    (df['Age group'] == 'Total') &
    (df['Sex (DESC)'] == 'Total')
][['REF_AREA', 'Reference Area', 'TIME_PERIOD', 'Observation']].copy()
trend.columns = ['district_code', 'district_name', 'year', 'population']
trend['population'] = trend['population'].round().astype(int)
out2 = OUT_DIR / 'zimstat_district_population_trend.csv'
trend.to_csv(out2, index=False)
print(f"Wrote {out2}  ({len(trend)} rows, years {trend['year'].min()}-{trend['year'].max()})")

# Summary
print(f"\nCoverage: {len(result)} districts across {result['province'].dropna().nunique()} provinces")
print(f"Provinces: {', '.join(sorted(result['province'].dropna().unique()))}")
urban = result[result['urban_rural'] == 'urban']
rural = result[result['urban_rural'] == 'rural']
print(f"Urban: {len(urban)} districts ({urban['population'].sum():,} people)")
print(f"Rural: {len(rural)} districts ({rural['population'].sum():,} people)")
