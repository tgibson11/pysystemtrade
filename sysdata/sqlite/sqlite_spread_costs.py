import sqlite3
from typing import Callable

import pandas as pd

from syscore.constants import arg_not_supplied
from syscore.exceptions import missingData
from sysdata.futures.spread_costs import spreadCostData
from sysdata.sqlite.sqlite_data import sqliteData, _row_to_dict
from syslogging.logger import *

TABLE_NAME = "spread_cost"

# Columns
INSTRUMENT_CODE = "instrument_code"
SPREAD_COST = "spread_cost"

COLUMN_DEFS = [
    f"{INSTRUMENT_CODE} TEXT PRIMARY KEY",
    f"{SPREAD_COST} FLOAT",
]


class sqliteSpreadCostData(spreadCostData, sqliteData):
    """
    Read and write data class to get spread costs


    """

    def __init__(
        self,
        sqlite_conn: sqlite3.Connection = arg_not_supplied,
        log=get_logger("sqliteSpreadCostData")
    ):
        spreadCostData.__init__(self, log=log)
        sqliteData.__init__(self, sqlite_conn=sqlite_conn)

    def __repr__(self):
        return "SQLite data connection for spread cost data"

    @property
    def table_name(self) -> str:
        return TABLE_NAME

    @property
    def column_defs(self) -> list:
        return COLUMN_DEFS

    @property
    def _row_factory(self) -> Callable:
        return _spread_cost_factory

    def delete_spread_cost(self, instrument_code: str):
        self._delete({INSTRUMENT_CODE: instrument_code})

    def get_list_of_instruments(self) -> list:
        sql = f"SELECT {INSTRUMENT_CODE} FROM {self.table_name}"
        rows = self.sqlite_conn.execute(sql).fetchall()
        instruments = [row[0] for row in rows]
        return instruments

    def get_spread_costs_as_series(self) -> pd.Series:
        return self._get_spread_costs_as_series_if_individual_spreads_provided()

    def get_spread_cost(self, instrument_code: str) -> float:
        try:
            spread_cost = self._select_one({INSTRUMENT_CODE: instrument_code})
        except missingData:
            self.log.warning(
                f"No spread cost in database for {instrument_code}, using 0"
            )
            return 0.0

        return spread_cost

    def update_spread_cost(self, instrument_code: str, spread_cost: float):
        params = {
            INSTRUMENT_CODE: instrument_code,
            SPREAD_COST: spread_cost,
        }
        self._insert(params, allow_replace=True)


def _spread_cost_factory(cursor, row) -> float:
    row_dict = _row_to_dict(cursor, row)
    return row_dict[SPREAD_COST]
