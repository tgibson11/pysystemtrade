import io
import time
import urllib.parse

import pandas as pd
import requests

from syscore.dateutils import Frequency
from syscore.objects import missing_data
from sysdata.barchart.bc_instruments_data import BarchartFuturesInstrumentData
from syslogdiag.log_to_screen import logger, logtoscreen
from sysobjects.contracts import futuresContract

BARCHART_URL = "https://www.barchart.com/"

freq_mapping = {
    Frequency.Hour: "60",
    Frequency.Minutes_15: "15",
    Frequency.Minutes_5: "5",
    Frequency.Minute: "1",
}


class BcConnection(object):

    """
    Handles connection and config for getting info from Barchart.com
    """

    def __init__(self, log=logtoscreen("BcConnection", log_level="on")):

        log.label(broker="Barchart")

        # start HTTP session
        self._session = requests.Session()
        self._session.headers.update({"User-Agent": "Mozilla/5.0"})
        self._log = log

    def __repr__(self):
        return f"Barchart connection: {BARCHART_URL}"

    @property
    def log(self):
        return self._log

    @property
    def barchart_futures_instrument_data(self) -> BarchartFuturesInstrumentData:
        return BarchartFuturesInstrumentData(log=self.log)

    def has_data_for_contract(self, futures_contract: futuresContract) -> bool:
        """
        Does Barchart have data for a given contract?
        This implementation just checks for the existence of a top level info page for the given contract
        :param futures_contract: internal contract identifier
        :type futures_contract: futuresContract
        :return: whether Barchart knows about the contract
        :rtype: bool
        """
        try:
            contract_id = self.get_barchart_id(futures_contract)
            resp = self._get_overview(contract_id)
            return resp.status_code == 200

        except Exception as e:
            self.log.error("Error: %s" % e)
            return False

    def get_historical_futures_data_for_contract(
        self, instr_symbol: str, bar_freq: Frequency = Frequency.Day
    ) -> pd.DataFrame:
        """
        Get historical daily data
        :param instr_symbol: contract (where instrument has barchart metadata)
        :type instr_symbol: str
        :param bar_freq: frequency of price data requested
        :type bar_freq: Frequency, one of 'Day', 'Hour', 'Minutes_15', 'Minutes_5', 'Minute', 'Seconds_10'
        :return: df
        :rtype: pandas DataFrame
        """

        try:

            if bar_freq == Frequency.Second or bar_freq == Frequency.Seconds_10:
                raise NotImplementedError(
                    f"Barchart supported data frequencies: {self._valid_freqs()}"
                )

            if instr_symbol is None:
                self.log.warn(f"get_historical_futures_data_for_contract() instr_symbol is required")
                return missing_data

            # GET the futures quote chart page, scrape to get XSRF token
            # https://www.barchart.com/futures/quotes/GCM21/interactive-chart
            chart_url = (
                BARCHART_URL + f"futures/quotes/{instr_symbol}/interactive-chart"
            )
            chart_resp = self._session.get(chart_url)
            xsrf = urllib.parse.unquote(chart_resp.cookies["XSRF-TOKEN"])

            headers = {
                "content-type": "text/plain; charset=UTF-8",
                "Accept-Encoding": "gzip, deflate, br",
                "Referer": chart_url,
                "x-xsrf-token": xsrf,
            }

            payload = {
                "symbol": instr_symbol,
                "maxrecords": "640",
                "volume": "contract",
                "order": "asc",
                "dividends": "false",
                "backadjust": "false",
                "days to expiration": "1",
                "contractroll": "combined",
            }

            if bar_freq == Frequency.Day:
                data_url = BARCHART_URL + "proxies/timeseries/queryeod.ashx"
                payload["data"] = "daily"
                payload["contractroll"] = "expiration"
            else:
                data_url = BARCHART_URL + "proxies/timeseries/queryminutes.ashx"
                payload["interval"] = freq_mapping[bar_freq]
                payload["contractroll"] = "combined"

            # get prices for instrument from BC internal API
            prices_resp = self._session.get(data_url, headers=headers, params=payload)
            ratelimit = prices_resp.headers["x-ratelimit-remaining"]
            if int(ratelimit) <= 15:
                time.sleep(20)
            self.log.msg(
                f"GET {data_url} {instr_symbol}, {prices_resp.status_code}, ratelimit {ratelimit}"
            )

            # read response into dataframe
            iostr = io.StringIO(prices_resp.text)
            df = pd.read_csv(iostr, header=None)

            # convert to expected format
            price_data_as_df = self._raw_barchart_data_to_df(
                df, bar_freq=bar_freq, log=self.log
            )
            self.log.msg(f"Latest price {price_data_as_df.index[-1]} with {bar_freq}")

            return price_data_as_df

        except Exception as ex:
            self.log.error(f"Problem getting historical data: {ex}")
            return missing_data

    def get_barchart_id(self, futures_contract: futuresContract) -> str:
        instr_code = futures_contract.instrument_code
        bc_instr_code = self.barchart_futures_instrument_data.get_brokers_instrument_code(instr_code)
        letter_month = futures_contract.contract_date.letter_month()
        two_digit_year_str = futures_contract.date_str[2, 4]
        barchart_id = bc_instr_code + letter_month + two_digit_year_str
        return barchart_id

    @staticmethod
    def _raw_barchart_data_to_df(
        price_data_raw: pd.DataFrame, log: logger, bar_freq: Frequency = Frequency.Day
    ) -> pd.DataFrame:

        if price_data_raw is None:
            log.warn("No historical price data from Barchart")
            return missing_data

        date_format = "%Y-%m-%d"

        if bar_freq == Frequency.Day:
            price_data_as_df = price_data_raw.iloc[:, [1, 2, 3, 4, 5, 7]].copy()
        else:
            price_data_as_df = price_data_raw.iloc[:, [0, 2, 3, 4, 5, 6]].copy()
            date_format = "%Y-%m-%d %H:%M"

        price_data_as_df.columns = ["index", "OPEN", "HIGH", "LOW", "FINAL", "VOLUME"]
        price_data_as_df["index"] = pd.to_datetime(
            price_data_as_df["index"], format=date_format
        )
        price_data_as_df.set_index("index", inplace=True)

        return price_data_as_df

    def _get_overview(self, contract_id):
        """
        GET the futures overview page, eg https://www.barchart.com/futures/quotes/B6M21/overview
        :param contract_id: contract identifier
        :type contract_id: str
        :return: resp
        :rtype: HTTP response object
        """
        url = BARCHART_URL + "futures/quotes/%s/overview" % contract_id
        resp = self._session.get(url)
        self.log.msg(f"GET {url}, response {resp.status_code}")
        return resp

    @staticmethod
    def _valid_freqs():
        return [v.name for i, v in enumerate(Frequency) if not i >= 6]
