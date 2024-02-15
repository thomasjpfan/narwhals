import pandas as pd
import polars_api_compat
import polars as pl
from datetime import datetime

df = pd.DataFrame({'a': [1,2,3], 'b': [4,5,6]})
dfx, plx = polars_api_compat.convert(df, api_version='0.20')

result = dfx.with_columns(
    c = plx.col('a') + plx.col('b'),
    d = plx.col('a') - plx.col('a').mean(),
)
print(result.dataframe)
result = dfx.with_columns(
    plx.all() *2
)
print(result.dataframe)

result = dfx.with_columns(
    horizonal_sum = plx.sum_horizontal(plx.col('a'), plx.col('b'))
)
print(result.dataframe)
result = dfx.select(
    plx.all().sum()
)
print(result.dataframe)

# i mean, could well have something that takes multiples, right?
# i think, just need to splat them?

# when should index validation happen?
# - in validate_comparand: yeah, probably
# - in select and with_columns: yeah, if they're the same length

# really take your time here. utils should do everything!
