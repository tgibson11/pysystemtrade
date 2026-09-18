import sqlite3
from typing import Callable

from syscore.constants import arg_not_supplied
from sysdata.production.position_limits import positionLimitData
from sysdata.sqlite.sqlite_data import sqliteData, _row_to_dict
from syslogging.logger import *
from sysobjects.production.tradeable_object import (
    listOfInstrumentStrategies,
    instrumentStrategy,
)

INSTRUMENT_TABLE_NAME = "instrument_position_limit"
STRATEGY_TABLE_NAME = "strategy_position_limit"

# Columns
STRATEGY = "strategy"
INSTRUMENT_CODE = "instrument_code"
POSITION_LIMIT = "position_limit"

INSTRUMENT_COLUMN_DEFS = [
    f"{INSTRUMENT_CODE} TEXT PRIMARY KEY",
    f"{POSITION_LIMIT} INTEGER",
]

STRATEGY_COLUMN_DEFS = [
    f"{STRATEGY} TEXT",
    f"{INSTRUMENT_CODE} TEXT",
    f"{POSITION_LIMIT} INTEGER",
    f"PRIMARY KEY (STRATEGY, INSTRUMENT_CODE)",
]


class sqlitePositionLimitData(positionLimitData):

    def __init__(
        self,
        sqlite_conn: sqlite3.Connection = arg_not_supplied,
        log=get_logger("sqlitePositionLimitData")
    ):
        super().__init__(log=log)
        self._strategy_data = _sqliteStrategyPositionLimitData(sqlite_conn)
        self._instrument_data = _sqliteInstrumentPositionLimitData(sqlite_conn)

    def __repr__(self):
        return "Data connection for position limit data"

    @property
    def strategy_data(self):
        return self._strategy_data

    @property
    def instrument_data(self):
        return self._instrument_data

    def get_all_instruments_with_limits(self) -> list:
        return self._instrument_data.get_all_instruments_with_limits()

    def get_all_instrument_strategies_with_limits(self) -> listOfInstrumentStrategies:
        return self._strategy_data.get_all_instrument_strategies_with_limits()

    def delete_position_limit_for_instrument_strategy(
        self, instrument_strategy: instrumentStrategy
    ):
        self._strategy_data.delete_position_limit_for_instrument_strategy(
            instrument_strategy
        )

    def delete_position_limit_for_instrument(self, instrument_code: str):
        self._instrument_data.delete_position_limit_for_instrument(instrument_code)

    def _get_abs_position_limit_for_instrument_strategy(
        self, instrument_strategy: instrumentStrategy
    ) -> int:
        return self._strategy_data.get_abs_position_limit_for_instrument_strategy(
            instrument_strategy
        )

    def _get_abs_position_limit_for_instrument(self, instrument_code: str) -> int:
        return self._instrument_data.get_abs_position_limit_for_instrument(
            instrument_code
        )

    def set_position_limit_for_instrument_strategy(
        self, instrument_strategy: instrumentStrategy, new_position_limit: int
    ):
        self._strategy_data.set_position_limit_for_instrument_strategy(
            instrument_strategy, new_position_limit
        )

    def set_position_limit_for_instrument(
        self, instrument_code: str, new_position_limit: int
    ):
        self._instrument_data.set_position_limit_for_instrument(
            instrument_code, new_position_limit
        )


class _sqliteInstrumentPositionLimitData(sqliteData):
    def __init__(
        self,
        sqlite_conn: sqlite3.Connection = arg_not_supplied,
    ):
        sqliteData.__init__(self, sqlite_conn=sqlite_conn)

    def __repr__(self):
        return "Data connection for instrument position limit data"

    @property
    def table_name(self) -> str:
        return INSTRUMENT_TABLE_NAME

    @property
    def column_defs(self) -> list:
        return INSTRUMENT_COLUMN_DEFS

    @property
    def _row_factory(self) -> Callable:
        return _position_limit_factory

    def get_all_instruments_with_limits(self) -> list:
        sql = f"SELECT {INSTRUMENT_CODE} FROM {self.table_name}"
        rows = self.sqlite_conn.execute(sql).fetchall()
        instruments = [row[0] for row in rows]
        return instruments

    def delete_position_limit_for_instrument(self, instrument_code):
        params = {
            INSTRUMENT_CODE: instrument_code,
        }
        self._delete(params)

    def get_abs_position_limit_for_instrument(self, instrument_code):
        params = {
            INSTRUMENT_CODE: instrument_code,
        }
        return self._select_one(params)

    def set_position_limit_for_instrument(
        self, instrument_code: str, new_position_limit: int
    ):
        params = {
            INSTRUMENT_CODE: instrument_code,
            POSITION_LIMIT: new_position_limit,
        }
        self._insert(params, allow_replace=True)


class _sqliteStrategyPositionLimitData(sqliteData):
    def __init__(
        self,
        sqlite_conn: sqlite3.Connection = arg_not_supplied,
    ):
        sqliteData.__init__(self, sqlite_conn=sqlite_conn)

    def __repr__(self):
        return "Data connection for strategy position limit data"

    @property
    def table_name(self) -> str:
        return STRATEGY_TABLE_NAME

    @property
    def column_defs(self) -> list:
        return STRATEGY_COLUMN_DEFS

    @property
    def _row_factory(self) -> Callable:
        return _position_limit_factory

    def get_all_instrument_strategies_with_limits(self) -> listOfInstrumentStrategies:
        sql = f"SELECT {STRATEGY}, {INSTRUMENT_CODE} FROM {self.table_name}"
        rows = self.sqlite_conn.execute(sql).fetchall()
        instrument_strategies = [
            instrumentStrategy(strategy_name=row(0), instrument_code=row(1))
            for row in rows
        ]
        return listOfInstrumentStrategies(instrument_strategies)

    def delete_position_limit_for_instrument_strategy(
        self, instrument_strategy: instrumentStrategy
    ):
        params = {
            STRATEGY: instrument_strategy.strategy_name,
            INSTRUMENT_CODE: instrument_strategy.instrument_code,
        }
        self._delete(params)

    def get_abs_position_limit_for_instrument_strategy(
        self, instrument_strategy: instrumentStrategy
    ):
        params = {
            STRATEGY: instrument_strategy.strategy_name,
            INSTRUMENT_CODE: instrument_strategy.instrument_code,
        }
        return self._select_one(params)

    def set_position_limit_for_instrument_strategy(
        self, instrument_strategy: instrumentStrategy, new_position_limit: int
    ):
        params = {
            STRATEGY: instrument_strategy.strategy_name,
            INSTRUMENT_CODE: instrument_strategy.instrument_code,
            POSITION_LIMIT: new_position_limit,
        }
        self._insert(params, allow_replace=True)


def _position_limit_factory(cursor, row) -> int:
    row_dict = _row_to_dict(cursor, row)
    position_limit = row_dict.get(POSITION_LIMIT)
    return position_limit
