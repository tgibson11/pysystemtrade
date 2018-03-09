"""
Populate a mongo DB collection with instrument data from a csv
"""

from sysdata.mongodb.mongo_futures_instruments import mongoFuturesInstrumentData
from sysinit.futures.csv_data_readers.instruments_from_csv import initCsvFuturesInstrumentData

data_out = mongoFuturesInstrumentData()
data_in = initCsvFuturesInstrumentData(config_file="private.my_system.instrumentconfig.csv")

instrument_list = data_in.get_list_of_instruments()

for instrument_code in instrument_list:
    instrument_object = data_in.get_instrument_data(instrument_code)
    data_out.delete_instrument_data(instrument_code, are_you_sure=True)
    data_out.add_instrument_data(instrument_object)

    # check
    instrument_added = data_out.get_instrument_data(instrument_code)
    print("Added %s to %s" % (instrument_added.instrument_code, data_out))
