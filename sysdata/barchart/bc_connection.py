from syslogdiag.log_to_screen import logtoscreen


class bcConnection(object):

    def __init__(
        self,
        log=logtoscreen("bcConnection")
    ):
        """
         :param log: logging object
         """
        self._log = log
        log.label(broker="Barchart")

