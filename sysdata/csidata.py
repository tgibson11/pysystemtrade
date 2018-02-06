import glob
import os

import pandas as pd

from syscore.genutils import str_of_int
from syscore.pdutils import pd_readcsv
from sysdata.csv.csvfuturesdata import csvFuturesData


class CsiFuturesData(csvFuturesData):

    def get_raw_price(self, instrument_code):
        """
        Get instrument price

        :param instrument_code: instrument to get prices for
        :type instrument_code: str

        :returns: pd.DataFrame

        """

        # Read from .csv
        self.log.msg(
            "Loading csv data for %s" % instrument_code,
            instrument_code=instrument_code)
        filename = self.get_instrument_filename(instrument_code)
        instrpricedata = pd_readcsv(filename, date_index_name="Date")
        instrpricedata.columns = ["price", "month", "unadjusted"]
        instrpricedata = instrpricedata.groupby(level=0).last()
        instrpricedata = pd.Series(instrpricedata.iloc[:, 0])
        return instrpricedata

    def get_instrument_raw_carry_data(self, instrument_code):
        """
        Returns a pd. dataframe with the 4 columns PRICE, PRICE_CONTRACT

        These are specifically needed for futures trading

        To use carry trading rules it also needs to return CARRY and CARRY_CONTRACT,
        but I don't currently have this data

        :param instrument_code: instrument to get carry data for
        :type instrument_code: str

        :returns: pd.DataFrame

        """

        self.log.msg(
            "Loading csv carry data for %s" % instrument_code,
            instrument_code=instrument_code)

        filename = self.get_instrument_filename(instrument_code)
        instrcarrydata = pd_readcsv(filename, date_index_name="Date")
        instrcarrydata = instrcarrydata.iloc[:, [1, 2]]
        instrcarrydata.columns = ["PRICE_CONTRACT", "PRICE"]

        instrcarrydata.PRICE_CONTRACT = instrcarrydata.PRICE_CONTRACT.apply(
            str_of_int)

        return instrcarrydata

    def get_instrument_filename(self, instrument_code):
        csisymbol = self._get_instrument_data().loc[instrument_code, 'CSISymbol']
        pattern = os.path.join(self._datapath, csisymbol + "*.TXT")
        filename = glob.glob(pattern)[0]
        return filename

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

if __name__ == '__main__':
    import doctest
    doctest.testmod()
