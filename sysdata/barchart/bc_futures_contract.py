from sysdata.barchart.bc_instruments import BcFuturesInstrument
from sysobjects.contracts import futuresContract


class BcFuturesContract(object):

    def __init__(
            self,
            futures_contract: futuresContract,
            bc_futures_instrument: BcFuturesInstrument,
    ):
        self._futures_contract = futures_contract
        self._bc_futures_instrument = bc_futures_instrument

    @property
    def bc_symbol(self) -> str:
        return self._bc_futures_instrument.bc_symbol

    @property
    def bc_price_multiplier(self) -> float:
        return self._bc_futures_instrument.bc_price_multiplier

    @property
    def contract_date(self):
        return self._futures_contract.contract_date

    def get_bc_contract_id(self) -> str:
        bc_symbol = self.bc_symbol
        month_letter = self.contract_date.letter_month()
        year_str = str(self.contract_date.year())
        barchart_id = f"{bc_symbol}{month_letter}{year_str[len(year_str) - 2:]}"
        return barchart_id
