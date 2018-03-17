import glob
import os
import pandas as pd

from syscore.fileutils import get_pathname_for_package
from syscore.pdutils import pd_readcsv
from sysdata.arctic.arctic_and_mongo_sim_futures_data import mongoFuturesConfigDataForSim, dbconnections
from sysdata.csv.csv_sim_futures_data import csvFXData, csvFuturesAdjustedPriceData, csvFuturesMultiplePriceData, \
    csvPaths
from sysdata.mongodb.mongo_roll_data import mongoRollParametersData


class CsiFuturesData(csvFXData, csvFuturesAdjustedPriceData, mongoFuturesConfigDataForSim, csvFuturesMultiplePriceData):

    def __init__(self, override_datapath=None, datapath_dict=None):
        if datapath_dict is None:
            datapath_dict = {}
        csvPaths.__init__(self, override_datapath=override_datapath, datapath_dict=datapath_dict)
        dbconnections.__init__(self, "production")
        self._instrument_data = None
        self._roll_parameters_data = None

    def get_instrument_data(self):
        if self._instrument_data is None:
            self._instrument_data = self.get_all_instrument_data()
            print(self._instrument_data)
        return self._instrument_data

    def get_instrument_ib_symbol(self, instrument_code):
        instr_data = self.get_instrument_data()
        ib_symbol = instr_data.loc[instrument_code, 'IBSymbol']
        return ib_symbol

    def has_prev_month_expiry(self, instrument_code):
        roll_params = self._get_roll_parameters(instrument_code)
        return roll_params.approx_expiry_offset < 0

    def _get_roll_parameters(self, instrument_code):
        if not self._roll_parameters_data:
            # print("Loading roll parameters from MongoDB")
            self._roll_parameters_data = mongoRollParametersData()
        return self._roll_parameters_data.get_roll_parameters(instrument_code)

    def get_raw_price(self, instrument_code):
        # Read from .csv
        print("Loading raw price data for " + instrument_code)
        filename = self.get_instrument_filename(instrument_code)
        instrpricedata = pd_readcsv(filename, date_index_name="Date")
        instrpricedata.columns = ["price", "month", "unadjusted"]
        instrpricedata = instrpricedata.groupby(level=0).last()
        instrpricedata = pd.Series(instrpricedata.iloc[:, 0])
        return instrpricedata

    def get_instrument_filename(self, instrument_code):
        csisymbol = self.get_instrument_data().loc[instrument_code, 'CSISymbol']
        path_with_dots = self._resolve_path("adjusted_prices")
        path = get_pathname_for_package(path_with_dots)
        pattern = os.path.join(path, csisymbol + "*.TXT")
        filename = glob.glob(pattern)[0]
        return filename
