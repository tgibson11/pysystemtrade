from dataclasses import dataclass
from sysobjects.instruments import futuresInstrument


@dataclass
class BcInstrumentConfigData:
    symbol: str
    price_multiplier: float = 1.0


@dataclass
class BcFuturesInstrument(object):
    instrument: futuresInstrument
    bc_data: BcInstrumentConfigData

    def __repr__(self):
        return "symbol='%s', price_multiplier=%.2f' " % (self.bc_symbol, self.bc_price_multiplier)

    @property
    def instrument_code(self):
        return self.instrument.instrument_code

    @property
    def bc_symbol(self):
        return self.bc_data.symbol

    @property
    def bc_price_multiplier(self):
        return self.bc_data.price_multiplier
