from syscore.objects import body_text, ALL_ROLL_INSTRUMENTS

# We want a roll report (We could merge this into another kind of report)
# We want to be able to have it emailed, or run it offline
# To have it emailed, we'll call the report function and optionally pass the output to a text file not stdout
# Reports consist of multiple calls to functions with data object, each of which returns a displayable object
# We also chuck in a title and a timestamp
from sysproduction.reporting.api import reportingApi


def roll_info(data, instrument_code=ALL_ROLL_INSTRUMENTS):
    """
    Get some roll info. For all markets which are:

    - currently rolling
    - need to have roll status changed now or in the near future

    We calculate:
    - Volume data
    - Curve data
    - Length to expiry data (contract and/or carry)
    - Current roll status
    - Suggested roll status

    :param: data blob
    :return: list of pd.DataFrame
    """
    reporting_api = reportingApi(data)

    formatted_output = []

    formatted_output.append(reporting_api.terse_header("Roll report"))
    formatted_output.append(reporting_api.table_of_roll_data(instrument_code))
    formatted_output.append(
        body_text(
            "Roll_exp is days until preferred roll set by roll parameters. Prc_exp is days until price contract expires, "
            "Crry_exp is days until carry contract expires"
        )
    )
    formatted_output.append(body_text("Contract suffix: p=price, f=forward, c=carry"))
    formatted_output.append(
        body_text(
            "Contract volumes over recent days, normalised so largest volume is 1.0"
        )
    )

    formatted_output.append(reporting_api.footer())

    return formatted_output
