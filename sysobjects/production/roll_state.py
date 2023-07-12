from enum import Enum

RollState = Enum(
    "RollState",
    (
        "No_Roll",
        "Passive",
        "Force",
        "Force_Outright",
        "Roll_Adjusted",
        "Close",
        "No_Open",
    ),
)

list_of_all_roll_states = [state.name for state in RollState]

no_roll_state = RollState.No_Roll
roll_adj_state = RollState.Roll_Adjusted
roll_close_state = RollState.Close
no_open_state = RollState.No_Open
default_state = no_roll_state
passive_roll_state = RollState.Passive

roll_explanations = {
    RollState.No_Roll: "No rolling happens. Will only trade priced contract.",
    RollState.Passive: "Allow the contract to roll naturally (closing trades in priced contract, opening trades in forward contract)",
    RollState.Force: "Force the contract to roll ASAP using spread order",
    RollState.Force_Outright: "Force the contract to roll ASAP using two outright orders",
    RollState.Roll_Adjusted: "Roll adjusted prices from existing priced to new forward contract (after adjusted prices have been changed, will automatically move state to no roll",
    RollState.Close: "Close position in near contract only",
    RollState.No_Open: "No opening trades as close to expiry but forward not liquid enough",
}


def is_double_sided_trade_roll_state(roll_state: RollState):
    return roll_state in [RollState.Force, RollState.Force_Outright]


def is_roll_state_requiring_order_generation(roll_state: RollState) -> bool:
    return roll_state in [RollState.Force, RollState.Force_Outright, RollState.Close]


def is_type_of_active_rolling_roll_state(roll_state: RollState):
    return (
        is_roll_state_requiring_order_generation(roll_state)
        or roll_state == RollState.Roll_Adjusted
    )


def explain_roll_state_str(roll_state: RollState):
    return roll_explanations[RollState[roll_state]]


def name_of_roll_state(roll_state: RollState):
    return roll_state.name


def complete_roll_state(roll_state: RollState, priced_position):
    if priced_position == 0:
        flag_position_in_priced = 0
    else:
        flag_position_in_priced = 1

    return "%s%s" % (name_of_roll_state(roll_state), flag_position_in_priced)


def allowable_roll_state_from_current_and_position(
    current_roll_state: RollState, priced_position: int
):
    # Transition matrix: First option is recommended
    # A 0 suffix indicates we have no position in the priced contract
    # A 1 suffix indicates we do have a position in the priced contract
    allowed_transition = dict(
        No_Roll0=["Roll_Adjusted", "Passive", "No_Roll", "No_Open"],
        No_Roll1=["Passive", "Force", "Force_Outright", "No_Roll", "Close", "No_Open"],
        Passive0=["Roll_Adjusted", "Passive", "No_Roll", "No_Open"],
        Passive1=["Force", "Force_Outright", "Passive", "No_Roll", "Close", "No_Open"],
        Force0=["Roll_Adjusted", "Passive"],
        Force1=["Force", "Force_Outright", "Passive", "No_Roll", "Close", "No_Open"],
        Force_Outright0=["Roll_Adjusted", "Passive"],
        Force_Outright1=[
            "Force",
            "Force_Outright",
            "Passive",
            "No_Roll",
            "Close",
            "No_Open",
        ],
        Close0=["Roll_Adjusted", "Passive"],
        Close1=["Close", "Force", "Force_Outright", "Passive", "No_Roll", "No_Open"],
        Roll_Adjusted0=["No_Roll"],
        Roll_Adjusted1=["Roll_Adjusted"],
        No_Open0=["Roll_Adjusted", "Passive", "No_Open"],
        No_Open1=["Close", "Force", "Force_Outright", "Passive", "No_Roll"],
    )

    status_plus_position = complete_roll_state(current_roll_state, priced_position)
    try:
        allowable_states = allowed_transition[status_plus_position]
    except KeyError:
        raise Exception("State plus position %s not recognised" % status_plus_position)

    return allowable_states


ALL_ROLL_INSTRUMENTS = "ALL"
