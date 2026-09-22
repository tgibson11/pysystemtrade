import sqlite3
from typing import Callable

from syscore.constants import arg_not_supplied

from sysdata.production.temporary_close import temporaryCloseData
from sysdata.sqlite.sqlite_data import sqliteData, _row_to_dict
from sysobjects.production.position_limits import positionLimitForInstrument
from syslogging.logger import *

TABLE_NAME = "temporary_close"

# Columns
INSTRUMENT_CODE = "instrument_code"
POSITION_LIMIT = "position_limit"

COLUMN_DEFS = [
    f"{INSTRUMENT_CODE} TEXT PRIMARY KEY",
    f"{POSITION_LIMIT} INTEGER",
]


class sqliteTemporaryCloseData(temporaryCloseData, sqliteData):
    def __init__(
        self,
        sqlite_conn: sqlite3.Connection = arg_not_supplied,
        log=get_logger("sqlitetemporaryCloseData")
    ):
        temporaryCloseData.__init__(self, log=log)
        sqliteData.__init__(self, sqlite_conn=sqlite_conn)

    def __repr__(self):
        return "sqliteTemporaryCloseDataData"

    @property
    def table_name(self) -> str:
        return TABLE_NAME

    @property
    def column_defs(self) -> list:
        return COLUMN_DEFS

    @property
    def _row_factory(self) -> Callable:
        return _position_limit_factory

    def get_list_of_instruments(self):
        sql = f"SELECT {INSTRUMENT_CODE} FROM {self.table_name}"
        rows = self.sqlite_conn.execute(sql).fetchall()
        instruments = [row[0] for row in rows]
        return instruments

    def get_stored_position_limit_for_instrument(
        self, instrument_code: str
    ) -> positionLimitForInstrument:
        return self._select_one({INSTRUMENT_CODE: instrument_code})

    def _add_stored_position_limit_without_checking(
        self, position_limit_for_instrument: positionLimitForInstrument
    ):
        params = {
            INSTRUMENT_CODE: position_limit_for_instrument.key,
            POSITION_LIMIT: position_limit_for_instrument.position_limit,
        }
        self._insert(params, allow_replace=True)

    def does_instrument_have_position_limit_stored(self, instrument_code) -> bool:
        list_of_keys = self.get_list_of_instruments()
        return instrument_code in list_of_keys

    def _delete_stored_position_limit_without_checking(self, instrument_code: str):
        self._delete({INSTRUMENT_CODE: instrument_code})


def _position_limit_factory(cursor, row) -> positionLimitForInstrument:
    row_dict = _row_to_dict(cursor, row)
    return positionLimitForInstrument(
        row_dict[INSTRUMENT_CODE],
        row_dict[POSITION_LIMIT]
    )

