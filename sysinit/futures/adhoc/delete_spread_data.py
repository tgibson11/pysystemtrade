from sysdata.arctic.arctic_spreads import arcticSpreadsForInstrumentData
from sysdata.mongodb.mongo_connection import mongoDb
from sysproduction.data.prices import get_valid_instrument_code_from_user

mongo_db = mongoDb()
data = arcticSpreadsForInstrumentData(mongo_db=mongo_db)

do_another = True

while do_another:
    exit_code = "EXIT"
    instrument_code = get_valid_instrument_code_from_user(allow_exit=True, exit_code=exit_code)

    if instrument_code == exit_code:
        do_another = False
    else:
        data.delete_spreads(instrument_code=instrument_code, are_you_sure=True)
