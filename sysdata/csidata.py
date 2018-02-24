import glob
import os

import pandas as pd

from datetime import datetime
from syscore.genutils import str_of_int
from syscore.pdutils import pd_readcsv
from sysdata.csv.csvfuturesdata import csvFuturesData
from sysdata.mongodb.mongo_futures_instruments import mongoFuturesInstrumentData
from sysdata.mongodb.mongo_roll_data import mongoRollParametersData


class CsiFuturesData(csvFuturesData):

    def __init__(self, datapath=None, absolute_datapath=None):
        super().__init__(datapath, absolute_datapath)
        self._list_of_instruments = None
        self._instrument_data = None
        self._roll_parameters_data = None

    def get_instrument_list(self):
        if not self._list_of_instruments:
            self.log.msg("Loading instrument config from MongoDB")
            self._list_of_instruments = mongoFuturesInstrumentData().get_list_of_instruments()
        return self._list_of_instruments

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
        roll_params = self._get_roll_parameters(instrument_code)
        return roll_params.approx_expiry_offset < 0

    def get_roll_offset_days(self, instrument_code):
        roll_params = self._get_roll_parameters(instrument_code)
        return roll_params.roll_offset_day

    def get_next_contract(self, instrument_code):
        roll_params = self._get_roll_parameters(instrument_code)
        return roll_params.approx_first_held_contractDate_after_date(datetime.now())

    def _get_instrument_data(self):
        """
        Get a data frame of interesting information about instruments from MongoDB

        :returns: pd.DataFrame

        """

        if self._instrument_data is None:
            self.log.msg("Loading instrument config from MongoDB")

            instruments = self.get_instrument_list()
            data = mongoFuturesInstrumentData()

            d = []
            for instr_code in instruments:
                instr = data.get_instrument_data(instr_code)
                d.append(dict(Instrument=instr_code, Pointsize=instr.meta_data['point_size'],
                              AssetClass=instr.meta_data['asset_class'], Currency=instr.meta_data['currency'],
                              IBSymbol=instr.meta_data['ib_symbol'], CSISymbol=instr.meta_data['csi_symbol']))

            self._instrument_data = pd.DataFrame.from_records(d).set_index('Instrument')

        return self._instrument_data

    def _get_roll_parameters(self, instrument_code):
        if not self._roll_parameters_data:
            self.log.msg("Loading roll parameters from MongoDB")
            self._roll_parameters_data = mongoRollParametersData()
        return self._roll_parameters_data.get_roll_parameters(instrument_code)


if __name__ == '__main__':
    import doctest
    doctest.testmod()
