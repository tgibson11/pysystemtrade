from systems.accounts.account_forecast import accountForecast
from systems.accounts.account_subsystem import accountSubsystem
from systems.accounts.account_instruments import accountInstruments


class accountsStage(accountForecast, accountSubsystem, accountInstruments):

    @property
    def name(self):
        return "accounts"
