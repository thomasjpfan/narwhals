# ruff: noqa
from typing import Any

import polars

from polars_api_compat import to_original_api
from polars_api_compat import to_polars_api


def q2(
    region_ds_raw: Any,
    nation_ds_raw: Any,
    supplier_ds_raw: Any,
    part_ds_raw: Any,
    part_supp_ds_raw: Any,
) -> Any:
    var_1 = 15
    var_2 = "BRASS"
    var_3 = "EUROPE"

    region_ds, pl = to_polars_api(region_ds_raw, version="0.20")
    nation_ds, _ = to_polars_api(nation_ds_raw, version="0.20")
    supplier_ds, _ = to_polars_api(supplier_ds_raw, version="0.20")
    part_ds, _ = to_polars_api(part_ds_raw, version="0.20")
    part_supp_ds, _ = to_polars_api(part_supp_ds_raw, version="0.20")

    result_q2 = (
        part_ds.join(part_supp_ds, left_on="p_partkey", right_on="ps_partkey")
        .join(supplier_ds, left_on="ps_suppkey", right_on="s_suppkey")
        .join(nation_ds, left_on="s_nationkey", right_on="n_nationkey")
        .join(region_ds, left_on="n_regionkey", right_on="r_regionkey")
        .filter(pl.col("p_size") == var_1)
        .filter(pl.col("p_type").str.ends_with(var_2))
        .filter(pl.col("r_name") == var_3)
    ).cache()

    final_cols = [
        "s_acctbal",
        "s_name",
        "n_name",
        "p_partkey",
        "p_mfgr",
        "s_address",
        "s_phone",
        "s_comment",
    ]

    q_final = (
        result_q2.group_by("p_partkey")
        .agg(pl.min("ps_supplycost").alias("ps_supplycost"))
        .join(
            result_q2,
            left_on=["p_partkey", "ps_supplycost"],
            right_on=["p_partkey", "ps_supplycost"],
        )
        .select(final_cols)
        .sort(
            by=["s_acctbal", "n_name", "s_name", "p_partkey"],
            descending=[True, False, False, False],
        )
        .limit(100)
        .with_columns(pl.col(pl.datatypes.Utf8).str.strip_chars().name.keep())
    )

    return to_original_api(q_final.collect())


region_ds = polars.read_parquet("../tpch-data/region.parquet").to_pandas()
ration_ds = polars.read_parquet("../tpch-data/nation.parquet").to_pandas()
supplier_ds = polars.read_parquet("../tpch-data/supplier.parquet").to_pandas()
part_ds = polars.read_parquet("../tpch-data/part.parquet").to_pandas()
part_supp_ds = polars.read_parquet("../tpch-data/partsupp.parquet").to_pandas()
print(q2(region_ds, ration_ds, supplier_ds, part_ds, part_supp_ds))