"""
For a given list of futures contracts

read price data from CSI, and then write to Arctic
Write list of futures contracts to mongodb database
"""
import datetime

from sysdata.arctic.arctic_futures_per_contract_prices import arcticFuturesContractPriceData
from sysdata.csi.csi_futures import CsiFuturesContractPriceData, CsiFuturesConfiguration
from sysdata.futures.contracts import futuresContract
from sysdata.futures.instruments import futuresInstrument
from sysdata.mongodb.mongo_roll_data import mongoRollParametersData


def get_roll_parameters_from_mongo(instrument_code):

    mongo_roll_parameters = mongoRollParametersData()

    roll_parameters = mongo_roll_parameters.get_roll_parameters(instrument_code)
    if roll_parameters.empty():
        raise Exception("Instrument %s missing from %s" % (instrument_code, mongo_roll_parameters))

    return roll_parameters


def create_list_of_contracts(instrument_code):
    instrument_object = futuresInstrument(instrument_code)
    print(instrument_code)
    roll_parameters = get_roll_parameters_from_mongo(instrument_code)

    held_contract_date = roll_parameters.approx_first_held_contractDate_at_date(datetime.datetime.now())
    carry_contract_date = held_contract_date.carry_contract()

    held_contract = futuresContract(instrument_object, held_contract_date)
    carry_contract = futuresContract(instrument_object, carry_contract_date)

    contracts = [held_contract, carry_contract]

    return contracts


def get_and_write_prices_for_contract_list_from_csi_to_arctic(contracts):
    csi_prices_data = CsiFuturesContractPriceData()
    arctic_prices_data = arcticFuturesContractPriceData()

    for contract_object in contracts:
        print("Processing %s" % contract_object.ident())
        csi_price = csi_prices_data.get_prices_for_contract_object(contract_object)

        if csi_price.empty:
            print("Problem reading price data this contract - skipping")
        else:
            print("Read ok, trying to write to arctic")
            try:
                arctic_prices_data.write_prices_for_contract_object(contract_object, csi_price)
            except Exception as e:
                raise Exception("Some kind of issue with arctic - stopping so you can fix it", e)


def get_prices_for_all_instruments():
    for instrument in CsiFuturesConfiguration().get_list_of_instruments():
        get_prices_for_one_instrument(instrument)


def get_prices_for_one_instrument(instrument_code):
    contracts = create_list_of_contracts(instrument_code)
    print("Generated %d contracts" % len(contracts))
    get_and_write_prices_for_contract_list_from_csi_to_arctic(contracts)


if __name__ == '__main__':
    get_prices_for_one_instrument(instrument_code='VIX')
    # get_prices_for_all_instruments()
