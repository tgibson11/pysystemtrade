from typing import Callable

from syscore.constants import arg_not_supplied
from syscore.exceptions import missingData
from sysdata.sqlite.sqlite_data import sqliteData, _row_to_dict
from sysexecution.order_stacks.broker_order_stack import brokerOrderStackData
from sysexecution.order_stacks.contract_order_stack import contractOrderStackData
from sysexecution.order_stacks.instrument_order_stack import instrumentOrderStackData
from sysexecution.order_stacks.order_stack import orderStackData, missingOrder
from sysexecution.orders.base_orders import Order
from sysexecution.orders.broker_orders import brokerOrder
from sysexecution.orders.contract_orders import contractOrder
from sysexecution.orders.instrument_orders import instrumentOrder
from sysexecution.orders.named_order_objects import no_children
from syslogging.logger import *

# Columns common to all orders
ORDER_ID = "order_id"
KEY = "key"
TRADE = "trade"
FILL = "fill"
FILL_DATETIME = "fill_datetime"
FILLED_PRICE = "filled_price"
LOCKED = "locked"
PARENT = "parent"
CHILDREN = "children"
ACTIVE = "active"
ORDER_TYPE = "order_type"
LIMIT_PRICE = "limit_price"
ROLL_ORDER = "roll_order"

ORDER_COLUMN_DEFS = [
    f"{ORDER_ID} INTEGER PRIMARY KEY",
    f"{KEY} TEXT",
    f"{TRADE} LIST_OF_INT",
    f"{FILL} LIST_OF_INT",
    f"{FILL_DATETIME} DATETIME",
    f"{FILLED_PRICE} FLOAT",
    f"{LOCKED} BOOL",
    f"{PARENT} INTEGER",
    f"{CHILDREN} LIST_OF_INT",
    f"{ACTIVE} BOOL",
    f"{ORDER_TYPE} TEXT",
    f"{LIMIT_PRICE} FLOAT",
    f"{ROLL_ORDER} INTEGER",
]


class sqliteOrderStackData(orderStackData, sqliteData):

    def __init__(
        self, sqlite_conn=arg_not_supplied, log=get_logger("sqliteOrderStackData")
    ):
        orderStackData.__init__(self, log=log)
        sqliteData.__init__(self, sqlite_conn=sqlite_conn)
        self._order_id_data = sqliteMaxOrderIdData(self.sqlite_conn)

    def __repr__(self):
        return f"{self._name} with {self.number_of_orders_on_stack()} active orders"

    @property
    def table_name(self) -> str:
        raise NotImplementedError

    @property
    def column_defs(self) -> list:
        raise NotImplementedError

    @property
    def _row_factory(self) -> Callable:
        raise NotImplementedError

    @property
    def order_id_data(self):
        return self._order_id_data

    def get_order_with_id_from_stack(self, order_id: int):
        try:
            order = self._select_one({ORDER_ID: order_id})
        except missingData:
            raise missingOrder
        return order

    def _get_list_of_all_order_ids(self) -> list:
        sql = f"SELECT {ORDER_ID} FROM {self.table_name}"
        rows = self.sqlite_conn.execute(sql).fetchall()
        order_ids = [row[0] for row in rows]
        return order_ids

    def _change_order_on_stack_no_checking(self, order_id: int, order):
        set_params = order.as_dict()
        set_params.pop("order_id")

        where_params = {ORDER_ID: order_id}
        self._update(set_params, where_params)

    def _put_order_on_stack_no_checking(self, order: Order):
        self._insert(order.as_dict())

    def _get_next_order_id(self) -> int:
        return self._order_id_data.get_next_order_id(self.table_name)

    def _remove_order_with_id_from_stack_no_checking(self, order_id):
        self._delete({ORDER_ID: order_id})


INSTRUMENT_STACK_NAME = "instrument_order_stack"

# Instrument-specific columns
LIMIT_CONTRACT = "limit_contract"
REFERENCE_CONTRACT = "reference_contract"
REFERENCE_DATETIME = "reference_datetime"
REFERENCE_PRICE = "reference_price"
MANUAL_TRADE = "manual_trade"
GENERATED_DATETIME = "generated_datetime"

INSTRUMENT_ONLY_DEFS = [
    f"{LIMIT_CONTRACT} TEXT",
    f"{REFERENCE_CONTRACT} TEXT",
    f"{REFERENCE_DATETIME} DATETIME",
    f"{REFERENCE_PRICE} FLOAT",
    f"{MANUAL_TRADE} INTEGER",
    f"{GENERATED_DATETIME} DATETIME",
]
INSTRUMENT_COLUMN_DEFS = ORDER_COLUMN_DEFS + INSTRUMENT_ONLY_DEFS


class sqliteInstrumentOrderStackData(sqliteOrderStackData, instrumentOrderStackData):

    @property
    def table_name(self) -> str:
        return INSTRUMENT_STACK_NAME

    @property
    def column_defs(self) -> list:
        return INSTRUMENT_COLUMN_DEFS

    @property
    def _row_factory(self) -> Callable:
        return _instrument_order_factory


def _instrument_order_factory(cursor, row) -> instrumentOrder:
    row_dict = _row_to_dict(cursor, row)
    if row_dict[CHILDREN] is None:
        row_dict[CHILDREN] = no_children
    order = instrumentOrder.from_dict(row_dict)
    return order


CONTRACT_STACK_NAME = "contract_order_stack"

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
    f"{REFERENCE_PRICE} FLOAT",  # Also used for instrument orders
    f"{MANUAL_TRADE} INTEGER",  # Also used for instrument orders
    f"{GENERATED_DATETIME} DATETIME",  # Also used for instrument orders
]
CONTRACT_COLUMN_DEFS = ORDER_COLUMN_DEFS + CONTRACT_ONLY_DEFS


class sqliteContractOrderStackData(sqliteOrderStackData, contractOrderStackData):

    @property
    def table_name(self) -> str:
        return CONTRACT_STACK_NAME

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


BROKER_STACK_NAME = "broker_order_stack"

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


class sqliteBrokerOrderStackData(sqliteOrderStackData, brokerOrderStackData):

    @property
    def table_name(self) -> str:
        return BROKER_STACK_NAME

    @property
    def column_defs(self) -> list:
        return BROKER_COLUMN_DEFS

    @property
    def _row_factory(self) -> Callable:
        return _broker_order_factory


def _broker_order_factory(cursor, row) -> brokerOrder:
    row_dict = _row_to_dict(cursor, row)
    if row_dict[CHILDREN] is None:
        row_dict[CHILDREN] = no_children
    if row_dict[LEG_FILLED_PRICE] is None:
        row_dict[LEG_FILLED_PRICE] = []
    order = brokerOrder.from_dict(row_dict)
    return order


ORDER_ID_TABLE = "order_id"

ORDER_STACK = "order_stack"
MAX_ORDER_ID = "max_order_id"

ORDER_ID_COLUMN_DEFS = [
    f"{ORDER_STACK} TEXT PRIMARY KEY",
    f"{MAX_ORDER_ID} INTEGER",
]


class sqliteMaxOrderIdData(sqliteData):
    def __init__(
        self, sqlite_conn=arg_not_supplied
    ):
        sqliteData.__init__(self, sqlite_conn=sqlite_conn)

    @property
    def table_name(self) -> str:
        return ORDER_ID_TABLE

    @property
    def column_defs(self) -> list:
        return ORDER_ID_COLUMN_DEFS

    @property
    def _row_factory(self) -> Callable:
        return _order_id_factory

    def get_next_order_id(self, order_stack: str) -> int:
        max_orderid = self._get_current_max_order_id(order_stack)
        new_orderid = max_orderid + 1
        self._update_max_order_id(order_stack, new_orderid)
        return new_orderid

    def _get_current_max_order_id(self, order_stack: str) -> int:
        try:
            max_order_id = self._select_one({ORDER_STACK: order_stack})
        except missingData:
            max_order_id = self._create_and_return_max_order_id(order_stack)
        return max_order_id

    def _create_and_return_max_order_id(self, order_stack: str):
        first_order_id = 1
        self._update_max_order_id(order_stack, first_order_id)
        return first_order_id

    def _update_max_order_id(self, order_stack: str, max_order_id: int):
        params = {
            ORDER_STACK: order_stack,
            MAX_ORDER_ID: max_order_id,
        }
        self._insert(params, allow_replace=True)


def _order_id_factory(cursor, row) -> str:
    row_dict = _row_to_dict(cursor, row)
    order_id = row_dict.get(MAX_ORDER_ID)
    return order_id
