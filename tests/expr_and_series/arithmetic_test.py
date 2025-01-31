from __future__ import annotations

from typing import Any

import hypothesis.strategies as st
import pandas as pd
import polars as pl
import pyarrow as pa
import pytest
from hypothesis import assume
from hypothesis import given

import narwhals.stable.v1 as nw
from narwhals.utils import parse_version
from tests.utils import compare_dicts


@pytest.mark.parametrize(
    ("attr", "rhs", "expected"),
    [
        ("__add__", 1, [2, 3, 4]),
        ("__sub__", 1, [0, 1, 2]),
        ("__mul__", 2, [2, 4, 6]),
        ("__truediv__", 2.0, [0.5, 1.0, 1.5]),
        ("__truediv__", 1, [1, 2, 3]),
        ("__floordiv__", 2, [0, 1, 1]),
        ("__mod__", 2, [1, 0, 1]),
        ("__pow__", 2, [1, 4, 9]),
    ],
)
def test_arithmetic_expr(
    attr: str,
    rhs: Any,
    expected: list[Any],
    constructor: Any,
    request: Any,
) -> None:
    if attr == "__mod__" and any(
        x in str(constructor) for x in ["pandas_pyarrow", "modin"]
    ):
        request.applymarker(pytest.mark.xfail)

    data = {"a": [1.0, 2, 3]}
    df = nw.from_native(constructor(data))
    result = df.select(getattr(nw.col("a"), attr)(rhs))
    compare_dicts(result, {"a": expected})


@pytest.mark.parametrize(
    ("attr", "rhs", "expected"),
    [
        ("__radd__", 1, [2, 3, 4]),
        ("__rsub__", 1, [0, -1, -2]),
        ("__rmul__", 2, [2, 4, 6]),
        ("__rtruediv__", 2.0, [2, 1, 2 / 3]),
        ("__rfloordiv__", 2, [2, 1, 0]),
        ("__rmod__", 2, [0, 0, 2]),
        ("__rpow__", 2, [2, 4, 8]),
    ],
)
def test_right_arithmetic_expr(
    attr: str,
    rhs: Any,
    expected: list[Any],
    constructor: Any,
    request: Any,
) -> None:
    if attr == "__rmod__" and any(
        x in str(constructor) for x in ["pandas_pyarrow", "modin"]
    ):
        request.applymarker(pytest.mark.xfail)

    data = {"a": [1, 2, 3]}
    df = nw.from_native(constructor(data))
    result = df.select(a=getattr(nw.col("a"), attr)(rhs))
    compare_dicts(result, {"a": expected})


@pytest.mark.parametrize(
    ("attr", "rhs", "expected"),
    [
        ("__add__", 1, [2, 3, 4]),
        ("__sub__", 1, [0, 1, 2]),
        ("__mul__", 2, [2, 4, 6]),
        ("__truediv__", 2.0, [0.5, 1.0, 1.5]),
        ("__truediv__", 1, [1, 2, 3]),
        ("__floordiv__", 2, [0, 1, 1]),
        ("__mod__", 2, [1, 0, 1]),
        ("__pow__", 2, [1, 4, 9]),
    ],
)
def test_arithmetic_series(
    attr: str,
    rhs: Any,
    expected: list[Any],
    constructor_eager: Any,
    request: Any,
) -> None:
    if attr == "__mod__" and any(
        x in str(constructor_eager) for x in ["pandas_pyarrow", "modin"]
    ):
        request.applymarker(pytest.mark.xfail)

    data = {"a": [1, 2, 3]}
    df = nw.from_native(constructor_eager(data), eager_only=True)
    result = df.select(getattr(df["a"], attr)(rhs))
    compare_dicts(result, {"a": expected})


@pytest.mark.parametrize(
    ("attr", "rhs", "expected"),
    [
        ("__radd__", 1, [2, 3, 4]),
        ("__rsub__", 1, [0, -1, -2]),
        ("__rmul__", 2, [2, 4, 6]),
        ("__rtruediv__", 2.0, [2, 1, 2 / 3]),
        ("__rfloordiv__", 2, [2, 1, 0]),
        ("__rmod__", 2, [0, 0, 2]),
        ("__rpow__", 2, [2, 4, 8]),
    ],
)
def test_right_arithmetic_series(
    attr: str,
    rhs: Any,
    expected: list[Any],
    constructor_eager: Any,
    request: Any,
) -> None:
    if attr == "__rmod__" and any(
        x in str(constructor_eager) for x in ["pandas_pyarrow", "modin"]
    ):
        request.applymarker(pytest.mark.xfail)

    data = {"a": [1, 2, 3]}
    df = nw.from_native(constructor_eager(data), eager_only=True)
    result = df.select(a=getattr(df["a"], attr)(rhs))
    compare_dicts(result, {"a": expected})


def test_truediv_same_dims(constructor_eager: Any, request: Any) -> None:
    if "polars" in str(constructor_eager):
        # https://github.com/pola-rs/polars/issues/17760
        request.applymarker(pytest.mark.xfail)
    s_left = nw.from_native(constructor_eager({"a": [1, 2, 3]}), eager_only=True)["a"]
    s_right = nw.from_native(constructor_eager({"a": [2, 2, 1]}), eager_only=True)["a"]
    result = (s_left / s_right).to_list()
    assert result == [0.5, 1.0, 3.0]
    result = (s_left.__rtruediv__(s_right)).to_list()
    assert result == [2, 1, 1 / 3]


@pytest.mark.slow()
@given(  # type: ignore[misc]
    left=st.integers(-100, 100),
    right=st.integers(-100, 100),
)
@pytest.mark.skipif(
    parse_version(pd.__version__) < (2, 0), reason="convert_dtypes not available"
)
def test_floordiv(left: int, right: int) -> None:
    # hypothesis complains if we add `constructor` as an argument, so this
    # test is a bit manual unfortunately
    assume(right != 0)
    expected = {"a": [left // right]}
    result = nw.from_native(pd.DataFrame({"a": [left]}), eager_only=True).select(
        nw.col("a") // right
    )
    compare_dicts(result, expected)
    if parse_version(pd.__version__) < (2, 2):  # pragma: no cover
        # Bug in old version of pandas
        pass
    else:
        result = nw.from_native(
            pd.DataFrame({"a": [left]}).convert_dtypes(dtype_backend="pyarrow"),
            eager_only=True,
        ).select(nw.col("a") // right)
        compare_dicts(result, expected)
    result = nw.from_native(
        pd.DataFrame({"a": [left]}).convert_dtypes(), eager_only=True
    ).select(nw.col("a") // right)
    compare_dicts(result, expected)
    result = nw.from_native(pl.DataFrame({"a": [left]}), eager_only=True).select(
        nw.col("a") // right
    )
    compare_dicts(result, expected)
    result = nw.from_native(pa.table({"a": [left]}), eager_only=True).select(
        nw.col("a") // right
    )
    compare_dicts(result, expected)


@pytest.mark.slow()
@given(  # type: ignore[misc]
    left=st.integers(-100, 100),
    right=st.integers(-100, 100),
)
@pytest.mark.skipif(
    parse_version(pd.__version__) < (2, 0), reason="convert_dtypes not available"
)
def test_mod(left: int, right: int) -> None:
    # hypothesis complains if we add `constructor` as an argument, so this
    # test is a bit manual unfortunately
    assume(right != 0)
    expected = {"a": [left % right]}
    result = nw.from_native(pd.DataFrame({"a": [left]}), eager_only=True).select(
        nw.col("a") % right
    )
    compare_dicts(result, expected)
    result = nw.from_native(
        pd.DataFrame({"a": [left]}).convert_dtypes(), eager_only=True
    ).select(nw.col("a") % right)
    compare_dicts(result, expected)
    result = nw.from_native(pl.DataFrame({"a": [left]}), eager_only=True).select(
        nw.col("a") % right
    )
    compare_dicts(result, expected)
    result = nw.from_native(pa.table({"a": [left]}), eager_only=True).select(
        nw.col("a") % right
    )
    compare_dicts(result, expected)
