"""
For a given list of futures contracts defined by Quandl start dates:

read price data from quandl, and then write to arctic
Write list of futures contracts to mongodb database
"""
import datetime

from sysdata.mongodb.mongo_futures_instruments import mongoFuturesInstrumentData
from sysdata.quandl.quandl_futures import (
    quandlFuturesConfiguration,
    quandlFuturesContractPriceData,
)
from sysobjects.contracts import listOfFuturesContracts, futuresContract
from sysobjects.instruments import futuresInstrument
from sysdata.mongodb.mongo_roll_data import mongoRollParametersData
from sysdata.arctic.arctic_futures_per_contract_prices import (
    arcticFuturesContractPriceData,
)
from sysobjects.rolls import contractDateWithRollParameters


def get_roll_parameters_from_mongo(instrument_code):

    mongo_roll_parameters = mongoRollParametersData()

    roll_parameters = mongo_roll_parameters.get_roll_parameters(
        instrument_code)
    if roll_parameters.empty():
        raise Exception(
            "Instrument %s missing from %s" %
            (instrument_code, mongo_roll_parameters))

    return roll_parameters


def get_first_contract_date_from_quandl(instrument_code):
    config = quandlFuturesConfiguration()
    return config.get_first_contract_date(instrument_code)


def create_list_of_contracts(instrument_code):
    instrument_object = futuresInstrument(instrument_code)
    print(instrument_code)
    roll_parameters = get_roll_parameters_from_mongo(instrument_code)
    first_contract_date = get_first_contract_date_from_quandl(instrument_code)

    list_of_contracts = historical_price_contracts(
        instrument_object, roll_parameters, first_contract_date
    )

    return list_of_contracts


def get_and_write_prices_for_contract_list_from_quandl_to_arctic(
        list_of_contracts):
    quandl_prices_data = quandlFuturesContractPriceData()
    arctic_prices_data = arcticFuturesContractPriceData()

    for contract_object in list_of_contracts:
        print("Processing %s" % contract_object.key)
        quandl_price = quandl_prices_data.get_prices_for_contract_object(
            contract_object
        )

        if quandl_price.empty:
            print("Problem reading price data this contract - skipping")
        else:
            print("Read ok, trying to write to arctic")
            try:
                arctic_prices_data.write_prices_for_contract_object(
                    contract_object, quandl_price
                )
            except BaseException:
                raise Exception(
                    "Some kind of issue with arctic - stopping so you can fix it"
                )


# TODO the following functions used to be methods on listOfFuturesContracts
# Rob has removed them as part of his refactoring; I'm not sure if this will be temporary or not

MAX_CONTRACT_SIZE = 10000


def historical_price_contracts(
    instrument_object,
    roll_parameters,
    first_contract_date,
    end_date=datetime.datetime.now(),
):
    """
    We want to get all the contracts that fit in the roll cycle, bearing in mind the RollOffsetDays (in roll_parameters)
      So for example suppose we want all contracts since 1st January 1980, to the present day, for
      Eurodollar; where the rollcycle = "HMUZ" (quarterly IMM) and where the rollOffSetDays is 1100
      (we want to be around 3 years in the future; eg 12 contracts). If it's current 1st January 2018
      then we'd get all contracts with expiries between 1st January 1980 to approx 1st January 2021

    This uses the 'priceRollCycle' rollCycle in instrument_object, which is a superset of the heldRollCycle


    :param instrument_object: An instrument object
    :param roll_parameters: rollParameters
    :param first_contract_date: The first contract date, 'eg yyyymm'
    :param end_date: The date when we want to stop getting data, defaults to today

    :return: list of futuresContracts
    """

    first_contract = futuresContract(
        instrument_object, contractDateWithRollParameters(
            roll_parameters, first_contract_date))

    assert end_date > first_contract.expiry_date

    current_held_contract_date = roll_parameters.approx_first_held_futuresContract_at_date(end_date)
    current_held_contract = futuresContract(instrument_object, current_held_contract_date)

    current_priced_contract_date = roll_parameters.approx_first_priced_futuresContract_at_date(end_date)
    current_priced_contract = futuresContract(instrument_object, current_priced_contract_date)

    current_carry_contract = current_held_contract.carry_contract()

    # these are all str thats okay
    last_contract_date = max(
        [
            current_held_contract.date,
            current_priced_contract.date,
            current_carry_contract.date,
        ]
    )

    list_of_contracts = [first_contract]

    # note the same instrument_object will be shared by all in the list so
    # we can modify it directly if needed
    date_still_valid = True
    current_contract = first_contract

    while date_still_valid:
        next_contract = current_contract.next_priced_contract()

        list_of_contracts.append(next_contract)

        if next_contract.date >= last_contract_date:
            date_still_valid = False
            # will now terminate
        if len(list_of_contracts) > MAX_CONTRACT_SIZE:
            raise Exception("Too many contracts - check your inputs")

        current_contract = next_contract

    return listOfFuturesContracts(list_of_contracts)


if __name__ == '__main__':
    instrument_data = mongoFuturesInstrumentData()
    print(instrument_data)
    instrument_list = instrument_data.get_list_of_instruments()

    for instrument in instrument_list:

        contracts = create_list_of_contracts(instrument)
        print(contracts)

        print("Generated %d contracts" % len(contracts))

        get_and_write_prices_for_contract_list_from_quandl_to_arctic(contracts)
