from .models import Provider, ProviderInterface, Currency, CurrencyExchangeRate


class MockProvider(ProviderInterface):

    name = 'Mock Provider'

    def get_latest_rates_dict(self, base_currency_code):
        js = {
            "success": True,
            "timestamp": 1519296206,
            "base": base_currency_code,
            "date": "2024-02-25",
            "rates": {
                "AUD": 3.33,
                "CAD": 3.33,
                "CHF": 3.33,
                "CNY": 3.33,
                "GBP": 3.33,
                "JPY": 3.33,
                "USD": 3.33,
            }
        }
        assert self._is_sanity_json(js)
        return js['rates']

    def get_rates_dict_timeseries(self, base_currency_code, date_from, date_to):
        js = {
            "success": True,
            "timestamp": 1519296206,
            "base": base_currency_code,
            "date": "2024-02-25",
            "rates": {
                '2020-01-01': {
                    "AUD": 1.11,
                    "CAD": 1.11,
                    "CHF": 1.11,
                    "CNY": 1.11,
                    "GBP": 1.11,
                    "JPY": 1.11,
                    "USD": 1.11,
                },
                '2020-01-02': {
                    "AUD": 2.22,
                    "CAD": 2.22,
                    "CHF": 2.22,
                    "CNY": 2.22,
                    "GBP": 2.22,
                    "JPY": 2.22,
                    "USD": 2.22,
                }
            }
        }
        assert self._is_sanity_json(js)
        return js['rates']


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
