from systems.forecast_scale_cap import *
from statsmodels.distributions.empirical_distribution import ECDF


class ForecastScaleCapVolAtten(ForecastScaleCap):

    @diagnostic()
    def get_vol_quantile_points(self, instrument_code):
        # More properly this would go in raw data perhaps
        self.log.msg("Calculating vol quantile for %s" % instrument_code)
        daily_vol = self.parent.rawdata.get_daily_percentage_volatility(instrument_code)
        ten_year_vol = daily_vol.rolling(2500, min_periods=10).mean()
        normalised_vol = daily_vol / ten_year_vol

        normalised_vol_q = quantile_of_points_in_data_series(normalised_vol)

        return normalised_vol_q

    @diagnostic()
    def get_vol_attenuation(self, instrument_code):
        normalised_vol_q = self.get_vol_quantile_points(instrument_code)
        vol_attenuation = normalised_vol_q.apply(multiplier_function)

        smoothed_vol_attenuation = vol_attenuation.ewm(span=10).mean()

        return smoothed_vol_attenuation

    @input
    def get_raw_forecast_before_attenuation(self, instrument_code, rule_variation_name):
        # original code for get_raw_forecast
        raw_forecast = self.parent.rules.get_raw_forecast(
            instrument_code, rule_variation_name
        )

        return raw_forecast

    @diagnostic()
    def get_raw_forecast(self, instrument_code, rule_variation_name):
        # overridden method this will be called downstream so don't change name
        raw_forecast_before_atten = self.get_raw_forecast_before_attenuation(instrument_code, rule_variation_name)

        vol_attenutation = self.get_vol_attenuation(instrument_code)

        attenuated_forecast = raw_forecast_before_atten * vol_attenutation

        return attenuated_forecast


def quantile_of_points_in_data_series(data_series):
    results = [quantile_of_points_in_data_series_row(data_series, irow) for irow in range(len(data_series))]
    results_series = pd.Series(results, index=data_series.index)

    return results_series


# this is a little slow so suggestions for speeding up are welcome
def quantile_of_points_in_data_series_row(data_series, irow):
    if irow < 2:
        return np.nan
    historical_data = list(data_series[:irow].values)
    current_value = data_series[irow]
    ecdf_s = ECDF(historical_data)

    return ecdf_s(current_value)


def multiplier_function(vol_quantile):
    if np.isnan(vol_quantile):
        return 1.0

    return 2 - 1.5 * vol_quantile