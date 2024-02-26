from django.db import models
import requests
from django.core.cache import cache
from my_currency.settings import CACHE_TIME_IN_SECONDS


class Currency(models.Model):
    code = models.CharField(max_length=3, unique=True)
    name = models.CharField(max_length=20)
    symbol = models.CharField(max_length=10)

    def __str__(self):
        return self.code

    class Meta:
        ordering = ('code',)


class CurrencyExchangeRate(models.Model):
    source_currency = models.ForeignKey(Currency, on_delete=models.CASCADE, related_name='exchanges')
    exchanged_currency = models.ForeignKey(Currency, on_delete=models.CASCADE)
    valuation_date = models.DateField(db_index=True)
    rate_value = models.DecimalField(decimal_places=6, max_digits=18)

    class Meta:
        unique_together = ('source_currency', 'exchanged_currency', 'valuation_date')
        ordering = ('valuation_date', 'source_currency', 'exchanged_currency')

    def __str__(self):
        return f"At {self.valuation_date.strftime('%Y-%m-%d')}, 1 {self.source_currency.code} = {self.rate_value} {self.exchanged_currency.code}"


class ProviderInterface:

    name = None

    def get_rates_dict_timeseries(self, base_currency_code, date_from, date_to):
        raise NotImplementedError("Subclasses must implement this method")

    def get_latest_rates_dict(self, base_currency_code):
        raise NotImplementedError("Subclasses must implement this method")

    def _is_sanity_json(self, js):
        return bool(
            isinstance(js, dict) and js.get('success') == True and
            isinstance(js.get('rates'), dict)
        )

    def _get_rates_dict_from_json(self, js):
        assert self._is_sanity_json(js)
        return js['rates']

    def _get_latest_rates_from_timeseries(self, rates):
        assert self._is_timeseries_sanity(rates)
        latest_date = list(sorted(rates.keys()))[-1]
        return rates[latest_date]

    def _is_timeseries_sanity(self, rates):
        return bool(
            rates and isinstance(rates, dict) and
            all(isinstance(k, str) and len(k) == 10 for k in rates.keys()) and
            all(isinstance(v, dict) for v in rates.values())
        )

    def _filter_timeseries(self, rates, date_from, date_to):
        assert self._is_timeseries_sanity(rates)
        return {k: v for k, v in rates.items() if date_from <= k <= date_to}


class Provider(models.Model, ProviderInterface):
    name = models.CharField(max_length=100, unique=True)
    access_key = models.CharField(max_length=100)
    timeseries_endpoint = models.CharField(max_length=200, blank=True, default='', help_text='Use {0} for access_key, {1} for base_currency, {2} for date_from, {3} for date_to. For example, url could be http://data.fixer.io/api/timeseries?access_key={0}&base={1}&start_date={2}&end_date={3}')
    latest_endpoint = models.CharField(max_length=200, blank=True, default='', help_text='Use {0} for access_key and {1} for base_curreny. For example, http://data.fixer.io/api/latest?access_key={0}&base={1}')
    historical_hardcoded_json = models.JSONField(null=True, blank=True)
    priority = models.IntegerField(default=0)
    is_default = models.BooleanField(default=False)

    def __str__(self):
        return self.name
    
    class Meta:
        ordering = ('-is_default', '-priority',)

    def get_rates_dict_timeseries(self, base_currency_code, date_from, date_to):
        js = None
        if self.historical_hardcoded_json:
            js = self.historical_hardcoded_json
        else:
            url = self.timeseries_endpoint.format(self.access_key, base_currency_code, date_from, date_to)
            js = cache.get(url)
            if not js:
                js = requests.get(url).json()
                cache.set(url, js, CACHE_TIME_IN_SECONDS)
        if self._is_sanity_json(js):
            return self._get_rates_dict_from_json(js)
        return {}
        # raise ValueError(f"Failed to get rates from {self.timeseries_endpoint} for {base_currency_code}")

    def get_latest_rates_dict(self, base_currency_code):
        if self.historical_hardcoded_json:
            js = self.historical_hardcoded_json
            if self._is_sanity_json(js):
                rates = self._get_rates_dict_from_json(js)
                latest_date = list(sorted(rates.keys()))[-1]
                return rates[latest_date]
        else:
            url = self.latest_endpoint.format(self.access_key, base_currency_code)
            js = cache.get(url)
            if not js:
                js = requests.get(url).json()
                cache.set(url, js, 60 * 60 * 24)
            if self._is_sanity_json(js):
                return self._get_rates_dict_from_json(js)
        return {}
        # raise ValueError(f"Failed to get rates from {self.latest_endpoint} for {base_currency_code}")