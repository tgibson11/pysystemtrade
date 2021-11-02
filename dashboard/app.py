from flask import Flask, g, render_template, request
from werkzeug.local import LocalProxy

import sysproduction.reporting.api
from syscore.objects import missing_data
from syscore.genutils import str2Bool

from sysdata.config.control_config import get_control_config

from sysdata.data_blob import dataBlob

from sysobjects.production.roll_state import RollState


from sysproduction.data.prices import diagPrices
from sysproduction.reporting import (
    costs_report,
    liquidity_report,
    pandl_report,
    risk_report,
    roll_report,
    trades_report,
    status_reporting,
)
from sysproduction.data.broker import dataBroker
from sysproduction.data.control_process import dataControlProcess
from sysproduction.data.capital import dataCapital
from sysproduction.data.positions import diagPositions, dataOptimalPositions
from sysproduction.interactive_update_roll_status import (
    modify_roll_state,
    setup_roll_data_with_state_reporting,
)
from sysproduction.utilities.rolls import rollingAdjustedAndMultiplePrices

import syscore.dateutils


from pprint import pprint

import asyncio
import datetime
import json
import pandas as pd

app = Flask(__name__)


def get_data():
    if not hasattr(g, "data"):
        g.data = dataBlob(log_name="dashboard")
    return g.data


data = LocalProxy(get_data)


@app.teardown_appcontext
def cleanup_data(exception):
    if hasattr(g, "data"):
        g.data.close()
        del g.data


def dict_of_df_to_dict(d, orient):
    return {
        k: json.loads(v.to_json(orient=orient, date_format="iso"))
        if isinstance(v, pd.DataFrame)
        else v
        for k, v in d.items()
    }


@app.route("/")
def index():
    return render_template("index.html")


@app.route("/capital")
def capital():
    capital_data = dataCapital(data)
    capital_series = capital_data.get_series_of_all_global_capital()
    now = capital_series.iloc[-1]["Actual"]
    yesterday = capital_series.last("1D").iloc[0]["Actual"]
    return {"now": now, "yesterday": yesterday}


@app.route("/costs")
def costs():
    end = datetime.datetime.now()
    start = syscore.dateutils.n_days_ago(250)
    costs = costs_report.get_costs_report_data(data, start, end)
    df_costs = costs["combined_df_costs"].to_dict(orient="index")
    df_costs = {k: {kk: str(vv) for kk, vv in v.items()} for k, v in df_costs.items()}
    costs["combined_df_costs"] = df_costs
    costs["table_of_SR_costs"] = costs["table_of_SR_costs"].to_dict(orient="index")
    return costs


@app.route("/forex")
def forex():
    asyncio.set_event_loop(asyncio.new_event_loop())
    data_broker = dataBroker(data)
    return data_broker.broker_fx_balances()


@app.route("/liquidity")
def liquidity():
    liquidity_data = sysproduction.reporting.api.get_liquidity_report_data(data)[
        "all_liquidity_df"
    ].to_dict(orient="index")
    return liquidity_data


@app.route("/pandl")
def pandl():
    end = datetime.datetime.now()
    start = syscore.dateutils.n_days_ago(1)
    pandl_data = pandl_report.get_pandl_report_data(data, start, end)._asdict()
    pandl_data["pandl_for_instruments_across_strategies"] = pandl_data[
        "pandl_for_instruments_across_strategies"
    ].to_dict(orient="records")
    pandl_data["strategies"] = pandl_data["strategies"].to_dict(orient="records")
    pandl_data["sector_pandl"] = pandl_data["sector_pandl"].to_dict(orient="records")
    return pandl_data


@app.route("/processes")
def processes():
    status_data = status_reporting.get_status_report_data(data)
    data_control = dataControlProcess(data)
    data_control.check_if_pid_running_and_if_not_finish_all_processes()
    df = status_data["method"]
    df.set_index(["process_name"], append=True, inplace=True)
    df = df.swaplevel(0, 1)
    status_data["method"] = df
    status_data["position_limits"].set_index(["keys"], inplace=True)
    status_data = dict_of_df_to_dict(status_data, orient="index")
    allprocess = {}
    for k in status_data["process"].keys():
        allprocess[k] = {
            **status_data["process"].get(k, {}),
            **status_data["process2"].get(k, {}),
            **status_data["process3"].get(k, {}),
        }
    status_data["process"] = allprocess
    status_data.pop("process2")
    status_data.pop("process3")
    return status_data


@app.route("/reconcile")
def reconcile():
    diag_positions = diagPositions(data)
    data_optimal = dataOptimalPositions(data)
    optimal_positions = data_optimal.get_pd_of_position_breaks().to_dict()
    strategies = {}
    for instrument in optimal_positions["breaks"].keys():
        strategies[instrument] = {
            "break": optimal_positions["breaks"][instrument],
            "optimal": str(optimal_positions["optimal"][instrument]),
            "current": optimal_positions["current"][instrument],
        }

    positions = {}

    db_breaks = (
        diag_positions.get_list_of_breaks_between_contract_and_strategy_positions()
    )
    ib_breaks = []
    gateway_ok = True
    try:
        asyncio.set_event_loop(asyncio.new_event_loop())
        data_broker = dataBroker(data)
        db_contract_pos = (
            data_broker.get_db_contract_positions_with_IB_expiries()
            .as_pd_df()
            .to_dict()
        )
        for idx in db_contract_pos["instrument_code"].keys():
            code = db_contract_pos["instrument_code"][idx]
            contract_date = db_contract_pos["contract_date"][idx]
            position = db_contract_pos["position"][idx]
            positions[code + "-" + contract_date] = {
                "code": code,
                "contract_date": contract_date,
                "db_position": position,
            }
        ib_contract_pos = (
            data_broker.get_all_current_contract_positions().as_pd_df().to_dict()
        )
        for idx in ib_contract_pos["instrument_code"].keys():
            code = ib_contract_pos["instrument_code"][idx]
            contract_date = ib_contract_pos["contract_date"][idx]
            position = ib_contract_pos["position"][idx]
            positions[code + "-" + contract_date]["ib_position"] = position
        ib_breaks = (
            data_broker.get_list_of_breaks_between_broker_and_db_contract_positions()
        )
    except:
        # IB gateway connection failed
        gateway_ok = False
    return {
        "strategy": strategies,
        "positions": positions,
        "db_breaks": db_breaks,
        "ib_breaks": ib_breaks,
        "gateway_ok": gateway_ok,
    }


@app.route("/rolls")
def rolls():
    diag_prices = diagPrices(data)

    all_instruments = diag_prices.get_list_of_instruments_in_multiple_prices()
    report = {}
    for instrument in all_instruments:
        report[instrument] = roll_report.get_roll_data_for_instrument_DEPRECATED(instrument, data)
        roll_data = setup_roll_data_with_state_reporting(data, instrument)
        report[instrument]["allowable"] = roll_data.allowable_roll_states_as_list_of_str

    return report


@app.route("/rolls", methods=["POST"])
def rolls_post():
    instrument = request.form["instrument"]
    new_state = RollState[request.form["state"]]

    if new_state == RollState.Roll_Adjusted and request.form["confirmed"] != "true":
        # Send back the adjusted prices for checking
        number_to_return = 6
        try:
            rolling = rollingAdjustedAndMultiplePrices(data, instrument)
            current_multiple = {
                str(k): v
                for k, v in rolling.current_multiple_prices.tail(number_to_return)
                .to_dict(orient="index")
                .items()
            }
            # We need to convert values to strings because there are
            # sometimes NaNs which are not valid json
            new_multiple = {
                str(k): {kk: str(vv) for kk, vv in v.items()}
                for k, v in rolling.updated_multiple_prices.tail(number_to_return + 1)
                .to_dict(orient="index")
                .items()
            }
            current_adjusted = {
                str(k): round(v, 2)
                for k, v in rolling.current_adjusted_prices.tail(number_to_return)
                .to_dict()
                .items()
            }
            new_adjusted = {
                str(k): round(v, 2)
                for k, v in rolling.new_adjusted_prices.tail(number_to_return + 1)
                .to_dict()
                .items()
            }
            single = {
                k: {"current": current_adjusted[k], "new": new_adjusted[k]}
                for k in current_adjusted.keys()
            }
            multiple = {
                k: {"current": current_multiple[k], "new": new_multiple[k]}
                for k in current_adjusted.keys()
            }
            new_date = list(new_adjusted.keys())[-1]
            single[new_date] = {"new": new_adjusted[new_date]}
            multiple[new_date] = {"new": new_multiple[new_date]}
            prices = {"single": single, "multiple": multiple}
            return prices
        except:
            # Cannot roll for some reason
            return {}

    roll_data = setup_roll_data_with_state_reporting(data, instrument)
    modify_roll_state(
        data, instrument, roll_data.original_roll_status, new_state, False
    )
    roll_data = setup_roll_data_with_state_reporting(data, instrument)
    return {
        "new_state": request.form["state"],
        "allowable": roll_data.allowable_roll_states_as_list_of_str,
    }


@app.route("/risk")
def risk():
    risk_data = risk_report.calculate_risk_report_data(data)
    risk_data["corr_data"] = risk_data["corr_data"].as_pd()
    risk_data = dict_of_df_to_dict(risk_data, "index")
    return risk_data


@app.route("/trades")
def trades():
    end = datetime.datetime.now()
    start = syscore.dateutils.n_days_ago(1)
    return_data = {}
    trades_data = dict_of_df_to_dict(
        trades_report.get_trades_report_data(data, start, end), "index"
    )
    return_data["overview"] = {
        k: {kk: str(vv) for kk, vv in v.items()}
        for k, v in trades_data["overview"].items()
    }
    return_data["delays"] = {
        k: {kk: str(vv) for kk, vv in v.items()}
        for k, v in trades_data["delays"].items()
    }
    return_data["raw_slippage"] = {
        k: {kk: str(vv) for kk, vv in v.items()}
        for k, v in trades_data["raw_slippage"].items()
    }
    return_data["vol_slippage"] = {
        k: {kk: str(vv) for kk, vv in v.items()}
        for k, v in trades_data["vol_slippage"].items()
    }
    return_data["cash_slippage"] = {
        k: {kk: str(vv) for kk, vv in v.items()}
        for k, v in trades_data["cash_slippage"].items()
    }

    return return_data


@app.route("/strategy")
def strategy():
    return {}


def visible_on_lan() -> bool:
    config = get_control_config()
    visible = config.get_element_or_missing_data("dashboard_visible_on_lan")
    if visible is missing_data:
        return False

    visible = str2Bool(visible)

    return visible


if __name__ == "__main__":
    visible = visible_on_lan()
    if visible:
        data = dataBlob()
        data.log.warn(
            "Starting dashboard with web page visible to all - security implications!!!!"
        )
        app.run(
            threaded=True,
            use_debugger=False,
            use_reloader=False,
            passthrough_errors=True,
            host="0.0.0.0",
        )

    else:
        app.run(
            threaded=True,
            use_debugger=False,
            use_reloader=False,
            passthrough_errors=True,
        )
