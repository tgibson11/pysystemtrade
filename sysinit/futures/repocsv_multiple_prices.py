"""
Copy from csv repo files to arctic for multiple prices
"""

from sysdata.csv.csv_multiple_prices import csvFuturesMultiplePricesData
from sysdata.arctic.arctic_multiple_prices import arcticFuturesMultiplePricesData
from sysdata.mongodb.mongo_futures_instruments import mongoFuturesInstrumentData

if __name__ == "__main__":
    instrument_code = input("Instrument code? <return to abort, ALL for all configured instruments> ")
    if instrument_code == "":
        exit()

    arctic_multiple_prices = arcticFuturesMultiplePricesData()
    csv_multiple_prices = csvFuturesMultiplePricesData()

    if instrument_code == "ALL":
        instrument_data = mongoFuturesInstrumentData()
        instrument_list = instrument_data.get_list_of_instruments()
        print(instrument_list)

        for instrument in instrument_list:
            print(instrument)
            multiple_prices = csv_multiple_prices.get_multiple_prices(instrument)

            print(multiple_prices)

            arctic_multiple_prices.add_multiple_prices(
                instrument, multiple_prices, ignore_duplication=True
            )

    else:
        multiple_prices = csv_multiple_prices.get_multiple_prices(instrument_code)

        print(multiple_prices)

        arctic_multiple_prices.add_multiple_prices(
            instrument_code, multiple_prices, ignore_duplication=True
        )
