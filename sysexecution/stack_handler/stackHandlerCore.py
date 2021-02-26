"""
Stack handler is a giant object, so we split it up into files/classes

This 'core' is inherited by all the other classes and just initialises, plus does some common functions

"""
from collections import namedtuple
from syscore.objects import (
    arg_not_supplied,
    failure,
    success)

from sysdata.data_blob import dataBlob

from sysexecution.order_stacks.order_stack import orderStackData, failureWithRollback
from sysexecution.orders.base_orders import Order
from sysexecution.orders.list_of_orders import listOfOrders

from sysproduction.data.orders import dataOrders

class stackHandlerCore(object):
    def __init__(self, data: dataBlob=arg_not_supplied):
        if data is arg_not_supplied:
            data = dataBlob()

        self._data = data
        self._log = data.log

        order_data = dataOrders(data)

        instrument_stack = order_data.db_instrument_stack_data
        contract_stack = order_data.db_contract_stack_data
        broker_stack = order_data.db_broker_stack_data

        self._instrument_stack = instrument_stack
        self._contract_stack = contract_stack
        self._broker_stack = broker_stack


    @property
    def data(self):
        return self._data

    @property
    def log(self):
        return self._log

    @property
    def instrument_stack(self):
        return self._instrument_stack

    @property
    def contract_stack(self):
        return self._contract_stack

    @property
    def broker_stack(self):
        return self._broker_stack


def put_children_on_stack(child_stack: orderStackData, parent_order: Order,
                          list_of_child_orders: listOfOrders,
                          parent_log) -> list:

    try:
        list_of_child_ids = child_stack.put_list_of_orders_on_stack(
            list_of_child_orders
        )
    except failureWithRollback as e:
        parent_log.warn("Tried to add child orders but %s; rolled back so can try again (parent %s)" %
                        (str(e), str(parent_order)))
        return []

    except Exception as e:
        parent_log.critical(
            "Tried to add child orders, error %s and couldn't roll back! Order stack may well be corrupted!" % str(
                e))
        return []

    return list_of_child_ids

def add_children_to_parent_or_rollback_children(parent_order: Order,
                                                list_of_child_ids: list,
                                                parent_stack: orderStackData,
                                                child_stack: orderStackData,
                                                parent_log):
    try:
        parent_stack.add_children_to_order_without_existing_children(
            parent_order.order_id, list_of_child_ids
        )
    except Exception as e:
        try:
            child_stack.rollback_list_of_orders_on_stack(list_of_child_ids)
            parent_log.warn("Tried to add child orders to parent but %s; rolled back so can try again (parent %s)" %
                          (str(e), str(parent_order)))
            return failure
        except:
            parent_log.critical(
                "Tried to add child orders, error %s and couldn't roll back! Order stack may well be corrupted!" % str(
                    e))
            return failure

    return success

def log_successful_adding(list_of_child_orders: listOfOrders,
                          list_of_child_ids: list,
                          parent_order: Order,
                          parent_log):

    for child_order, child_id in zip(
            list_of_child_orders, list_of_child_ids):
        child_log = child_order.log_with_attributes(parent_log)
        child_log.msg(
            "Put child order %s on stack with ID %d from parent order %s"
            % (str(child_order), child_id, str(parent_order))
        )

def rollback_parents_and_children_and_handle_exceptions(parent_stack: orderStackData,
             child_stack: orderStackData,
             parent_order_id: int,
             list_of_child_order_ids: list,
            parent_log,
            error_from_adding_child_orders: Exception):

    ##
    try:
        rollback_parents_and_children(child_stack=child_stack,
                                      parent_stack=parent_stack,
                                      list_of_child_order_ids=list_of_child_order_ids,
                                      parent_order_id=parent_order_id)
        parent_log.warn("Error %s when adding a set of parents and children but managed to rollback" % str(
            error_from_adding_child_orders))
        return None

    except Exception as rollback_exception:
        ## bloody hell even the rollback has failed, throw everything out of the pram
        parent_log.critical(
            "Error %s when adding a set of parents and children and couldn't rollback got error %s! Stack may be corrupted" %
            (str(error_from_adding_child_orders), str(rollback_exception)))
        return None


def rollback_parents_and_children(parent_stack: orderStackData,
             child_stack: orderStackData,
             parent_order_id: int,
             list_of_child_order_ids: list):


    ## parent order might be locked
    parent_stack.unlock_order_on_stack(parent_order_id)
    parent_stack.deactivate_order(parent_order_id)
    parent_stack.remove_order_with_id_from_stack(parent_order_id)

    # If any children, roll them back also
    if len(list_of_child_order_ids) > 0:
        child_stack.rollback_list_of_orders_on_stack(
            list_of_child_order_ids)



orderFamily = namedtuple('orderFamily', ['instrument_order_id',
                                         'list_of_contract_order_id',
                                        'list_of_broker_order_id'])