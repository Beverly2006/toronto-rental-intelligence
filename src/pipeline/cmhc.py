"""Parse CMHC Rental Market Survey 'Average Rent by Bedroom Type by Zone' exports."""
import csv
import io
import re
from pathlib import Path

import pandas as pd

RAW_FILE = Path("data/raw") / "cmhc_avg_rent_zone_bedroom_2025-10_row-apartment.csv"

BEDROOM_TYPES = {
    "Studio": "studio",
    "1 Bedroom": "1_bed",
    "2 Bedroom": "2_bed",
    "3 Bedroom +": "3_bed_plus",
    "Total": "total",
}
VALID_GRADES = {"a", "b", "c", "d"}
SUPPRESSED = "**"


def parse_cmhc_rent_table(text: str) -> pd.DataFrame:
    """Turn the exported CSV text into one tidy row per zone and bedroom type."""
    rows = list(csv.reader(io.StringIO(text)))

    # Rows 1-2 describe the table: area, month, structure type.
    cma = rows[0][0].split("—")[0].strip()
    match = re.match(r"^(\w+) (\d{4}) (.+)$", rows[1][0].strip())
    if match is None:
        raise ValueError(f"Unexpected period line: {rows[1][0]!r}")
    month_name, year, structure_type = match.groups()
    survey_month = pd.to_datetime(f"{month_name} {year}").strftime("%Y-%m")

    # Row 3: labels sit in every second column (each rent is followed by a grade).
    labels = [cell.strip() for cell in rows[2][1::2] if cell.strip()]
    unknown = [label for label in labels if label not in BEDROOM_TYPES]
    if unknown:
        raise ValueError(f"Unknown bedroom labels: {unknown}")

    records = []
    for row in rows[3:]:
        if not row or not row[0].strip():
            break  # blank line: the data block is over, footnotes follow
        zone = row[0].strip()
        for i, label in enumerate(labels):
            raw_rent = row[1 + 2 * i].strip()
            grade = row[2 + 2 * i].strip() if len(row) > 2 + 2 * i else ""
            suppressed = raw_rent == SUPPRESSED

            if suppressed:
                avg_rent, reliability = float("nan"), None
            else:
                if grade not in VALID_GRADES:
                    raise ValueError(f"Bad grade {grade!r} for {zone} / {label}")
                avg_rent, reliability = float(raw_rent.replace(",", "")), grade

            records.append(
                {
                    "cma": cma,
                    "zone": zone,
                    "bedroom_type": BEDROOM_TYPES[label],
                    "avg_rent": avg_rent,
                    "reliability": reliability,
                    "is_suppressed": suppressed,
                    "is_cma_total": zone == cma,
                    "survey_month": survey_month,
                    "structure_type": structure_type,
                }
            )
    return pd.DataFrame(records)


def load_cmhc_rent_table(path: Path = RAW_FILE) -> pd.DataFrame:
    """Read the raw CMHC export and return the tidy table."""
    raw_bytes = Path(path).read_bytes()
    try:
        text = raw_bytes.decode("utf-8-sig")
    except UnicodeDecodeError:
        # CMHC portal exports are saved in Windows-1252 (the dash is byte 0x97)
        text = raw_bytes.decode("cp1252")
    return parse_cmhc_rent_table(text)

