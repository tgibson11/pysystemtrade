from sysbrokers.baseServer import brokerServer
from sysbrokers.ibUtils import identified_as, finishableQueue, ACCOUNT_VALUE_FLAG, ACCOUNT_UPDATE_FLAG
from ibapi.wrapper import EWrapper

import queue


class ibServer(EWrapper, brokerServer):
    """
    Server specific to interactive brokers

    Overrides the methods in the base class specifically for IB

    """

    def __init__(self):
        super().__init__()
        self._my_errors = queue.Queue()
        self._time_queue = queue.Queue()
        # use a dict as could have different accountids
        self._my_accounts = {}
        # We set these up as we could get things coming along before we run an init
        self._my_positions = queue.Queue()

    # Error handling code
    def get_error(self, timeout=5):
        if self.is_error():
            try:
                return self._my_errors.get(timeout=timeout)
            except queue.Empty:
                return None

        return None

    def is_error(self):
        an_error_if = not self._my_errors.empty()
        return an_error_if

    def error(self, id, errorCode, errorString):
        # Overridden method
        errormsg = "IB error id %d errorcode %d string %s" % (id, errorCode, errorString)
        self._my_errors.put(errormsg)

    # Time telling code
    def init_time(self):
        return self._time_queue

    def currentTime(self, time_from_server):
        # Overridden method
        self._time_queue.put(time_from_server)

    # get positions code
    def init_positions(self):
        positions_queue = self._my_positions = queue.Queue()
        return positions_queue

    def position(self, account, contract, position, avgCost):
        # uses a simple tuple, but you could do other, fancier, things here
        position_object = (account, contract, position, avgCost)
        self._my_positions.put(position_object)

    def positionEnd(self):
        # overridden method
        self._my_positions.put(finishableQueue.FINISHED)

    # get accounting data
    def init_accounts(self, accountName):
        accounting_queue = self._my_accounts[accountName] = queue.Queue()
        return accounting_queue

    def updateAccountValue(self, key: str, val: str, currency: str, accountName: str):
        # use this to separate out different account data
        data = identified_as(ACCOUNT_VALUE_FLAG, (key, val, currency))
        self._my_accounts[accountName].put(data)

    def updatePortfolio(self, contract, position: float,
                        marketPrice: float, marketValue: float,
                        averageCost: float, unrealizedPNL: float,
                        realizedPNL: float, accountName: str):
        # use this to separate out different account data
        data = identified_as(ACCOUNT_UPDATE_FLAG, (contract, position, marketPrice, marketValue, averageCost,
                                                   unrealizedPNL, realizedPNL))
        self._my_accounts[accountName].put(data)

    def accountDownloadEnd(self, accountName: str):
        self._my_accounts[accountName].put(finishableQueue.FINISHED)
