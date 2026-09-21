import sqlite3
from typing import Callable

from syscore.constants import arg_not_supplied
from sysdata.production.roll_state import rollStateData
from sysdata.sqlite.sqlite_data import sqliteData, _row_to_dict
from syslogging.logger import *

TABLE_NAME = "roll_status"

# Columns
INSTRUMENT_CODE = "instrument_code"
ROLL_STATE = "roll_state"

COLUMN_DEFS = [
    f"{INSTRUMENT_CODE} TEXT PRIMARY KEY",
    f"{ROLL_STATE} TEXT",
]


class sqliteRollStateData(rollStateData, sqliteData):
    """
    Read and write data class to get roll state data


    """

    def __init__(
        self,
        sqlite_conn: sqlite3.Connection = arg_not_supplied,
        log=get_logger("sqliteRollStateData")
    ):
        rollStateData.__init__(self, log=log)
        sqliteData.__init__(self, sqlite_conn=sqlite_conn)

    def __repr__(self):
        return "SQLite data connection for futures roll state"

    @property
    def table_name(self) -> str:
        return TABLE_NAME

    @property
    def column_defs(self) -> list:
        return COLUMN_DEFS

    @property
    def _row_factory(self) -> Callable:
        return _roll_state_factory

    def get_list_of_instruments(self) -> list:
        sql = f"SELECT {INSTRUMENT_CODE} FROM {self.table_name}"
        rows = self.sqlite_conn.execute(sql).fetchall()
        instruments = [row[0] for row in rows]
        return instruments

    def _get_roll_state_as_str_no_default(self, instrument_code: str):
        return self._select_one({INSTRUMENT_CODE: instrument_code})

    def _set_roll_state_as_str_without_checking(
        self, instrument_code: str, new_roll_state_as_str: str
    ):
        params = {
            INSTRUMENT_CODE: instrument_code,
            ROLL_STATE: new_roll_state_as_str,
        }
        self._insert(params, allow_replace=True)


def _roll_state_factory(cursor, row) -> str:
    row_dict = _row_to_dict(cursor, row)
    return row_dict[ROLL_STATE]
