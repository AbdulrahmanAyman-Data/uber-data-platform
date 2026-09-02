"""
scripts/compute_zone_geometries.py

Produces the small zone reference file that common/dimensions.build_dim_zone()
reads to build Dim_Zone: LocationID + zone attributes + the full zone
polygon as WKT (no centroid, no H3 -- see docs/hvfhs_data_mapping.md).

Runs in TWO modes:

1. Manual/local (files already downloaded):
   python scripts/compute_zone_geometries.py \
       --lookup-csv data/raw/taxi_zone_lookup.csv \
       --shapefile-zip data/raw/taxi_zones.zip \
       --out data/reference/taxi_zone_geometries.csv

2. NiFi-triggered (self-contained -- downloads both source files itself,
   prints the resulting CSV to stdout instead of writing a file). This is
   the mode the NiFi ExecuteStreamCommand processor uses -- see
   docs/nifi_zone_geometries_flow.md:
   python scripts/compute_zone_geometries.py --stdout

Only pass --lookup-csv/--shapefile-zip if you already have the files
locally; omit them and the script downloads fresh copies from the official
TLC URLs into a temp directory.
"""
import argparse
import zipfile
import tempfile
import os
import sys
import urllib.request

import pandas as pd
import geopandas as gpd

LOOKUP_URL = "https://d37ci6vzurychx.cloudfront.net/misc/taxi_zone_lookup.csv"
SHAPEFILE_URL = "https://d37ci6vzurychx.cloudfront.net/misc/taxi_zones.zip"


def log(msg: str):
    # NiFi captures stdout as the flowfile content when --stdout is used,
    # so all progress/diagnostic messages MUST go to stderr, never stdout.
    print(msg, file=sys.stderr)


def download(url: str, dest_path: str):
    log(f"Downloading {url} -> {dest_path}")
    urllib.request.urlretrieve(url, dest_path)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--lookup-csv", default=None,
                         help="Path to an already-downloaded taxi_zone_lookup.csv. "
                              "Omit to download it fresh from the official TLC URL.")
    parser.add_argument("--shapefile-zip", default=None,
                         help="Path to an already-downloaded taxi_zones.zip. "
                              "Omit to download it fresh from the official TLC URL.")
    parser.add_argument("--out", default=None,
                         help="Output CSV path. Omit (or use --stdout) to print to stdout instead.")
    parser.add_argument("--stdout", action="store_true",
                         help="Print the resulting CSV to stdout instead of writing a file "
                              "(used by the NiFi ExecuteStreamCommand flow).")
    args = parser.parse_args()

    with tempfile.TemporaryDirectory() as tmp_dir:
        lookup_csv_path = args.lookup_csv
        shapefile_zip_path = args.shapefile_zip

        if lookup_csv_path is None:
            lookup_csv_path = os.path.join(tmp_dir, "taxi_zone_lookup.csv")
            download(LOOKUP_URL, lookup_csv_path)

        if shapefile_zip_path is None:
            shapefile_zip_path = os.path.join(tmp_dir, "taxi_zones.zip")
            download(SHAPEFILE_URL, shapefile_zip_path)

        log(f"Reading zone lookup table: {lookup_csv_path}")
        lookup_df = pd.read_csv(lookup_csv_path)
        lookup_df = lookup_df.rename(columns={
            "LocationID": "location_id",
            "Borough": "borough",
            "Zone": "zone_name",
            "service_zone": "service_zone",
        })

        log(f"Extracting shapefile: {shapefile_zip_path}")
        extract_dir = os.path.join(tmp_dir, "shp")
        os.makedirs(extract_dir, exist_ok=True)
        with zipfile.ZipFile(shapefile_zip_path, "r") as zf:
            zf.extractall(extract_dir)

        shp_files = []

        for root, dirs, files in os.walk(extract_dir):
            for file in files:
                if file.lower().endswith(".shp"):
                    shp_files.append(os.path.join(root, file))
        if not shp_files:
            raise FileNotFoundError(
                "No .shp file found inside the zip. NOTE: the TLC page labels this "
                "download '(PARQUET)' next to a .zip link -- almost certainly a "
                "labeling mistake on their site. If it really is Parquet, read it "
                "with geopandas.read_parquet() instead and adjust this script."
            )
        shp_path = shp_files[0]

        log(f"Loading geometries from: {shp_path}")
        zones_gdf = gpd.read_file(shp_path)

        # Reproject feet (NY State Plane) -> WGS84 degrees, needed for any
        # future H3 usage even though we don't compute H3 here.
        if zones_gdf.crs is None:
            log("WARNING: shapefile has no CRS set -- assuming EPSG:2263 (NY State Plane).")
            zones_gdf = zones_gdf.set_crs(epsg=2263)
        zones_gdf = zones_gdf.to_crs(epsg=4326)

        zones_gdf["polygon_wkt"] = zones_gdf.geometry.apply(lambda geom: geom.wkt)

        geom_df = zones_gdf[["LocationID", "polygon_wkt"]].rename(columns={"LocationID": "location_id"})

    merged = lookup_df.merge(geom_df, on="location_id", how="left")

    missing = merged["polygon_wkt"].isna().sum()
    if missing > 0:
        log(f"WARNING: {missing} zone(s) have no matching geometry -- polygon_wkt will be null for those.")

    merged = merged[["location_id", "borough", "zone_name", "service_zone", "polygon_wkt"]]

    if args.stdout or args.out is None:
        merged.to_csv(sys.stdout, index=False)
    else:
        os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
        merged.to_csv(args.out, index=False)
        log(f"Wrote {len(merged)} zones to: {args.out}")


if __name__ == "__main__":
    main()
