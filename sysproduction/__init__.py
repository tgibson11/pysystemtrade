# _ prefix prevents naming conflicts with imports in other scripts
import pandas as _pd

from sysproduction.use_account import use_account

# Show all columns when printing a DataFrame
_pd.options.display.width = 0
# Show more rows when printing a DataFrame
# Default is 10: the first 5 and last 5
_pd.options.display.min_rows = 30

# Prompt user to select the account (config) to use
use_account()
