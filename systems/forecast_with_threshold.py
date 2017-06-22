import math
import pandas as pd

from systems.forecast_combine import ForecastCombine


class ForecastWithThreshold(ForecastCombine):
    def get_combined_forecast(self, instrument_code):

        combined_forecast = super(ForecastWithThreshold, self).get_combined_forecast(instrument_code)

        system = self.parent
        use_threshold = False
        if "use_forecast_threshold" in dir(system.config) and instrument_code in system.config.use_forecast_threshold:
            use_threshold = system.config.use_forecast_threshold[instrument_code]

        if use_threshold:

            self.log.msg("Applying forecast threshold for %s" % instrument_code, instrument_code=instrument_code)

            # apply threshold
            def map_forecast_value(x):
                x = float(x)
                if math.isnan(x):
                    return 0.0
                if x <= -20.0:
                    return -30.0
                if -20.0 < x < -10.0:
                    return -(abs(x) - 10.0) * 3
                if -10.0 <= x <= 10.0:
                    return 0.0
                if 10.0 < x < 20.0:
                    return (abs(x) - 10.0) * 3
                return 30.0

            combined_forecast = combined_forecast.apply(lambda x: map_forecast_value(x))

        return combined_forecast
