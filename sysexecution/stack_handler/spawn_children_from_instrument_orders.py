from collections import namedtuple
import numpy as np


from syscore.genutils import sign
from syscore.objects import (
    missing_order,

    success,
    missing_data)

from sysdata.data_blob import dataBlob

from sysobjects.contracts import futuresContract

from sysproduction.data.contracts import dataContracts
from sysproduction.data.positions import diagPositions
from sysproduction.data.prices import diagPrices
from sysproduction.data.controls import dataLocks

from sysexecution.order_stacks.order_stack import orderStackData
from sysexecution.orders.base_orders import Order
from sysexecution.orders.contract_orders import contractOrder, contractOrderType

from sysexecution.orders.list_of_orders import listOfOrders
from sysexecution.orders.instrument_orders import instrumentOrder, instrumentOrderType



from sysexecution.algos.allocate_algo_to_order import (
    allocate_algo_to_list_of_contract_orders,
)
from sysexecution.stack_handler.stackHandlerCore import stackHandlerCore, put_children_on_stack, add_children_to_parent_or_rollback_children, log_successful_adding

class stackHandlerForSpawning(stackHandlerCore):
    def spawn_children_from_new_instrument_orders(self):
        new_order_ids = self.instrument_stack.list_of_new_orders()
        for instrument_order_id in new_order_ids:
            self.spawn_children_from_instrument_order_id(instrument_order_id)

    def spawn_children_from_instrument_order_id(self, instrument_order_id: int):

        instrument_order = self.instrument_stack.get_order_with_id_from_stack(
            instrument_order_id
        )
        if instrument_order is missing_order:
            return None

        data_locks = dataLocks(self.data)
        instrument_locked = data_locks.is_instrument_locked(
            instrument_order.instrument_code
        )
        if instrument_locked:
            #log.msg("Instrument is locked, not spawning order")
            return None

        list_of_contract_orders = spawn_children_from_instrument_order(
            self.data, instrument_order
        )

        log = instrument_order.log_with_attributes(self.log)
        log.msg(
            "List of contract orders spawned %s" %
            str(list_of_contract_orders))

        self.add_children_to_stack_and_child_id_to_parent(
            self.instrument_stack,
            self.contract_stack,
            instrument_order,
            list_of_contract_orders,
        )


    def add_children_to_stack_and_child_id_to_parent(
        self, parent_stack: orderStackData,
            child_stack: orderStackData,
            parent_order: Order,
            list_of_child_orders: listOfOrders
    ):

        parent_log = parent_order.log_with_attributes(self.log)

        list_of_child_ids = put_children_on_stack(child_stack=child_stack,
                                                  list_of_child_orders=list_of_child_orders,
                                                  parent_log=parent_log,
                                                  parent_order=parent_order)
        if len(list_of_child_ids)==0:
            return None

        success_or_failure = add_children_to_parent_or_rollback_children(child_stack=child_stack,
                                                                         parent_order=parent_order,
                                                                         parent_log=parent_log,
                                                                         parent_stack=parent_stack,
                                                                         list_of_child_ids=list_of_child_ids)

        if success_or_failure is success:
            log_successful_adding(list_of_child_orders=list_of_child_orders,
                                  list_of_child_ids=list_of_child_ids,
                                  parent_order=parent_order,
                                  parent_log=parent_log)




def spawn_children_from_instrument_order(data: dataBlob,
                                         instrument_order: instrumentOrder):

    spawn_function = function_to_process_instrument(
        instrument_order.instrument_code)
    list_of_contract_orders = spawn_function(data, instrument_order)
    list_of_contract_orders = allocate_algo_to_list_of_contract_orders(
        data, list_of_contract_orders, instrument_order
    )

    return list_of_contract_orders


def function_to_process_instrument(instrument_code: str) -> 'function':
    """
    FIX ME in future this will handle spread orders, but for now is only for 'single instruments'

    We can get spread trades from rolls but these are not processed here

    :param instrument_code:
    :return: function
    """
    function_dict = dict(
        single_instrument=single_instrument_child_orders,
        inter_market=inter_market_instrument_child_orders,
        intra_market=intra_market_instrument_child_orders,
    )
    instrument_type = "single_instrument"

    required_function = function_dict[instrument_type]

    return required_function


def single_instrument_child_orders(data: dataBlob,
                                   instrument_order: instrumentOrder) -> listOfOrders:
    """
    Generate child orders for a single instrument (not rolls)

    :param data: dataBlob. Required as uses roll data to determine appropriate instrument
    :param instrument_order:
    :return: A list of contractOrders to submit to the stack
    """
    # We don't allow zero trades to be spawned
    # Zero trades can enter the instrument stack, where they can potentially
    # modify existing trades
    if instrument_order.is_zero_trade():
        return listOfOrders([])

    # Get required contract(s) depending on roll status
    list_of_child_contract_dates_and_trades = (
        get_required_contract_trade_for_instrument(data, instrument_order)
    )

    list_of_contract_orders = list_of_contract_orders_from_list_of_child_date_and_trade(
        instrument_order, list_of_child_contract_dates_and_trades)

    # Get reference price for relevant contract(s)
    # used for TCA
    # Adjust price if reference contract is different from required contract
    list_of_contract_orders = calculate_reference_prices_for_direct_child_orders(
        data, instrument_order, list_of_contract_orders)

    # Now get the limit prices, where relevant
    # Adjust limit price if limit_contract is different from required contract
    list_of_contract_orders = calculate_limit_prices_for_direct_child_orders(
        data, instrument_order, list_of_contract_orders
    )

    return list_of_contract_orders

contractIdAndTrade = namedtuple("contractIDAndTrade", ["contract_id", "trade"])

def get_required_contract_trade_for_instrument(data: dataBlob,
                                               instrument_order: instrumentOrder) -> list:
    """
    Return the contract to trade for a given instrument

    Depends on roll status and trade vs position:
     - roll_states = ['No_Roll', 'Passive', 'Force', 'Force_Outright', 'Roll_Adjusted']

    If 'No Roll' then trade current contract
    If 'Passive', and no position in current contract: trade next contract
    If 'Passive', and reducing trade which leaves zero or something in current contract: trade current contract
    If 'Passive', and reducing trade which is larger than current contract position: trade current and next contract
    If 'Passive', and increasing trade: trade next contract
    If 'Force' or 'Force Outright' or 'Roll_Adjusted': don't trade

    :param instrument_order:
    :param data: dataBlog
    :return: tuple: list of child orders: each is a tuple: contract str or missing_contract, trade int
    """
    instrument_code = instrument_order.instrument_code
    log = instrument_order.log_with_attributes(data.log)
    trade = instrument_order.as_single_trade_qty_or_error()
    if trade is missing_order:
        log.critical("Instrument order can't be a spread order")
        return []

    diag_positions = diagPositions(data)

    if diag_positions.is_roll_state_no_roll(instrument_code):
        diag_contracts = dataContracts(data)
        current_contract = diag_contracts.get_priced_contract_id(instrument_code)

        log.msg(
            "No roll, allocating entire order %s to current contract %s"
            % (str(instrument_order), current_contract)
        )
        return [contractIdAndTrade(current_contract, trade)]

    elif diag_positions.is_roll_state_passive(instrument_code):
        # no log as function does it
        list_of_child_contract_dates_and_trades = passive_roll_child_order(data=data,
                                                                  instrument_order = instrument_order,
                                                                  trade = trade
                                                                    )

        return list_of_child_contract_dates_and_trades

    elif diag_positions.is_type_of_active_rolling_roll_state(instrument_code):
        log.msg(
            "Roll state is active rolling, not going to generate trade for order %s" %
            (str(instrument_order)))
        return []

    else:
        log.critical(
            "Roll state %s not understood: can't generate trade for %s"
            % (diag_positions.get_name_of_roll_state(instrument_code), str(instrument_order))
        )
        return []


def passive_roll_child_order(
    data: dataBlob,
    trade: int,
    instrument_order: instrumentOrder,
    ) -> list:

    log = instrument_order.log_with_attributes(data.log)
    diag_positions = diagPositions(data)
    instrument_code = instrument_order.instrument_code

    diag_contracts = dataContracts(data)
    current_contract = diag_contracts.get_priced_contract_id(instrument_code)
    next_contract = diag_contracts.get_forward_contract_id(instrument_code)

    contract = futuresContract(instrument_code, current_contract)

    position_current_contract = (
        diag_positions.get_position_for_contract(contract)
    )

    # Break out because so darn complicated
    if position_current_contract == 0:
        # Passive roll and no position in the current contract, start trading
        # the next contract
        log.msg(
            "Passive roll handling order %s, no position in current contract, entire trade in next contract %s" %
            (str(instrument_order), next_contract))
        return [contractIdAndTrade(next_contract, trade)]

    # ok still have a position in the current contract
    increasing_trade = sign(trade) == sign(position_current_contract)
    if increasing_trade:
        # Passive roll and increasing trade
        # Do it all in next contract
        log.msg(
            "Passive roll handling order %s, increasing trade, entire trade in next contract %s" %
            (str(instrument_order), next_contract))
        return [contractIdAndTrade(next_contract, trade)]

    # ok a reducing trade
    new_position = position_current_contract + trade
    sign_of_position_is_unchanged = sign(position_current_contract) == sign(
        new_position
    )
    if new_position == 0 or sign_of_position_is_unchanged:
        # A reducing trade that we can do entirely in the current contract
        log.msg(
            "Passive roll handling order %s, reducing trade, entire trade in next contract %s" %
            (str(instrument_order), next_contract))
        return [contractIdAndTrade(current_contract, trade)]


    # OKAY to recap: it's a passive roll, but the trade will be split between
    # current and next
    list_of_child_contract_dates_and_trades = \
        passive_trade_split_over_two_contracts(trade=trade,
                                               current_contract=current_contract,
                                               next_contract=next_contract,
                                               position_current_contract=position_current_contract)
    log.msg(
        "Passive roll handling order %s, reducing trade, split trade between contract %s and %s" %
        (str(instrument_order), current_contract, next_contract))

    return list_of_child_contract_dates_and_trades

def passive_trade_split_over_two_contracts(trade: int,
                        position_current_contract: int,
                        current_contract: str,
                        next_contract: str) -> list:
    """
    >>> passive_trade_split_over_two_contracts(5, -2, "a", "b")
    [contractIDAndTrade(contract_id='a', trade=2), contractIDAndTrade(contract_id='b', trade=3)]
    >>> passive_trade_split_over_two_contracts(-5, 2, "a", "b")
    [contractIDAndTrade(contract_id='a', trade=-2), contractIDAndTrade(contract_id='b', trade=-3)]

    :param trade: int
    :param position_current_contract: int
    :param current_contract: str
    :param next_contract: str
    :return: list
    """

    trade_in_current_contract = -position_current_contract
    trade_in_next_contract = trade - trade_in_current_contract

    return [
        contractIdAndTrade(current_contract, trade_in_current_contract),
        contractIdAndTrade(next_contract, trade_in_next_contract),
    ]


def list_of_contract_orders_from_list_of_child_date_and_trade(
    instrument_order: instrumentOrder, list_of_child_contract_dates_and_trades: list
) -> listOfOrders:

    list_of_contract_orders = [
        contract_order_for_direct_instrument_child_date_and_trade(
            instrument_order, child_date_and_trade
        )
        for child_date_and_trade in list_of_child_contract_dates_and_trades
    ]

    list_of_contract_orders = listOfOrders(list_of_contract_orders)

    return list_of_contract_orders


def contract_order_for_direct_instrument_child_date_and_trade(
    instrument_order: instrumentOrder,
        child_date_and_trade: contractIdAndTrade
) -> contractOrder:
    """
    Gets a child contract order from a parent instrument order where the instrument is 'direct'
       eg the instrument name is the same as the instrument traded
       (This will not be the case for inter market orders)

    :param instrument_order: original parent order
    :param child_date_and_trade:
    :return: contractOrder. Fields reference_price, algo_to_use, limit_price will be set later
    """

    child_contract, child_trade = child_date_and_trade
    parent_id = instrument_order.order_id
    strategy = instrument_order.strategy_name
    instrument = instrument_order.instrument_code
    order_type = map_instrument_order_type_to_contract_order_type(instrument_order.order_type)

    # parent, limit and reference information will be added later
    child_contract_order = contractOrder(
        strategy,
        instrument,
        child_contract,
        child_trade,
        order_type = order_type,
        parent=parent_id,
    )

    return child_contract_order


def map_instrument_order_type_to_contract_order_type(instrument_order_type: instrumentOrderType) \
        -> contractOrderType:
    # will only work for matching order types eg best, limit, market, panic
    type_string = instrument_order_type.as_string()
    contract_order_type = contractOrderType(type_string)

    return contract_order_type


def intra_market_instrument_child_orders(data, instrument_order):
    """
    Generate child orders for intra-market instrument (not rolls)

    :param data: dataBlob. Required as uses roll data to determine appropriate instrument
    :param instrument_order:
    :return: A list of contractOrders to submit to the stack
    """

    # Get required contracts depending on roll status

    # Get reference price for relevant contract spread

    # Adjust limit price if limit_contracts is different from required
    # contracts

    raise NotImplementedError


def inter_market_instrument_child_orders(data, instrument_order):
    """
    Generate child orders for inter market instrument (not rolls)

    :param data: dataBlob. Required as uses roll data to determine appropriate instrument
    :param instrument_order:
    :return: A list of contractOrders to submit to the stack
    """

    # Get required contracts depending on roll status

    # Get reference price for relevant contract spread

    # Adjust limit price if limit_contracts is different from required
    # contracts

    raise NotImplementedError


def calculate_reference_prices_for_direct_child_orders(
    data: dataBlob,
        instrument_order: instrumentOrder,
        list_of_contract_orders: listOfOrders
) -> listOfOrders:
    """
    A direct child order only contains one contract id i.e. not an intramarket spread

    :param data:
    :param instrument_order:
    :param list_of_contract_orders:
    :return:
    """
    list_of_contract_orders = [
        add_reference_price_to_a_direct_child_order(data, instrument_order, child_order)
        for child_order in list_of_contract_orders
    ]

    list_of_contract_orders = listOfOrders(list_of_contract_orders)

    return list_of_contract_orders


def add_reference_price_to_a_direct_child_order(
        data: dataBlob,
        instrument_order: instrumentOrder,
        child_order: contractOrder):
    """

    :param data: dataBlob
    :param instrument_order:
    :param child_order: will be modified
    :return: child order
    """

    contract_to_match = instrument_order.reference_contract
    price_to_adjust = instrument_order.reference_price

    if contract_to_match is None or price_to_adjust is None:
        # No reference price so don't bother
        return child_order

    new_reference_price = calculate_adjusted_price_for_a_direct_child_order(
        data, child_order, contract_to_match, price_to_adjust
    )

    if new_reference_price is missing_data:
        log = instrument_order.log_with_attributes(data.log)
        log.warn(
            "Couldn't adjust reference price for order %s child %s going from %s to %s, can't do TCA" %
            (str(instrument_order),
             str(child_order),
                contract_to_match,
                child_order.contract_date,
             ))
        return child_order

    child_order.reference_price = new_reference_price

    return child_order


def calculate_adjusted_price_for_a_direct_child_order(
    data: dataBlob,
        child_order: contractOrder,
        original_contract_date: str,
        original_price: float
) -> float:
    """

    :param data:
    :param child_order:
    :param original_contract_date:
    :param original_price:
    :return: float or missing data
    """
    instrument_code = child_order.instrument_code
    try:
        assert not child_order.calendar_spread_order
    except BaseException:
        raise Exception(
            "You have tried to adjust the price for a spread contract order assuming it is a single leg order"
        )

    child_contract_date = child_order.contract_date_key

    if original_contract_date == child_contract_date:
        return original_price

    diag_prices = diagPrices(data)
    contract_list = [original_contract_date, child_contract_date]
    _last_matched_date, list_of_matching_prices = diag_prices.get_last_matched_date_and_prices_for_contract_list(
        instrument_code, contract_list
    )
    differential = list_of_matching_prices[1] - list_of_matching_prices[0]

    if np.isnan(differential):
        # can't adjust
        # note need to test code there may be other ways in which this fails
        return missing_data

    adjusted_price = original_price + differential

    return adjusted_price


def calculate_limit_prices_for_direct_child_orders(
    data: dataBlob,
        instrument_order: instrumentOrder,
        list_of_contract_orders: listOfOrders
) -> listOfOrders:
    """
    A direct child order only contains one contract id i.e. not an intramarket spread

    :param data:
    :param instrument_order:
    :param list_of_contract_orders:
    :return: list of contract orders
    """
    list_of_contract_orders = [
        add_limit_price_to_a_direct_child_order(data, instrument_order, child_order)
        for child_order in list_of_contract_orders
    ]

    flag_missing_orders = [
        child_order is missing_order for child_order in list_of_contract_orders
    ]
    if any(flag_missing_orders):
        log = instrument_order.log_with_attributes(data.log)
        log.critical(
            "Couldn't adjust limit price for at least one child order %s: can't execute any child orders" %
            str(instrument_order)
        )
        return listOfOrders([])

    list_of_contract_orders = listOfOrders(list_of_contract_orders)

    return list_of_contract_orders


def add_limit_price_to_a_direct_child_order(
        data: dataBlob,
        instrument_order: instrumentOrder,
        child_order: contractOrder) -> contractOrder:
    """

    :param data: dataBlob
    :param instrument_order:
    :param child_order: will be modified
    :return: float
    """

    contract_to_match = instrument_order.limit_contract
    price_to_adjust = instrument_order.limit_price

    if contract_to_match is None or price_to_adjust is None:
        # No limit price so don't bother
        return child_order

    new_limit_price = calculate_adjusted_price_for_a_direct_child_order(
        data,  child_order, contract_to_match, price_to_adjust
    )
    if new_limit_price is missing_data:
        # This is a serious problem
        # We can't possibly execute any part of the parent order
        log = instrument_order.log_with_attributes(data.log)
        log.critical(
            "Couldn't adjust limit price for order %s child %s going from %s to %s" %
            (str(instrument_order),
             str(child_order),
                contract_to_match,
                child_order.contract_date,
             )
        )
        return missing_order

    child_order.limit_price = new_limit_price

    return child_order
