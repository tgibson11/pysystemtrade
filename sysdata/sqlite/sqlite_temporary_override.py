import sqlite3
from typing import Callable

from syscore.exceptions import missingData
from syscore.constants import arg_not_supplied

from sysdata.production.temporary_override import temporaryOverrideData
from sysdata.sqlite.sqlite_data import sqliteData, _row_to_dict
from sysobjects.production.override import Override
from syslogging.logger import get_logger
from sysobjects.production.override import DEFAULT_OVERRIDE

TABLE_NAME = "temporary_override"

# Columns
INSTRUMENT_CODE = "instrument_code"
OVERRIDE = "override"

COLUMN_DEFS = [
    f"{INSTRUMENT_CODE} TEXT PRIMARY KEY",
    f"{OVERRIDE} FLOAT",
]


class sqliteTemporaryOverrideData(temporaryOverrideData, sqliteData):
    def __init__(
        self,
        sqlite_conn: sqlite3.Connection = arg_not_supplied,
        log=get_logger("sqliteTemporaryOverrideData")
    ):
        temporaryOverrideData.__init__(self, log=log)
        sqliteData.__init__(self, sqlite_conn=sqlite_conn)

    def __repr__(self):
        return "sqliteTemporaryOverrideData"

    @property
    def table_name(self) -> str:
        return TABLE_NAME

    @property
    def column_defs(self) -> list:
        return COLUMN_DEFS

    @property
    def _row_factory(self) -> Callable:
        return _override_factory

    def get_stored_override_for_instrument(self, instrument_code: str) -> Override:
        try:
            override = self._select_one({INSTRUMENT_CODE: instrument_code})
        except missingData:
            return DEFAULT_OVERRIDE
        return override

    def _add_stored_override_without_checking(
        self, instrument_code: str, override_for_instrument: Override
    ):
        params = {
            INSTRUMENT_CODE: instrument_code,
            OVERRIDE: override_for_instrument.as_numeric_value(),
        }
        self._insert(params, allow_replace=True)

    def _delete_stored_override_without_checking(self, instrument_code: str):
        self._delete({INSTRUMENT_CODE: instrument_code})

    def does_instrument_have_override_stored(self, instrument_code) -> bool:
        try:
            self._select_one({INSTRUMENT_CODE: instrument_code})
        except missingData:
            return False
        return True


def _override_factory(cursor, row) -> Override:
    row_dict = _row_to_dict(cursor, row)
    numeric_value = row_dict.get(OVERRIDE)
    override = Override.from_numeric_value(numeric_value)
    return override