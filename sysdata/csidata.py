"""
Get futures data from CSI data files
"""
import glob
import os

import pandas as pd

from syscore.fileutils import get_pathname_for_package
from syscore.genutils import str_of_int
from syscore.pdutils import pd_readcsv
from sysdata.futuresdata import FuturesData

"""
Static variable to store location of data
"""
LEGACY_DATA_PATH = "sysdata.legacycsv"


class CsiFuturesData(FuturesData):
    """
        Get futures specific data from CSI data files

        Extends the FuturesData class for a specific data source

    """

    def __init__(self, datapath=None, absolute_datapath=None):
        """
        Create a FuturesData object for reading files from datapath
        inherits from FuturesData

        :param datapath: relative path to find files
        :type datapath: None or str

        :param absolute_datapath: absolute path to find files (not used if datapath specified)
        :type datapath: None or str


        :returns: new CsiFuturesData object

        """

        super().__init__()

        # Use (1) provided relative datapath, (2) absolute_datapath

        if datapath is not None:
            resolved_datapath = get_pathname_for_package(datapath)
        else:
            if absolute_datapath is not None:
                resolved_datapath = absolute_datapath
            else:
                raise ValueError("datapath or absolute_datapath is required")

        """
        Most Data objects that read data from a specific place have a 'source' of some kind
        Here it's a directory
        """
        setattr(self, "_datapath", resolved_datapath)

    def _get_all_cost_data(self):
        """
        Get a data frame of cost data

        :returns: pd.DataFrame

        """

        self.log.msg("Loading csv cost file")

        # First check the specified data path
        filename = os.path.join(self._datapath, "costs_analysis.csv")
        try:
            instr_data = pd.read_csv(filename)
            instr_data.index = instr_data.Instrument
            return instr_data
        except OSError:
            # If not found, check the default data path
            filename = os.path.join(get_pathname_for_package(LEGACY_DATA_PATH), "costs_analysis.csv")
            try:
                instr_data = pd.read_csv(filename)
                instr_data.index = instr_data.Instrument
                return instr_data
            except OSError:
                self.log.warn("Cost file not found %s" % filename)
                return None

    def get_raw_cost_data(self, instrument_code):
        """
        Get's cost data for an instrument

        Get cost data

        Execution slippage [half spread] price units
        Commission (local currency) per block
        Commission - percentage of value (0.01 is 1%)
        Commission (local currency) per block

        :param instrument_code: instrument to value for
        :type instrument_code: str

        :returns: dict of floats

        """

        default_costs = dict(
            price_slippage=0.0,
            value_of_block_commission=0.0,
            percentage_cost=0.0,
            value_of_pertrade_commission=0.0)

        cost_data = self._get_all_cost_data()

        if cost_data is None:
            ##
            return default_costs

        try:
            block_move_value = cost_data.loc[instrument_code, [
                'Slippage', 'PerBlock', 'Percentage', 'PerTrade'
            ]]
        except KeyError:
            self.log.warn(
                "Cost data not found for %s, using zero" % instrument_code)
            return default_costs

        return dict(
            price_slippage=block_move_value[0],
            value_of_block_commission=block_move_value[1],
            percentage_cost=block_move_value[2],
            value_of_pertrade_commission=block_move_value[3])

    def get_raw_price(self, instrument_code):
        """
        Get instrument price

        :param instrument_code: instrument to get prices for
        :type instrument_code: str

        :returns: pd.DataFrame

        """

        csisymbol = self._get_instrument_data().loc[instrument_code, 'CSISymbol']

        # Read from CSI data files
        self.log.msg(
            "Loading CSI data for %s" % instrument_code,
            instrument_code=instrument_code)

        # B = back-adjusted
        pathname = os.path.join(self._datapath, csisymbol + "*B.TXT")
        # Assume only 1 matching file
        filename = glob.glob(pathname)[0]
        instrpricedata = pd_readcsv(filename, header=None, date_format="%Y%m%d")
        instrpricedata.columns = ["open", "high", "low", "price", "volume", "open_interest", "expiry", "unadjusted"]
        instrpricedata = instrpricedata.groupby(level=0).last()
        instrpricedata = pd.Series(instrpricedata.iloc[:, 3])
        return instrpricedata

    def get_instrument_raw_carry_data(self, instrument_code):
        """
        Returns a pd. dataframe with the 4 columns PRICE, CARRY, PRICE_CONTRACT, CARRY_CONTRACT

        These are specifically needed for futures trading

        IMPORTANT: this implementation currently returns PRICE and PRICE_CONTRACT only!

        :param instrument_code: instrument to get carry data for
        :type instrument_code: str

        :returns: pd.DataFrame

        """

        self.log.msg(
            "Loading CSI carry data for %s" % instrument_code,
            instrument_code=instrument_code)

        csisymbol = self._get_instrument_data().loc[instrument_code, 'CSISymbol']

        # B = back-adjusted
        pathname = os.path.join(self._datapath, csisymbol + "*B.TXT")
        # Assume only 1 matching file
        filename = glob.glob(pathname)[0]

        instrcarrydata = pd_readcsv(filename, header=None, date_format="%Y%m%d")

        instrcarrydata = instrcarrydata.iloc[:, [6, 7]]
        instrcarrydata.columns = ["PRICE_CONTRACT", "PRICE"]

        instrcarrydata.PRICE_CONTRACT = instrcarrydata.PRICE_CONTRACT.apply(
            str_of_int)

        return instrcarrydata

    def _get_instrument_data(self):
        """
        Get a data frame of interesting information about instruments, either
        from a file or cached

        :returns: pd.DataFrame

        """

        self.log.msg("Loading csv instrument config")

        filename = os.path.join(self._datapath, "instrumentconfig.csv")
        instr_data = pd.read_csv(filename)
        instr_data.index = instr_data.Instrument

        return instr_data

    def get_instrument_list(self):
        """
        list of instruments in this data set

        :returns: list of str

        """

        instr_data = self._get_instrument_data()

        return list(instr_data.Instrument)

    def get_instrument_asset_classes(self):
        """
        Returns dataframe with index of instruments, column AssetClass

        """
        instr_data = self._get_instrument_data()
        instr_assets = instr_data.AssetClass

        return instr_assets

    def get_value_of_block_price_move(self, instrument_code):
        """
        How much is a $1 move worth in value terms?

        :param instrument_code: instrument to get value for
        :type instrument_code: str

        :returns: float

        """

        instr_data = self._get_instrument_data()
        block_move_value = instr_data.loc[instrument_code, 'Pointsize']

        return block_move_value

    def get_instrument_currency(self, instrument_code):
        """
        What is the currency that this instrument is priced in?

        :param instrument_code: instrument to get value for
        :type instrument_code: str

        :returns: str

        """

        instr_data = self._get_instrument_data()
        currency = instr_data.loc[instrument_code, 'Currency']

        return currency

    def get_instrument_ib_symbol(self, instrument_code):
        instr_data = self._get_instrument_data()
        ib_symbol = instr_data.loc[instrument_code, 'IBSymbol']
        return ib_symbol

    def instrument_has_prev_month_expiry(self, instrument_code):
        instr_data = self._get_instrument_data()
        prev_month_expiry = instr_data.loc[instrument_code, 'PrevMonthExpiry']
        return prev_month_expiry

    def get_instrument_roll_window(self, instrument_code):
        instr_data = self._get_instrument_data()
        roll_window = instr_data.loc[instrument_code, 'RollWindow']
        return roll_window

    def _get_fx_data(self, currency1, currency2):
        """
        Get fx data

        :param currency1: numerator currency
        :type currency1: str

        :param currency2: denominator currency
        :type currency2: str

        :returns: Tx1 pd.DataFrame, or None if not available

        """

        self.log.msg("Loading csv fx data", fx="%s%s" % (currency1, currency2))

        if currency1 != currency2:
            error_msg = "FX for CSI data is not yet supported, using constant 1:1 exchange rate"
            self.log.critical(error_msg)

        return self._get_default_series()

if __name__ == '__main__':
    import doctest
    doctest.testmod()
