## Console roll data report
## We also have a report function to email

from sysproduction.diagnostic.reporting import run_report
from sysproduction.diagnostic.report_configs import roll_report_config


def interactive_roll_info(instrument_code: str = "ALL"):
    """

    Print information about whether futures contracts should be rolled

    :param instrument_code: The instrument code, for example 'AUD', 'CRUDE_W'. Specify ALL for everything
    :return: None, but print results
    """

    config = roll_report_config.new_config_with_modified_output("console")
    config.modify_kwargs(instrument_code = instrument_code)
    run_report(roll_report_config)


if __name__ == '__main__':
    interactive_roll_info()
