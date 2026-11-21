import json
from pathlib import Path

import pandas as pd

path = Path("data/raw") / "Neighbourhoods - 4326.geojson"

with open(path, encoding="utf-8") as f:
    data = json.load(f)

print("Type:", data["type"])
print("Number of features:", len(data["features"]))

rows = [feature["properties"] for feature in data["features"]]
df = pd.DataFrame(rows)

print(df.columns.tolist())
print(df.head())