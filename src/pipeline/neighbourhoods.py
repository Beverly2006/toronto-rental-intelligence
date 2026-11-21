"""Load and clean the City of Toronto neighbourhood boundaries."""
import json
from pathlib import Path

import pandas as pd

RAW_FILE = Path("data/raw") / "Neighbourhoods - 4326.geojson"

def parse_neighbourhoods(geojson: dict) -> pd.DataFrame:
    """"Turn a neighbourhoods GeoJSON dict into a clean table (no geometry)."""
    rows = [feature["properties"] for feature in geojson["features"]]
    raw = pd.DataFrame(rows)

    clean = pd.DataFrame(
        {
            "neighbourhood_id": raw["AREA_SHORT_CODE"].astype(int),
            "neighbourhood_name": raw["AREA_NAME"].str.strip(),
            "classification": raw["CLASSIFICATION"],
        }
    )
    return clean.sort_values("neighbourhood_id").reset_index(drop=True)

def load_neighbourhoods(path: Path = RAW_FILE) -> pd.DataFrame:
    """Read the raw GeoJSON file and return the clean table"""
    with open(path, encoding="utf-8") as f:
        geojson = json.load(f)
    return parse_neighbourhoods(geojson)

   