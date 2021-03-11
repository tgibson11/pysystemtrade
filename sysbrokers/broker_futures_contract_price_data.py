from syscore.objects import missing_contract, missing_data


from sysdata.futures.futures_per_contract_prices import (
    futuresContractPriceData,
)


from sysexecution.tick_data import tickerObject, dataFrameOfRecentTicks
from sysexecution.orders.contract_orders import contractOrder
from sysexecution.orders.broker_orders import brokerOrder

from sysobjects.futures_per_contract_prices import futuresContractPrices
from sysobjects.contracts import futuresContract, listOfFuturesContracts

from syslogdiag.log_to_screen import logtoscreen


class brokerFuturesContractPriceData(futuresContractPriceData):
    """
    Extends the baseData object to a data source that reads in and writes prices for specific futures contracts

    This gets HISTORIC data from interactive brokers. It is blocking code
    In a live production system it is suitable for running on a daily basis to get end of day prices

    """

    def __init__(self, log=logtoscreen(
            "brokerFuturesContractPriceData")):
        super().__init__(log=log)



    def get_ticker_object_for_order(self, order: contractOrder) -> tickerObject:
        raise NotImplementedError

    def cancel_market_data_for_order(self, order: brokerOrder):
        raise NotImplementedError

    def get_recent_bid_ask_tick_data_for_contract_object(self, contract_object: futuresContract) ->dataFrameOfRecentTicks:
        raise NotImplementedError

    def _write_prices_for_contract_object_no_checking(self, *args, **kwargs):
        raise NotImplementedError("Broker is a read only source of prices")

    def delete_prices_for_contract_object(self, *args, **kwargs):
        raise NotImplementedError("Broker is a read only source of prices")

    def _delete_prices_for_contract_object_with_no_checks_be_careful(
        self, futures_contract_object: futuresContract
    ):
        raise NotImplementedError("Broker is a read only source of prices")
