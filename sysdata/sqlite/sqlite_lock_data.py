import sqlite3
from typing import Callable

from syscore.constants import arg_not_supplied
from syscore.exceptions import missingData
from sysdata.production.locks import lockData, lock_on, lock_off
from sysdata.sqlite.sqlite_data import sqliteData, _row_to_dict
from syslogging.logger import *

TABLE_NAME = "locked_instrument"

# Columns
INSTRUMENT_CODE = "instrument_code"

COLUMN_DEFS = [
    f"{INSTRUMENT_CODE} TEXT PRIMARY KEY",
]


class sqliteLockData(lockData, sqliteData):
    """
    Read and write data class to get lock data


    """

    def __init__(
        self,
        sqlite_conn: sqlite3.Connection = arg_not_supplied,
        log=get_logger("sqliteLockData")
    ):
        lockData.__init__(self, log=log)
        sqliteData.__init__(self, sqlite_conn=sqlite_conn)

    def __repr__(self):
        return "sqliteLockData"

    @property
    def table_name(self) -> str:
        return TABLE_NAME

    @property
    def column_defs(self) -> list:
        return COLUMN_DEFS

    @property
    def _row_factory(self) -> Callable:
        return _lock_factory

    def _get_lock_for_instrument_no_checking(self, instrument_code: str) -> str:
        try:
            self._select_one({INSTRUMENT_CODE: instrument_code})
        except missingData:
            return lock_off
        return lock_on

    def add_lock_for_instrument(self, instrument_code: str):
        self._insert({INSTRUMENT_CODE: instrument_code}, allow_replace=True)

    def remove_lock_for_instrument(self, instrument_code):
        self._delete({INSTRUMENT_CODE: instrument_code})

    def get_list_of_locked_instruments(self):
        locked_instruments = self._select_all()
        return locked_instruments


def _lock_factory(cursor, row) -> str:
    row_dict = _row_to_dict(cursor, row)
    instrument_code = row_dict.get(INSTRUMENT_CODE)
    return instrument_code