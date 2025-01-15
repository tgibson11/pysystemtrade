from systems.provided.rob_system.run_system import futures_system

system = futures_system(config_filename="/Users/Todd/PyCharmProjects/private/system_config.yaml")

system.log.msg("Sharpe Ratio: " + str(system.accounts.portfolio().sharpe()))

# Daily % gain/loss
# with pd.option_context('display.max_rows', None):
#    print(system.accounts.portfolio().percent())

# print(system.accounts.portfolio().stats())

system.accounts.portfolio().curve().plot()
matplotlib.use('TkAgg')
plt.show()

