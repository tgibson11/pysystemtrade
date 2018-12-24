"""
Get futures data from CSI export files

"""

import pandas as pd

from syscore.fileutils import get_filename_for_package
from sysdata.futures.contracts import futuresContract
from sysdata.futures.futures_per_contract_prices import futuresContractPriceData, futuresContractPrices

CSI_FUTURES_CONFIG_FILE = get_filename_for_package("private.my_system.config.CsiFuturesConfig.csv")


class CsiFuturesConfiguration(object):

    def __init__(self, config_file=CSI_FUTURES_CONFIG_FILE):

        self._config_file = config_file

    def get_list_of_instruments(self):
        config_data = self._get_config_information()

        return list(config_data.index)

    def get_instrument_config(self, instrument_code):

        if instrument_code not in self.get_list_of_instruments():
            raise Exception("Instrument %s missing from config file %s" % (instrument_code, self._config_file))

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
        except Exception:
            raise Exception("Can't read file %s" % self._config_file)

        try:
            config_data.index = config_data.CODE
            config_data.drop("CODE", 1, inplace=True)

        except Exception:
            raise Exception("Badly configured file %s" % self._config_file)

        return config_data

    def get_csi_code_for_instrument(self, instrument_code):

        config = self.get_instrument_config(instrument_code)
        return config.CSI_CODE

    def get_csi_dividing_factor(self, instrument_code):

        config = self.get_instrument_config(instrument_code)
        factor = config.FACTOR

        return float(factor)


USE_DEFAULT = object()


class _CsiFuturesContract(futuresContract):
    """
    An individual futures contract, with some additional methods
    """

    def __init__(self, futures_contract, csi_instrument_data=USE_DEFAULT):
        """
        We always create a CSI contract from an existing, normal, contract

        :param futures_contract: of type FuturesContract
        """

        super().__init__(futures_contract.instrument, futures_contract.contract_date)

        if csi_instrument_data is USE_DEFAULT:
            csi_instrument_data = CsiFuturesConfiguration()

        self._csi_instrument_data = csi_instrument_data

    def csi_filename(self):
        """
        Returns the CSI filename for a given contract

        :return: str
        """

        # TODO implement
        # quandl_year = str(self.contract_date.year())
        # quandl_month = self.contract_date.letter_month()
        #
        # try:
        #     quandl_date_id = quandl_month + quandl_year
        #
        #     market = self.get_quandlmarket_for_instrument()
        #     codename = self.get_quandlcode_for_instrument()
        #
        #     quandldef = '%s/%s%s' % (market, codename, quandl_date_id)
        #
        #     return quandldef
        # except Exception:
        #     raise ValueError("Can't turn %s %s into a CSI Contract" % (self.instrument_code, self.contract_date))

    def get_csi_code_for_instrument(self):

        return self._csi_instrument_data.get_csi_code_for_instrument(self.instrument_code)

    def get_dividing_factor(self):

        return self._csi_instrument_data.get_csi_dividing_factor(self.instrument_code)


class CsiFuturesContractPriceData(futuresContractPriceData):
    """
    Class to specifically get individual futures price data from CSI
    """

    def __init__(self):

        super().__init__()

        self.name = "simData connection for individual futures contracts prices, CSI"

    def __repr__(self):
        return self.name

    def get_prices_for_contract_object(self, contract_object):
        return self._get_prices_for_contract_object_no_checking(contract_object)

    def _get_prices_for_contract_object_no_checking(self, futures_contract_object):
        """

        :param futures_contract_object: futuresContract
        :return: futuresContractPrices
        """
        self.log.label(instrument_code=futures_contract_object.instrument_code,
                       contract_date=futures_contract_object.date)

        try:
            csi_contract = _CsiFuturesContract(futures_contract_object)
        except Exception as exception:
            self.log.warning("Can't parse contract object to find the CSI filename", exception)
            return futuresContractPrices.create_empty()

        try:
            contract_data = pd.read_csv(csi_contract.csi_filename())
        except Exception as exception:
            self.log.warn("Can't read CSV file for %s error %s" % (csi_contract.csi_filename(), exception))
            return futuresContractPrices.create_empty()

        try:
            data = CsiFuturesContractPrices(contract_data)
        except Exception as exception:
            self.log.error(
                "CSI data error: data fields are not as expected %s" % ",".join(list(contract_data.columns)), exception)
            return futuresContractPrices.create_empty()

        # apply multiplier
        factor = csi_contract.get_dividing_factor()
        data.divide(factor)

        return data

    def write_prices_for_contract_object(self, futures_contract_object, futures_price_data):
        pass

    def _delete_prices_for_contract_object_with_no_checks_be_careful(self, futures_contract_object):
        pass

    def get_contracts_with_price_data(self):
        pass


class CsiFuturesContractPrices(futuresContractPrices):
    """
    Parses CSI format into our format

    Does any transformations needed to price etc
    """

    def __init__(self, contract_data):

        # TODO implement
        # try:
        #     new_data = pd.DataFrame(dict(OPEN=contract_data.Open,
        #                                  CLOSE=contract_data.Last,
        #                                  HIGH=contract_data.High,
        #                                  LOW=contract_data.Low,
        #                                  SETTLE=contract_data.Settle))
        # except AttributeError:
        #     try:
        #         new_data = pd.DataFrame(dict(OPEN=contract_data.Open,
        #                                      CLOSE=contract_data.Close,
        #                                      HIGH=contract_data.High,
        #                                      LOW=contract_data.Low,
        #                                      SETTLE=contract_data.Settle))
        #     except AttributeError:
        #         try:
        #             new_data = pd.DataFrame(dict(OPEN=contract_data.Open,
        #                                          CLOSE=contract_data.Settle,
        #                                          HIGH=contract_data.High,
        #                                          LOW=contract_data.Low,
        #                                          SETTLE=contract_data.Settle))
        #         except AttributeError:
        #             raise Exception(
        #                 "CSI data error: data fields %s are not as expected" % ",".join(list(contract_data.columns)))

        super().__init__(contract_data)
