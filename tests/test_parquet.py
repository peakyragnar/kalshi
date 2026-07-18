import polars as pl

from kalshi_data.core.parquet import read_shards


def test_read_shards_relaxes_null_and_string_schema(tmp_path):
    pl.DataFrame({"ticker": ["OLD"], "settled_time": [None]}).write_parquet(
        tmp_path / "part-0000.parquet"
    )
    pl.DataFrame(
        {"ticker": ["NEW"], "settled_time": ["2026-07-18T00:00:00Z"]}
    ).write_parquet(tmp_path / "part-0001.parquet")

    out = read_shards(tmp_path)

    assert out.schema["settled_time"] == pl.String
    assert out.sort("ticker")["settled_time"].to_list() == [
        "2026-07-18T00:00:00Z",
        None,
    ]
