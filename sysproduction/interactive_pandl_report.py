from sysproduction.diagnostic.report_configs import daily_pandl_report_config
from sysproduction.diagnostic.reporting import run_report


def interactive_daily_pandl_report(calendar_days_back):
    config = daily_pandl_report_config.new_config_with_modified_output("console")
    config.modify_kwargs(title="P&L report", calendar_days_back=calendar_days_back)
    run_report(config)


if __name__ == '__main__':
    interactive_daily_pandl_report(int(input("Calendar days for P&L:")))
