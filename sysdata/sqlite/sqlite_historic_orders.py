import datetime
from typing import Callable

from syscore.constants import arg_not_supplied
from syscore.exceptions import missingData
from sysdata.production.historic_orders import genericOrdersData, strategyHistoricOrdersData, \
    contractHistoricOrdersData, brokerHistoricOrdersData
from sysdata.sqlite.sqlite_data import sqliteData, _row_to_dict
from sysdata.sqlite.sqlite_order_stack import ORDER_ID, FILL_DATETIME, ORDER_COLUMN_DEFS, KEY, CHILDREN
from sysexecution.order_stacks.order_stack import missingOrder
from sysexecution.orders.base_orders import Order
from sysexecution.orders.broker_orders import brokerOrder
from sysexecution.orders.contract_orders import contractOrder
from sysexecution.orders.instrument_orders import instrumentOrder
from sysexecution.orders.named_order_objects import no_children
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

# Strategy-specific columns
LIMIT_CONTRACT = "limit_contract"
REFERENCE_CONTRACT = "reference_contract"
REFERENCE_DATETIME = "reference_datetime"
REFERENCE_PRICE = "reference_price"
MANUAL_TRADE = "manual_trade"
GENERATED_DATETIME = "generated_datetime"

STRATEGY_ONLY_DEFS = [
    f"{LIMIT_CONTRACT} TEXT",
    f"{REFERENCE_CONTRACT} TEXT",
    f"{REFERENCE_DATETIME} DATETIME",
    f"{REFERENCE_PRICE} FLOAT",
    f"{MANUAL_TRADE} INTEGER",
    f"{GENERATED_DATETIME} DATETIME",
]
STRATEGY_COLUMN_DEFS = ORDER_COLUMN_DEFS + STRATEGY_ONLY_DEFS


class sqliteStrategyHistoricOrdersData(
    sqliteGenericHistoricOrdersData, strategyHistoricOrdersData
):
    @property
    def table_name(self) -> str:
        return STRATEGY_TABLE_NAME

    @property
    def column_defs(self) -> list:
        return STRATEGY_COLUMN_DEFS

    @property
    def _row_factory(self) -> Callable:
        return _strategy_order_factory

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


def _strategy_order_factory(cursor, row) -> instrumentOrder:
    row_dict = _row_to_dict(cursor, row)
    if row_dict[CHILDREN] is None:
        row_dict[CHILDREN] = no_children
    order = instrumentOrder.from_dict(row_dict)
    return order


CONTRACT_TABLE_NAME = "CONTRACT_HISTORIC_ORDER"

# Contract-specific columns
ALGO_TO_USE = "algo_to_use"
MANUAL_FILL = "manual_fill"
CALENDAR_SPREAD_ORDER = "calendar_spread_order"
INTER_SPREAD_ORDER = "inter_spread_order"
REFERENCE_OF_CONTROLLING_ALGO = "reference_of_controlling_algo"

CONTRACT_ONLY_DEFS = [
    f"{ALGO_TO_USE} TEXT",
    f"{MANUAL_FILL} BOOL",
    f"{CALENDAR_SPREAD_ORDER} BOOL",
    f"{INTER_SPREAD_ORDER} BOOL",
    f"{REFERENCE_OF_CONTROLLING_ALGO} TEXT",
    f"{REFERENCE_PRICE} FLOAT",  # Also used by strategy orders
    f"{MANUAL_TRADE} INTEGER",  # Also used by strategy orders
    f"{GENERATED_DATETIME} DATETIME",  # Also used by strategy orders
]
CONTRACT_COLUMN_DEFS = ORDER_COLUMN_DEFS + CONTRACT_ONLY_DEFS


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


def _contract_order_factory(cursor, row) -> contractOrder:
    row_dict = _row_to_dict(cursor, row)
    if row_dict[CHILDREN] is None:
        row_dict[CHILDREN] = no_children
    order = contractOrder.from_dict(row_dict)
    return order


BROKER_TABLE_NAME = "BROKER_HISTORIC_ORDER"

# Broker-specific columns
ALGO_USED = "algo_used"
SUBMIT_DATETIME = "submit_datetime"
SIDE_PRICE = "side_price"
MID_PRICE = "mid_price"
OFFSIDE_PRICE = "offside_price"
ALGO_COMMENT = "algo_comment"
BROKER = "broker"
BROKER_ACCOUNT = "broker_account"
BROKER_PERMID = "broker_permid"
BROKER_TEMPID = "broker_tempid"
BROKER_CLIENTID = "broker_clientid"
COMMISSION = "commission"
LEG_FILLED_PRICE = "leg_filled_price"

BROKER_ONLY_DEFS = [
    f"{ALGO_USED} TEXT",
    f"{SUBMIT_DATETIME} DATETIME",
    f"{MANUAL_FILL} BOOL",  # Also used for contract orders
    f"{CALENDAR_SPREAD_ORDER} BOOL",  # Also used for contract orders
    f"{SIDE_PRICE} FLOAT",
    f"{MID_PRICE} FLOAT",
    f"{OFFSIDE_PRICE} FLOAT",
    f"{ALGO_COMMENT} TEXT",
    f"{BROKER} TEXT",
    f"{BROKER_ACCOUNT} TEXT",
    f"{BROKER_PERMID} TEXT",
    f"{BROKER_TEMPID} TEXT",
    f"{BROKER_CLIENTID} TEXT",
    f"{COMMISSION} FLOAT",
    f"{LEG_FILLED_PRICE} LIST_OF_FLOAT",
]
BROKER_COLUMN_DEFS = ORDER_COLUMN_DEFS + BROKER_ONLY_DEFS


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


def _broker_order_factory(cursor, row) -> brokerOrder:
    row_dict = _row_to_dict(cursor, row)
    if row_dict[CHILDREN] is None:
        row_dict[CHILDREN] = no_children
    if row_dict[LEG_FILLED_PRICE] is None:
        row_dict[LEG_FILLED_PRICE] = []
    order = brokerOrder.from_dict(row_dict)
    return order
