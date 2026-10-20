import pandas as pd

# Display all columns when printing a DataFrame
pd.set_option("display.max_columns", 0)

# Display all rows when printing a DataFrame
pd.set_option("display.max_rows", 0)

# Display all columns if width exceeds display width
pd.set_option("display.expand_frame_repr", False)
