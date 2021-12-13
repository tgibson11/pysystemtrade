from sysdata.arctic.arctic_futures_per_contract_prices import (
    arcticFuturesContractPriceData,
)
from sysdata.arctic.arctic_multiple_prices import arcticFuturesMultiplePricesData
from sysdata.arctic.arctic_adjusted_prices import arcticFuturesAdjustedPricesData

from sysdata.csv.csv_roll_calendars import csvRollCalendarData
from sysdata.csv.csv_multiple_prices import csvFuturesMultiplePricesData
from sysdata.csv.csv_adjusted_prices import csvFuturesAdjustedPricesData

from sysobjects.contracts import futuresContract

db_data_individual_prices = arcticFuturesContractPriceData()
db_data_multiple_prices = arcticFuturesMultiplePricesData()
db_data_adjusted_prices = arcticFuturesAdjustedPricesData()

csv_roll_calendar = csvRollCalendarData()
csv_multiple = csvFuturesMultiplePricesData()
csv_adjusted = csvFuturesAdjustedPricesData()


def clone_data_for_instrument(
    instrument_from: str, instrument_to: str, write_to_csv: bool = False
):

    clone_prices_per_contract(instrument_from, instrument_to)
    if write_to_csv:
        clone_roll_calendar(instrument_from, instrument_to)

    clone_multiple_prices(instrument_from, instrument_to, write_to_csv=write_to_csv)
    clone_adjusted_prices(instrument_from, instrument_to, write_to_csv=write_to_csv)


def clone_prices_per_contract(instrument_from: str, instrument_to: str):

    list_of_contract_dates = (
        db_data_individual_prices.contract_dates_with_price_data_for_instrument_code(
            instrument_from
        )
    )

    _ = [
        clone_single_contract(instrument_from, instrument_to, contract_date)
        for contract_date in list_of_contract_dates
    ]


def clone_single_contract(instrument_from: str, instrument_to: str, contract_date: str):

    data_in = db_data_individual_prices.get_prices_for_contract_object(
        futuresContract(instrument_from, contract_date)
    )
    db_data_individual_prices.write_prices_for_contract_object(
        futuresContract(instrument_to, contract_date), futures_price_data=data_in
    )


def clone_roll_calendar(instrument_from: str, instrument_to: str):

    roll_calendar = csv_roll_calendar.get_roll_calendar(instrument_from)
    csv_roll_calendar.add_roll_calendar(instrument_to, roll_calendar=roll_calendar)


def clone_multiple_prices(
    instrument_from: str, instrument_to: str, write_to_csv: bool = True
):

    prices = db_data_multiple_prices.get_multiple_prices(instrument_from)
    db_data_multiple_prices.add_multiple_prices(
        instrument_to, multiple_price_data=prices
    )

    if write_to_csv:
        csv_multiple.add_multiple_prices(instrument_to, multiple_price_data=prices)


def clone_adjusted_prices(
    instrument_from: str, instrument_to: str, write_to_csv: bool = True
):

    prices = db_data_adjusted_prices.get_adjusted_prices(instrument_from)
    db_data_adjusted_prices.add_adjusted_prices(
        instrument_to, adjusted_price_data=prices
    )
    if write_to_csv:
        csv_adjusted.add_adjusted_prices(instrument_to, adjusted_price_data=prices)
