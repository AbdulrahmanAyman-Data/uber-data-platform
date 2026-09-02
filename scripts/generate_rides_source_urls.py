"""
scripts/generate_rides_source_urls.py

Generates the list of monthly NYC TLC HVFHS trip data URLs for a fixed
year range (default: 2024 and 2025 — 24 months total) and writes them,
one per line, to a text file that the NiFi flow watches (GetFile) and
ingests.

Usage:
    python scripts/generate_rides_source_urls.py
    python scripts/generate_rides_source_urls.py --start-year 2024 --end-year 2025 --out nifi/rides-source/rides_source_urls.txt
"""
import argparse
import os

BASE_URL = "https://d37ci6vzurychx.cloudfront.net/trip-data"


def year_month_range(start_year: int, end_year: int):
    """Yields (year, month) tuples for every month from Jan start_year
    through Dec end_year, inclusive."""
    for year in range(start_year, end_year + 1):
        for month in range(1, 13):
            yield (year, month)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--start-year", type=int, default=2024, help="First year to include (default: 2024)")
    parser.add_argument("--end-year", type=int, default=2024, help="Last year to include (default: 2025)")
    parser.add_argument("--out", default="nifi/rides-source/rides_source_urls.txt", help="Output file path")
    args = parser.parse_args()

    if args.start_year > args.end_year:
        raise ValueError("--start-year must be <= --end-year")

    urls = [
        f"{BASE_URL}/fhvhv_tripdata_{y:04d}-{m:02d}.parquet"
        for (y, m) in year_month_range(args.start_year, args.end_year)
    ]

    os.makedirs(os.path.dirname(args.out), exist_ok=True)
    with open(args.out, "w") as f:
        f.write("\n".join(urls) + "\n")

    print(f"Wrote {len(urls)} URLs to {args.out}")
    print(f"Range: {urls[0]}  ...  {urls[-1]}")


if __name__ == "__main__":
    main()
