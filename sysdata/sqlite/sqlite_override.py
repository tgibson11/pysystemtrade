import sqlite3
from typing import Callable

from syscore.constants import arg_not_supplied
from syscore.exceptions import missingData
from sysdata.production.override import overrideData
from sysdata.sqlite.sqlite_data import sqliteData, _row_to_dict, _params_dict_to_where_clause
from sysobjects.production.override import Override
from syslogging.logger import *

TABLE_NAME = "override"

# Columns
TYPE = "type"
KEY = "key"
VALUE = "value"

COLUMN_DEFS = [
    f"{TYPE} TEXT",
    f"{KEY} TEXT",
    f"{VALUE} FLOAT",
    f"PRIMARY KEY (TYPE, KEY)",
]


class sqliteOverrideData(overrideData, sqliteData):
    """
    Read and write data class to get override state data


    """

    def __init__(
        self,
        sqlite_conn: sqlite3.Connection = arg_not_supplied,
        log=get_logger("sqliteOverrideData")
    ):
        overrideData.__init__(self, log=log)
        sqliteData.__init__(self, sqlite_conn=sqlite_conn)

    def __repr__(self):
        return "sqliteOverrideData"

    @property
    def table_name(self) -> str:
        return TABLE_NAME

    @property
    def column_defs(self) -> list:
        return COLUMN_DEFS

    @property
    def _row_factory(self) -> Callable:
        return _override_factory

    def _get_override_object_for_type_and_key(
        self, override_type: str, key: str
    ) -> Override:
        params = {TYPE: override_type, KEY: key}
        try:
            override = self._select_one(params)
        except missingData:
            return self.default_override()
        return override

    def _update_override(
        self, override_type: str, key: str, new_override_object: Override
    ):
        if new_override_object.is_no_override():
            self._update_override_to_no_override(override_type, key)
        else:
            self._update_other_type_of_override(override_type, key, new_override_object)

    def _update_override_to_no_override(self, override_type: str, key: str):
        params = {TYPE: override_type, KEY: key}
        self._delete(params)

    def _update_other_type_of_override(
        self, override_type: str, key: str, new_override_object: Override
    ):
        value = new_override_object.as_numeric_value()
        params = {TYPE: override_type, KEY: key, VALUE: value}
        self._insert(params, allow_replace=True)

    def _get_dict_of_items_with_overrides_for_type(self, override_type: str) -> dict:
        params = {TYPE: override_type}
        where_clause = _params_dict_to_where_clause(params)
        sql = f"SELECT {KEY}, {VALUE} FROM {self.table_name} {where_clause}"
        rows = self.sqlite_conn.execute(sql, params).fetchall()
        override_dict = {
            row[0]: Override.from_numeric_value(row[1])
            for row in rows
        }
        return override_dict

    def _delete_all_overrides_without_checking(self):
        self.log.warning("DELETING ALL OVERRIDES!")
        self._delete(delete_all_rows=True)


def _override_factory(cursor, row) -> Override:
    row_dict = _row_to_dict(cursor, row)
    value = row_dict.get(VALUE)
    override = Override.from_numeric_value(value)
    return override