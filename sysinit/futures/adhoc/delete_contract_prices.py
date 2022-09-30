from syscore.dateutils import Frequency
from sysdata.arctic.arctic_futures_per_contract_prices import arcticFuturesContractPriceData
from sysdata.data_blob import dataBlob
from sysdata.mongodb.mongo_connection import mongoDb
from sysobjects.contracts import futuresContract
from sysproduction.data.contracts import get_valid_instrument_code_and_contractid_from_user
from sysproduction.data.prices import get_valid_instrument_code_from_user

mongo_db = mongoDb()
arctic_prices = arcticFuturesContractPriceData()

do_another = True

while do_another:
    exit_code = "EXIT"
    instrument_code = get_valid_instrument_code_from_user(allow_exit=True, exit_code=exit_code, source="single")

    if instrument_code != exit_code:

        delete_all_contracts_for_instrument = input("Delete ALL contracts for instrument? (y/n)")
        if delete_all_contracts_for_instrument == "y":
            contracts_to_delete = arctic_prices.contracts_with_merged_price_data_for_instrument_code(instrument_code)
        else:
            instrument_code, contract_date = get_valid_instrument_code_and_contractid_from_user(
                dataBlob(), instrument_code=instrument_code)
            contracts_to_delete = [futuresContract(instrument_code, contract_date)]

        for contract in contracts_to_delete:
            arctic_prices.delete_merged_prices_for_contract_object(contract, areyousure=True)
            arctic_prices.delete_prices_at_frequency_for_contract_object(contract, Frequency.Day, areyousure=True)
            arctic_prices.delete_prices_at_frequency_for_contract_object(contract, Frequency.Hour, areyousure=True)
