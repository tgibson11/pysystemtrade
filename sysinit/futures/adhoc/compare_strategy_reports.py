from typing import Tuple

import pandas as pd
from pandas import DataFrame, Series

from syscore.constants import user_exit
from sysdata.config.configdata import Config
from sysdata.config.control_config import get_control_config
from sysdata.config.production_config import get_production_config
from sysdata.data_blob import dataBlob
from sysproduction.interactive_diagnostics import get_valid_code_from_list


def compare_strategy_reports():
    data = dataBlob()
    config = get_production_config()
    control_config = get_control_config()
    report_1 = config.get_element("compare_strategy_report_1")
    report_2 = config.get_element("compare_strategy_report_2")

    # Parse tables from reports
    optimal_positions_1 = parse_table(
        report_1, table_name="Optimal positions", index_col=1
    )
    optimal_positions_2 = parse_table(
        report_2, table_name="Optimal positions", index_col=1
    )
    portfolio_positions_1 = parse_table(report_1, table_name="Portfolio positions")
    portfolio_positions_2 = parse_table(report_2, table_name="Portfolio positions")
    subsystem_positions_1 = parse_table(report_1, table_name="Subsystem position")
    subsystem_positions_2 = parse_table(report_2, table_name="Subsystem position")
    weighted_forecasts_1 = parse_table(report_1, table_name="Weighted forecasts")
    weighted_forecasts_2 = parse_table(report_2, table_name="Weighted forecasts")
    unweighted_forecasts_1 = parse_table(report_1, table_name="Unweighted forecasts")
    unweighted_forecasts_2 = parse_table(report_2, table_name="Unweighted forecasts")
    forecast_weights_1 = parse_table(report_1, table_name="Forecast weights")
    forecast_weights_2 = parse_table(report_2, table_name="Forecast weights")

    # Extract relevant columns
    optimum_weights_1 = optimal_positions_1["optimum_weight"]
    optimum_weights_2 = optimal_positions_2["optimum_weight"]
    instr_weights_1 = portfolio_positions_1["weight"]
    instr_weights_2 = portfolio_positions_2["weight"]
    combined_forecasts_1 = subsystem_positions_1["forecast"]
    combined_forecasts_2 = subsystem_positions_2["forecast"]

    # Calculate optimum weight difference (for sorting)
    optimum_weight_diff = optimum_weights_2.subtract(optimum_weights_1, fill_value=0)
    optimum_weight_diff = optimum_weight_diff.abs()
    optimum_weight_diff = optimum_weight_diff.rename("optimum_weight_diff")

    # Calculate FDMs
    fdms_1 = calc_fdms(weighted_forecasts_1, combined_forecasts_1)
    fdms_2 = calc_fdms(weighted_forecasts_2, combined_forecasts_2)

    # Append report identifier to column names
    optimum_weights_1 = optimum_weights_1.rename("optimum_weight_1")
    optimum_weights_2 = optimum_weights_2.rename("optimum_weight_2")
    instr_weights_1 = instr_weights_1.rename("instr_weight_1")
    instr_weights_2 = instr_weights_2.rename("instr_weight_2")
    combined_forecasts_1 = combined_forecasts_1.rename("combined_forecast_1")
    combined_forecasts_2 = combined_forecasts_2.rename("combined_forecast_2")
    fdms_1 = fdms_1.rename("FDM_1")
    fdms_2 = fdms_2.rename("FDM_2")

    # Construct the primary result
    optimum_weights = pd.concat(
        [
            optimum_weights_1,
            optimum_weights_2,
            optimum_weight_diff,
            instr_weights_1,
            instr_weights_2,
            combined_forecasts_1,
            combined_forecasts_2,
            fdms_1,
            fdms_2,
        ],
        axis=1,
        join="outer",
    )

    optimum_weights = optimum_weights.sort_values(
        "optimum_weight_diff", ascending=False
    )
    print_with_title(optimum_weights, "Optimal Weights & Key Inputs")

    # Select an instrument for further analysis, or exit
    instruments = optimum_weights.index.values
    instrument = get_valid_code_from_list(instruments)
    if instrument is user_exit:
        return

    # Extract weighted forecasts for instrument
    instr_weighted_forecasts_1 = weighted_forecasts_1.loc[instrument].rename("forecast_1")
    instr_weighted_forecasts_2 = weighted_forecasts_2.loc[instrument].rename("forecast_2")

    # Calculate forecast difference (for sorting)
    forecast_diff = instr_weighted_forecasts_2.subtract(instr_weighted_forecasts_1, fill_value=0)
    forecast_diff = forecast_diff.abs()
    forecast_diff = forecast_diff.rename("forecast_diff")

    # Construct weighted forecasts result
    weighted_forecasts = (pd.concat(
        [
            instr_weighted_forecasts_1,
            instr_weighted_forecasts_2,
            forecast_diff,
        ],
        axis=1,
        join="outer",
    ))

    weighted_forecasts = weighted_forecasts.sort_values(
        "forecast_diff", ascending=False
    )

    print_with_title(weighted_forecasts, f"Weighted Forecasts for {instrument}")

    # Select a forecast for further analysis, or exit
    forecasts = weighted_forecasts.index.values
    forecast = get_valid_code_from_list(forecasts)
    if forecast is user_exit:
        return

    # Extract forecast weights for selected forecast
    forecast_weights_for_forecast_1 = forecast_weights_1[forecast].rename("forecast_weight_1")
    forecast_weights_for_forecast_2 = forecast_weights_2[forecast].rename("forecast_weight_2")

    # Construct forecast weights result
    forecast_weights = (pd.concat(
        [
            forecast_weights_for_forecast_1,
            forecast_weights_for_forecast_2,
        ],
        axis=1,
        join="outer",
    ))

    print_with_title(forecast_weights, f"Forecast weights for {forecast}")

    # Extract unweighted forecasts for selected forecast
    unweighted_forecasts_for_forecast_1 = unweighted_forecasts_1[forecast].rename("unweighted_forecast_1")
    unweighted_forecasts_for_forecast_2 = unweighted_forecasts_2[forecast].rename("unweighted_forecast_2")

    # Get configured forecast scalars
    process_configuration_methods = control_config.get_element("process_configuration_methods")
    run_systems_config = process_configuration_methods.get("run_systems")
    # Assmume there is just one system defined, and get it, regardless of name
    my_system_config = next(iter(run_systems_config.values()))
    config_filename = my_system_config.get("backtest_config_filename")
    system_config = Config(config_filename)
    forecast_scalars_dict = system_config.get_element("forecast_scalars")
    forecast_scalar = forecast_scalars_dict.get(forecast)
    configured_forecast_scalars = pd.Series(
        forecast_scalar, index=unweighted_forecasts_for_forecast_1.index
    )
    configured_forecast_scalars = configured_forecast_scalars.rename("forecast_scalar_2_config")

    # Infer forecast scalars
    implied_forecast_scalars = (
        unweighted_forecasts_for_forecast_1 * configured_forecast_scalars / unweighted_forecasts_for_forecast_2
    )
    implied_forecast_scalars = implied_forecast_scalars.rename("forecast_scalar_1_implied")
    implied_forecast_scalars = round(implied_forecast_scalars, 3)

    # Construct unweighted forecasts & forecast scalars result
    unweighted_forecasts = (pd.concat(
        [
            unweighted_forecasts_for_forecast_1,
            unweighted_forecasts_for_forecast_2,
            implied_forecast_scalars,
            configured_forecast_scalars,
        ],
        axis=1,
        join="outer",
    ))

    print_with_title(unweighted_forecasts, f"Unweighted forecasts for {forecast}")


def parse_table(filepath: str, table_name: str, index_col: int = 0) -> DataFrame:
    header_index, last_row_index = calc_table_start_end(
        filepath, table_name
    )

    num_rows = last_row_index - header_index

    table = pd.read_fwf(
        filepath,
        skiprows=header_index,
        nrows=num_rows,
        index_col=index_col,
    )

    return table


def calc_table_start_end(filepath: str, table_name: str) -> Tuple[int, int]:
    header_index = None
    last_row_index = None
    with open(filepath,'r') as file:
        for idx, line in enumerate(file):
            if header_index is None and line.strip() == table_name:
                header_index = idx + 2
            elif header_index is not None and idx > header_index and line.strip() == "":
                last_row_index = idx - 1
                break
    return header_index, last_row_index


def calc_fdms(weighted_forecasts: DataFrame, combined_forecasts: Series) -> Series:
    sum_weighted_forecasts = weighted_forecasts.sum(axis=1, skipna=True)
    fdms = round(combined_forecasts / sum_weighted_forecasts, 1)
    return fdms


def compare_forecast_tables(df1: DataFrame, df2: DataFrame) -> DataFrame:
    result = df2.fillna(0) - df1.fillna(0)

    sum_by_instrument = result.sum(axis=1, skipna=True).rename("Total")
    result = pd.concat([result, sum_by_instrument], axis=1)

    result.loc['Total'] = result.sum(skipna=True)
    return result


def print_with_title(df: DataFrame, title: str):
    from sysproduction.reporting.reporting_functions import table
    from sysproduction.reporting.reporting_functions import parse_table as parse_report_table
    print(parse_report_table(table(title, str(df))))

if __name__ == "__main__":
    compare_strategy_reports()