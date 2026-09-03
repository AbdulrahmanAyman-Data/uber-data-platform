import argparse
import zipfile
import tempfile
import os
import sys
import urllib.request

import pandas as pd
import geopandas as gpd
import h3

LOOKUP_URL = "https://d37ci6vzurychx.cloudfront.net/misc/taxi_zone_lookup.csv"
SHAPEFILE_URL = "https://d37ci6vzurychx.cloudfront.net/misc/taxi_zones.zip"

H3_RESOLUTION = 8  # ~0.46 km^2 hexagons -- matches common/geo.py's H3_RESOLUTION


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
    parser.add_argument("--resolution", type=int, default=H3_RESOLUTION,
                         help=f"H3 resolution for the centroid geo_hash (default: {H3_RESOLUTION}).")
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

        # Reproject feet (NY State Plane) -> WGS84 degrees -- required both
        # for the WKT we keep and for a correct H3 geo_hash below.
        if zones_gdf.crs is None:
            log("WARNING: shapefile has no CRS set -- assuming EPSG:2263 (NY State Plane).")
            zones_gdf = zones_gdf.set_crs(epsg=2263)
        zones_gdf = zones_gdf.to_crs(epsg=4326)

        zones_gdf["polygon_wkt"] = zones_gdf.geometry.apply(lambda geom: geom.wkt)

        # Centroid in WGS84 degrees (computed AFTER to_crs(epsg=4326), so
        # this is a true lat/lon pair). For a handful of oddly-shaped /
        # multi-part zones (islands, zones split by water) the geometric
        # centroid can fall outside the polygon -- swap to
        # geom.representative_point() below if that matters for your case.
        centroids = zones_gdf.geometry.centroid
        zones_gdf["centroid_lat"] = centroids.y
        zones_gdf["centroid_lon"] = centroids.x

        # H3 geo_hash of the centroid -- computed HERE, not in Spark.
        zones_gdf["geo_hash"] = zones_gdf.apply(
            lambda row: h3.latlng_to_cell(row["centroid_lat"], row["centroid_lon"], args.resolution),
            axis=1,
        )
        zones_gdf["h3_resolution"] = args.resolution

        geom_df = zones_gdf[
            ["LocationID", "polygon_wkt", "centroid_lat", "centroid_lon", "geo_hash", "h3_resolution"]
        ].rename(columns={"LocationID": "location_id"})

    merged = lookup_df.merge(geom_df, on="location_id", how="left")

    missing = merged["polygon_wkt"].isna().sum()
    if missing > 0:
        log(f"WARNING: {missing} zone(s) have no matching geometry -- polygon_wkt/centroid/geo_hash will be null for those.")

    merged = merged[
        [
            "location_id",
            "borough",
            "zone_name",
            "service_zone",
            "polygon_wkt",
            "centroid_lat",
            "centroid_lon",
            "geo_hash",
            "h3_resolution",
        ]
    ]

    if args.stdout or args.out is None:
        merged.to_csv(sys.stdout, index=False)
    else:
        os.makedirs(os.path.dirname(args.out) or ".", exist_ok=True)
        merged.to_csv(args.out, index=False)
        log(f"Wrote {len(merged)} zones to: {args.out}")


if __name__ == "__main__":
    main()
