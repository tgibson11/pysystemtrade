# _ prefix prevents naming conflicts with imports in other scripts
import pandas as _pd

# Show all columns when printing a DataFrame
_pd.options.display.width = 0
# Show more rows when printing a DataFrame
# Default is 10: the first 5 and last 5
_pd.options.display.min_rows = 30
