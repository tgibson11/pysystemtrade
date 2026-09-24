import sqlite3
from typing import Callable

from syscore.constants import arg_not_supplied
from sysdata.production.trade_limits import (
    tradeLimitData,
    listOfInstrumentStrategyKeyAndDays,
    instrumentStrategyKeyAndDays,
)
from sysdata.sqlite.sqlite_data import sqliteData, _row_to_dict
from sysobjects.production.tradeable_object import instrumentStrategy
from syslogging.logger import *

TABLE_NAME = "trade_limit"

# Columns
INSTRUMENT_STRATEGY_KEY = "instrument_strategy_key"
PERIOD_DAYS = "period_days"
TRADE_LIMIT = "trade_limit"
TRADES_SINCE_LAST_RESET = "trades_since_last_reset"
LAST_RESET_TIME = "last_reset_time"

COLUMN_DEFS = [
    f"{INSTRUMENT_STRATEGY_KEY} TEXT",
    f"{PERIOD_DAYS} INTEGER",
    f"{TRADE_LIMIT} INTEGER",
    f"{TRADES_SINCE_LAST_RESET} INTEGER",
    f"{LAST_RESET_TIME} DATETIME",
    f"PRIMARY KEY ({INSTRUMENT_STRATEGY_KEY}, {PERIOD_DAYS})",
]


class sqliteTradeLimitData(tradeLimitData, sqliteData):

    def __init__(
        self,
        sqlite_conn: sqlite3.Connection = arg_not_supplied,
        log=get_logger("sqliteTradeLimitData")
    ):
        tradeLimitData.__init__(self, log=log)
        sqliteData.__init__(self, sqlite_conn=sqlite_conn)

    def __repr__(self):
        return "SQLite data connection for trade limit data"

    @property
    def table_name(self) -> str:
        return TABLE_NAME

    @property
    def column_defs(self) -> list:
        return COLUMN_DEFS

    @property
    def _row_factory(self) -> Callable:
        return _trade_limit_factory

    def _get_trade_limit_as_dict_or_missing_data(
        self, instrument_strategy: instrumentStrategy, period_days: int
    ) -> dict:
        params = {
            INSTRUMENT_STRATEGY_KEY: instrument_strategy.key,
            PERIOD_DAYS: period_days,
        }
        return self._select_one(params)

    def _update_trade_limit_as_dict(self, trade_limit_dict: dict):
        self._insert(trade_limit_dict, allow_replace=True)

    def _get_all_limit_keys(self) -> listOfInstrumentStrategyKeyAndDays:
        trade_limit_dicts = self._select_many()

        trade_limit_keys = [
            _from_trade_limit_dict_to_isd(trade_limit_dict)
            for trade_limit_dict in trade_limit_dicts
        ]
        list_of_isd = listOfInstrumentStrategyKeyAndDays(trade_limit_keys)

        return list_of_isd


def _from_trade_limit_dict_to_isd(result_dict: dict) -> instrumentStrategyKeyAndDays:
    instrument_strategy_key = result_dict[INSTRUMENT_STRATEGY_KEY]
    return instrumentStrategyKeyAndDays(
        instrument_strategy_key, result_dict[PERIOD_DAYS]
    )


def _trade_limit_factory(cursor, row) -> dict:
    return _row_to_dict(cursor, row)
