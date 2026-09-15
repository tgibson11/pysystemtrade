import sqlite3
from typing import Callable

import pandas as pd

from syscore.constants import arg_not_supplied
from sysdata.production.margin import marginData, seriesOfMargin
from sysdata.sqlite.sqlite_data import sqliteData
from syslogging.logger import *

TABLE_NAME = "margin"

# Columns
STRATEGY_NAME = "strategy_name"
DATETIME = "datetime"
MARGIN = "margin"

COLUMN_DEFS = [
    f"{STRATEGY_NAME} TEXT",
    f"{DATETIME} DATETIME",
    f"{MARGIN} FLOAT",
    f"PRIMARY KEY ({STRATEGY_NAME}, {DATETIME})"
]

class sqliteMarginData(marginData, sqliteData):

    def __init__(
        self,
        sqlite_conn: sqlite3.Connection = arg_not_supplied,
        log=get_logger("sqliteMarginData"),
    ):
        sqliteData.__init__(self, sqlite_conn=sqlite_conn)
        self._log = log

    def __repr__(self):
        return "Margin data"

    @property
    def log(self):
        return self._log

    @property
    def table_name(self) -> str:
        return TABLE_NAME

    @property
    def column_defs(self) -> list:
        return COLUMN_DEFS

    @property
    def _row_factory(self) -> Callable:
        return sqlite3.Row

    def get_series_of_strategy_margin(self, strategy_name: str) -> seriesOfMargin:
        rows = self._get_data_dict_for_strategy_margin(strategy_name)
        series_of_margin = from_rows_to_margin_series(rows)
        return series_of_margin

    def _get_data_dict_for_strategy_margin(self, strategy_name: str) -> list:
        rows = self._select_many({STRATEGY_NAME: strategy_name})
        return rows

    def _write_series_of_strategy_margin(
        self, strategy_name: str, series_of_margin: seriesOfMargin
    ):
        params = from_series_of_margin_to_params(
            strategy_name, series_of_margin
        )
        self._insert_many(params, allow_replace=True)

    def _get_list_of_strategies_with_margin_including_total(self) -> list:
        sql = f"SELECT DISTINCT {STRATEGY_NAME} FROM {self.table_name}"
        rows = self.sqlite_conn.execute(sql).fetchall()
        strategies = [row[0] for row in rows]
        return strategies


def from_rows_to_margin_series(rows: list[sqlite3.Row]) -> seriesOfMargin:
    datetimes = [row[DATETIME] for row in rows]
    margin_values = [row[MARGIN] for row in rows]

    pd_series = pd.Series(
        margin_values, index=datetimes, dtype="float64"
    )
    pd_series = pd_series.sort_index()

    return seriesOfMargin(pd_series)


def from_series_of_margin_to_params(
    strategy_name: str, series_of_margin: seriesOfMargin
) -> list[dict]:
    list_of_timestamps = list(series_of_margin.index)
    list_of_datetimes = [ts.to_pydatetime() for ts in list_of_timestamps]
    list_of_values = list(series_of_margin.values)
    list_of_dicts = [
        {
            STRATEGY_NAME: strategy_name,
            DATETIME: dt,
            MARGIN: value,
        }
        for dt, value in zip(list_of_datetimes, list_of_values)
    ]
    return list_of_dicts
