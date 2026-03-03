#!/usr/bin/env python3
"""Download NYC parking regulation data and convert to compact JSON with lat/lon."""

import csv
import gzip
import json
import os
import urllib.request

from pyproj import Transformer

CSV_URL = "https://data.cityofnewyork.us/api/views/nfid-uabd/rows.csv?accessType=DOWNLOAD"
CSV_FILE = "parking_signs.csv"
OUTPUT = "parking_data.json"
OUTPUT_GZ = "parking_data.json.gz"

BOROUGH_CODES = {
    "Brooklyn": "Bk", "Bronx": "Bx", "Manhattan": "M",
    "Queens": "Q", "Staten Island": "SI",
}

# NY State Plane Long Island (ft) -> WGS84
transformer = Transformer.from_crs("EPSG:2263", "EPSG:4326", always_xy=True)


def download():
    print(f"Downloading CSV from NYC Open Data...")
    urllib.request.urlretrieve(CSV_URL, CSV_FILE)
    size_mb = os.path.getsize(CSV_FILE) / 1024 / 1024
    print(f"Downloaded {CSV_FILE} ({size_mb:.1f} MB)")


def process():
    locations = {}
    skipped = 0

    with open(CSV_FILE, newline="", encoding="utf-8") as f:
        reader = csv.DictReader(f)
        for row in reader:
            x_str = row["sign_x_coord"].strip()
            y_str = row["sign_y_coord"].strip()

            if not x_str or not y_str:
                skipped += 1
                continue
            try:
                x, y = float(x_str), float(y_str)
            except ValueError:
                skipped += 1
                continue

            borough = row["borough"].strip()
            if borough not in BOROUGH_CODES:
                skipped += 1
                continue

            key = (x_str, y_str)
            if key not in locations:
                lon, lat = transformer.transform(x, y)
                locations[key] = {
                    "lat": round(lat, 6),
                    "lon": round(lon, 6),
                    "st": row["on_street"].strip(),
                    "fr": row["from_street"].strip(),
                    "to": row["to_street"].strip(),
                    "b": BOROUGH_CODES[borough],
                    "sd": row["side_of_street"].strip(),
                    "sg": [],
                }

            locations[key]["sg"].append(row["sign_description"].strip())

    # Compact array format: [lat, lon, borough, street, from, to, side, [signs]]
    output = [
        [l["lat"], l["lon"], l["b"], l["st"], l["fr"], l["to"], l["sd"], l["sg"]]
        for l in locations.values()
    ]

    with open(OUTPUT, "w") as f:
        json.dump(output, f, separators=(",", ":"))

    with gzip.open(OUTPUT_GZ, "wt", compresslevel=9) as f:
        json.dump(output, f, separators=(",", ":"))

    json_mb = os.path.getsize(OUTPUT) / 1024 / 1024
    gz_mb = os.path.getsize(OUTPUT_GZ) / 1024 / 1024
    print(f"Wrote {len(output):,} locations ({skipped:,} rows skipped)")
    print(f"  {OUTPUT}: {json_mb:.1f} MB")
    print(f"  {OUTPUT_GZ}: {gz_mb:.1f} MB")


if __name__ == "__main__":
    download()
    process()
