import requests

BASE_URL = 'http://localhost:8000/'
CURRENCIES_URL = BASE_URL + 'currencies/'
ONE_CURRENCE_URL = BASE_URL + 'currencies/{}/'

def create_currency(code, name, symbol):
    curr_url = ONE_CURRENCE_URL.format(code)
    existing_curr_response = requests.get(curr_url)
    if existing_curr_response.status_code == 200:
        requests.delete(curr_url)
    existing_curr_response = requests.get(curr_url)
    assert existing_curr_response.status_code == 404
    assert existing_curr_response.json() == {'detail': 'Not found.'}
    curr_response = requests.post(
        CURRENCIES_URL,
        data={'code': code, 'name': name, 'symbol': symbol}
    )
    assert curr_response.status_code == 201

create_currency('CU1', 'Currency 1', 'C1')
create_currency('CU2', 'Currency 2', 'C2')

r = requests.get(CURRENCIES_URL)
assert r.status_code == 200
assert any(x['code'] == 'CU1' and x['name'] == 'Currency 1' and x['symbol'] == 'C1' for x in r.json())
assert any(x['code'] == 'CU2' and x['name'] == 'Currency 2' and x['symbol'] == 'C2' for x in r.json())

r = requests.post(
    BASE_URL + 'currency_exchange_rates/',
    data={
        'source_currency': 'CU1', 'exchanged_currency': 'CU2',
        'rate_value': 1.2, 'valuation_date': '2022-01-01'
    }
)
assert r.status_code == 201
r = requests.put(
    BASE_URL + 'currency_exchange_rates/{}/'.format(r.json()['id']),
    data={'rate_value': '1.2', 'valuation_date': '2022-01-02'}
)
assert r.status_code == 200, r.status_code
assert r.json()['rate_value'] == '1.200000'
assert r.json()['valuation_date'] == '2022-01-02'

print('Finished successfully!')