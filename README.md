# TECHDEV-ZIMBABWE: Mapping Zimbabwe's Digital Deserts

**ITU Data Hackathon 2026 — Stage 2 Submission**

An open, reproducible data pipeline that identifies, measures, and visualises
coverage, quality, and affordability gaps in connectivity across Zimbabwe using
ITU DataHub indicators, POTRAZ sector data, and World Bank socio-economic
indicators. The core output is a **Digital Desert Index (DDI)** — a composite
score per district that makes digital exclusion visible and measurable.

---

## Prerequisites

- **Python 3.10+** with pip
- ~500 MB disk space for data and outputs
- Internet access (for World Bank API and GADM download)

Install dependencies:

```bash
pip install wbdata pandas matplotlib geopandas
```

---

## Reproduction steps (start to finish)

Follow these steps in order. Every command is run from the repository root.
At the end you will have all figures, CSVs, and the district-level GeoPackage
used in the submission.

### Step 1: Pull World Bank data (automated, ~1 minute)

```bash
python src/extract_worldbank.py
```

**What it does:** Connects to the World Bank API via the `wbdata` library and
pulls 25 indicators for 6 countries (Zimbabwe, Zambia, Mozambique, Malawi,
Botswana, South Africa), 2010–latest. Pulls one indicator at a time so a
single failure doesn't kill the run.

**Indicators pulled:**

| Tier | Indicator | WB Code |
|---|---|---|
| Core | GNI per capita (USD, PPP) | NY.GNP.PCAP.CD, NY.GNP.PCAP.PP.CD |
| Core | GDP per capita | NY.GDP.PCAP.CD |
| Core | Poverty headcount (national, $2.15/day) | SI.POV.NAHC, SI.POV.DDAY |
| Core | Gini index | SI.POV.GINI |
| Core | Population, rural/urban split | SP.POP.TOTL, SP.RUR.TOTL.ZS, SP.URB.TOTL.IN.ZS |
| Core | Electricity access (total, rural, urban) | EG.ELC.ACCS.ZS, .RU.ZS, .UR.ZS |
| Tier 2 | Literacy, secondary enrolment, education spending | SE.ADT.LITR.ZS, SE.SEC.ENRR, SE.XPD.TOTL.GD.ZS |
| Tier 2 | Physicians, health spending | SH.MED.PHYS.ZS, SH.XPD.CHEX.GD.ZS |
| Tier 2 | Account ownership (total, male, female) | FX.OWN.TOTL.ZS, .MA.ZS, .FE.ZS |
| Tier 2 | Female labour force participation | SL.TLF.CACT.FE.ZS |
| Cross-check | Mobile subs, internet users, fixed broadband | IT.CEL.SETS.P2, IT.NET.USER.ZS, IT.NET.BBND.P2 |
| Context | Agriculture as % of GDP | NV.AGR.TOTL.ZS |

**Output:**
- `data/raw/worldbank/wb_indicators_wide.csv` (one row per country-year)
- `data/raw/worldbank/wb_indicators_long.csv` (one row per country-year-indicator)
- `data/raw/worldbank/wb_zimbabwe_summary.csv` (latest value per indicator)

### Step 2: Process POTRAZ Q4 2025 data (~5 seconds)

```bash
python src/extract_potraz.py
```

**What it does:** The POTRAZ Q4 2025 Abridged Sector Performance Report
(published April 2026) is a 28-page PDF. Rather than using PDF parsing
libraries (which are brittle on POTRAZ's table formatting), we transcribed
the seven key tables directly into the script as Python dictionaries. This
is more reliable for small, well-defined tables and allows us to add inline
comments documenting each figure's context.

**Tables transcribed:**

| Table | Description | Key finding |
|---|---|---|
| Table 8 | Base stations by operator × technology (2G/3G/LTE/5G) | 366 total 5G base stations, all urban |
| Table 9 | Base stations by area (urban vs rural) | 64.3% urban, 35.7% rural |
| Table 10 | Geographic and population coverage by technology | Rural LTE = 29.0%, Urban LTE = 95.9% |
| Table 1 | Active mobile subscriptions by operator | Econet 73.75%, NetOne 24.44%, Telecel 1.81% |
| Table 14 | Internet/data subscriptions by technology | Starlink VSAT +31.6% QoQ |
| Table 6 | Data usage by application | WhatsApp 20.69%, YouTube 9.53% |
| Headlines | Aggregate indicators | 107.04% mobile penetration, 84.55% internet penetration |

**Output:** `data/processed/potraz_q4_2025_*.csv` (7 files)

### Step 3: Download and process ITU DataHub CSVs (~30 minutes manual + ~10 seconds processing)

ITU DataHub (datahub.itu.int) has no public bulk-download API. You must
download CSVs manually from the web interface.

**3a. Manual download:**

1. Go to https://datahub.itu.int/data/
2. For each indicator below, select all countries (or filter to Zimbabwe +
   Zambia + Mozambique + Malawi + Botswana + South Africa) and all available
   years, then click "Download CSV"
3. Save each CSV into `data/raw/itu/` with the filename shown

| Filename to save as | ITU DataHub indicator to search for |
|---|---|
| `itu_3g_coverage.csv` | Population coverage, by mobile network technology → filter "At least 3G" |
| `itu_4g_coverage.csv` | Population coverage, by mobile network technology → filter "At least LTE/WiMAX" |
| `itu_5g_coverage.csv` | Population coverage, by mobile network technology → filter "At least 5G" |
| `itu_mobile_subs.csv` | Mobile-cellular subscriptions |
| `itu_mobile_broadband.csv` | Active mobile-broadband subscriptions |
| `itu_fixed_broadband.csv` | Fixed-broadband subscriptions |
| `itu_internet_users.csv` | Individuals using the Internet |
| `itu_basket_data_voice_low.csv` | Mobile broadband data and voice low-consumption basket total (70 min, 50 SMS, 1 GB) |
| `itu_basket_data_voice_high.csv` | Mobile broadband data and voice high-consumption basket total (140 min, 20 SMS, 5 GB) |
| `itu_basket_data_only.csv` | Data-only mobile broadband basket 5 GB |
| `itu_basket_fixed_bb.csv` | Fixed-broadband Internet 5GB |
| `itu_intl_bandwidth.csv` | International bandwidth usage |

**Note:** ITU may export these as a single CSV with all technologies or
separate files. The script auto-detects column names (it looks for columns
containing "iso", "year"/"time", and "value"/"observation") so it handles
both formats. If the download gives you a different filename, you can either
rename it or add the filename to the `INDICATOR_FILES` dict in the script.

**Note on affordability series:** ITU publishes three variants of each
basket (seriesCode ending in `$` = USD value, `_GNI` = % of GNI per capita,
`_PPP` = PPP-adjusted). The script prefers `_GNI` where available. For
Zimbabwe, the data+voice baskets only have the `$` variant — the DDI
script converts these to % of GNI using the World Bank GNI figure.

**3b. Process:**

```bash
python src/extract_itu.py
```

**Output:**
- `data/processed/itu_indicators_wide.csv` (one row per country, all indicators as columns)
- `data/processed/itu_indicators_long.csv`
- `data/processed/itu_zimbabwe_summary.csv`

### Step 4: Compute the Digital Desert Index (~2 seconds)

```bash
python src/compute_ddi.py
```

**What it does:** Computes the DDI for each country in the dataset. The DDI
is an equally-weighted composite of four sub-pillars, each scaled 0–100
(higher = worse):

```
DDI = mean(coverage_gap, adoption_gap, affordability_gap, electricity_gap)
```

**Sub-pillar formulas:**

| Pillar | Formula | Source preference |
|---|---|---|
| Coverage gap | `100 - pop_covered_4g_pct` | ITU → POTRAZ override for ZWE → WB internet users (fallback) |
| Adoption gap | `100 - internet_users_pct` | ITU → WB internet users |
| Affordability gap | `min(100, basket_data_voice_low_pct_gni × 10)` | ITU basket (GNI series) → ITU basket (USD, converted) |
| Electricity gap | `100 - electricity_access_rural_pct` | WB rural electricity |

**Zimbabwe-specific override:** The script detects POTRAZ Q4 2025 data
(if `data/processed/potraz_q4_2025_headlines.csv` exists) and computes a
population-weighted 4G coverage figure: `rural_4g × 0.6011 + urban_4g × 0.3989`
= 29.0 × 0.6011 + 95.9 × 0.3989 = 55.69%. This replaces the ITU figure
(51.6%) for Zimbabwe only, since POTRAZ is more current.

**Output:**
- `data/processed/ddi_country.csv` — DDI + sub-pillars per country
- `data/processed/ddi_country_long.csv` — one row per country-pillar (for charting)
- `data/processed/ddi_summary.txt` — human-readable ranking

### Step 5: Generate country-level charts (~5 seconds)

```bash
python src/make_figures.py
python src/make_figures_zwe.py
```

**Output (in `outputs/figures/`):**
- `ddi_country_ranking.png` — horizontal bar chart, DDI by country
- `ddi_pillar_breakdown.png` — grouped bars, four pillars per country
- `zwe_rural_urban_coverage_gap.png` — the 67-point LTE gap chart
- `zwe_base_station_distribution.png` — urban/rural infrastructure bias
- `zwe_internet_tech_mix.png` — Starlink +31.6% growth story
- `itu_fixed_bb_affordability_trend.png` — 2018–2025 time series

### Step 6: Download GADM boundaries (once, ~30 seconds)

```bash
mkdir -p data/raw/geo
wget https://geodata.ucdavis.edu/gadm/gadm4.1/gpkg/gadm41_ZWE.gpkg -P data/raw/geo/
```

Alternative (shapefile):
```bash
wget https://geodata.ucdavis.edu/gadm/gadm4.1/shp/gadm41_ZWE_shp.zip -P data/raw/geo/
```

### Step 7: Build the district-level master table (~10 seconds)

```bash
python src/build_district_table.py
```

**What it does:** Reads the GADM GeoPackage (ADM_ADM_2 layer = districts),
classifies each district as urban or rural, applies POTRAZ rural/urban
coverage figures, apportions base stations by population weight within each
class, and computes the district-level DDI using the same four-pillar formula.

**Output:**
- `data/processed/zwe_districts_master.gpkg` — GeoPackage (geometry + indicators)
- `data/processed/zwe_districts_master.csv` — flat CSV

### Step 8: Generate district choropleth maps (~10 seconds)

```bash
python src/make_district_map.py
```

**Output:**
- `outputs/figures/zwe_district_ddi_map.png` — districts coloured by DDI
- `outputs/figures/zwe_district_coverage_map.png` — districts coloured by 4G coverage gap

---

## Directory layout

```
techdev-zimbabwe/
├── README.md                           ← This file
├── src/
│   ├── extract_worldbank.py            ← Step 1: World Bank API pull
│   ├── extract_potraz.py               ← Step 2: POTRAZ Q4 2025 table transcription
│   ├── extract_itu.py                  ← Step 3: ITU DataHub CSV processor
│   ├── extract_zimstat.py              ← Step 4: ZimStat 2022 Census processing
│   ├── compute_ddi.py                  ← Step 5: DDI computation
│   ├── make_figures.py                 ← Step 6a: SADC comparison charts
│   ├── make_figures_zwe.py             ← Step 6b: Zimbabwe-specific charts
│   ├── build_district_table.py         ← Step 7: district-level master table
│   ├── make_district_map.py            ← Step 8: choropleth maps
│   └── extract_opencellid.py           ← Step 9: OpenCellID tower analysis
├── dashboard/
│   └── app.py                          ← Streamlit interactive dashboard
├── data/
│   ├── raw/
│   │   ├── worldbank/                  ← Output of Step 1
│   │   ├── itu/                        ← Where YOU put downloaded ITU CSVs (Step 3)
│   │   ├── zimstat/                    ← Census Excel + ICT Index PDFs
│   │   ├── opencellid/                 ← MCC 648 tower CSV
│   │   └── geo/                        ← Where YOU put GADM download
│   └── processed/                      ← Output of Steps 2-5, 7, 9
└── outputs/
    └── figures/                        ← Output of Steps 6, 8
```

---

## DDI methodology

### Definition

The Digital Desert Index (DDI) is a composite indicator that quantifies
digital exclusion along four dimensions: coverage, adoption, affordability,
and enabling infrastructure (electricity). It produces a score from 0
(fully connected) to 100 (completely excluded) for any geographic unit
(country or district).

### Design principles

1. **Simplicity over sophistication.** Four pillars, equal weights, arithmetic
   mean. No black-box models or subjective expert weights.
2. **Reproducibility.** Every input is publicly available. The code is open.
   Running the same scripts on the same data produces the same numbers.
3. **Source layering.** ITU DataHub is the primary spine (required by the
   hackathon). POTRAZ provides the freshest Zimbabwe-specific data. World
   Bank provides socio-economic context. Each source is documented and
   its contribution to the DDI is traceable.
4. **Graceful degradation.** If a data source is unavailable, the DDI still
   computes using available pillars (minimum 3 of 4) and flags missing data.

### Pillar definitions

| Pillar | Raw indicator | Gap formula | Score range | Scale rationale |
|---|---|---|---|---|
| Coverage | % pop with 4G/LTE | 100 − value | 0 (100% covered) to 100 (0% covered) | Direct inversion |
| Adoption | % individuals using internet | 100 − value | 0 (everyone online) to 100 (nobody online) | Direct inversion |
| Affordability | Basket price as % of GNI p.c. | min(100, value × 10) | 0 (free) to 100 (≥10% of GNI) | UN target of 2% maps to score 20 |
| Electricity | % rural pop with electricity | 100 − value | 0 (universal access) to 100 (no access) | Direct inversion |

### Composite

```
DDI = (coverage_gap + adoption_gap + affordability_gap + electricity_gap) / 4
```

Equal weights are used because: (a) no empirical basis exists for preferring
one pillar over another in the Zimbabwean context; (b) equal weights are
transparent and reproducible; (c) we tested alternative weights (coverage ×2,
affordability ×2) and found the country ranking is robust — Zimbabwe stays
4th out of 6 under all tested schemes.

### Known limitations

- **District-level DDI is currently binary** (urban vs rural) because POTRAZ
  publishes coverage at the national rural/urban level, not per district.
  ZimStat district populations (available for 4 of 10 provinces) and
  OpenCellID tower density provide partial district-level variance.
- **ZimStat coverage is partial.** Population projections cover 42 districts
  across Manicaland, Mashonaland Central, East and West. The remaining 6
  provinces (Bulawayo, Harare, Masvingo, Matabeleland North/South, Midlands)
  use area-based population apportionment.
- **Affordability pillar uses national GNI,** not district income. This
  understates affordability barriers in poorer districts.
- **No measured quality pillar.** The DDI uses electricity access as a proxy
  for real-world network availability rather than measured speed data. The
  electricity pillar captures "can the tower stay powered?" which is a
  binding constraint in rural Zimbabwe.
- **OpenCellID is crowdsourced** with 99% NetOne bias. Used for relative
  district-level ranking, not absolute counts.

---

## Data sources and licences

| Source | Licence | Access | Citation |
|---|---|---|---|
| ITU DataHub | CC BY-NC-SA 3.0 IGO | datahub.itu.int | Cite with indicator name + access date |
| POTRAZ Q4 2025 Report | Public sector | potraz.gov.zw | "POTRAZ, Postal & Telecommunications Abridged Sector Performance Report, Q4 2025" |
| World Bank Open Data | CC BY-4.0 | data.worldbank.org | "World Bank, World Development Indicators" |
| ZimStat | Public sector | zimstat.co.zw | "ZimStat, Population Projection by Districts" |
| OpenCellID | CC BY-SA 4.0 | opencellid.org | "OpenCellID, MCC 648" |
| GADM 4.1 | Free for non-commercial academic use | gadm.org | "GADM version 4.1" |

---

## Future iterations

| Enhancement | Data needed | Impact |
|---|---|---|
| ZimStat full coverage | Remaining 6 provinces from ZimStat portal | Real populations for all 66 districts |
| POTRAZ provincial base stations | Provincial breakdown (if published) | Province-level DDI variation |
| Measured quality data | ITU QoS indicators or operator speed reports | Fifth DDI pillar: quality gap |
| Streamlit dashboard | (uses existing data) | Interactive exploration for policymakers |

---

## Contact

Team TECHDEV-ZIMBABWE — ITU Data Hackathon 2026
