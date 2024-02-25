import json
from django.core.management.base import BaseCommand
from default_app.models import Currency, CurrencyExchangeRate
from datetime import datetime

class Command(BaseCommand):
    help = 'Imports historical exchange rates from a JSON file'

    def add_arguments(self, parser):
        parser.add_argument('file_path', type=str, help='Path to the JSON file containing the exchange rates')

    def handle(self, *args, **options):
        file_path = options['file_path']
        already_in_db = 0
        with open(file_path, mode='r') as file:
            data = json.load(file)
            for item in data:
                source_currency, _ = Currency.objects.get_or_create(code=item['source_currency'])
                exchanged_currency, _ = Currency.objects.get_or_create(code=item['exchanged_currency'])
                _, created = CurrencyExchangeRate.objects.update_or_create(
                    valuation_date=datetime.strptime(item['valuation_date'], '%Y-%m-%d'),
                    source_currency=source_currency,
                    exchanged_currency=exchanged_currency,
                    rate_value=item['rate_value']
                )
                already_in_db += int(not created)
        self.stdout.write(self.style.SUCCESS('Successfully imported %s exchange rates (%s already existed) from "%s"' % (len(data), already_in_db, file_path, )))
