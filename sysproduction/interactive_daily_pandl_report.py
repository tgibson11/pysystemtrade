from sysproduction.diagnostic.reporting import run_report
from syscore.objects import report_config


def interactive_daily_pandl_report():
    pandl_report_config = report_config(title="One day P&L report",
                                        function="sysproduction.diagnostic.profits.pandl_info",
                                        output="console")

    run_report(pandl_report_config, calendar_days_back=1)


if __name__ == '__main__':
    interactive_daily_pandl_report()
