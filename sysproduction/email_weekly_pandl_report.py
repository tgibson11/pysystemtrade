from sysproduction.diagnostic.reporting import run_report
from syscore.objects import report_config


def email_weekly_pandl_report():

    pandl_report_config = report_config(title="Weekly P&L report",
                                        function="sysproduction.diagnostic.profits.pandl_info",
                                        output="email")

    run_report(pandl_report_config, calendar_days_back=7)
