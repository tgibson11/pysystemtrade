import datetime as dt
import sqlite3

from sqlite3 import Connection
from typing import Callable

import pandas as pd

from syscore.constants import arg_not_supplied
from syscore.exceptions import missingData
from sysdata.config.production_config import get_production_config


class sqliteData(object):

    def __init__(self, sqlite_conn: Connection = arg_not_supplied):
        if sqlite_conn is arg_not_supplied:
            sqlite_conn = get_sqlite_connection()
        self._sqlite_conn = sqlite_conn

    @property
    def sqlite_conn(self) -> Connection:
        return self._sqlite_conn

    @property
    def table_name(self) -> str:
        raise NotImplementedError()

    @property
    def column_defs(self) -> list:
        raise NotImplementedError()

    @property
    def _row_factory(self) -> Callable:
        raise NotImplementedError()

    def _select_one(self, params: dict = None):
        if params is None:
            params = {}
        where_clause = _params_dict_to_where_clause(params)
        sql = f"SELECT * FROM {self.table_name} {where_clause}"

        cursor = self.sqlite_conn.cursor()
        cursor.row_factory = self._row_factory
        result = cursor.execute(sql, params).fetchone()
        if result is None:
            raise missingData
        return result

    def _select_many(self, params: dict = None) -> list:
        if params is None:
            params = {}
        where_clause = _params_dict_to_where_clause(params)
        sql = f"SELECT * FROM {self.table_name} {where_clause}"
        cursor = self.sqlite_conn.cursor()
        cursor.row_factory = self._row_factory
        results = cursor.execute(sql, params).fetchall()
        return results

    def _select_all(self) -> list:
        return self._select_many()

    def _insert(self, params: dict, allow_replace: bool = False):
        if allow_replace:
            replace = "OR REPLACE"
        else:
            replace = ""

        columns = params.keys()
        placeholders = [f":{col}" for col in columns]

        sql = (
            f"INSERT {replace} INTO {self.table_name} ({','.join(columns)}) "
            f"VALUES ({','.join(placeholders)})"
        )

        with self.sqlite_conn:
            self.sqlite_conn.execute(sql, params)

    def _insert_many(self, params: list, allow_replace: bool = False):
        if len(params) == 0:
            return

        if allow_replace:
            replace = "OR REPLACE"
        else:
            replace = ""

        columns = params[0].keys()
        placeholders = [f":{col}" for col in columns]

        sql = (
            f"INSERT {replace} INTO {self.table_name} ({','.join(columns)}) "
            f"VALUES ({','.join(placeholders)})"
        )

        with self.sqlite_conn:
            self.sqlite_conn.executemany(sql, params)

    def _update(self, set_params: dict, where_params: dict = None):
        if where_params is None:
            where_params = {}

        # If this assertion fails, we'll need to be more clever
        assert (set_key not in where_params for set_key in set_params.keys())

        set_clause = _params_dict_to_set_clause(set_params)
        where_clause = _params_dict_to_where_clause(where_params)

        sql = f"UPDATE {self.table_name} {set_clause} {where_clause}"

        merged_params = set_params | where_params

        with self.sqlite_conn:
            self.sqlite_conn.execute(sql, merged_params)

    def _delete(self, params: dict = None):
        if params is None:
            params = {}
        where_clause = _params_dict_to_where_clause(params)
        sql = f"DELETE FROM {self.table_name} {where_clause}"
        with self.sqlite_conn:
            self.sqlite_conn.execute(sql, params)

    # Table management

    def _table_exists(self) -> bool:
        sql = "SELECT 1 FROM sqlite_master WHERE type='table' AND name=:name"
        params = {"name": self.table_name}
        tables = self.sqlite_conn.execute(sql, params).fetchall()
        exists = len(tables) > 0
        return exists

    def _create_table(self):
        if self._table_exists():
            print("Table already exists")
            return

        sql = f"CREATE TABLE {self.table_name} ({','.join(self.column_defs)})"

        with self.sqlite_conn:
            self.sqlite_conn.execute(sql)

    def _drop_table(self):
        with self.sqlite_conn:
            self.sqlite_conn.execute(f"DROP TABLE IF EXISTS {self.table_name}")


def get_sqlite_connection(db_file_name: str = arg_not_supplied) -> Connection:
    if db_file_name is arg_not_supplied:
        config = get_production_config()
        db_file_name = config.get_element("sqlite_database")

    sqlite_conn = sqlite3.connect(
        db_file_name, detect_types=sqlite3.PARSE_DECLTYPES, autocommit=True
    )
    return sqlite_conn


def _params_dict_to_where_clause(params: dict) -> str:
    if len(params) == 0:
        return ""
    conditions = [f"{col} = :{col}" for col in params.keys()]
    where_clause = f"WHERE {' and '.join(conditions)}"
    return where_clause


def _params_dict_to_set_clause(params: dict) -> str:
    conditions = [f"{col} = :{col}" for col in params.keys()]
    set_clause = f"SET {','.join(conditions)}"
    return set_clause


def _row_to_dict(cursor, row) -> dict:
    field_names = [column[0] for column in cursor.description]
    row_dict = {key: value for key, value in zip(field_names, row)}
    return row_dict


# Adapters

def _adapt_date_iso(val):
    """Adapt datetime.date to ISO 8601 date."""
    return val.isoformat()


def _adapt_datetime_iso(val):
    """Adapt datetime.datetime to timezone-naive ISO 8601 date."""
    return val.replace(tzinfo=None).isoformat()


def _adapt_timestamp_iso(val):
    """Adapt pandas.Timestamp to timezone-naive ISO 8601 date."""
    python_datetime = val.to_pydatetime()
    return _adapt_datetime_iso(python_datetime)


def _adapt_list(val):
    """Adapt list to string"""
    return ",".join(str(item) for item in val)


sqlite3.register_adapter(dt.date, _adapt_date_iso)
sqlite3.register_adapter(dt.datetime, _adapt_datetime_iso)
sqlite3.register_adapter(pd.Timestamp, _adapt_datetime_iso)
sqlite3.register_adapter(list, _adapt_list)


# Converters

def _convert_date(val):
    """Convert ISO 8601 date to datetime.date object."""
    return dt.date.fromisoformat(val.decode())


def _convert_datetime(val):
    """Convert ISO 8601 datetime to datetime.datetime object."""
    return dt.datetime.fromisoformat(val.decode())


def _convert_bool(val):
    """Convert integer value to bool."""
    return bool(int(val))


def _convert_list_of_int(val):
    """Convert string of comma separated integers to list."""
    return [int(item) for item in val.decode().split(",")]


def _convert_list_of_float(val):
    """Convert string of comma separated floats to list."""
    return [float(item) for item in val.decode().split(",")]


sqlite3.register_converter("date", _convert_date)
sqlite3.register_converter("datetime", _convert_datetime)
sqlite3.register_converter("bool", _convert_bool)
sqlite3.register_converter("list_of_int", _convert_list_of_int)
sqlite3.register_converter("list_of_float", _convert_list_of_float)
