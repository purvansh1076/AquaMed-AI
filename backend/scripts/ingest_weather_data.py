"""
AquaMediAI — Weather Ingestion & FAO-56 Agronomic Processing CLI
=================================================================

CLI script to fetch, clean, and process daily weather observations
from NASA POWER for pilot agricultural command areas in Maharashtra, India.

Usage
-----
    # Ingest using live NASA POWER API (Ahmednagar pilot, 2023):
    python backend/scripts/ingest_weather_data.py --region maharashtra_ahmednagar --start 20230101 --end 20231231

    # Offline mode using bundled local fixture:
    python backend/scripts/ingest_weather_data.py --offline

    # From backend/ directory:
    python scripts/ingest_weather_data.py --offline
"""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

# Ensure backend/ is on sys.path
BACKEND_DIR = Path(__file__).resolve().parent.parent
if str(BACKEND_DIR) not in sys.path:
    sys.path.insert(0, str(BACKEND_DIR))

from app.data import (
    PREDEFINED_REGIONS,
    AgronomicDataPipeline,
    NasaPowerClient,
    get_region_config,
)

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)-8s | %(message)s",
    datefmt="%H:%M:%S",
    handlers=[logging.StreamHandler(sys.stdout)],
)
logger = logging.getLogger(__name__)


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(
        description="AquaMediAI — Ingest and process NASA POWER weather data for agricultural basins",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog=__doc__,
    )
    parser.add_argument(
        "--region",
        type=str,
        default="maharashtra_ahmednagar",
        choices=list(PREDEFINED_REGIONS.keys()),
        help="Target pilot region ID (default: maharashtra_ahmednagar)",
    )
    parser.add_argument(
        "--start",
        type=str,
        default="20230101",
        help="Start date YYYYMMDD (default: 20230101)",
    )
    parser.add_argument(
        "--end",
        type=str,
        default="20231231",
        help="End date YYYYMMDD (default: 20231231)",
    )
    parser.add_argument(
        "--offline",
        action="store_true",
        help="Run in offline mode using bundled sample fixture (no internet required)",
    )
    parser.add_argument(
        "--fixture-path",
        type=str,
        default=None,
        help="Optional custom path to local NASA POWER JSON fixture",
    )
    return parser.parse_args()


def print_banner(text: str, char: str = "=", width: int = 70) -> None:
    print(char * width)
    print(f" {text}")
    print(char * width)


def main() -> int:
    args = parse_args()
    region = get_region_config(args.region)

    print_banner("AquaMediAI -- NASA POWER Agroclimatology Ingestion Pipeline")
    print(f" Pilot Region : {region.region_name}")
    print(f" Centroid     : {region.latitude:.4f} N, {region.longitude:.4f} E (Elev: {region.elevation_m}m)")
    print(f" Basin        : {region.basin_name}")
    print(f" Period       : {args.start} to {args.end}")
    print(f" Execution    : {'OFFLINE (Local Fixture)' if args.offline else 'LIVE (NASA POWER API)'}")
    print("-" * 70)

    try:
        # Step 1: Ingestion
        client = NasaPowerClient(region=region)
        payload = client.fetch_daily_weather(
            start_date=args.start,
            end_date=args.end,
            save_raw=True,
            offline_fixture_path=args.fixture_path if args.fixture_path else (
                (BACKEND_DIR / "tests" / "fixtures" / "nasa_power_ahmednagar_sample.json")
                if args.offline else None
            ),
        )

        df_raw = client.parse_payload_to_dataframe(payload)
        logger.info("Parsed %d daily weather records from NASA POWER.", len(df_raw))

        # Step 2: Processing & FAO-56 ET0 Calculation
        pipeline = AgronomicDataPipeline(region=region)
        df_clean, report = pipeline.process(df_raw, save_csv=True)

        print("\n" + "=" * 70)
        print(" INGESTION & AGRONOMIC VALIDATION REPORT")
        print("=" * 70)
        print(f" Status            : {report.status}")
        print(f" Records Processed : {report.total_records} days")
        print(f" Date Range        : {report.date_start} to {report.date_end}")
        print(f" Mean ET0          : {report.mean_et0_mm_per_day:.2f} mm/day")
        print(f" ET0 Min / Max     : {report.min_et0_mm_per_day:.2f} / {report.max_et0_mm_per_day:.2f} mm/day")
        print(f" Total Rain        : {report.total_precipitation_mm:.1f} mm")
        print(f" Effective Rain    : {report.total_effective_precipitation_mm:.1f} mm")
        print(f" Missing Cells     : {sum(report.missing_values_detected.values())} (Imputed: {report.imputed_records_count})")
        print("-" * 70)
        print(f" Raw JSON saved to : {client.raw_dir.resolve()}")
        print(f" Clean CSV saved to: {pipeline.processed_dir.resolve()}")
        print("=" * 70)
        return 0

    except Exception as exc:
        logger.error("Data ingestion failed: %s", exc, exc_info=True)
        return 1


if __name__ == "__main__":
    sys.exit(main())
