
from syscore.objects import  arg_not_supplied
from syslogdiag.log_to_screen import logtoscreen

from sysbrokers.IB.client.ib_fx_client import ibFxClient
from sysbrokers.IB.ib_connection import connectionIB
from sysbrokers.IB.ib_translate_broker_order_objects import tradeWithContract
from sysbrokers.broker_fx_handling import brokerFxHandlingData



class ibFxHandlingData(brokerFxHandlingData):
    def __init__(self, ibconnection: connectionIB, log=logtoscreen(
            "ibFXHandlingData")):
        self._ibconnection = ibconnection
        super().__init__(log=log)

    def __repr__(self):
        return "IB FX handling data %s" % str(self.ib_client)


    @property
    def ibconnection(self) -> connectionIB:
        return self._ibconnection

    @property
    def ib_client(self) -> ibFxClient:
        client = getattr(self, "_ib_client", None)
        if client is None:
             client = self._ib_client = ibFxClient(ibconnection=self.ibconnection,
                                                   log = self.log)

        return client

    def broker_fx_balances(self) -> dict:
        return self.ib_client.broker_fx_balances()

    def broker_fx_market_order(
            self,
            trade: float,
            ccy1: str,
            account: str=arg_not_supplied,
            ccy2: str="USD") -> tradeWithContract:

        submitted_fx_trade = self.ib_client.broker_fx_market_order(
            trade, ccy1, ccy2=ccy2, account=account
        )

        return submitted_fx_trade
