# my-currency

API for users to calculate currency exchange rates (interview process)

Models: As suggested, we are using the models CurrencyExchangeRate and Currency. Apart from it, the model Provider was created, that can containt either a static historic json data, or urls to obtain the exchange rates from. The urls are cached using the default cache system provided by Django, so that we don't do the same request in a 1-hour window.

Local storage: An external database like postgres or redis could be used, but currently the default storage is local: The database is a SQLite database, which is not good if we wanted to deploy the project but for its current scope it is good enough. It generates a local db.sqlite3 file with the information.

Service: To run it locally use the following commands:

1. Have python and pip installed
2. `python -m venv env`
3. `source env/bin/activate`
4. `pip install -r my_currency/requirements.txt`

Create environment file:

5. `echo "ENV=test" > my_currency/.env`
6. `echo "SECRET_KEY="$(openssl rand -base64 38) >> my_currency/.env`
7. `python my_currency/manage.py makemigrations`
8. `python my_currency/manage.py migrate`
9. `python my_currency/manage.py runserver`


Test:

`source env/bin/activate`

`python my_currency/manage.py test my_currency`

should have all (at least 6) tests successful.
One test will take some seconds because it tests the cache storage.

API Endpoints:
* /v1/rates-for-time-period/
 * Params: 
  * source_currency: 3-letter code like EUR or USD
  * date_from: Day string with format yyyy-mm-dd. Default is 1900-01-01 (to show all historic data)
  * date_to: Same format as date_from. Default is the day of the request.
  * provider: String with the provider name. If it exists in the database, it is the first one that will be tried.
 * Response: Json with keys:
  * success: True
  * rates: Dictionary where the keys are the days in the time period, and their values are also dictionaries with currency codes as keys, rates as values.
  * Examples: {"success": True, "rates": {"2020-01-01": {"USD": 1.1}, "2020-01-02": {"USD": 1.12}}}
* /v1/calculate-exchange/
        * Params: 
            * source_currency: 3-letter code like EUR or USD
            * exchanged_currency: 3-letter code like EUR or USD
            * amount: float number
            * provider: String with the provider name. If it exists in the database, it is the first one that will be tried.
        * Response: Json with keys:
            * success: True
            * value: Amount of "exchanged_currenct" that result from converting (today, or with latest rate) "amount" of "source_currenct".
            * Examples: {"success": True, "value": 1.12}
    - /v1/calculate-exchange-twrr/
        - Params: 
            - source_currency: 3-letter code like EUR or USD
            - start_date: Day string with format yyyy-mm-dd. Default is 1900-01-01 (to show all historic data)
            - provider: String with the provider name. If it exists in the database, it is the first one that will be tried.
            - amount: float number
            - exchanged_currency: 3-letter code like EUR or USD
        - Response: Json with keys:
            - success: True
            - values: Dictionary where the keys are the days in the provider's history that are available, and the values are the converted amount for that day.
            - Examples: {"success": True, "values": {"2020-01-01": 1.1, "2020-01-02": 1.12}}
    - /v1/current-rate-conversion/
        - Params: 
            - source_currency: 3-letter code like EUR or USD
            - provider: String with the provider name. If it exists in the database, it is the first one that will be tried.
        - Response: Json with keys:
            - success: True
            - rates: Dictionary where the keys are the available currencies, rates as values.
            - Examples: {"success": True, "rates": {"USD": 1.1, "AUD": 1.32}}

Back office (Frontends):
    - /history-graph/ (Graph View)
        - Simple frontend where user can select currency_from, currency_to, input an amount.
        - After button is clicked, a graph is displayed with the converted amount for all the historic available dates.
        - Async view: If a graph is displayed and a new CurrencyExchangeRate appears in database (which is the provider that is currently being used, without this being a parameter), then a new point appears on the graph displaying this data.
    - /current-conversion/ (Converter View)
        - Simple frontend to select currency_from and multiple currency_to (for selecting multiple use Ctrl or Command in Mac), and get a table with the current (latest) rates for the selected "currencies_to".

Provider interface:
    - Priority: The providers are sorted thsi way: If a provider is given as parameter, it's the first one that's going to be tries. After that, the "StoredDataProvider" is the one that's going to be used; it basically takes the information from the database, since a requirement mentioned that if data is in the database, it should be used, and if not, then try different providers. After these possibly two providers, the other ones that are in the database (either with urls or a hardcoded json) are sorted by the is_default boolean, and then by priority (greater to lower).
    - Pluggable: The code assumes that the url endpoints work in a similar way as Fixer. So (to avoid code injection), the way it currently works is that a Provider instance can have two endpoints (for historic data and for latest rates), and can also have a hardcoded historic json.
    - Resiliency: As mentioned above, if a Provider does not have information, we use the next one according to is_default and priority.

Mocked data (command in management): A command can fill the database with exchange rates for one currency (param) to a list of hardcoded currencies, for the last days (amount of days is a parameter). Cleaning the data is an option, it's the last parameter and if it is true/True/1/yes, it will erase all the existing data from the database:
`python my_currency/manage.py fill_database_with_random_data EUR 50 true`
That command will clean the database and then create exchange rates for the last 50 days from EUR to the list of currencies already defined in the code.

Async data: A celery worker could be used to scrape data daily from a provider's url, for example, and store it. This is not yet done.

Store data from json file (command in management): A command can fill the database with information from a JSON file, like this:
`python my_currency/manage.py import_exchange_rates my_currency/default_app/historical_rates.json`
That would take the list of ExchangeRates from historical_rates.json and create model instances in the database.