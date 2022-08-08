import requests

from sysdata.barchart.bc_instruments_data import BarchartFuturesInstrumentData
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

        # start HTTP session
        self._session = requests.Session()
        self._session.headers.update({"User-Agent": "Mozilla/5.0"})

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

    def get_barchart_id(self, futures_contract: futuresContract) -> str:
        instr_code = futures_contract.instrument_code
        bc_instr_code = self.barchart_futures_instrument_data.get_brokers_instrument_code(instr_code)
        month_code = futures_contract.contract_date.letter_month()
        year = futures_contract.contract_date.year()
        barchart_id = f"{bc_instr_code}{month_code}{str(year)[len(str(year)) - 2:]}"
        return barchart_id

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
