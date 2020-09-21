import datetime

from sysproduction.data.get_data import dataBlob
from syscore.objects import arg_not_supplied


class diagInstruments(object):
    def __init__(self, data=arg_not_supplied):
        # Check data has the right elements to do this
        if data is arg_not_supplied:
            data = dataBlob()

        data.add_class_list(" mongoFuturesInstrumentData")
        self.data = data

    def get_point_size(self, instrument_code):
        return self.get_meta_data(instrument_code)['Pointsize']

    def get_currency(self, instrument_code):
        return self.get_meta_data(instrument_code)['Currency']

    def get_asset_class(self, instrument_code):
        return self.get_meta_data(instrument_code)['AssetClass']

    def get_description(self, instrument_code):
        return self.get_meta_data(instrument_code)['Description']

    def get_meta_data(self, instrument_code):
        return self.data.db_futures_instrument.get_instrument_data(instrument_code).meta_data
