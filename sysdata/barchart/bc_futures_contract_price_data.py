from typing import Optional

from sysbrokers.broker_futures_contract_price_data import brokerFuturesContractPriceData
from syscore.dateutils import Frequency, DAILY_PRICE_FREQ
from syscore.exceptions import missingData
from sysdata.barchart.bc_connection import ConnectionBC
from sysdata.barchart.bc_futures_contract import BcFuturesContract
from sysdata.barchart.bc_instruments_data import BarchartFuturesInstrumentData
from sysdata.data_blob import dataBlob
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

    def __init__(self, bc_connection: ConnectionBC, data: dataBlob, log=logtoscreen("bcFuturesContractPriceData")):
        self._bc_connection = bc_connection
        self._futures_instrument_data = BarchartFuturesInstrumentData(log=log)
        super().__init__(data=data, log=log)

    def __repr__(self):
        return "Barchart futures per contract price data"

    @property
    def barchart(self):
        return self._bc_connection

    @property
    def futures_instrument_data(self) -> BarchartFuturesInstrumentData:
        return self._futures_instrument_data

    def has_merged_price_data_for_contract(self, futures_contract: futuresContract) -> bool:
        """
        Does Barchart have data for a given contract?

        Overridden because the parent implementation is to check a list of all available contracts,
        which we can't get from Barchart
        :param futures_contract:
        :return: bool
        """

        bc_contract_id = self._get_bc_contract_id(futures_contract)
        return self.barchart.has_data_for_contract(bc_contract_id)

    def has_price_data_for_contract_at_frequency(self, contract_object: futuresContract, frequency: Frequency) -> bool:
        """
        Does Barchart have data for a given contract?

        Overridden because the parent implementation is to check a list of all available contracts,
        which we can't get from Barchart
        :param contract_object:
        :param frequency
        :return: bool
        """
        # This check isn't for a specific frequency though
        bc_contract_id = self._get_bc_contract_id(contract_object)
        return self.barchart.has_data_for_contract(bc_contract_id)

    def get_contracts_with_merged_price_data(self) -> listOfFuturesContracts:
        raise NotImplementedError("Do not use get_contracts_with_merged_price_data with Barchart")

    def get_contracts_with_price_data_for_frequency(self, frequency: Frequency) -> listOfFuturesContracts:
        raise NotImplementedError("Do not use get_contracts_with_price_data_for_frequency with Barchart")

    def get_prices_at_frequency_for_potentially_expired_contract_object(
            self, contract: futuresContract, freq: Frequency = DAILY_PRICE_FREQ) -> futuresContractPrices:

        price_data = self._get_prices_at_frequency_for_contract_object_no_checking(contract, frequency=freq)
        return price_data

    def _get_merged_prices_for_contract_object_no_checking(
            self, contract_object: futuresContract) -> futuresContractPrices:
        price_series = self._get_prices_at_frequency_for_contract_object_no_checking(
            contract_object, frequency=DAILY_PRICE_FREQ
        )

        return price_series

    def _get_prices_at_frequency_for_contract_object_no_checking(self, contract_object: futuresContract,
                                                                 frequency: Frequency) -> futuresContractPrices:
        """
        Get historical prices at a particular frequency

        :param contract_object:  futuresContract
        :param frequency: Frequency; one of D, H, 15M, 5M, M, 10S, S
        :return: data
        """

        new_log = contract_object.log(self.log)

        bc_futures_contract = self._get_bc_futures_contract(contract_object)

        try:
            price_data = self.barchart.get_historical_futures_data_for_contract(
                bc_futures_contract=bc_futures_contract,
                bar_freq=frequency,
            )
        except missingData:
            new_log.warn(
                "Something went wrong getting Barchart price data for %s"
                % str(contract_object)
            )
            raise

        if len(price_data) == 0:
            new_log.warn(
                "No Barchart price data found for %s"
                % str(contract_object)
            )
            return futuresContractPrices.create_empty()

        return futuresContractPrices(price_data)

    def _get_bc_futures_instrument(self, futures_contract: futuresContract):
        instrument_code = futures_contract.instrument_code
        return self.futures_instrument_data.get_bc_futures_instrument(instrument_code)

    def _get_bc_futures_contract(self, futures_contract: futuresContract):
        bc_futures_instrument = self._get_bc_futures_instrument(futures_contract)
        bc_futures_contract = BcFuturesContract(
            futures_contract=futures_contract,
            bc_futures_instrument=bc_futures_instrument
        )
        return bc_futures_contract

    def _get_bc_contract_id(self, futures_contract: futuresContract):
        bc_futures_instrument = self._get_bc_futures_instrument(futures_contract)
        bc_futures_contract = BcFuturesContract(
            futures_contract=futures_contract,
            bc_futures_instrument=bc_futures_instrument
        )
        return bc_futures_contract.get_bc_contract_id()

    def get_ticker_object_for_order(self, order: contractOrder) -> Optional[tickerObject]:
        return None

    def cancel_market_data_for_order(self, order: brokerOrder):
        pass

    def get_recent_bid_ask_tick_data_for_contract_object(self,
                                                         contract_object: futuresContract) -> dataFrameOfRecentTicks:
        return dataFrameOfRecentTicks.create_empty()

    def _write_merged_prices_for_contract_object_no_checking(self, *args, **kwargs):
        raise NotImplementedError("Barchart is a read only source of prices")

    def _write_prices_at_frequency_for_contract_object_no_checking(self, futures_contract_object: futuresContract,
                                                                   futures_price_data: futuresContractPrices,
                                                                   frequency: Frequency = DAILY_PRICE_FREQ):
        raise NotImplementedError("Barchart is a read only source of prices")

    def delete_merged_prices_for_contract_object(self, *args, **kwargs):
        raise NotImplementedError("Barchart is a read only source of prices")

    def _delete_merged_prices_for_contract_object_with_no_checks_be_careful(self,
                                                                            futures_contract_object: futuresContract):
        raise NotImplementedError("Barchart is a read only source of prices")

    def _delete_prices_at_frequency_for_contract_object_with_no_checks_be_careful(
            self, futures_contract_object: futuresContract, frequency: Frequency = DAILY_PRICE_FREQ):
        raise NotImplementedError("Barchart is a read only source of prices")
