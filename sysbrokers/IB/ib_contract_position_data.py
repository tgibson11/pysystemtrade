from syslogdiag.log_to_screen import logtoscreen
from sysbrokers.IB.ib_futures_contracts_data import ibFuturesContractData

from sysbrokers.IB.client.ib_positions_client import ibPositionsClient
from sysbrokers.IB.ib_instruments_data import ibFuturesInstrumentData
from sysbrokers.IB.ib_connection import connectionIB
from sysbrokers.broker_contract_position_data import brokerContractPositionData

from syscore.objects import arg_not_supplied, missing_contract


from sysobjects.production.positions import contractPosition, listOfContractPositions
from sysobjects.contracts import futuresContract

class ibContractPositionData(brokerContractPositionData):
    def __init__(self, ibconnection: connectionIB, log=logtoscreen(
            "ibFuturesContractPriceData")):
        self._ibconnection = ibconnection
        super().__init__(log=log)

    @property
    def ibconnection(self) -> connectionIB:
        return self._ibconnection

    @property
    def ib_client(self) -> ibPositionsClient:
        client = getattr(self, "_ib_client", None)
        if client is None:
             client = self._ib_client = ibPositionsClient(ibconnection=self.ibconnection,
                                                   log = self.log)

        return client


    def __repr__(self):
        return "IB Futures per contract position data %s" % str(
            self.ib_client)

    @property
    def futures_contract_data(self) ->  ibFuturesContractData:
        return ibFuturesContractData(self.ibconnection, log=self.log)

    @property
    def futures_instrument_data(self) -> ibFuturesInstrumentData:
        return ibFuturesInstrumentData(self.ibconnection, log = self.log)

    def get_all_current_positions_as_list_with_contract_objects(
        self, account_id=arg_not_supplied
    ) -> listOfContractPositions:

        all_positions = self._get_all_futures_positions_as_raw_list(
            account_id=account_id
        )
        current_positions = []
        for position_entry in all_positions:
            contract_position_object = self._get_contract_position_for_raw_entry(position_entry)
            if contract_position_object is missing_contract:
                continue
            else:
                current_positions.append(contract_position_object)

        list_of_contract_positions = listOfContractPositions(current_positions)

        return list_of_contract_positions

    def _get_contract_position_for_raw_entry(self, position_entry) -> contractPosition:
        position = position_entry["position"]
        if position == 0:
            return missing_contract

        ib_code = position_entry["symbol"]
        instrument_code = (
            self.futures_instrument_data.get_instrument_code_from_broker_code(ib_code))
        expiry = position_entry["expiry"]

        contract = futuresContract(instrument_code, expiry)

        contract_position_object = contractPosition(
            position, contract
        )

        return contract_position_object

    def _get_all_futures_positions_as_raw_list(
            self, account_id: str=arg_not_supplied) -> list:
        self.ib_client.refresh()
        all_positions = self.ib_client.broker_get_positions(
            account_id=account_id)
        positions = all_positions.get("FUT", [])

        return positions


    def get_position_as_df_for_contract_object(self, *args, **kwargs):
        raise Exception("Only current position data available from IB")

    def update_position_for_contract_object(self, *args, **kwargs):
        raise Exception("IB position data is read only")

    def delete_last_position_for_contract_object(self, *args, **kwargs):
        raise Exception("IB position data is read only")

    def _get_series_for_args_dict(self, *args, **kwargs):
        raise Exception("Only current position data available from IB")

    def _update_entry_for_args_dict(self, *args, **kwargs):
        raise Exception("IB position data is read only")

    def _delete_last_entry_for_args_dict(self, *args, **kwargs):
        raise Exception("IB position data is read only")

    def _get_list_of_args_dict(self) -> list:
        raise Exception("Args dict not used for IB")

    def get_list_of_instruments_with_any_position(self):
        raise  Exception("Not implemented for IB")