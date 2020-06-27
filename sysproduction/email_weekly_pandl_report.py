from sysproduction.diagnostic.report_configs import daily_pandl_report_config
from sysproduction.diagnostic.reporting import run_report


def email_weekly_pandl_report():

    config = daily_pandl_report_config.new_config_with_modified_output("email")
    config.modify_kwargs(title="Weekly P&L report", calendar_days_back=7)
    run_report(config)

