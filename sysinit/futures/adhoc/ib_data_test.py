import datetime

from ib_insync import Future
from ib_insync import IB

ib = IB()
ib.connect("127.0.0.1", 7496)
ib.reqMarketDataType(3)
contract = Future("MES", "202303", "CME")
ib.qualifyContracts(contract)

# Historical
bars = ib.reqHistoricalData(contract, endDateTime='', durationStr='1 M', barSizeSetting='1 day', whatToShow='TRADES',
                            useRTH=True, formatDate=1)
print(bars)

# Ticks
recent_time = datetime.datetime.now() - datetime.timedelta(seconds=60)
tick_data = ib.reqHistoricalTicks(
    contract, recent_time, "", 200, "BID_ASK", useRth=False
)
print(tick_data)

# Streaming
ib.reqMktData(contract, "", False, False)
ticker = ib.ticker(contract)
print(ticker)


