"""
Update spot FX prices using interactive brokers data, dump into mongodb
"""

from syscore.objects import success, failure, data_error
from syslogdiag.emailing import send_mail_msg

from sysbrokers.IB.ibConnection import connectionIB
from sysdata.mongodb.mongo_connection import mongoDb
from syslogdiag.log import logToMongod as logger

from sysproduction.data.get_data import dataBlob


def update_fx_prices():
    """
    Update FX prices stored in Arctic (Mongo) with interactive brokers prices (usually going back about a year)

    :return: Nothing
    """

    with mongoDb() as mongo_db,\
        logger("Update-FX-prices", mongo_db=mongo_db) as log,\
        connectionIB(log=log.setup(component="IB-connection")) as ib_conn:

        data = dataBlob("ibFxPricesData arcticFxPricesData", ib_conn=ib_conn, mongo_db=mongo_db)

        list_of_codes_all = data.ib_fx_prices.get_list_of_fxcodes()  # codes must be in .csv file /sysbrokers/IB/ibConfigSpotFx.csv
        log.msg("FX Codes: %s" % str(list_of_codes_all))

        for fx_code in list_of_codes_all:
            try:
                log.label(currency_code = fx_code)
                update_fx_prices_for_code(fx_code, data)
            except Exception as e:
                log.warn("Something went wrong with FX update %s" % e)

    return success

def update_fx_prices_for_code(fx_code, data):
    new_fx_prices = data.ib_fx_prices.get_fx_prices(fx_code) # returns fxPrices object
    rows_added = data.arctic_fx_prices.update_fx_prices(fx_code, new_fx_prices, check_for_spike=True)

    if rows_added is data_error:
        msg = "Spike found in prices for %s: need to manually check by running update_manual_check_fx_prices" % str(fx_code)
        data.log.warn(msg)
        try:
            send_mail_msg(msg, "FX Price Spike")
        except:
            data.log.warn("Couldn't send email about price spike")

    return success

