"""
Extract key tables from POTRAZ Q4 2025 Abridged Sector Performance Report.

This report is the freshest source for Zimbabwe-specific telecoms data (published
April 2026). Because the PDF tables are well-structured but small, we transcribe
them directly here rather than parse the PDF - this is more reliable and the data
is small enough to maintain manually for new quarters.

For future quarters, update the constants below from the new POTRAZ report.

Outputs (in ./data/processed/):
    potraz_q4_2025_base_stations.csv         Table 8: base stations by operator x technology
    potraz_q4_2025_base_stations_by_area.csv Table 9: urban vs rural base stations
    potraz_q4_2025_coverage.csv              Table 10: geographic and population coverage
    potraz_q4_2025_subscriptions.csv         Active mobile and internet subscriptions
    potraz_q4_2025_internet_tech.csv         Table 14: internet subscriptions by technology
    potraz_q4_2025_headlines.csv             Single-row summary of headline indicators
"""
from pathlib import Path
import pandas as pd

OUT_DIR = Path("data/processed")
OUT_DIR.mkdir(parents=True, exist_ok=True)

QUARTER = "Q4 2025"
REPORT_DATE = "2026-04-30"  # Published end of April 2026

# === Table 8: Base stations by operator x technology (Q4 2025) ===
base_stations = pd.DataFrame([
    {"operator": "Econet",  "technology": "2G",  "q3_2025": 2903, "q4_2025": 2981, "net_addition": 78},
    {"operator": "Econet",  "technology": "3G",  "q3_2025": 1919, "q4_2025": 1997, "net_addition": 78},
    {"operator": "Econet",  "technology": "LTE", "q3_2025": 1747, "q4_2025": 1825, "net_addition": 78},
    {"operator": "Econet",  "technology": "5G",  "q3_2025":  298, "q4_2025":  340, "net_addition": 42},
    {"operator": "NetOne",  "technology": "2G",  "q3_2025": 1459, "q4_2025": 1449, "net_addition": -10},
    {"operator": "NetOne",  "technology": "3G",  "q3_2025": 1600, "q4_2025": 1620, "net_addition": 20},
    {"operator": "NetOne",  "technology": "LTE", "q3_2025": 1654, "q4_2025": 1743, "net_addition": 89},
    {"operator": "NetOne",  "technology": "5G",  "q3_2025":   21, "q4_2025":   26, "net_addition": 5},
    {"operator": "Telecel", "technology": "2G",  "q3_2025":  671, "q4_2025":  671, "net_addition": 0},
    {"operator": "Telecel", "technology": "3G",  "q3_2025":  435, "q4_2025":  435, "net_addition": 0},
    {"operator": "Telecel", "technology": "LTE", "q3_2025":   17, "q4_2025":   17, "net_addition": 0},
    {"operator": "Telecel", "technology": "5G",  "q3_2025":    0, "q4_2025":    0, "net_addition": 0},
])

# === Table 9: Base stations by area (urban vs rural) ===
base_stations_area = pd.DataFrame([
    {"operator": "Econet",  "urban": 4886, "rural": 2257, "share_urban_pct": 58.01, "share_rural_pct": 48.22},
    {"operator": "NetOne",  "urban": 2678, "rural": 2160, "share_urban_pct": 31.79, "share_rural_pct": 46.14},
    {"operator": "Telecel", "urban":  859, "rural":  264, "share_urban_pct": 10.20, "share_rural_pct":  5.64},
    {"operator": "Total",   "urban": 8423, "rural": 4681, "share_urban_pct": 64.28, "share_rural_pct": 35.72},
])
# 64.28% urban vs 35.72% rural means: of ALL base stations, two-thirds are urban
# even though only ~40% of population is urban -> 1.6x infrastructure bias toward urban

# === Table 10: Geographic and Population Coverage ===
coverage = pd.DataFrame([
    {"technology": "2G",  "geographic_coverage_pct": 81.7, "pop_coverage_rural_pct": 79.0, "pop_coverage_urban_pct": 99.9},
    {"technology": "3G",  "geographic_coverage_pct": 75.4, "pop_coverage_rural_pct": 73.7, "pop_coverage_urban_pct": 99.9},
    {"technology": "LTE", "geographic_coverage_pct": 59.3, "pop_coverage_rural_pct": 29.0, "pop_coverage_urban_pct": 95.9},
    {"technology": "5G",  "geographic_coverage_pct": 15.9, "pop_coverage_rural_pct":  0.0, "pop_coverage_urban_pct": 18.9},
])
# CRITICAL FINDING: Rural 4G/LTE coverage is only 29% of population vs 95.9% urban
# This is a 67-point gap - much sharper than the 3G picture suggests

# === Active Mobile Subscriptions ===
mobile_subs = pd.DataFrame([
    {"operator": "Econet",  "q3_2025": 12064749, "q4_2025": 12374206, "change_pct":  2.56, "market_share_q4_pct": 73.75},
    {"operator": "NetOne",  "q3_2025":  4062894, "q4_2025":  4101492, "change_pct":  0.95, "market_share_q4_pct": 24.44},
    {"operator": "Telecel", "q3_2025":   305042, "q4_2025":   303284, "change_pct": -0.58, "market_share_q4_pct":  1.81},
    {"operator": "Total",   "q3_2025": 16432685, "q4_2025": 16778982, "change_pct":  2.11, "market_share_q4_pct":100.00},
])

# === Table 14: Internet/data subscriptions by technology ===
internet_tech = pd.DataFrame([
    {"technology": "Mobile Internet Subscriptions", "q3_2025": 12630975, "q4_2025": 12863731, "change_pct":  1.84},
    {"technology": "Fixed LTE",                     "q3_2025":   133958, "q4_2025":   143323, "change_pct":  6.99},
    {"technology": "Leased Lines",                  "q3_2025":     3433, "q4_2025":     3445, "change_pct":  0.35},
    {"technology": "DSL",                           "q3_2025":    89256, "q4_2025":    87713, "change_pct": -1.73},
    {"technology": "WiMAX",                         "q3_2025":     1503, "q4_2025":     1305, "change_pct":-13.17},
    {"technology": "CDMA",                          "q3_2025":      101, "q4_2025":       78, "change_pct":-22.77},
    {"technology": "VSAT (Starlink)",               "q3_2025":    50949, "q4_2025":    67057, "change_pct": 31.62},
    {"technology": "Active Fibre Subscriptions",    "q3_2025":    80272, "q4_2025":    86225, "change_pct":  7.42},
    {"technology": "Total",                         "q3_2025": 12990447, "q4_2025": 13252877, "change_pct":  2.02},
])
# Note: Starlink VSAT +31.6% in one quarter - fastest-growing technology in Zimbabwe

# === Headline indicators (single row summary) ===
headlines = pd.DataFrame([{
    "quarter":                          QUARTER,
    "report_date":                      REPORT_DATE,
    "active_mobile_subscriptions":      16778982,
    "mobile_penetration_pct":           107.04,
    "active_internet_subscriptions":    13252877,
    "internet_penetration_pct":         84.55,
    "broadband_penetration_pct":        82.63,
    "active_fixed_telephone_subs":      304383,
    "fixed_teledensity_pct":            1.942,
    "mobile_data_traffic_pb":           160.33,
    "fixed_data_traffic_pb":            479.94,
    "mno_revenue_zwg":                  7735011519,
    "mno_operating_costs_zwg":          4643955390,
    "mno_capex_zwg":                    1080614651,
    "mno_cost_to_income_ratio_pct":     59.95,
    "mno_arpu_zwg":                     460.99,
    "total_2g_base_stations":           5101,
    "total_3g_base_stations":           4052,
    "total_lte_base_stations":          3585,
    "total_5g_base_stations":           366,
    "total_urban_base_stations":        8423,
    "total_rural_base_stations":        4681,
    "rural_4g_population_coverage_pct": 29.0,
    "urban_4g_population_coverage_pct": 95.9,
    "rural_5g_population_coverage_pct": 0.0,
    "urban_5g_population_coverage_pct": 18.9,
    "estimated_population":             15675158,  # from ZIMSTAT projections cited in POTRAZ
}])

# === Top social media data usage (Table 6) ===
data_usage = pd.DataFrame([
    {"application": "WhatsApp", "traffic_mb": 33171887008, "share_pct": 20.69},
    {"application": "YouTube",  "traffic_mb": 15282603065, "share_pct":  9.53},
    {"application": "Facebook", "traffic_mb": 12649650064, "share_pct":  7.89},
    {"application": "X",        "traffic_mb":   647851067, "share_pct":  0.40},
    {"application": "Other",    "traffic_mb": 98576285378, "share_pct": 61.48},
])

# === Save everything ===
outputs = {
    "potraz_q4_2025_base_stations.csv":          base_stations,
    "potraz_q4_2025_base_stations_by_area.csv":  base_stations_area,
    "potraz_q4_2025_coverage.csv":               coverage,
    "potraz_q4_2025_subscriptions.csv":          mobile_subs,
    "potraz_q4_2025_internet_tech.csv":          internet_tech,
    "potraz_q4_2025_headlines.csv":              headlines,
    "potraz_q4_2025_data_usage.csv":             data_usage,
}

for fname, df in outputs.items():
    p = OUT_DIR / fname
    df.to_csv(p, index=False)
    print(f"Wrote {p}  ({len(df)} rows)")

# === Print the key insights ===
print()
print("=" * 70)
print("KEY INSIGHTS FROM POTRAZ Q4 2025 (for the slide deck)")
print("=" * 70)
print()
print("Coverage gap is much sharper than headline numbers suggest:")
print(f"  - Rural 4G/LTE population coverage:    29.0%")
print(f"  - Urban 4G/LTE population coverage:    95.9%")
print(f"  - RURAL-URBAN 4G GAP:                  66.9 percentage points")
print()
print(f"  - Rural 5G population coverage:         0.0%")
print(f"  - Urban 5G population coverage:        18.9%")
print()
print("Infrastructure is biased toward urban areas:")
print(f"  - Urban base stations:  {8423:,}  (64.28%)")
print(f"  - Rural base stations:  {4681:,}  (35.72%)")
print(f"  - But ~60% of population lives rurally - a 24-point underservicing gap")
print()
print("Telecel is collapsing (DDI implication: market increasingly duopolistic):")
print(f"  - Telecel rural base stations: 264 (5.64% of rural total)")
print(f"  - Telecel 5G/LTE rural presence: effectively zero")
print()
print("Starlink is the fastest-growing connectivity tech:")
print(f"  - VSAT subscriptions Q3 to Q4: +31.6%")
print(f"  - Starlink fixed data traffic Q3 to Q4: +42.8%")
print(f"  - Critical: this fills gaps where terrestrial networks don't reach")
