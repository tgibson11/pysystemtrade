from sysbrokers.baseServer import brokerServer
from ibapi.wrapper import EWrapper

import queue


class ibServer(EWrapper, brokerServer):
    """
    Server specific to interactive brokers

    Overrides the methods in the base class specifically for IB

    """

    def __init__(self):
        super().__init__()
        error_queue = queue.Queue()
        self._my_errors = error_queue
        time_queue = queue.Queue()
        self._time_queue = time_queue

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
        # Overriden method
        errormsg = "IB error id %d errorcode %d string %s" % (id, errorCode, errorString)
        self._my_errors.put(errormsg)

    # Time telling code
    def init_time(self):
        return self._time_queue

    def currentTime(self, time_from_server):
        # Overriden method
        self._time_queue.put(time_from_server)
