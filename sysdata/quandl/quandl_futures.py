"""
Get data from quandl for futures

"""

from sysobjects.contracts import futuresContract, listOfFuturesContracts
from syscore.dateutils import adjust_timestamp_to_include_notional_close_and_time_offset
from sysdata.futures.futures_per_contract_prices import (
    futuresContractPriceData,
)
from sysobjects.futures_per_contract_prices import futuresContractPrices
from syscore.fileutils import get_filename_for_package
from sysdata.quandl.quandl_utils import load_private_key

import quandl
import pandas as pd

QUANDL_FUTURES_CONFIG_FILE = get_filename_for_package(
    "sysdata.quandl.QuandlFuturesConfig.csv"
)

quandl.ApiConfig.api_key = load_private_key()


class QuandlFuturesConfiguration(object):
    def __init__(self, config_file=QUANDL_FUTURES_CONFIG_FILE):

        self._config_file = config_file

    def get_list_of_instruments(self):
        config_data = self._get_config_information()

        return list(config_data.index)

    def get_instrument_config(self, instrument_code):

        if instrument_code not in self.get_list_of_instruments():
            raise Exception(
                "Instrument %s missing from config file %s"
                % (instrument_code, self._config_file)
            )

        config_data = self._get_config_information()
        data_for_code = config_data.loc[instrument_code]

        return data_for_code

    def _get_config_information(self):
        """
        Get configuration information

        :return: dict of config information relating to self.instrument_code
        """

        try:
            config_data = pd.read_csv(self._config_file)
        except BaseException:
            raise Exception("Can't read file %s" % self._config_file)

        try:
            config_data.index = config_data.CODE
            config_data.drop("CODE", 1, inplace=True)

        except BaseException:
            raise Exception("Badly configured file %s" % self._config_file)

        return config_data

    def get_quandlcode_for_instrument(self, instrument_code):

        config = self.get_instrument_config(instrument_code)
        return config.QCODE

    def get_quandlmarket_for_instrument(self, instrument_code):

        config = self.get_instrument_config(instrument_code)
        return config.MARKET

    def get_first_contract_date(self, instrument_code):

        config = self.get_instrument_config(instrument_code)
        start_date = config.FIRST_CONTRACT

        return "%d" % start_date

    def get_quandl_dividing_factor(self, instrument_code):

        config = self.get_instrument_config(instrument_code)
        factor = config.FACTOR

        return float(factor)


USE_DEFAULT = object()


class _QuandlFuturesContract(futuresContract):
    """
    An individual futures contract, with additional Quandl methods
    """

    def __init__(self, futures_contract, quandl_instrument_data=USE_DEFAULT):
        """
        We always create a quandl contract from an existing, normal, contract

        :param futures_contract: of type FuturesContract
        """

        super().__init__(futures_contract.instrument, futures_contract.date_str)

        if quandl_instrument_data is USE_DEFAULT:
            quandl_instrument_data = QuandlFuturesConfiguration()

        self._quandl_instrument_data = quandl_instrument_data

    def quandl_identifier(self):
        """
        Returns the Quandl identifier for a given contract

        :return: str
        """

        quandl_year = str(self.contract_date.year())
        quandl_month = self.contract_date.letter_month()

        quandl_date_id = quandl_month + quandl_year

        market = self.get_quandlmarket_for_instrument()
        codename = self.get_quandlcode_for_instrument()

        quandldef = "%s/%s%s" % (market, codename, quandl_date_id)

        return quandldef

    def get_quandlcode_for_instrument(self):

        return self._quandl_instrument_data.get_quandlcode_for_instrument(
            self.instrument_code
        )

    def get_quandlmarket_for_instrument(self):

        return self._quandl_instrument_data.get_quandlmarket_for_instrument(
            self.instrument_code
        )

    def get_start_date(self):

        return self._quandl_instrument_data.get_first_contract_date(
            self.instrument_code)

    def get_dividing_factor(self):

        return self._quandl_instrument_data.get_quandl_dividing_factor(
            self.instrument_code
        )


class QuandlFuturesContractPriceData(futuresContractPriceData):
    """
    Class to specifically get individual futures price data for quandl
    """

    def __init__(self):

        super().__init__()

        self.name = "simData connection for individual futures contracts prices, Quandl"

    def __repr__(self):
        return self.name

    def get_prices_for_contract_object(self, contract_object):
        """
        We do this because we have no way of checking if QUANDL has something without actually trying to get it
        """
        return self._get_prices_for_contract_object_no_checking(
            contract_object)

    def _get_prices_for_contract_object_no_checking(
            self, futures_contract_object):
        """

        :param futures_contract_object: futuresContract
        :return: futuresContractPrices
        """
        self.log.label(
            instrument_code=futures_contract_object.instrument_code,
            contract_date=futures_contract_object.date_str,
        )

        quandl_contract = _QuandlFuturesContract(futures_contract_object)

        try:
            contract_data = quandl.get(quandl_contract.quandl_identifier())
        except Exception as exception:
            self.log.warn(
                "Can't get QUANDL data for %s error %s"
                % (quandl_contract.quandl_identifier(), exception)
            )
            return futuresContractPrices.create_empty()

        try:
            data = QuandlFuturesContractPrices(contract_data)
        except BaseException:
            self.log.error(
                "Quandl API error: data fields are not as expected %s"
                % ",".join(list(contract_data.columns))
            )
            raise

        # apply multiplier to price columns
        factor = quandl_contract.get_dividing_factor()
        all_cols = data.columns.values
        price_cols = all_cols[all_cols != 'VOLUME']
        data[price_cols] /= factor

        return data

    def get_contracts_with_price_data(self) -> listOfFuturesContracts:
        raise NotImplementedError

    def _delete_prices_for_contract_object_with_no_checks_be_careful(self, futures_contract_object: futuresContract):
        raise NotImplementedError

    def _write_prices_for_contract_object_no_checking(self, futures_contract_object: futuresContract,
                                                      futures_price_data: futuresContractPrices):
        raise NotImplementedError

    def _get_prices_at_frequency_for_contract_object_no_checking(self, contract_object: futuresContract,
                                                                 freq: str) -> futuresContractPrices:
        raise NotImplementedError


class QuandlFuturesContractPrices(futuresContractPrices):
    """
    Parses Quandl format into our format

    Does any transformations needed to price etc
    """

    def __init__(self, contract_data):

        if 'Last' in contract_data.columns:
            last_count = contract_data.Last.count()
        else:
            last_count = 0

        if 'Close' in contract_data.columns:
            close_count = contract_data.Close.count()
        else:
            close_count = 0

        if 'Settle' in contract_data.columns:
            settle_count = contract_data.Settle.count()
        else:
            settle_count = 0

        if last_count >= max(close_count, settle_count):
            final_series = contract_data.Last
        elif close_count >= settle_count:
            final_series = contract_data.Close
        else:
            final_series = contract_data.Settle

        # For VIX: the latest date often has 0.00 close, but settle is populated
        if final_series[-1] == 0 and contract_data.Settle[-1] != 0:
            final_series[-1] = contract_data.Settle[-1]

        if 'Volume' in contract_data.columns:
            volume_series = contract_data.Volume
        elif 'Total Volume' in contract_data.columns:
            volume_series = contract_data['Total Volume']
        else:
            volume_series = None

        try:
            new_data = pd.DataFrame(dict(OPEN=contract_data.Open,
                                         FINAL=final_series,
                                         HIGH=contract_data.High,
                                         LOW=contract_data.Low,
                                         VOLUME=volume_series))
        except AttributeError:
            raise Exception(
                "Quandl API error: data fields %s are not as expected" % ",".join(list(contract_data.columns)))

        # Adjust timestamps to notional closing time
        date_index = [
            adjust_timestamp_to_include_notional_close_and_time_offset(timestamp)
            for timestamp in new_data.index
        ]
        new_data.index = date_index

        super().__init__(new_data)

    @property
    def _constructor_expanddim(self):
        raise NotImplementedError