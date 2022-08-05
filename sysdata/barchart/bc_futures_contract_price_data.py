from sysbrokers.broker_futures_contract_price_data import brokerFuturesContractPriceData
from syscore.dateutils import Frequency, DAILY_PRICE_FREQ
from syscore.objects import missing_data, missing_instrument
from sysdata.barchart.bc_connection import BcConnection
from sysdata.barchart.bc_instruments_data import BarchartFuturesInstrumentData
from sysexecution.orders.broker_orders import brokerOrder
from sysexecution.orders.contract_orders import contractOrder
from sysexecution.tick_data import dataFrameOfRecentTicks, tickerObject
from syslogdiag.log_to_screen import logtoscreen
from sysobjects.contracts import futuresContract
from sysobjects.futures_per_contract_prices import futuresContractPrices


class BarchartFuturesContractPriceData(brokerFuturesContractPriceData):

    """
    Extends the futuresContractPriceData object to a data source that reads in prices
    for specific futures contracts

    This gets HISTORIC data from barchart.com
    In a live production system it is suitable for running on a daily basis to get end of day prices
    """

    def __init__(self, log=logtoscreen("barchartFuturesContractPriceData")):
        super().__init__(log=log)
        self._barchart = BcConnection()

    def __repr__(self):
        return f"Barchart Futures per contract price data {str(self._barchart)}"

    @property
    def log(self):
        return self._log

    @property
    def barchart(self):
        return self._barchart

    @property
    def futures_instrument_data(self) -> BarchartFuturesInstrumentData:
        return BarchartFuturesInstrumentData(log=self.log)

    def has_data_for_contract(self, futures_contract: futuresContract) -> bool:
        return self._barchart.has_data_for_contract(futures_contract)

    def get_list_of_instrument_codes_with_price_data(self) -> list:
        # return list of instruments for which pricing is configured
        list_of_instruments = self.futures_instrument_data.get_list_of_instruments()
        return list_of_instruments

    def get_contracts_with_price_data(self):
        raise NotImplementedError(
            "Do not use get_contracts_with_price_data() with Barchart"
        )

    def _get_prices_for_contract_object_no_checking(
        self, contract_object: futuresContract
    ) -> futuresContractPrices:
        return self._get_prices_at_frequency_for_contract_object_no_checking(
            contract_object, freq="D"
        )

    def _get_prices_at_frequency_for_contract_object_no_checking(
        self, contract_object: futuresContract, freq: Frequency
    ) -> futuresContractPrices:

        """
        Get historical prices at a particular frequency

        We override this method, rather than _get_prices_at_frequency_for_contract_object_no_checking
        Because the list of dates returned by contracts_with_price_data is likely to not match (expiries)

        :param contract_object:  futuresContract
        :param freq: str; one of D, H, 15M, 5M, M, 10S, S
        :return: data
        """

        barchart_contract_id = self.barchart.get_barchart_id(contract_object)

        if barchart_contract_id is missing_instrument:
            self.log.warn(f"Can't get data for {str(contract_object)}")
            return futuresContractPrices.create_empty()

        price_data = self._barchart.get_historical_futures_data_for_contract(
            barchart_contract_id, bar_freq=freq
        )

        if price_data is missing_data:
            self.log.warn(
                f"Problem getting Barchart price data for {str(contract_object)}",
                instrument_code=contract_object.instrument_code,
                contract_date=contract_object.contract_date.date_str,
            )
            price_data = futuresContractPrices.create_empty()

        elif len(price_data) == 0:
            self.log.warn(f"No Barchart price data found for {str(contract_object)}")
            price_data = futuresContractPrices.create_empty()
        else:
            price_data = futuresContractPrices(price_data)

        return price_data

    def _write_prices_for_contract_object_no_checking(self, *args, **kwargs):
        raise NotImplementedError("Barchart is a read only source of prices")

    def delete_prices_for_contract_object(self, *args, **kwargs):
        raise NotImplementedError("Barchart is a read only source of prices")

    def _delete_prices_for_contract_object_with_no_checks_be_careful(
        self, contract_object: futuresContract
    ):
        raise NotImplementedError("Barchart is a read only source of prices")

    def get_ticker_object_for_order(self, order: contractOrder) -> tickerObject:
        raise NotImplementedError("Not implemented for Barchart, it is not a broker")

    def cancel_market_data_for_order(self, order: brokerOrder):
        raise NotImplementedError("Not implemented for Barchart, it is not a broker")

    def get_recent_bid_ask_tick_data_for_contract_object(
        self, contract_object: futuresContract
    ) -> dataFrameOfRecentTicks:
        raise NotImplementedError("Not implemented for Barchart, it is not a broker")

    def get_prices_at_frequency_for_potentially_expired_contract_object(
        self, contract: futuresContract, freq: Frequency = DAILY_PRICE_FREQ
    ) -> futuresContractPrices:
        raise NotImplementedError("Not implemented for Barchart")
