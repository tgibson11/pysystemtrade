"""
For a given list of futures contracts defined by Quandl start dates:

read price data from quandl, and then write to artic
Write list of futures contracts to mongodb database
"""

from sysdata.arctic.arctic_futures_per_contract_prices import arcticFuturesContractPriceData
from sysdata.csv.csv_roll_calendars import csvRollCalendarData
from sysdata.futures.contracts import listOfFuturesContracts
from sysdata.futures.instruments import futuresInstrument
from sysdata.futures.roll_calendars import rollCalendar
from sysdata.futures.rolls import contractDateWithRollParameters
from sysdata.mongodb.mongo_roll_data import mongoRollParametersData
from sysdata.quandl.quandl_futures import quandlFuturesConfiguration, quandlFuturesContractPriceData


def get_roll_parameters_from_mongo(instrument_code):

    mongo_roll_parameters = mongoRollParametersData()

    roll_parameters = mongo_roll_parameters.get_roll_parameters(instrument_code)
    if roll_parameters.empty():
        raise Exception("Instrument %s missing from %s" % (instrument_code, mongo_roll_parameters))

    return roll_parameters


def get_first_contract_date_from_quandl(instrument_code):
    config = quandlFuturesConfiguration()
    return config.get_first_contract_date(instrument_code)


def create_list_of_contracts(instrument_code, current_only=False):
    instrument_object = futuresInstrument(instrument_code)
    print(instrument_code)
    roll_parameters = get_roll_parameters_from_mongo(instrument_code)

    if not current_only:
        first_contract_date = get_first_contract_date_from_quandl(instrument_code)
    else:
        roll_calendar = rollCalendar(csvRollCalendarData().get_roll_calendar(instrument_code))
        last_contract_date = contractDateWithRollParameters(roll_parameters,
                                                            roll_calendar.last_current_contract().contract_date)
        unexpired_contract_dates = last_contract_date.get_unexpired_contracts_from_now_to_contract_date()
        first_contract_date = unexpired_contract_dates[-1].contract_date

    list_of_contracts = listOfFuturesContracts.historical_price_contracts(instrument_object, roll_parameters,
                                                                      first_contract_date)

    return list_of_contracts


def get_and_write_prices_for_contract_list_from_quandl_to_arctic(list_of_contracts):
    quandl_prices_data = quandlFuturesContractPriceData()
    arctic_prices_data = arcticFuturesContractPriceData()

    for contract_object in list_of_contracts:
        print("Processing %s" % contract_object.ident())
        quandl_price = quandl_prices_data.get_prices_for_contract_object(contract_object)
        # print(quandl_price)

        if quandl_price.empty:
            print("Problem reading price data this contract - skipping")
        else:
            if quandl_price.tail(1).iloc[0]['SETTLE'] == 0.0:
                # Drop last row if settle price is 0
                quandl_price = quandl_price[:-1]
            print("Read ok, trying to write to arctic")
            try:
                arctic_prices_data.write_prices_for_contract_object(contract_object, quandl_price)
            except:
                raise Exception("Some kind of issue with arctic - stopping so you can fix it")


def get_prices_for_instruments(instrument_list=None, current_only=False):
    if not instrument_list:
        instrument_list = quandlFuturesConfiguration().get_list_of_instruments()
    for instrument_code in instrument_list:
        contracts = create_list_of_contracts(instrument_code, current_only=current_only)
        print("Generated %d contracts" % len(contracts))
        get_and_write_prices_for_contract_list_from_quandl_to_arctic(contracts)


if __name__ == '__main__':
    get_prices_for_instruments(instrument_list=[], current_only=True)
