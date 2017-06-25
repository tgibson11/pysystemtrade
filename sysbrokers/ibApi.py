from sysbrokers.ibClient import ibClient
from sysbrokers.ibServer import ibServer
from threading import Thread


class IBApi(ibClient, ibServer):

    def __init__(self, ipaddress, portid, clientid):
        ibServer.__init__(self)
        ibClient.__init__(self, wrapper=self)
        self.connect(ipaddress, portid, clientid)

        thread = Thread(target=self.run)
        thread.start()
        setattr(self, "_thread", thread)
