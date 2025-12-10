import matplotlib
import pandas as pd
from matplotlib import pyplot as plt

from sysdata.config.production_config import get_production_config
from sysdata.data_blob import get_parquet_root_directory
from sysdata.parquet.parquet_access import ParquetAccess
from sysdata.parquet.parquet_futures_per_contract_prices import parquetFuturesContractPriceData

config = get_production_config()
parquet_root_directory = get_parquet_root_directory(config)
parquet_access = ParquetAccess(parquet_root_directory)
historical_prices = parquetFuturesContractPriceData(parquet_access)

hist_prices = historical_prices.get_merged_prices_for_instrument("EURIBOR-ICE")

prices_final = hist_prices.final_prices()
prices_final_as_pd = pd.concat(prices_final, axis=1)

# print(prices_final_as_pd['1998-01-01':'1998-12-31'].to_string())
# exit(0)

# Inspect prices
prices_final_as_pd.plot()
matplotlib.use('TkAgg')
plt.show()

# Inspect % change
perc = prices_final_as_pd.diff()/prices_final_as_pd.shift(1)
perc.plot()
plt.show()
