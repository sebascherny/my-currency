import json
from django.core.management.base import BaseCommand
from default_app.models import Currency, CurrencyExchangeRate
from datetime import datetime, timedelta
import random

class Command(BaseCommand):
    help = 'Cleans database and creates random exchange rates in database for testing purposes'

    def add_arguments(self, parser):
        parser.add_argument('base_currency_code', type=str, help='3 letter code of the base currency')
        parser.add_argument('number_of_days', type=int, help='Number of days to generate exchange rates for')
        parser.add_argument('erase_data', type=str, help='True/False, if it is True, it will erase all data in the database before creating new data, if it is False, it will only create new data without erasing the old data.')


    def handle(self, *args, **options):
        all_currencies = ['USD', 'EUR', 'GBP', 'JPY', 'AUD', 'CAD', 'CHF', 'CNY']
        if options['erase_data'] in ('True', 'true', '1', 'yes'):
            rates_deleted, _ = CurrencyExchangeRate.objects.all().delete()
            currencies_deleted, _ = Currency.objects.all().delete()
            self.stdout.write(self.style.SUCCESS('Successfully cleaned data (%s exchange rates, %s currencies)' % (rates_deleted, currencies_deleted)))
        base_currency_code = options['base_currency_code']
        number_of_days = options['number_of_days']
        for currency in all_currencies + ([base_currency_code] if base_currency_code not in all_currencies else []):
            Currency.objects.update_or_create(code=currency, name=currency, symbol=currency)
        for currency in all_currencies:
            initial_rate = 0.5 + random.random()
            if currency == base_currency_code:
                # initial_rate = 1.0
                continue
            for i in range(number_of_days):
                CurrencyExchangeRate.objects.update_or_create(
                    source_currency=Currency.objects.get(code=base_currency_code),
                    exchanged_currency=Currency.objects.get(code=currency),
                    valuation_date=datetime.now().date() - timedelta(days=i),
                    defaults={'rate_value': initial_rate + random.uniform(-0.01, 0.01)}
                )
        self.stdout.write(self.style.SUCCESS('Successfully created exchange rates for %s days from %s to %s' % (number_of_days, base_currency_code, all_currencies, )))
