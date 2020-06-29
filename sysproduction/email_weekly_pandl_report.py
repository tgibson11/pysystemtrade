from sysproduction.diagnostic.report_configs import weekly_pandl_report_config
from sysproduction.diagnostic.reporting import run_report


def email_weekly_pandl_report():

    config = weekly_pandl_report_config.new_config_with_modified_output("email")
    run_report(config)


if __name__ == '__main__':
    email_weekly_pandl_report()
