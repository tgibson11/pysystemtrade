from sysdata.barchart.bc_connection import ConnectionBC
from sysdata.data_blob import dataBlob
from sysproduction.data.contracts import dataContracts

bc = ConnectionBC()

data = dataBlob(log_name="Barchart-Test")
diag_contracts = dataContracts(data)
all_contracts_list = diag_contracts.get_all_contract_objects_for_instrument_code("AUD")
contract_list = all_contracts_list.currently_sampling()
print(contract_list)

for contract in contract_list[0:1]:
    prices = bc.get_historical_futures_data_for_contract(contract)
    print(f"\n{prices}")
