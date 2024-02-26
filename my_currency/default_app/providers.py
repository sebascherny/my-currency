from .models import ProviderInterface, Currency
import json
import os


class MockProvider(ProviderInterface):

    name = 'Mock Provider'
    path_from_this_folder = 'json_files/mock_provider_data.json'

    def get_latest_rates_dict(self, base_currency_code):
        with open(os.path.join(os.path.dirname(__file__), self.path_from_this_folder)) as f:
            js = json.load(f)
        js["base"] = base_currency_code
        assert self._is_sanity_json(js)
        rates = js['rates']
        rates = self._get_latest_rates_from_timeseries(rates)
        return rates

    def get_rates_dict_timeseries(self, base_currency_code, date_from, date_to):
        with open(os.path.join(os.path.dirname(__file__), self.path_from_this_folder)) as f:
            js = json.load(f)
        js["base"] = base_currency_code
        assert self._is_sanity_json(js)
        rates = js['rates']
        assert self._is_timeseries_sanity(rates)
        rates = self._filter_timeseries(rates, date_from, date_to)
        return rates


class StoredDataProvider(ProviderInterface):

    name = 'Stored Data Provider'

    def get_latest_rates_dict(self, base_currency_code):
        rates = {}
        base_currency_object = Currency.objects.all().filter(code=base_currency_code).first()
        if not base_currency_object:
            return rates
        for currency in Currency.objects.all():
            latest_rate = base_currency_object.exchanges.filter(
                exchanged_currency=currency
            ).last()
            if latest_rate:
                rates[currency.code] = float(latest_rate.rate_value)
        return rates
    
    def _get_date_key(self, valuation_date):
        return valuation_date.strftime("%Y-%m-%d")

    def get_rates_dict_timeseries(self, base_currency_code, date_from, date_to):
        rates = {}
        base_currency_object = Currency.objects.all().filter(code=base_currency_code).first()
        if not base_currency_object:
            return rates
        for rate in base_currency_object.exchanges.filter(
            valuation_date__gte=date_from,
            valuation_date__lte=date_to
        ):
            date_key = self._get_date_key(rate.valuation_date)
            if date_key not in rates:
                rates[date_key] = {}
            rates[date_key][rate.exchanged_currency.code] = float(rate.rate_value)
        return rates
