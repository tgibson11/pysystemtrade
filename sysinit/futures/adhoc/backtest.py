import logging

from sysdata.config.configdata import Config
from systems.provided.rob_system.run_system import futures_system

logging.getLogger("arctic").setLevel(logging.ERROR)

config = Config("/home/todd/private/system_config.yaml")
system = futures_system(config=config)

system.log.msg("Sharpe Ratio: " + str(system.accounts.portfolio().sharpe()))

# Daily % gain/loss
# with pd.option_context('display.max_rows', None):
#    print(system.accounts.portfolio().percent())

# system.accounts.portfolio().curve().plot()

print(system.accounts.portfolio().stats())
