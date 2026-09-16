import datetime
from typing import Callable

from syscore.constants import arg_not_supplied
from syscore.exceptions import missingData
from sysdata.production.historic_orders import (
    genericOrdersData,
    strategyHistoricOrdersData,
    contractHistoricOrdersData,
    brokerHistoricOrdersData,
)
from sysdata.sqlite.sqlite_data import sqliteData
from sysdata.sqlite.sqlite_order_stack import (
    ORDER_ID,
    FILL_DATETIME,
    KEY,
    INSTRUMENT_COLUMN_DEFS,
    _instrument_order_factory,
    CONTRACT_COLUMN_DEFS,
    _contract_order_factory,
    BROKER_COLUMN_DEFS,
    _broker_order_factory,
)
from sysexecution.order_stacks.order_stack import missingOrder
from sysexecution.orders.base_orders import Order
from syslogging.logger import get_logger
from sysobjects.production.tradeable_object import instrumentStrategy, futuresContractStrategy


class sqliteGenericHistoricOrdersData(genericOrdersData, sqliteData):

    def __init__(
        self,
        sqlite_conn=arg_not_supplied,
        log=get_logger("sqliteGenericHistoricOrdersData")
    ):
        genericOrdersData.__init__(self, log=log)
        sqliteData.__init__(self, sqlite_conn=sqlite_conn)

    def _add_order_to_data_no_checking(self, order: Order):
        # Duplicates will be overridden, so be careful
        self._insert(order.as_dict(), allow_replace=True)

    def get_order_with_orderid(self, order_id: int):
        try:
            order = self._select_one({ORDER_ID: order_id})
        except missingData:
            raise missingOrder
        return order

    def _delete_order_with_orderid_without_checking(self, order_id):
        self._delete({ORDER_ID: order_id})

    def update_order_with_orderid(self, order_id, order):
        set_params = order.as_dict()
        set_params.pop("order_id")

        where_params = {ORDER_ID: order_id}
        self._update(set_params, where_params)

    def get_list_of_order_ids(self) -> list:
        sql = f"SELECT {ORDER_ID} FROM {self.table_name}"
        rows = self.sqlite_conn.execute(sql).fetchall()
        order_ids = [row[0] for row in rows]
        return order_ids

    def get_list_of_order_ids_in_date_range(
        self,
        period_start: datetime.datetime,
        period_end: datetime.datetime = arg_not_supplied,
    ) -> list:
        if period_end is arg_not_supplied:
            period_end = datetime.datetime.now()

        where_clause = f"WHERE {FILL_DATETIME} >= :start AND {FILL_DATETIME} < :end"
        sql = f"SELECT {ORDER_ID} FROM {self.table_name} {where_clause}"
        params = {"start": period_start, "end": period_end}

        rows = self.sqlite_conn.execute(sql, params).fetchall()
        order_ids = [row[0] for row in rows]
        return order_ids


STRATEGY_TABLE_NAME = "STRATEGY_HISTORIC_ORDER"


class sqliteStrategyHistoricOrdersData(
    sqliteGenericHistoricOrdersData, strategyHistoricOrdersData
):
    @property
    def table_name(self) -> str:
        return STRATEGY_TABLE_NAME

    @property
    def column_defs(self) -> list:
        return INSTRUMENT_COLUMN_DEFS

    @property
    def _row_factory(self) -> Callable:
        return _instrument_order_factory

    def __repr__(self):
        return "Historic instrument/strategy orders"

    def get_list_of_order_ids_for_instrument_strategy(
        self, instrument_strategy: instrumentStrategy
    ) -> list:
        params = {
            KEY: instrument_strategy.key,
            "old_key": instrument_strategy.old_key
        }
        where_clause = f"WHERE {KEY} IN (:{KEY}, :old_key)"
        sql = f"SELECT {ORDER_ID} FROM {self.table_name} {where_clause}"
        rows = self.sqlite_conn.execute(sql, params).fetchall()
        order_ids = [row[0] for row in rows]
        return order_ids


CONTRACT_TABLE_NAME = "CONTRACT_HISTORIC_ORDER"


class sqliteContractHistoricOrdersData(
    sqliteGenericHistoricOrdersData, contractHistoricOrdersData
):
    def __repr__(self):
        return "Historic contract orders"

    @property
    def table_name(self) -> str:
        return CONTRACT_TABLE_NAME

    @property
    def column_defs(self) -> list:
        return CONTRACT_COLUMN_DEFS

    @property
    def _row_factory(self) -> Callable:
        return _contract_order_factory


BROKER_TABLE_NAME = "BROKER_HISTORIC_ORDER"


class sqliteBrokerHistoricOrdersData(
    sqliteGenericHistoricOrdersData, brokerHistoricOrdersData
):

    def __repr__(self):
        return "Historic broker orders"

    @property
    def table_name(self) -> str:
        return BROKER_TABLE_NAME

    @property
    def column_defs(self) -> list:
        return BROKER_COLUMN_DEFS

    @property
    def _row_factory(self) -> Callable:
        return _broker_order_factory

    def get_list_of_order_ids_for_instrument_and_contract_str(
        self, instrument_code: str, contract_str: str
    ) -> list:
        # Get lists of all order_ids and the corresponding keys
        sql = f"SELECT {ORDER_ID}, {KEY} FROM {self.table_name}"
        rows = self.sqlite_conn.execute(sql).fetchall()
        order_id_list = [row[0] for row in rows]
        key_list = [row[1] for row in rows]

        # Construct a futuresContractStrategy object from each key
        contract_strategies = [
            futuresContractStrategy.from_key(key) for key in key_list
        ]

        # Find futuresContractStrategies that match the specified instrument & contract,
        # and get the corresponding order_ids
        order_ids = [
            orderid
            for orderid, futures_contract_strategy in zip(
                order_id_list, contract_strategies
            )
            if futures_contract_strategy.contains_both(
                instrument_code=instrument_code,
                contract_str=contract_str,
            )
        ]

        return order_ids
