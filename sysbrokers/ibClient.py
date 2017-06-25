from sysbrokers.baseClient import brokerClient
from ibapi.client import EClient

import queue


class ibClient(EClient, brokerClient):
    """
    Client specific to interactive brokers

    Overrides the methods in the base class specifically for IB

    """

    def __init__(self, wrapper):
        # Set up with a wrapper inside
        EClient.__init__(self, wrapper)

    def speakingClock(self):
        """
        Basic example to tell the time
        :return: unix time, as an int
        """

        print("Getting the time from the server... ")

        # Make a place to store the time we're going to return
        # This is a queue
        time_storage = self.wrapper.init_time()

        # This is the native method in EClient, asks the server to send us the time please
        self.reqCurrentTime()

        # Try and get a valid time
        try:
            current_time = time_storage.get(timeout=10)
        except queue.Empty:
            print("Exceeded maximum wait for wrapper to respond")
            current_time = None

        while self.wrapper.is_error():
            print(self.wrapper.get_error())

        return current_time
