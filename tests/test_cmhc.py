import pandas as pd
import pytest

from src.pipeline.cmhc import load_cmhc_rent_table, parse_cmhc_rent_table

SAMPLE = '''Toronto — Average Rent by Bedroom Type by Zone
October 2025 Row / Apartment
,Studio,,1 Bedroom,,2 Bedroom,,3 Bedroom +,,Total,,
Toronto (Central),"1,606",a ,"2,042",a ,"2,776",b ,"3,580",d ,"2,163",a ,
Etobicoke (South),"1,502",a ,"1,493",a ,"1,762",a ,**,,"1,630",a ,
Toronto,"1,491",a ,"1,761",a ,"2,045",a ,"2,294",a ,"1,917",a ,

Notes
"The following letter codes are used to indicate the reliability of the estimates"
Source,CMHC Rental Market Survey
'''


def get(df, zone, bedroom_type):
    return df[(df["zone"] == zone) & (df["bedroom_type"] == bedroom_type)].iloc[0]


def test_parses_rent_and_reliability():
    df = parse_cmhc_rent_table(SAMPLE)
    row = get(df, "Toronto (Central)", "2_bed")
    assert row["avg_rent"] == 2776
    assert row["reliability"] == "b"


def test_suppressed_value_becomes_missing():
    df = parse_cmhc_rent_table(SAMPLE)
    row = get(df, "Etobicoke (South)", "3_bed_plus")
    assert pd.isna(row["avg_rent"])
    assert pd.isna(row["reliability"])
    assert row["is_suppressed"]


def test_stops_before_footnotes():
    df = parse_cmhc_rent_table(SAMPLE)
    assert set(df["zone"]) == {"Toronto (Central)", "Etobicoke (South)", "Toronto"}


def test_metadata_and_cma_total_flag():
    df = parse_cmhc_rent_table(SAMPLE)
    assert (df["survey_month"] == "2025-10").all()
    assert (df["structure_type"] == "Row / Apartment").all()
    assert set(df.loc[df["is_cma_total"], "zone"]) == {"Toronto"}


def test_unknown_bedroom_label_fails_loudly():
    bad = SAMPLE.replace(",Studio,", ",Penthouse,")
    with pytest.raises(ValueError):
        parse_cmhc_rent_table(bad)


def test_real_file_passes_sanity_checks():
    df = load_cmhc_rent_table()
    assert len(df) % 5 == 0
    assert not df.duplicated(["zone", "bedroom_type"]).any()
    assert df["is_cma_total"].sum() == 5
    assert df["avg_rent"].dropna().between(500, 6000).all()
    assert (df["is_suppressed"] == df["avg_rent"].isna()).all()
    assert set(df["reliability"].dropna()) <= {"a", "b", "c", "d"}

def test_loader_handles_windows_1252_encoding(tmp_path):
    path = tmp_path / "export.csv"
    path.write_bytes(SAMPLE.encode("cp1252"))

    df = load_cmhc_rent_table(path)

    assert df["cma"].iloc[0] == "Toronto"
    assert len(df) == 15