import io
import urllib.parse

import pandas as pd
import requests
from bs4 import BeautifulSoup

from syscore.dateutils import Frequency, DAILY_PRICE_FREQ
from syscore.objects import missing_data
from sysdata.barchart.bc_instruments_data import BarchartFuturesInstrumentData
from sysdata.config.production_config import get_production_config
from syslogdiag.log_to_screen import logtoscreen
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
        try:
            contract_id = self.get_barchart_id(futures_contract)
            resp = self._get_overview(contract_id)
            return resp.status_code == 200

        except Exception as e:
            self.log.error("Error: %s" % e)
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
        freq: Frequency = DAILY_PRICE_FREQ,
    ) -> pd.DataFrame:
        """
        Get historical daily data
        :param contract_object: internal contract identifier
        :type contract_object: futuresContract
        :param freq: frequency of price data requested
        :type freq: Frequency, one of 'Day', 'Hour', 'Minutes_15', 'Minutes_5', 'Minute', 'Seconds_10'
        :return: df
        :rtype: pandas DataFrame
        """

        try:

            if freq == Frequency.Second or freq == Frequency.Seconds_10:
                raise NotImplementedError(
                    f"Barchart supported data frequencies: {self._valid_freqs()}"
                )

            if contract_object is None:
                self.log.warn(f"get_historical_futures_data_for_contract() contract_object is required")
                return missing_data

            contract = self.get_barchart_id(contract_object)

            # open historic data download page for required contract
            url = f"{BARCHART_URL}futures/quotes/{contract}/historical-download"
            hist_resp = self.session.get(url)
            self.log.msg(f"GET {url}, status {hist_resp.status_code}")

            if hist_resp.status_code != 200:
                self.log.msg(f"No downloadable data found for contract '{contract}'\n")
                return missing_data
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
            resp = session.post(BARCHART_URL + 'my/download', headers=headers, data=payload)

            allowance = json.loads(resp.text)

            if allowance.get('error') is not None:
                return HistoricalDataResult.EXCEED

            if allowance['success']:

                self.log.info(f"POST {BARCHART_URL + 'my/download'}, "
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
                           'fileName': contract + '_Daily_Historical Data',
                           'symbol': contract,
                           'fields': 'tradeTime.format(Y-m-d),openPrice,highPrice,lowPrice,lastPrice,volume',
                           'startDate': start_date.strftime("%Y-%m-%d"),
                           'endDate': end_date.strftime("%Y-%m-%d"),
                           'orderBy': 'tradeTime',
                           'orderDir': 'asc',
                           'method': 'historical',
                           'limit': '10000',
                           'customView': 'true',
                           'pageTitle': 'Historical Data'}

                if period == 'daily':
                    payload['type'] = 'eod'
                    payload['period'] = 'daily'
                    dateformat = '%Y-%m-%d'

                if period == 'hourly':
                    payload['type'] = 'minutes'
                    payload['interval'] = 60
                    dateformat = '%m/%d/%Y %H:%M'

                if not dry_run:
                    resp = session.post(BARCHART_URL + 'my/download', headers=headers, data=payload)
                    logging.info(f"POST {BARCHART_URL + 'my/download'}, "
                                 f"status: {resp.status_code}, "
                                 f"data length: {len(resp.content)}")
                    if resp.status_code == 200:

                        if 'Error retrieving data' not in resp.text:

                            iostr = io.StringIO(resp.text)
                            df = pd.read_csv(iostr, skipfooter=1, engine='python')
                            df['Time'] = pd.to_datetime(df['Time'], format=dateformat)
                            df.set_index('Time', inplace=True)
                            df.index = df.index.tz_localize(tz='US/Central').tz_convert('UTC')
                            df = df.rename(columns={"Last": "Close"})

                            if len(df) < 3:
                                low_data = True

                            filename = f"{instrument}_{datecode}00.csv"
                            full_path = f"{path}/{filename}"
                            logging.info(f"writing to: {full_path}")

                            df.to_csv(full_path, date_format='%Y-%m-%dT%H:%M:%S%z')

                        else:
                            logging.info(f"Barchart data problem for '{instrument}_{datecode}00', not writing")

                else:
                    logging.info(f"Not POSTing to {BARCHART_URL + 'my/download'}, dry_run")

                logging.info(f"Finished getting Barchart historic prices for {contract}\n")

            # read response into dataframe
            iostr = io.StringIO(prices_resp.text)
            df = pd.read_csv(iostr, header=None)

            # convert to expected format
            # TODO see IB price client
            price_data_as_df = self._raw_barchart_data_to_df(df, bar_freq=freq, log=self.log)
            self.log.msg(f"Latest price {price_data_as_df.index[-1]} with {bar_freq}")

            return price_data_as_df

        except Exception as ex:
            self.log.error(f"Problem getting historical data: {ex}")
            return missing_data

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
