from syscore.constants import arg_not_supplied
from syscore.exceptions import missingData
from sysdata.sqlite.sqlite_data import sqliteData
from sysexecution.order_stacks.broker_order_stack import brokerOrderStackData
from sysexecution.order_stacks.contract_order_stack import contractOrderStackData
from sysexecution.order_stacks.instrument_order_stack import instrumentOrderStackData
from sysexecution.order_stacks.order_stack import orderStackData, missingOrder
from sysexecution.orders.base_orders import Order
from sysexecution.orders.broker_orders import brokerOrder
from sysexecution.orders.contract_orders import contractOrder
from sysexecution.orders.instrument_orders import instrumentOrder
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

ORDER_ID_STORE_KEY = "_ORDER_ID_STORE_KEY"
MAX_ORDER_KEY = "max_order_id"


class sqliteOrderStackData(orderStackData, sqliteData):

    def __init__(
        self, sqlite_conn=arg_not_supplied, log=get_logger("sqliteOrderStackData")
    ):
        orderStackData.__init__(self, log=log)
        sqliteData.__init__(self, sqlite_conn=sqlite_conn)

    def __repr__(self):
        return f"{self._name} with {self.number_of_orders_on_stack()} active orders"

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
        max_orderid = self._get_current_max_order_id()
        new_orderid = max_orderid + 1
        self._update_max_order_id(new_orderid)
        return new_orderid

    def _get_current_max_order_id(self) -> int:
        try:
            result_dict = self.mongo_data.get_result_dict_for_key(ORDER_ID_STORE_KEY)
        except missingData:
            orderid = self._create_and_return_max_order_id()
            return orderid

        order_id = result_dict[MAX_ORDER_KEY]

        return int(order_id)

    def _update_max_order_id(self, max_order_id: int):
        self.mongo_data.add_data(
            ORDER_ID_STORE_KEY, {MAX_ORDER_KEY: max_order_id}, allow_overwrite=True
        )

    def _create_and_return_max_order_id(self):
        first_order_id = 1
        self._update_max_order_id(first_order_id)

        return first_order_id

    def _remove_order_with_id_from_stack_no_checking(self, order_id):
        self.mongo_data.delete_data_without_any_warning(order_id)


class mongoInstrumentOrderStackData(sqliteOrderStackData, instrumentOrderStackData):
    def _collection_name(self):
        return "INSTRUMENT_ORDER_STACK"

    def _order_class(self):
        return instrumentOrder


class mongoContractOrderStackData(sqliteOrderStackData, contractOrderStackData):
    def _collection_name(self):
        return "CONTRACT_ORDER_STACK"

    def _order_class(self):
        return contractOrder


class mongoBrokerOrderStackData(sqliteOrderStackData, brokerOrderStackData):
    def _collection_name(self):
        return "BROKER_ORDER_STACK"

    def _order_class(self):
        return brokerOrder
