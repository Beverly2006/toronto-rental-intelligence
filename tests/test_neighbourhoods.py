from src.pipeline.neighbourhoods import load_neighbourhoods, parse_neighbourhoods


def make_feature(code, name, classification="NA"):
    return {
        "properties": {
            "AREA_SHORT_CODE": code,
            "AREA_NAME": name,
            "CLASSIFICATION": classification,
        }
    }


def test_parse_renames_columns_and_cleans_values():
    geojson = {"features": [make_feature("174", " South Eglinton-Davisville ")]}
    result = parse_neighbourhoods(geojson)

    assert list(result.columns) == [
        "neighbourhood_id",
        "neighbourhood_name",
        "classification",
    ]
    assert result.loc[0, "neighbourhood_id"] == 174
    assert result.loc[0, "neighbourhood_name"] == "South Eglinton-Davisville"


def test_parse_sorts_by_neighbourhood_id():
    geojson = {"features": [make_feature("5", "B"), make_feature("2", "A")]}
    result = parse_neighbourhoods(geojson)

    assert result["neighbourhood_id"].tolist() == [2, 5]


def test_real_file_has_158_unique_neighbourhoods():
    df = load_neighbourhoods()

    assert len(df) == 158
    assert df["neighbourhood_id"].is_unique
    assert df["neighbourhood_name"].is_unique