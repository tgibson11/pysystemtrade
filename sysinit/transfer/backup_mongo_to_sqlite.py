from syscore.interactive.input import true_if_answer_is_yes
from sysdata.data_blob import dataBlob
from sysdata.mongodb.mongo_IB_client_id import mongoIbBrokerClientIdData
from sysdata.mongodb.mongo_futures_contracts import mongoFuturesContractData
from sysdata.mongodb.mongo_historic_orders import mongoBrokerHistoricOrdersData, mongoContractHistoricOrdersData, \
    mongoStrategyHistoricOrdersData
from sysdata.mongodb.mongo_lock_data import mongoLockData
from sysdata.mongodb.mongo_margin import mongoMarginData
from sysdata.mongodb.mongo_order_stack import mongoBrokerOrderStackData, mongoContractOrderStackData, \
    mongoInstrumentOrderStackData
from sysdata.mongodb.mongo_override import mongoOverrideData
from sysdata.mongodb.mongo_position_limits import mongoPositionLimitData
from sysdata.mongodb.mongo_process_control import mongoControlProcessData
from sysdata.mongodb.mongo_roll_state_storage import mongoRollStateData
from sysdata.mongodb.mongo_spread_costs import mongoSpreadCostData
from sysdata.mongodb.mongo_temporary_close import mongoTemporaryCloseData
from sysdata.mongodb.mongo_temporary_override import mongoTemporaryOverrideData
from sysdata.mongodb.mongo_trade_limits import mongoTradeLimitData
from sysdata.sqlite.sqlite_IB_client_id import sqliteIbBrokerClientIdData
from sysdata.sqlite.sqlite_data import sqliteData
from sysdata.sqlite.sqlite_email_control import sqliteEmailControlData
from sysdata.sqlite.sqlite_futures_contracts import sqliteFuturesContractData
from sysdata.sqlite.sqlite_historic_orders import sqliteBrokerHistoricOrdersData, sqliteContractHistoricOrdersData, \
    sqliteStrategyHistoricOrdersData
from sysdata.sqlite.sqlite_lock_data import sqliteLockData
from sysdata.sqlite.sqlite_margin import sqliteMarginData
from sysdata.sqlite.sqlite_order_stack import sqliteBrokerOrderStackData, sqliteContractOrderStackData, \
    sqliteInstrumentOrderStackData
from sysdata.sqlite.sqlite_override import sqliteOverrideData
from sysdata.sqlite.sqlite_position_limits import sqlitePositionLimitData
from sysdata.sqlite.sqlite_process_control import sqliteControlProcessData
from sysdata.sqlite.sqlite_roll_state_storage import sqliteRollStateData
from sysdata.sqlite.sqlite_spread_costs import sqliteSpreadCostData
from sysdata.sqlite.sqlite_temporary_close import sqliteTemporaryCloseData
from sysdata.sqlite.sqlite_temporary_override import sqliteTemporaryOverrideData
from sysdata.sqlite.sqlite_trade_limits import sqliteTradeLimitData
from syslogdiag.mongo_email_control import mongoEmailControlData


def backup_mongo_to_sqlite():
    backup_data = get_data_blob("backup_mongo_to_sqlite")
    log = backup_data.log

    log.debug("Copying from mongo to sqlite")
    do = true_if_answer_is_yes("Do email control?")
    if do:
        backup_email_control_data(backup_data)

    do = true_if_answer_is_yes("Futures contracts?")
    if do:
        backup_contract_data(backup_data)

    do = true_if_answer_is_yes("Historical orders?")
    if do:
        backup_historical_orders(backup_data)

    do = true_if_answer_is_yes("IB client IDs?")
    if do:
        backup_ib_client_ids(backup_data)

    do = true_if_answer_is_yes("Lock data?")
    if do:
        backup_lock_data(backup_data)

    do = true_if_answer_is_yes("Margin data?")
    if do:
        backup_margin_data(backup_data)

    do = true_if_answer_is_yes("Order stacks?")
    if do:
        backup_order_stacks(backup_data)

    do = true_if_answer_is_yes("Overrides?")
    if do:
        backup_overrides(backup_data)

    do = true_if_answer_is_yes("Position limits?")
    if do:
        backup_position_limits(backup_data)

    do = true_if_answer_is_yes("Process controls?")
    if do:
        backup_process_controls(backup_data)

    do = true_if_answer_is_yes("Roll states?")
    if do:
        backup_roll_state_data(backup_data)

    do = true_if_answer_is_yes("Spread costs?")
    if do:
        backup_spread_cost_data(backup_data)

    do = true_if_answer_is_yes("Temporary close data?")
    if do:
        backup_temporary_close_data(backup_data)

    do = true_if_answer_is_yes("Temporary overrides?")
    if do:
        backup_temporary_overrides(backup_data)

    do = true_if_answer_is_yes("Trade limits?")
    if do:
        backup_trade_limits(backup_data)


def get_data_blob(logname):
    data = dataBlob(log_name=logname, keep_original_prefix=True)

    data.add_class_list(
        [
            sqliteEmailControlData,
            sqliteFuturesContractData,
            sqliteBrokerHistoricOrdersData,
            sqliteContractHistoricOrdersData,
            sqliteStrategyHistoricOrdersData,
            sqliteIbBrokerClientIdData,
            sqliteLockData,
            sqliteMarginData,
            sqliteBrokerOrderStackData,
            sqliteContractOrderStackData,
            sqliteInstrumentOrderStackData,
            sqliteOverrideData,
            sqlitePositionLimitData,
            sqliteControlProcessData,
            sqliteRollStateData,
            sqliteSpreadCostData,
            sqliteTemporaryCloseData,
            sqliteTemporaryOverrideData,
            sqliteTradeLimitData,
        ],
    )

    data.add_class_list(
        [
            mongoEmailControlData,
            mongoFuturesContractData,
            mongoBrokerHistoricOrdersData,
            mongoContractHistoricOrdersData,
            mongoStrategyHistoricOrdersData,
            mongoIbBrokerClientIdData,
            mongoLockData,
            mongoMarginData,
            mongoBrokerOrderStackData,
            mongoContractOrderStackData,
            mongoInstrumentOrderStackData,
            mongoOverrideData,
            mongoPositionLimitData,
            mongoControlProcessData,
            mongoRollStateData,
            mongoSpreadCostData,
            mongoTemporaryCloseData,
            mongoTemporaryOverrideData,
            mongoTradeLimitData,
        ],
    )

    return data


def backup_email_control_data(data):
    data.log.debug("Creating email control table (will not copy data)...")
    create_table(data.sqlite_email_control)


def backup_contract_data(data):
    create_table(data.sqlite_futures_contract)
    instrument_list = (
        data.mongo_futures_contract.get_list_of_all_instruments_with_contracts()
    )
    for instrument_code in instrument_list:
        contract_list = (
            data.mongo_futures_contract.get_all_contract_objects_for_instrument_code(
                instrument_code
            )
        )
        for contract in contract_list:
            data.sqlite_futures_contract.add_contract_data(contract)
        data.log.debug(f"Backed up contract data for {instrument_code}")


def backup_historical_orders(data):
    data.log.debug("Backing up strategy orders...")
    create_table(data.sqlite_strategy_historic_orders)
    list_of_orders = [
        data.mongo_strategy_historic_orders.get_order_with_orderid(id)
        for id in data.mongo_strategy_historic_orders.get_list_of_order_ids()
    ]
    for order in list_of_orders:
        data.sqlite_strategy_historic_orders.add_order_to_data(order)
    data.log.debug("Done")

    data.log.debug("Backing up contract orders...")
    create_table(data.sqlite_contract_historic_orders)
    list_of_orders = [
        data.mongo_contract_historic_orders.get_order_with_orderid(order_id)
        for order_id in data.mongo_contract_historic_orders.get_list_of_order_ids()
    ]
    for order in list_of_orders:
        data.sqlite_contract_historic_orders.add_order_to_data(order)
    data.log.debug("Done")

    data.log.debug("Backing up broker orders...")
    create_table(data.sqlite_broker_historic_orders)
    list_of_orders = [
        data.mongo_broker_historic_orders.get_order_with_orderid(order_id)
        for order_id in data.mongo_broker_historic_orders.get_list_of_order_ids()
    ]
    for order in list_of_orders:
        data.sqlite_broker_historic_orders.add_order_to_data(order)
    data.log.debug("Done")


def backup_ib_client_ids(data):
    create_table(data.sqlite_ib_broker_client_id)
    client_ids = data.mongo_ib_broker_client_id._get_list_of_clientids()
    for client_id in client_ids:
        data.sqlite_ib_broker_client_id._lock_clientid(client_id)
    data.log.debug("Backed up ib client ids...")


def backup_lock_data(data):
    create_table(data.sqlite_lock)
    locked_instruments = data.mongo_lock.get_list_of_locked_instruments()
    for instrument in locked_instruments:
        data.sqlite_lock.add_lock_for_instrument(instrument)
    data.log.debug("Backed up locked instruments...")


def backup_margin_data(data):
    create_table(data.sqlite_margin)
    strategies = data.mongo_margin._get_list_of_strategies_with_margin_including_total()
    for strategy in strategies:
        print(f"Migrating margin for {strategy}")
        margin_series = data.mongo_margin.get_series_of_strategy_margin(strategy)
        data.sqlite_margin._write_series_of_strategy_margin(strategy, margin_series)
    data.log.debug("Backed up margin data...")


def backup_order_stacks(data):
    data.log.debug("Backing up instrument order stack...")
    create_table(data.sqlite_instrument_order_stack)
    list_of_orders = [
        data.mongo_instrument_order_stack.get_order_with_orderid(id)
        for id in data.mongo_instrument_order_stack.get_list_of_order_ids()
    ]
    for order in list_of_orders:
        data.sqlite_instrument_order_stack.put_order_on_stack(order)
    data.log.debug("Done")

    data.log.debug("Backing up contract order stack...")
    create_table(data.sqlite_contract_order_stack)
    list_of_orders = [
        data.mongo_contract_order_stack.get_order_with_orderid(id)
        for id in data.mongo_contract_order_stack.get_list_of_order_ids()
    ]
    for order in list_of_orders:
        data.sqlite_contract_order_stack.put_order_on_stack(order)
    data.log.debug("Done")

    data.log.debug("Backing up broker order stack...")
    create_table(data.sqlite_broker_order_stack)
    list_of_orders = [
        data.mongo_broker_order_stack.get_order_with_orderid(id)
        for id in data.mongo_broker_order_stack.get_list_of_order_ids()
    ]
    for order in list_of_orders:
        data.sqlite_broker_order_stack.put_order_on_stack(order)
    data.log.debug("Done")

    data.log.debug("Backing up max order ID data...")
    order_id_data = data.sqlite_instrument_order_stack._order_id_data
    create_table(order_id_data)

    instrument_stack_name = data.sqlite_instrument_order_stack.table_name
    contract_stack_name = data.sqlite_contract_order_stack.table_name
    broker_stack_name = data.sqlite_broker_order_stack.table_name

    max_instrument_order_id = data.mongo_instrument_order_stack._get_current_max_order_id()
    max_contract_order_id = data.mongo_contract_order_stack._get_current_max_order_id()
    max_broker_order_id = data.mongo_broker_order_stack._get_current_max_order_id()

    order_id_data._update_max_order_id(instrument_stack_name, max_instrument_order_id)
    order_id_data._update_max_order_id(contract_stack_name, max_contract_order_id)
    order_id_data._update_max_order_id(broker_stack_name, max_broker_order_id)
    data.log.debug("Done")


def backup_overrides(data):
    data.log.debug("Backing up override data...")
    create_table(data.sqlite_override)
    overrides = data.mongo_override.get_dict_of_all_overrides()
    for key in overrides.keys():
        data.sqlite_override.update_override_for_instrument(key, overrides[key])


def backup_position_limits(data):
    data.log.debug("Backing up ib instrument position limits...")
    sqlite_instrument_data = data.sqlite_position_limit._instrument_data
    create_table(sqlite_instrument_data)
    instruments = data.mongo_position_limit.get_all_instruments_with_limits()
    for instrument in instruments:
        position_limit = data.mongo_position_limit.get_position_limit_object_for_instrument(
            instrument
        )
        data.sqlite_position_limit.set_position_limit_for_instrument(
            instrument, position_limit.position_limit
        )

    data.log.debug("Backed up strategy position limits...")
    sqlite_strategy_data = data.sqlite_position_limit._strategy_data
    create_table(sqlite_strategy_data)
    instrument_strategies = data.mongo_position_limit.get_all_instrument_strategies_with_limits()
    for instrument_strategy in instrument_strategies:
        position_limit = data.mongo_position_limit.get_position_limit_object_for_instrument_strategy(
            instrument_strategy
        )
        data.sqlite_position_limit.set_position_limit_for_instrument_strategy(
            instrument_strategy, position_limit.position_limit
        )


def backup_process_controls(data):
    data.log.debug("Creating process control table...")
    create_table(data.sqlite_control_process)

    data.log.debug("Creating process methods table...")
    create_table(data.sqlite_control_process.method_data)

    data.log.debug("Backing up process control data...")
    processes = data.mongo_control_process.get_dict_of_control_processes()
    for process_name in processes:
        process_object = processes[process_name]
        data.sqlite_control_process._add_control_for_process_name(
            process_name, process_object
        )


def backup_spread_cost_data(data):
    create_table(data.sqlite_spread_cost)
    instruments = data.mongo_spread_cost.get_list_of_instruments()
    for instrument in instruments:
        spread_cost = data.mongo_spread_cost.get_spread_cost(instrument)
        data.sqlite_spread_cost.update_spread_cost(instrument, spread_cost)
    data.log.debug("Backed up spread costs")


def backup_roll_state_data(data):
    create_table(data.sqlite_roll_state)
    instrument_list = data.mongo_roll_state.get_list_of_instruments()
    for instrument_code in instrument_list:
        roll_state = data.mongo_roll_state.get_roll_state(instrument_code)
        data.sqlite_roll_state.set_roll_state(instrument_code, roll_state)
    data.log.debug("Backed up roll states")


def backup_temporary_close_data(data):
    create_table(data.sqlite_temporary_close)
    instruments = data.mongo_temporary_close.get_list_of_instruments()
    for instrument in instruments:
        position_limit = (
            data.mongo_temporary_close.get_stored_position_limit_for_instrument(
                instrument
            )
        )
        data.sqlite_temporary_close.add_stored_position_limit(position_limit)
    data.log.debug("Backed up temporary close data")


def backup_temporary_overrides(data):
    create_table(data.sqlite_temporary_override)
    instruments = data.mongo_temporary_override.mongo_data.get_list_of_keys()
    for instrument in instruments:
        override = data.mongo_temporary_override.get_stored_override_for_instrument(
            instrument
        )
        data.sqlite_temporary_override.add_stored_override(instrument, override)
    data.log.debug("Backed up temporary overrides")


def backup_trade_limits(data):
    create_table(data.sqlite_trade_limit)
    trade_limits = data.mongo_trade_limit.get_all_limits()
    for trade_limit in trade_limits:
        data.sqlite_trade_limit._update_trade_limit_object(trade_limit)
    data.log.debug("Backed up trade limits")


def create_table(sqlite_data: sqliteData):
    if sqlite_data._table_exists():
        drop = true_if_answer_is_yes("Table exists! Do you want to drop it? (y/n)")
        if drop:
            sqlite_data._drop_table()
        else:
            print("OK, exiting...")
            exit(0)
    sqlite_data._create_table()


if __name__ == "__main__":
    backup_mongo_to_sqlite()
