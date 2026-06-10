#!/usr/bin/env python3
"""
TECHDEV-ZIMBABWE: Run the entire data pipeline end-to-end.

This script orchestrates all steps in the correct order, checks for
prerequisites, and reports what succeeded and what needs manual action.

Usage:
    python run_all.py           # Run everything possible
    python run_all.py --check   # Just check prerequisites, don't run

Prerequisites you must handle manually before running:
    1. pip install wbdata pandas matplotlib geopandas
    2. Download ITU CSVs from datahub.itu.int -> data/raw/itu/
    3. Download GADM 4.1 -> data/raw/geo/gadm41_ZWE.gpkg
    4. Download OpenCellID MCC 648 -> data/raw/opencellid/648.csv
"""
import subprocess
import sys
from pathlib import Path
import argparse
import time

ROOT = Path(__file__).parent
SRC = ROOT / "src"
DATA_RAW = ROOT / "data" / "raw"
DATA_PROC = ROOT / "data" / "processed"
OUTPUTS = ROOT / "outputs" / "figures"

# Pipeline steps in execution order
STEPS = [
    {
        "name": "World Bank extraction",
        "script": "extract_worldbank.py",
        "requires": [],
        "produces": ["data/raw/worldbank/wb_indicators_wide.csv"],
        "manual": False,
        "description": "Pulls 25 indicators for ZWE + 5 SADC peers from the World Bank API.",
    },
    {
        "name": "POTRAZ Q4 2025 extraction",
        "script": "extract_potraz.py",
        "requires": [],
        "produces": ["data/processed/potraz_q4_2025_headlines.csv",
                     "data/processed/potraz_q4_2025_coverage.csv"],
        "manual": False,
        "description": "Transcribes 7 tables from the POTRAZ Q4 2025 sector report into CSVs.",
    },
    {
        "name": "ITU DataHub processing",
        "script": "extract_itu.py",
        "requires": [],  # Soft requirement: CSV files in data/raw/itu/
        "produces": ["data/processed/itu_indicators_wide.csv"],
        "manual": True,
        "manual_action": "Download ITU CSVs from datahub.itu.int/data/ into data/raw/itu/",
        "description": "Merges manually-downloaded ITU CSVs into a unified indicator table.",
    },
    {
        "name": "ZimStat district populations",
        "script": "extract_zimstat.py",
        "requires": [],  # Soft: needs CSV in data/raw/zimstat/
        "produces": ["data/processed/zimstat_district_population_2025.csv"],
        "manual": True,
        "manual_action": "Download from https://www.zimstat.co.zw/ SDMX portal -> data/raw/zimstat/",
        "description": "Extracts 2025 population projections for 42 districts (4 provinces).",
    },
    {
        "name": "DDI computation",
        "script": "compute_ddi.py",
        "requires": ["data/raw/worldbank/wb_indicators_wide.csv"],
        "produces": ["data/processed/ddi_country.csv",
                     "data/processed/ddi_summary.txt"],
        "manual": False,
        "description": "Computes the Digital Desert Index for all countries.",
    },
    {
        "name": "Country comparison charts",
        "script": "make_figures.py",
        "requires": ["data/processed/ddi_country.csv"],
        "produces": ["outputs/figures/ddi_country_ranking.png",
                     "outputs/figures/ddi_pillar_breakdown.png"],
        "manual": False,
        "description": "DDI ranking bar chart and pillar breakdown.",
    },
    {
        "name": "Zimbabwe-specific charts",
        "script": "make_figures_zwe.py",
        "requires": ["data/processed/potraz_q4_2025_coverage.csv"],
        "produces": ["outputs/figures/zwe_rural_urban_coverage_gap.png",
                     "outputs/figures/zwe_base_station_distribution.png",
                     "outputs/figures/zwe_internet_tech_mix.png"],
        "manual": False,
        "description": "Rural-urban gap, base stations, internet tech mix charts.",
    },
    {
        "name": "District master table",
        "script": "build_district_table.py",
        "requires": ["data/raw/geo/gadm41_ZWE.gpkg",
                     "data/processed/potraz_q4_2025_coverage.csv"],
        "produces": ["data/processed/zwe_districts_master.gpkg",
                     "data/processed/zwe_districts_master.csv"],
        "manual": True,
        "manual_action": "Download GADM: wget https://geodata.ucdavis.edu/gadm/gadm4.1/gpkg/gadm41_ZWE.gpkg -P data/raw/geo/",
        "description": "Joins GADM districts to POTRAZ coverage + WB indicators.",
    },
    {
        "name": "District choropleth maps",
        "script": "make_district_map.py",
        "requires": ["data/processed/zwe_districts_master.gpkg"],
        "produces": ["outputs/figures/zwe_district_ddi_map.png",
                     "outputs/figures/zwe_district_coverage_map.png"],
        "manual": False,
        "description": "Choropleth maps of DDI and coverage gap by district.",
    },
    {
        "name": "OpenCellID tower analysis",
        "script": "extract_opencellid.py",
        "requires": ["data/raw/opencellid/648.csv",
                     "data/raw/geo/gadm41_ZWE.gpkg"],
        "produces": ["data/processed/opencellid_district_towers.csv",
                     "outputs/figures/opencellid_tower_analysis.png"],
        "manual": True,
        "manual_action": "Download from https://opencellid.org/downloads.php (MCC 648) -> data/raw/opencellid/648.csv",
        "description": "Spatial join of 8,587 crowdsourced towers to districts.",
    },
]


def check_prereqs():
    """Check which prerequisites are met."""
    print("=" * 70)
    print("PREREQUISITE CHECK")
    print("=" * 70)

    # Python packages
    pkgs = {"wbdata": False, "pandas": False, "matplotlib": False, "geopandas": False}
    for pkg in pkgs:
        try:
            __import__(pkg)
            pkgs[pkg] = True
        except ImportError:
            pass
    print("\nPython packages:")
    for pkg, ok in pkgs.items():
        print(f"  {'✓' if ok else '✗'} {pkg}")
    if not all(pkgs.values()):
        missing = [p for p, ok in pkgs.items() if not ok]
        print(f"\n  → pip install {' '.join(missing)}")

    # Manual downloads
    manual_files = {
        "GADM boundaries": ROOT / "data/raw/geo/gadm41_ZWE.gpkg",
        "OpenCellID towers": ROOT / "data/raw/opencellid/648.csv",
        "ITU CSVs (any)": ROOT / "data/raw/itu",
    }
    print("\nManual downloads:")
    for name, path in manual_files.items():
        if path.is_dir():
            csvs = list(path.glob("*.csv"))
            ok = len(csvs) > 0
            detail = f" ({len(csvs)} CSVs found)" if ok else " (empty)"
        else:
            ok = path.exists()
            detail = f" ({path.stat().st_size // 1024} KB)" if ok else ""
        print(f"  {'✓' if ok else '✗'} {name}{detail}")

    return all(pkgs.values())


def run_step(step, dry_run=False):
    """Run a single pipeline step."""
    script = SRC / step["script"]
    if not script.exists():
        return "MISSING", f"Script not found: {script}"

    # Check hard requirements
    for req in step["requires"]:
        req_path = ROOT / req
        if not req_path.exists():
            if step.get("manual"):
                return "SKIP", f"Manual prerequisite missing: {req}\n  → {step.get('manual_action', '')}"
            else:
                return "SKIP", f"Missing input: {req}"

    if dry_run:
        return "READY", ""

    # Run the script
    print(f"\n  Running: python src/{step['script']} ...")
    start = time.time()
    result = subprocess.run(
        [sys.executable, str(script)],
        cwd=str(ROOT),
        capture_output=True,
        text=True,
        timeout=300,
    )
    elapsed = time.time() - start

    if result.returncode == 0:
        # Verify outputs exist
        missing_outputs = [o for o in step["produces"] if not (ROOT / o).exists()]
        if missing_outputs:
            return "WARN", f"Script succeeded but missing outputs: {missing_outputs}"
        return "OK", f"{elapsed:.1f}s"
    else:
        # Show last 5 lines of stderr
        err_lines = result.stderr.strip().split("\n")[-5:]
        return "FAIL", "\n  ".join(err_lines)


def main():
    parser = argparse.ArgumentParser(description="Run the TECHDEV-ZIMBABWE pipeline")
    parser.add_argument("--check", action="store_true", help="Check prerequisites only")
    args = parser.parse_args()

    print()
    print("╔══════════════════════════════════════════════════════════════════╗")
    print("║  TECHDEV-ZIMBABWE: Mapping Zimbabwe's Digital Deserts          ║")
    print("║  ITU Data Hackathon 2026 — Full Pipeline Runner                ║")
    print("╚══════════════════════════════════════════════════════════════════╝")
    print()

    pkgs_ok = check_prereqs()

    if args.check:
        print("\nUse 'python run_all.py' (without --check) to run the pipeline.")
        return

    if not pkgs_ok:
        print("\nInstall missing packages first, then re-run.")
        return

    print()
    print("=" * 70)
    print("RUNNING PIPELINE")
    print("=" * 70)

    results = []
    for i, step in enumerate(STEPS, 1):
        print(f"\n[{i}/{len(STEPS)}] {step['name']}")
        print(f"  {step['description']}")
        status, detail = run_step(step)
        results.append((step["name"], status, detail))

        if status == "OK":
            print(f"  ✓ Done ({detail})")
        elif status == "SKIP":
            print(f"  ⊘ Skipped: {detail}")
        elif status == "FAIL":
            print(f"  ✗ Failed:\n  {detail}")
        elif status == "WARN":
            print(f"  ⚠ Warning: {detail}")
        elif status == "READY":
            print(f"  → Ready to run")

    # Summary
    print()
    print("=" * 70)
    print("PIPELINE SUMMARY")
    print("=" * 70)
    for name, status, detail in results:
        icon = {"OK": "✓", "SKIP": "⊘", "FAIL": "✗", "WARN": "⚠", "READY": "→"}
        print(f"  {icon.get(status, '?')} {name}: {status}")

    ok_count = sum(1 for _, s, _ in results if s == "OK")
    skip_count = sum(1 for _, s, _ in results if s == "SKIP")
    fail_count = sum(1 for _, s, _ in results if s == "FAIL")
    print(f"\n  {ok_count} succeeded, {skip_count} skipped, {fail_count} failed")

    # List produced files
    print()
    print("OUTPUT FILES:")
    for ext in ["csv", "gpkg", "txt"]:
        files = sorted(DATA_PROC.glob(f"*.{ext}")) if DATA_PROC.exists() else []
        for f in files:
            print(f"  data/processed/{f.name}  ({f.stat().st_size // 1024} KB)")
    if OUTPUTS.exists():
        for f in sorted(OUTPUTS.glob("*.png")):
            print(f"  outputs/figures/{f.name}  ({f.stat().st_size // 1024} KB)")


if __name__ == "__main__":
    main()
