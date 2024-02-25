from rest_framework import viewsets
from .models import Currency, CurrencyExchangeRate, Provider
from .serializers import CurrencySerializer, CurrencyExchangeRateSerializer
from django.http import JsonResponse, HttpResponseBadRequest
from .providers import MockProvider, StoredDataProvider
from rest_framework.decorators import api_view
import datetime
from django.shortcuts import render


class CurrencyViewSet(viewsets.ModelViewSet):
    queryset = Currency.objects.all()
    serializer_class = CurrencySerializer

class CurrencyExchangeRateViewSet(viewsets.ModelViewSet):
    queryset = CurrencyExchangeRate.objects.all()
    serializer_class = CurrencyExchangeRateSerializer


# def get_exchange_rate_data(source_currency, exchanged_currency, valuation_date, provider)


def get_rates_dict_from_some_provider(provider_name, source_currency, date_from=None, date_to=None, exchanged_currency=None):
    first_providers = []
    if provider_name:
        first_providers.append(Provider.objects.get(name=provider_name))
    first_providers.append(StoredDataProvider())
    for provider in first_providers + list(Provider.objects.exclude(name=provider_name)) + [MockProvider()]:
        if date_from:
            rates = provider.get_rates_dict_timeseries(source_currency, date_from, date_to)
        else:
            rates = provider.get_latest_rates_dict(source_currency)
            if exchanged_currency and rates and exchanged_currency not in rates:
                rates = {}
        if rates:
            return rates
    return {}
    # raise ValueError('No provider could provide the rates for {} (exchanged_currency={})'.format(source_currency, exchanged_currency))


@api_view(['GET'])
def get_list_of_rates_for_time_period(request):
    data = request.query_params.dict()
    source_currency = data.get('source_currency')
    date_from = data.get('date_from')
    date_to = data.get('date_to')
    if not date_from:
        date_from = '1900-01-01'
    if not date_to:
        date_to = datetime.datetime.now().strftime("%Y-%m-%d")
    provider_name = data.get('provider')
    rates = get_rates_dict_from_some_provider(provider_name, source_currency, date_from, date_to)
    if rates:
        return JsonResponse({'success': True, 'rates': rates})
    return HttpResponseBadRequest('Could not convert the currency')


@api_view(['GET'])
def currency_converter(request):
    data = request.query_params.dict()
    source_currency = data.get('source_currency')
    try:
        amount = float(data.get('amount'))
    except ValueError:
        return HttpResponseBadRequest('Amount must be a number')
    exchanged_currency = data.get('exchanged_currency')
    provider_name = data.get('provider')
    rates = get_rates_dict_from_some_provider(provider_name, source_currency, exchanged_currency=exchanged_currency)
    if rates and exchanged_currency in rates:
        return JsonResponse({'success': True, 'value': amount * rates[exchanged_currency]})
    return HttpResponseBadRequest('Could not convert the currency')


@api_view(['GET'])
def currency_converter_for_all_currencies(request):
    data = request.query_params.dict()
    source_currency = data.get('source_currency')
    provider_name = data.get('provider')
    rates = get_rates_dict_from_some_provider(provider_name, source_currency)
    if rates:
        return JsonResponse({'success': True, 'rates': rates})
    return HttpResponseBadRequest('Could not convert the currency')


@api_view(['GET'])
def get_time_weighted_exchange(request):
    data = request.query_params.dict()
    source_currency = data.get('source_currency')
    try:
        amount = float(data.get('amount'))
    except ValueError:
        return HttpResponseBadRequest('Amount must be a number')
    exchanged_currency = data.get('exchanged_currency')
    date_from = data.get('start_date')
    if not date_from:
        date_from = '1900-01-01'
    date_to = datetime.datetime.now().strftime("%Y-%m-%d")
    provider_name = data.get('provider')
    rates = get_rates_dict_from_some_provider(provider_name, source_currency, date_from, date_to)
    if rates:
        twrr_dict = {}
        for date_key in rates:
            if exchanged_currency in rates[date_key]:
                twrr_dict[date_key] = amount * rates[date_key][exchanged_currency]
        return JsonResponse({'success': True, 'values': twrr_dict})
    return HttpResponseBadRequest('Could not convert the currency')



def history_conversion_graph_view(request):
    currencies = Currency.objects.all().values_list('code', flat=True)
    return render(request, 'history_conversion_graph.html', {'currencies': currencies})


def current_conversion_view(request):
    currencies = Currency.objects.all().values_list('code', flat=True)
    return render(request, 'current_conversion_values.html', {'currencies': currencies})