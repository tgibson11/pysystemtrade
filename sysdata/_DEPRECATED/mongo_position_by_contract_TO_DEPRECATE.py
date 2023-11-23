from syscore.constants import arg_not_supplied

from sysdata.mongodb.mongo_generic import mongoDataWithMultipleKeys
from syslogdiag.log_to_screen import logtoscreen

POSITION_CONTRACT_COLLECTION = "futures_position_by_contract"


class mongoContractPositionData(object):
    """
    Read and write data class to get positions by contract


    """

    def __init__(self, mongo_db=arg_not_supplied, log=logtoscreen("")):
        self._log = log
        self._mongo_data = mongoDataWithMultipleKeys(
            POSITION_CONTRACT_COLLECTION, mongo_db=mongo_db
        )

    @property
    def mongo_data(self):
        return self._mongo_data

    @property
    def log(self):
        return self._log
