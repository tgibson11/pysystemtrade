from sysbrokers.broker_futures_contract_price_data import brokerFuturesContractPriceData
from syscore.dateutils import Frequency, DAILY_PRICE_FREQ
from sysdata.barchart.bc_connection import bcConnection
from sysexecution.orders.broker_orders import brokerOrder
from sysexecution.orders.contract_orders import contractOrder
from sysexecution.tick_data import dataFrameOfRecentTicks, tickerObject
from syslogdiag.log_to_screen import logtoscreen
from sysobjects.contracts import futuresContract, listOfFuturesContracts
from sysobjects.futures_per_contract_prices import futuresContractPrices


class bcFuturesContractPriceData(brokerFuturesContractPriceData):
    """
    Extends the base class to a data source that reads in prices for specific futures contracts

    This gets HISTORIC data from Barchart.com
    In a live production system it is suitable for running on a daily basis to get end of day prices

    """

    def __init__(self, bc_connection: bcConnection, log=logtoscreen("bcFuturesContractPriceData")):
        self._bc_connection = bc_connection
        super().__init__(log=log)

    def get_prices_at_frequency_for_potentially_expired_contract_object(
            self, contract: futuresContract, freq: Frequency = DAILY_PRICE_FREQ) -> futuresContractPrices:
        pass

    def get_ticker_object_for_order(self, order: contractOrder) -> tickerObject:
        pass

    def cancel_market_data_for_order(self, order: brokerOrder):
        pass

    def get_recent_bid_ask_tick_data_for_contract_object(self,
                                                         contract_object: futuresContract) -> dataFrameOfRecentTicks:
        pass

    def _write_prices_for_contract_object_no_checking(self, *args, **kwargs):
        pass

    def delete_prices_for_contract_object(self, *args, **kwargs):
        pass

    def _delete_prices_for_contract_object_with_no_checks_be_careful(self, futures_contract_object: futuresContract):
        pass

    def get_contracts_with_price_data(self) -> listOfFuturesContracts:
        return listOfFuturesContracts()

    def _get_prices_for_contract_object_no_checking(self, contract_object: futuresContract) -> futuresContractPrices:
        pass

    def _get_prices_at_frequency_for_contract_object_no_checking(self, contract_object: futuresContract,
                                                                 freq: Frequency) -> futuresContractPrices:
        pass
