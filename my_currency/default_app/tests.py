from django.test import TestCase
from rest_framework.test import APITestCase
from default_app.models import Currency, CurrencyExchangeRate, Provider
from unittest.mock import patch
from datetime import datetime
import time


class MockResponse():
    def __init__(self, js):
        self.js = js
    
    def json(self):
        return self.js

# Create your tests here.
class APIV1Test(APITestCase):
    def setUp(self):
        self.maxDiff = None

    def test_mock_provider(self):
        response = self.client.get(
            '/v1/calculate-exchange/',
            data={"source_currency": "ABC", "amount": 2, "exchanged_currency": "DEF"},
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content, b'Could not convert the currency')
        response = self.client.get(
            '/v1/calculate-exchange/',
            data={"source_currency": "EUR", "amount": 'amount', "exchanged_currency": "USD"},
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content, b'Amount must be a number')
        response = self.client.get(
            '/v1/calculate-exchange/',
            data={"source_currency": "EUR", "amount": 2, "exchanged_currency": "USD"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'success': True, 'value': 6.66})

    def test_stored_data_provider(self):
        usd = Currency.objects.create(code="USD", name="US Dollar", symbol="$")
        eur = Currency.objects.create(code="EUR", name="Euro", symbol="€")
        CurrencyExchangeRate.objects.create(
            source_currency=eur,
            exchanged_currency=usd,
            valuation_date=datetime.strptime("2020-01-01", '%Y-%m-%d'),
            rate_value=1.11
        )
        CurrencyExchangeRate.objects.create(
            source_currency=eur,
            exchanged_currency=usd,
            valuation_date=datetime.strptime("2020-01-02", '%Y-%m-%d'),
            rate_value=1.12
        )
        CurrencyExchangeRate.objects.create(
            source_currency=eur,
            exchanged_currency=usd,
            valuation_date=datetime.strptime("2020-01-03", '%Y-%m-%d'),
            rate_value=1.13
        )
        response = self.client.get(
            '/v1/calculate-exchange/',
            data={"source_currency": "EUR", "amount": 2, "exchanged_currency": "USD"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'success': True, 'value': 2 * 1.13})
        response = self.client.get(
            '/v1/rates-for-time-period/',
            data={"source_currency": "EUR", "amount": 2, "exchanged_currency": "USD", "date_from": "2020-01-01", "date_to": "2020-01-02"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'success': True, 'rates': {
            "2020-01-01": {'USD': 1.110000},
            "2020-01-02": {'USD': 1.120000},
        }})
        eur = Currency.objects.get(code="EUR")
        self.assertEqual([str(x) for x in eur.exchanges.all()], [
            'At 2020-01-01, 1 EUR = 1.110000 USD',
            'At 2020-01-02, 1 EUR = 1.120000 USD',
            'At 2020-01-03, 1 EUR = 1.130000 USD'
        ])

    def test_different_providers(self):
        usd = Currency.objects.create(code="USD", name="US Dollar", symbol="$")
        eur = Currency.objects.create(code="EUR", name="Euro", symbol="€")
        CurrencyExchangeRate.objects.create(
            source_currency=eur,
            exchanged_currency=usd,
            valuation_date=datetime.strptime("2020-01-01", '%Y-%m-%d'),
            rate_value=1.11
        )
        CurrencyExchangeRate.objects.create(
            source_currency=eur,
            exchanged_currency=usd,
            valuation_date=datetime.strptime("2020-01-02", '%Y-%m-%d'),
            rate_value=1.12
        )
        CurrencyExchangeRate.objects.create(
            source_currency=eur,
            exchanged_currency=usd,
            valuation_date=datetime.strptime("2020-01-03", '%Y-%m-%d'),
            rate_value=1.13
        )
        Provider.objects.create(name='Provider 1', access_key='123', priority=1, is_default=True,
                                historical_hardcoded_json={
                                    'rates': {
                                        '2020-01-01': {
                                            "AUD": 1.11,
                                        },
                                        '2020-01-02': {
                                            "AUD": 2.22,
                                        }
                                    },
                                    'success': True,
                                })
        Provider.objects.create(name='Provider 2', access_key='123', priority=2, is_default=True,
                                historical_hardcoded_json={
                                    'rates': {
                                        '2020-01-01': {
                                            "ABC": 0.05,
                                        },
                                    },
                                    'success': True,
                                })
        Provider.objects.create(name='Provider 3', access_key='123', priority=3, is_default=False,
                                historical_hardcoded_json={
                                    'rates': {
                                        '2020-01-02': {
                                            "GBP": 10,
                                        }
                                    },
                                    'success': True,
                                })
        self.assertEqual([p.name for p in Provider.objects.all()], ['Provider 2', 'Provider 1', 'Provider 3'])
        response = self.client.get(
            '/v1/calculate-exchange/',
            data={"source_currency": "EUR", "amount": 2, "exchanged_currency": "USD"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'success': True, 'value': 2 * 1.13})
        response = self.client.get(
            '/v1/calculate-exchange/',
            data={"source_currency": "EUR", "amount": 2, "exchanged_currency": "GBP", "provider": "Provider 3"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'success': True, 'value': 2 * 10})
        response = self.client.get(
            '/v1/calculate-exchange/',
            data={"source_currency": "EUR", "amount": 2, "exchanged_currency": "FGH", "provider": "Provider 3"},
        )
        self.assertEqual(response.status_code, 400)
        self.assertEqual(response.content, b'Could not convert the currency')
        Currency.objects.create(code="ABC", name="ABC", symbol="ABC")
        response = self.client.get(
            '/v1/calculate-exchange/',
            data={"source_currency": "EUR", "amount": 2, "exchanged_currency": "ABC", "provider": "Provider 3"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'success': True, 'value': 2 * 0.05})

    def test_time_weighted_exchange(self):
        usd = Currency.objects.create(code="USD", name="US Dollar", symbol="$")
        eur = Currency.objects.create(code="EUR", name="Euro", symbol="€")
        CurrencyExchangeRate.objects.create(
            source_currency=eur,
            exchanged_currency=usd,
            valuation_date=datetime.strptime("2020-01-01", '%Y-%m-%d'),
            rate_value=1.11
        )
        CurrencyExchangeRate.objects.create(
            source_currency=eur,
            exchanged_currency=usd,
            valuation_date=datetime.strptime("2020-01-02", '%Y-%m-%d'),
            rate_value=1.12
        )
        CurrencyExchangeRate.objects.create(
            source_currency=eur,
            exchanged_currency=usd,
            valuation_date=datetime.strptime("2020-01-03", '%Y-%m-%d'),
            rate_value=1.13
        )
        response = self.client.get(
            '/v1/calculate-exchange-twrr/',
            data={"source_currency": "EUR", "amount": 2, "exchanged_currency": "USD", "start_date": "2020-01-01"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'success': True, 'values': {
            "2020-01-01": 2 * 1.11,
            "2020-01-02": 2 * 1.12,
            "2020-01-03": 2 * 1.13,
        }})
        response = self.client.get(
            '/v1/calculate-exchange-twrr/',
            data={"source_currency": "EUR", "amount": 2, "exchanged_currency": "USD", "start_date": "2020-01-02"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'success': True, 'values': {
            "2020-01-02": 2 * 1.12,
            "2020-01-03": 2 * 1.13,
        }})
        response = self.client.get(
            '/v1/calculate-exchange-twrr/',
            data={"source_currency": "EUR", "amount": 2, "exchanged_currency": "USD", "start_date": "2020-01-03"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {
            'success': True, 'values': {
                "2020-01-03": 2 * 1.13
            }
        })
        response = self.client.get(
            '/v1/calculate-exchange-twrr/',
            data={"source_currency": "EUR", "amount": 2, "exchanged_currency": "ABC", "start_date": "2020-01-03"},
        )
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'values': {}, 'success': True})

    @patch('default_app.models.requests.get')
    def test_fixer_provider(self, mock_requests_get):
        today_date = datetime.now().strftime("%Y-%m-%d")
        usd_rate_1 = 1.322891
        usd_rate_2 = 1.315066
        usd_rate_3 = 1.314491
        usd_rate_latest = 1.23396
        def side_effect_mock_requests_get(url, *args):
            if 'api/timeseries' in url:
                if 'start_date=2020-01-01' in url:
                    start_date = '2020-01-01'
                    self.assertEqual(url, 'http://data.fixer.io/api/timeseries?access_key=asd&base=EUR&start_date=2020-01-01&end_date=' + today_date)
                else:
                    start_date = '2020-01-02'
                    self.assertEqual(url, 'http://data.fixer.io/api/timeseries?access_key=asd&base=EUR&start_date=2020-01-02&end_date=' + today_date)
                js = {
                    "success": True,
                    "timeseries": True,
                    "start_date": start_date,
                    "end_date": today_date,
                    "base": "EUR",
                    "rates": {
                        "2020-01-01": {
                        "USD": usd_rate_1,
                        "AUD": 1.278047,
                        "CAD": 1.302303
                        },
                        "2020-01-02": {
                            "USD": usd_rate_2,
                            "AUD": 1.274202,
                            "CAD": 1.299083
                        },
                        "2020-01-03": {
                            "USD": usd_rate_3,
                            "AUD": 1.280135,
                            "CAD": 1.296868
                        },
                    }
                }
                if start_date == '2020-01-02':
                    del js['rates']['2020-01-01']
                return MockResponse(js)
            else:
                self.assertEqual(url, 'http://data.fixer.io/api/latest?access_key=asd&base=EUR')
                return MockResponse(js={
                    "success": True,
                    "timestamp": 1519296206,
                    "base": "EUR",
                    "date": today_date,
                    "rates": {
                        "AUD": 1.566015,
                        "CAD": 1.560132,
                        "CHF": 1.154727,
                        "CNY": 7.827874,
                        "GBP": 0.882047,
                        "JPY": 132.360679,
                        "USD": usd_rate_latest,
                    }
                })
        mock_requests_get.side_effect = side_effect_mock_requests_get
        self.assertEqual(mock_requests_get.call_count, 0)
        Provider.objects.create(
            name='Fixer', access_key='asd', priority=1, is_default=True,
            timeseries_endpoint='http://data.fixer.io/api/timeseries?access_key={0}&base={1}&start_date={2}&end_date={3}',
            latest_endpoint='http://data.fixer.io/api/latest?access_key={0}&base={1}'
        )
        response = self.client.get(
            '/v1/calculate-exchange-twrr/',
            data={"source_currency": "EUR", "amount": 2, "exchanged_currency": "ABC", "start_date": "2020-01-01"},
        )
        self.assertEqual(mock_requests_get.call_count, 1)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'values': {}, 'success': True})
        # Checking cache works
        response = self.client.get(
            '/v1/calculate-exchange-twrr/',
            data={"source_currency": "EUR", "amount": 2, "exchanged_currency": "USD", "start_date": "2020-01-01"},
        )
        self.assertEqual(mock_requests_get.call_count, 1) # No new call because of cache
        response = self.client.get(
            '/v1/calculate-exchange-twrr/',
            data={"source_currency": "EUR", "amount": 2, "exchanged_currency": "USD", "start_date": "2020-01-01"},
        )
        self.assertEqual(mock_requests_get.call_count, 1) # No new call because of cache
        # Sleep and check cache was already lost
        time.sleep(5)
        response = self.client.get(
            '/v1/calculate-exchange-twrr/',
            data={"source_currency": "EUR", "amount": 2, "exchanged_currency": "USD", "start_date": "2020-01-01"},
        )
        self.assertEqual(mock_requests_get.call_count, 2) # New call
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'success': True, 'values': {
            '2020-01-01': 2 * usd_rate_1,
            '2020-01-02': 2 * usd_rate_2,
            '2020-01-03': 2 * usd_rate_3
        }})

        response = self.client.get(
            '/v1/calculate-exchange/',
            data={"source_currency": "EUR", "amount": 2, "exchanged_currency": "USD"},
        )
        self.assertEqual(mock_requests_get.call_count, 3)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'value': 2 * usd_rate_latest, 'success': True})

        response = self.client.get(
            '/v1/rates-for-time-period/',
            data={"source_currency": "EUR", "exchanged_currency": "USD", "date_from": "2020-01-02"},
        )
        self.assertEqual(mock_requests_get.call_count, 4)
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'success': True, 'rates': {
            # '2020-01-01': {'AUD': 1.278047, 'CAD': 1.302303, 'USD': usd_rate_1},
            '2020-01-02': {'AUD': 1.274202, 'CAD': 1.299083, 'USD': usd_rate_2},
            '2020-01-03': {'AUD': 1.280135, 'CAD': 1.296868, 'USD': usd_rate_3}
        }})

        response = self.client.get(
            '/v1/current-rate-conversion/',
            data={"source_currency": "EUR"},
        )
        self.assertEqual(mock_requests_get.call_count, 4) # No new call because of cache
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'success': True, 'rates': {
            'AUD': 1.566015,
            'CAD': 1.560132,
            'CHF': 1.154727,
            'CNY': 7.827874,
            'GBP': 0.882047,
            'JPY': 132.360679,
            'USD': usd_rate_latest
        }})

        # default provider is stored data if not specified
        CurrencyExchangeRate.objects.create(
            source_currency=Currency.objects.create(code="EUR", name="Euro", symbol="€"),
            exchanged_currency=Currency.objects.create(code="USD", name="USD Dollar", symbol="$"),
            valuation_date=datetime.strptime("2019-01-01", '%Y-%m-%d'),
            rate_value=5
        )
        response = self.client.get(
            '/v1/current-rate-conversion/',
            data={"source_currency": "EUR"},
        )
        self.assertEqual(mock_requests_get.call_count, 4) # No new call because of cache
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'success': True, 'rates': {
            'USD': 5
        }})
        # Specifying provider
        response = self.client.get(
            '/v1/current-rate-conversion/',
            data={"source_currency": "EUR", "provider": "Fixer"},
        )
        self.assertEqual(mock_requests_get.call_count, 4) # No new call because of cache
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'success': True, 'rates': {
            'AUD': 1.566015,
            'CAD': 1.560132,
            'CHF': 1.154727,
            'CNY': 7.827874,
            'GBP': 0.882047,
            'JPY': 132.360679,
            'USD': usd_rate_latest
        }})
        # If not found stored data, using Fixer
        def side_effect_mock_requests_get(url, *args):
            self.assertEqual(url, 'http://data.fixer.io/api/latest?access_key=asd&base=ABC')
            return MockResponse(js={
                "success": True,
                "timestamp": 1519296206,
                "base": "ABC",
                "date": today_date,
                "rates": {
                    "USD": usd_rate_latest,
                }
            })
        mock_requests_get.side_effect = side_effect_mock_requests_get
        response = self.client.get(
            '/v1/current-rate-conversion/',
            data={"source_currency": "ABC"},
        )
        self.assertEqual(mock_requests_get.call_count, 5) # New call because url changed
        self.assertEqual(response.status_code, 200)
        self.assertEqual(response.json(), {'success': True, 'rates': {
            'USD': usd_rate_latest
        }})


from default_app.websocket import GraphConsumer
import json
from channels.testing import WebsocketCommunicator
from channels.routing import URLRouter
from django.urls import path
from asgiref.sync import sync_to_async


@sync_to_async
def get_or_create_exchange_rate(curr_from, curr_to, valuation_date, rate):
    return CurrencyExchangeRate.objects.create(
        source_currency=Currency.objects.get_or_create(code=curr_from, name=curr_from, symbol=curr_from)[0],
        exchanged_currency=Currency.objects.get_or_create(code=curr_to, name=curr_to, symbol=curr_to)[0],
        valuation_date=valuation_date,
        rate_value=rate
    )


class WebsocketAccountConnectionTests(APITestCase):

    def setUp(self):
        self.maxDiff = None
        pass

    async def test_websocket_application(self):
        application = URLRouter(
            [path("testws/graph/", GraphConsumer.as_asgi())]
        )
        # Bad url does not connect
        communicator = WebsocketCommunicator(application, "ws/")
        with self.assertRaises(Exception) as exc:
            connected, subprotocol = await communicator.connect(5)
        self.assertTrue(isinstance(exc.exception, ValueError))
        self.assertEqual(str(exc.exception), "No route found for path 'ws/'.")
        # Url needs base_currency
        communicator = WebsocketCommunicator(application, "testws/graph/")
        connected, subprotocol = await communicator.connect(2)
        self.assertFalse(connected)
        # Good url with base_currency connects properly
        communicator = WebsocketCommunicator(application, "testws/graph/?base_currency=EUR")
        connected, subprotocol = await communicator.connect(2)
        self.assertTrue(connected)
        # Check receive event after exchange rate created
        # First creation
        await get_or_create_exchange_rate('EUR', 'USD', datetime.strptime('2020-01-01', '%Y-%m-%d'), 1.11)
        received_nothing = await communicator.receive_nothing(2)
        self.assertFalse(received_nothing)
        received_event = await communicator.receive_from(2)
        received_json = json.loads(received_event)
        self.assertEqual(
            received_json,
            {
                'new_exchange_rate': {
                    'exchanged_currency': 'USD',
                    'rate_value': '1.11',
                    'source_currency': 'EUR',
                    'valuation_date': '2020-01-01'
                }
            }
        )
        # Second creation
        await get_or_create_exchange_rate('EUR', 'AUD', datetime.strptime('2018-01-01', '%Y-%m-%d'), 2.1234)
        received_nothing = await communicator.receive_nothing(2)
        self.assertFalse(received_nothing)
        received_event = await communicator.receive_from(2)
        received_json = json.loads(received_event)
        self.assertEqual(
            received_json,
            {
                'new_exchange_rate': {
                    'exchanged_currency': 'AUD',
                    'rate_value': '2.1234',
                    'source_currency': 'EUR',
                    'valuation_date': '2018-01-01'
                }
            }
        )
        # Check that if currency_from is not EUR, it does not send the event
        await get_or_create_exchange_rate('USD', 'EUR', datetime.strptime('2018-01-01', '%Y-%m-%d'), 2.1234)
        received_nothing = await communicator.receive_nothing(2)
        self.assertTrue(received_nothing)