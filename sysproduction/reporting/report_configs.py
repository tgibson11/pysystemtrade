from copy import copy

from sysproduction.reporting.data.rolls import ALL_ROLL_INSTRUMENTS


class reportConfig(object):
    def __init__(self, title, function, output="console", **kwargs):
        assert output in ["console", "email", "file"]
        self.title = title
        self.function = function
        self.output = output
        self.kwargs = kwargs

    def __repr__(self):
        return "%s %s %s %s" % (
            self.title,
            self.function,
            self.output,
            str(self.kwargs),
        )

    def new_config_with_modified_output(self, output):
        new_config = copy(self)
        new_config.output = output

        return new_config

    def new_config_with_modify_kwargs(self, **kwargs):
        new_config = copy(self)
        new_config.modify_kwargs(**kwargs)

        return new_config

    def modify_kwargs(self, **kwargs):
        for key in kwargs.keys():
            self.kwargs[key] = kwargs[key]

        return self


status_report_config = reportConfig(
    title="Status report",
    function="sysproduction.reporting.status_reporting.system_status",
)

roll_report_config = reportConfig(
    title="Roll report",
    function="sysproduction.reporting.roll_report.roll_info",
    instrument_code=ALL_ROLL_INSTRUMENTS,
)

daily_pandl_report_config = reportConfig(
    title="P&L report",
    function="sysproduction.reporting.pandl_report.pandl_info",
    calendar_days_back=1,
)

reconcile_report_config = reportConfig(
    title="Reconcile report",
    function="sysproduction.reporting.reconcile_report.reconcile_info",
)

trade_report_config = reportConfig(
    title="Trade report",
    function="sysproduction.reporting.trades_report.trades_info",
    calendar_days_back=1,
)

strategy_report_config = reportConfig(
    title="Strategy report",
    function="sysproduction.reporting.strategies_report.strategy_report",
)

risk_report_config = reportConfig(
    title="Risk report", function="sysproduction.reporting.risk_report.risk_report"
)

liquidity_report_config = reportConfig(
    title="Liquidity report",
    function="sysproduction.reporting.liquidity_report.liquidity_report",
)

costs_report_config = reportConfig(
    title="Costs report",
    function="sysproduction.reporting.costs_report.costs_report",
    calendar_days_back=250,
)

## The reports will be run in this order
all_configs = dict(
    roll_report=roll_report_config,
    daily_pandl_report=daily_pandl_report_config,
    reconcile_report=reconcile_report_config,
    trade_report=trade_report_config,
    strategy_report=strategy_report_config,
    risk_report=risk_report_config,
    status_report=status_report_config,
    liquidity_report=liquidity_report_config,
    costs_report=costs_report_config,
)
