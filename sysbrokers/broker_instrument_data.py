from sysdata.data_blob import dataBlob
from sysdata.futures.instruments import futuresInstrumentData

from syslogging.logger import *


class brokerFuturesInstrumentData(futuresInstrumentData):
    """
    Extends the baseData object to a data source that reads in and writes prices for specific futures contracts

    This gets HISTORIC data from interactive brokers. It is blocking code
    In a live production system it is suitable for running on a daily basis to get end of day prices

    """

    def __init__(self, data: dataBlob, log=get_logger("brokerFuturesInstrumentData")):
        super().__init__(log=log)
        self._data = data

    def get_instrument_code_from_broker_contract_object(
        self, broker_contract_object: str
    ) -> str:
        raise NotImplementedError

    def get_list_of_instruments(self) -> list:
        raise NotImplementedError

    @property
    def data(self) -> dataBlob:
        return self._data
