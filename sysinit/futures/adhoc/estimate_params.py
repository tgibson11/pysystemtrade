import matplotlib
from matplotlib import pyplot as plt

from systems.diagoutput import systemDiag
from systems.provided.rob_system.run_system import futures_system

system = futures_system(
    config_filename="/Users/Todd/PyCharmProjects/private/system_config.yaml"
)

# system.config.use_forecast_scale_estimates = False
# system.config.use_forecast_weight_estimates = False
# system.config.use_forecast_div_mult_estimates = True
# system.config.use_instrument_weight_estimates = False
# system.config.use_instrument_div_mult_estimates = True

sysdiag = systemDiag(system)
sysdiag.yaml_config_with_estimated_parameters('someyamlfile.yaml')

system.log.info("Sharpe Ratio: " + str(system.accounts.portfolio().sharpe()))

system.accounts.portfolio().curve().plot()
matplotlib.use('TkAgg')
plt.show()