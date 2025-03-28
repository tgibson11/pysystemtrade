from syscontrol.run_process import processToRun
from sysexecution.stack_handler.stack_handler import stackHandler
from sysdata.data_blob import dataBlob


def run_stack_handler():
    process_name = "run_stack_handler"
    data = dataBlob(log_name=process_name)
    list_of_timer_names_and_functions = get_list_of_timer_functions_for_stack_handler()
    finished_function = get_finished_function()
    price_process = processToRun(
        process_name,
        data,
        list_of_timer_names_and_functions,
        finished_function,
    )
    price_process.run_process()


def get_list_of_timer_functions_for_stack_handler():
    stack_handler_data = dataBlob(log_name="stack_handler")
    stack_handler = stackHandler(stack_handler_data)
    list_of_timer_names_and_functions = [
        ("check_external_position_break", stack_handler),
        ("spawn_children_from_new_instrument_orders", stack_handler),
        ("generate_force_roll_orders", stack_handler),
        ("create_broker_orders_from_contract_orders", stack_handler),
        ("process_fills_stack", stack_handler),
        ("handle_completed_orders", stack_handler),
        ("safe_stack_removal", stack_handler),
        ("refresh_additional_sampling_all_instruments", stack_handler),
    ]

    return list_of_timer_names_and_functions

def get_finished_function():
    stack_handler_data = dataBlob(log_name="stack_handler")
    stack_handler = stackHandler(stack_handler_data)
    return stack_handler.all_stacks_empty

if __name__ == "__main__":
    run_stack_handler()
