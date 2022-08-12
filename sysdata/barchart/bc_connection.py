import calendar
import io
import json
import urllib.parse
from datetime import datetime, timedelta

import pandas as pd
import requests
from bs4 import BeautifulSoup
from dateutil.tz import tz

from syscore.dateutils import Frequency, DAILY_PRICE_FREQ, HOURLY_FREQ, strip_timezone_fromdatetime, \
    adjust_timestamp_to_include_notional_close_and_time_offset
from syscore.objects import missing_data
from sysdata.barchart.bc_instruments_data import BarchartFuturesInstrumentData
from sysdata.config.production_config import get_production_config
from syslogdiag.log_to_screen import logtoscreen
from syslogdiag.logger import logger
from sysobjects.contracts import futuresContract

BARCHART_URL = "https://www.barchart.com/"


class bcConnection(object):

    def __init__(self, log=logtoscreen("bcConnection")):
        """
         :param log: logging object
         """
        log.label(broker="Barchart")
        self._log = log
        self._session = None

    @property
    def log(self):
        return self._log

    @property
    def session(self):
        if self._session is None:
            session = self._create_bc_session()
            self._session = session
        else:
            session = self._session
        return session

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
        specific_log = futures_contract.specific_log(self.log)

        try:
            contract_id = self.get_barchart_id(futures_contract)
            resp = self._get_overview(contract_id, log=specific_log)
            return resp.status_code == 200

        except Exception as e:
            specific_log.error("Error: %s" % e)
            return False

    def get_barchart_id(self, futures_contract: futuresContract) -> str:
        instr_code = futures_contract.instrument_code
        bc_instr_code = self.barchart_futures_instrument_data.get_brokers_instrument_code(instr_code)
        month_code = futures_contract.contract_date.letter_month()
        year = futures_contract.contract_date.year()
        barchart_id = f"{bc_instr_code}{month_code}{str(year)[len(str(year)) - 2:]}"
        return barchart_id

    def get_historical_futures_data_for_contract(
        self,
        contract_object: futuresContract,
        bar_freq: Frequency = DAILY_PRICE_FREQ
    ) -> pd.DataFrame:
        """
        Get historical daily data

        :param contract_object: futuresContract
        :param bar_freq: Frequency; one of D, H, 5M, M, 10S, S
        :return: futuresContractPriceData
        """

        specific_log = contract_object.specific_log(self.log)

        price_data = self._get_generic_data_for_contract(contract_object, log=specific_log, bar_freq=bar_freq)

        return price_data

    def _get_generic_data_for_contract(
        self,
        contract: futuresContract,
        log: logger = None,
        bar_freq: Frequency = DAILY_PRICE_FREQ
    ) -> pd.DataFrame:
        """
        Get historical daily data

        :param contract: futuresContract
        :param bar_freq: Frequency; one of D, H, 5M, M, 10S, S
        :return: futuresContractPriceData
        """
        if log is None:
            log = self.log

        price_data_raw = self._get_prices_for_contract(contract, bar_freq=bar_freq, log=log)

        price_data_as_df = self._raw_bc_data_to_df(price_data_raw=price_data_raw, log=log)

        instr_code = contract.instrument_code
        bc_futures_instrument = self.barchart_futures_instrument_data.get_bc_futures_instrument(instr_code)
        bc_price_multiplier = bc_futures_instrument.bc_price_multiplier
        adj_price_data_as_df = self._apply_bc_price_multiplier(price_data_as_df, bc_price_multiplier)

        return adj_price_data_as_df

    def _get_prices_for_contract(
            self,
            contract: futuresContract,
            bar_freq: Frequency = DAILY_PRICE_FREQ,
            days: int = 120,
            log: logger = None,
            dry_run: bool = False):

        now = datetime.now()

        year = contract.contract_date.year()
        month = contract.contract_date.month()
        bc_contract_id = self.get_barchart_id(contract)

        # we need to work out a date range for which we want the prices

        # for expired contracts the end date would be the expiry date;
        # for KISS sake, lets assume expiry is last date of contract month
        end_date = datetime(year, month, calendar.monthrange(year, month)[1])

        # but, if that end_date is in the future, then we may as well make it today...
        if now.date() < end_date.date():
            end_date = now

        # assumption no.2: lets set start date at <day_count> days before end date
        day_count = timedelta(days=days)
        start_date = end_date - day_count

        log.msg(f"getting historic {bar_freq} prices for contract '{bc_contract_id}', "
                f"from {start_date.strftime('%Y-%m-%d')} "
                f"to {end_date.strftime('%Y-%m-%d')}")

        # open historic data download page for required contract
        url = f"{BARCHART_URL}futures/quotes/{bc_contract_id}/historical-download"
        hist_resp = self.session.get(url)
        log.msg(f"GET {url}, status {hist_resp.status_code}")

        if hist_resp.status_code != 200:
            log.msg(f"No downloadable data found for contract '{bc_contract_id}'\n")
            return None

        xsrf = urllib.parse.unquote(hist_resp.cookies['XSRF-TOKEN'])

        # scrape page for csrf_token
        hist_soup = BeautifulSoup(hist_resp.text, 'html.parser')
        hist_tag = hist_soup.find(name='meta', attrs={'name': 'csrf-token'})
        hist_csrf_token = hist_tag.attrs['content']

        # check allowance
        payload = {'onlyCheckPermissions': 'true'}
        headers = {
            'content-type': 'application/x-www-form-urlencoded',
            'Accept-Encoding': 'gzip, deflate, br',
            'Referer': url,
            'x-xsrf-token': xsrf
        }
        resp = self.session.post(BARCHART_URL + 'my/download', headers=headers, data=payload)

        allowance = json.loads(resp.text)

        if allowance.get('error') is not None:
            log.warn("Barchart daily download allowance exceeded")
            return None

        raw_bc_data = None

        if allowance['success']:

            log.msg(f"POST {BARCHART_URL + 'my/download'}, "
                    f"status: {resp.status_code}, "
                    f"allowance success: {allowance['success']}, "
                    f"allowance count: {allowance['count']}")

            # download data
            xsrf = urllib.parse.unquote(resp.cookies['XSRF-TOKEN'])
            headers = {
                'content-type': 'application/x-www-form-urlencoded',
                'Accept-Encoding': 'gzip, deflate, br',
                'Referer': url,
                'x-xsrf-token': xsrf
            }

            payload = {'_token': hist_csrf_token,
                       'fileName': bc_contract_id + '_Daily_Historical Data',
                       'symbol': bc_contract_id,
                       'fields': 'tradeTime.format(Y-m-d),openPrice,highPrice,lowPrice,lastPrice,volume',
                       'startDate': start_date.strftime("%Y-%m-%d"),
                       'endDate': end_date.strftime("%Y-%m-%d"),
                       'orderBy': 'tradeTime',
                       'orderDir': 'asc',
                       'method': 'historical',
                       'limit': '10000',
                       'customView': 'true',
                       'pageTitle': 'Historical Data'}

            if bar_freq == DAILY_PRICE_FREQ:
                payload['type'] = 'eod'
                payload['period'] = 'daily'

            if bar_freq == HOURLY_FREQ:
                payload['type'] = 'minutes'
                payload['interval'] = 60

            if not dry_run:
                resp = self.session.post(BARCHART_URL + 'my/download', headers=headers, data=payload)
                log.msg(f"POST {BARCHART_URL + 'my/download'}, "
                        f"status: {resp.status_code}, "
                        f"data length: {len(resp.content)}")
                if resp.status_code == 200:

                    if 'Error retrieving data' not in resp.text:

                        raw_bc_data = resp.text

                    else:
                        log.msg(f"Barchart data problem for '{bc_contract_id}', not writing")

            else:
                log.msg(f"Not POSTing to {BARCHART_URL + 'my/download'}, dry_run")

            log.msg(f"Finished getting Barchart historic prices for {bc_contract_id}\n")

        return raw_bc_data

    def _raw_bc_data_to_df(self, price_data_raw: str, log: logger) -> pd.DataFrame:

        if price_data_raw is None:
            log.warn("No price data from IB")
            return missing_data

        iostr = io.StringIO(price_data_raw)
        price_data_as_df = pd.read_csv(iostr, skipfooter=1, engine='python')

        price_data_as_df.columns = ["date", "OPEN", "HIGH", "LOW", "FINAL", "VOLUME"]

        date_index = [
            self._bc_timestamp_to_datetime(price_row)
            for price_row in price_data_as_df["date"]
        ]

        price_data_as_df.index = date_index
        price_data_as_df.drop('date', axis=1, inplace=True)

        return price_data_as_df

    def _bc_timestamp_to_datetime(self, timestamp_bc) -> datetime:
        """
        Converts Barchart time (CT) to local, and adjusts yyyymm to closing vector

        :param timestamp_bc: datetime.datetime
        :return: pd.datetime
        """

        local_timestamp_bc = self._adjust_bc_time_to_local(timestamp_bc)
        timestamp = pd.to_datetime(local_timestamp_bc)

        adjusted_ts = adjust_timestamp_to_include_notional_close_and_time_offset(timestamp)

        return adjusted_ts

    @staticmethod
    def _adjust_bc_time_to_local(timestamp_bc) -> datetime:

        if getattr(timestamp_bc, "tz_localize", None) is None:
            # daily, nothing to do
            return timestamp_bc

        # Barchart timestamp already includes tz
        timestamp_bc_with_tz = timestamp_bc
        local_timestamp_bc_with_tz = timestamp_bc_with_tz.astimezone(tz.tzlocal())
        local_timestamp_bc = strip_timezone_fromdatetime(local_timestamp_bc_with_tz)

        return local_timestamp_bc

    @staticmethod
    def _apply_bc_price_multiplier(price_data: pd.DataFrame, bc_price_multiplier: float):
        price_data[["OPEN", "HIGH", "LOW", "FINAL"]] = \
            price_data[["OPEN", "HIGH", "LOW", "FINAL"]] * bc_price_multiplier
        return price_data

    def _get_overview(self, contract_id, log: logger):
        """
        GET the futures overview page, eg https://www.barchart.com/futures/quotes/B6M21/overview
        :param contract_id: contract identifier
        :type contract_id: str
        :return: resp
        :rtype: HTTP response object
        """
        url = BARCHART_URL + "futures/quotes/%s/overview" % contract_id
        resp = self.session.get(url)
        log.msg(f"GET {url}, response {resp.status_code}")
        return resp

    def _create_bc_session(self):

        config = get_production_config()
        barchart_username = config.get_element_or_missing_data("barchart_username")
        barchart_password = config.get_element_or_missing_data("barchart_password")

        # start a session
        session = requests.Session()
        session.headers.update({'User-Agent': 'Mozilla/5.0'})
        if barchart_username is missing_data or barchart_password is missing_data:
            raise Exception('Barchart credentials are required')

        # GET the login page, scrape to get CSRF token
        resp = session.get(BARCHART_URL + 'login')
        soup = BeautifulSoup(resp.text, 'html.parser')
        tag = soup.find(type='hidden')
        csrf_token = tag.attrs['value']
        self.log.msg(f"GET {BARCHART_URL + 'login'}, status: {resp.status_code}, CSRF token: {csrf_token}")

        # login to site
        payload = {'email': barchart_username, 'password': barchart_password, '_token': csrf_token}
        resp = session.post(BARCHART_URL + 'login', data=payload)
        self.log.msg(f"POST {BARCHART_URL + 'login'}, status: {resp.status_code}")
        if resp.url == BARCHART_URL + 'login':
            raise Exception('Invalid Barchart credentials')

        return session

    @staticmethod
    def _valid_freqs():
        return [v.name for i, v in enumerate(Frequency) if not i >= 6]
