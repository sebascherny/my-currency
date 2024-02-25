from rest_framework import viewsets, mixins
from .models import Currency, CurrencyExchangeRate, Provider
from .serializers import CurrencySerializer, CurrencyExchangeRateSerializer
from django.http import JsonResponse, HttpResponseBadRequest
from .providers import MockProvider, StoredDataProvider
from rest_framework.decorators import api_view
import datetime
from django.shortcuts import render
from rest_framework import status
from rest_framework.response import Response


class CurrencyViewSet(viewsets.ModelViewSet):
    queryset = Currency.objects.all()
    serializer_class = CurrencySerializer
    lookup_field = 'code'


def _get_data_and_errors_for_exchange_rate_creation(data, is_partial=False):
    errors = []
    new_data = {}
    if 'source_currency' in data:
        source_currency_instance = Currency.objects.filter(code=data['source_currency']).first()
        if source_currency_instance:
            new_data['source_currency'] = source_currency_instance.id
        else:
            errors.append('source_currency {} is unknown.'.format(data['source_currency']))
    elif not is_partial:
        errors.append('source_currency is required.')
    if 'exchanged_currency' in data:
        exchanged_currency_instance = Currency.objects.filter(code=data['exchanged_currency']).first()
        if exchanged_currency_instance:
            new_data['exchanged_currency'] = exchanged_currency_instance.id
        else:
            errors.append('exchanged_currency {} is unknown.'.format(data['exchanged_currency']))
    elif not is_partial:
        errors.append('exchanged_currency is required.')
    if 'valuation_date' in data:
        try:
            new_data['valuation_date'] = datetime.datetime.strptime(data['valuation_date'], '%Y-%m-%d').date()
        except ValueError:
            errors.append('valuation_date {} is not in the format YYYY-MM-DD.'.format(data['valuation_date']))
    elif not is_partial:
        errors.append('valuation_date is required.')
    if 'rate_value' in data:
        try:
            new_data['rate_value'] = float(data['rate_value'])
        except ValueError:
            errors.append('rate_value {} is not a number.'.format(data['rate_value']))
    elif not is_partial:
        errors.append('rate_value is required.')
    return new_data, errors


class CurrencyExchangeRateViewSet(viewsets.ModelViewSet):
    queryset = CurrencyExchangeRate.objects.all()
    serializer_class = CurrencyExchangeRateSerializer
    lookup_field = 'id'

    def create(self, request, *args, **kwargs):
        data, errors = _get_data_and_errors_for_exchange_rate_creation(request.data.dict())
        if errors:
            return Response({'errors': errors}, status=status.HTTP_400_BAD_REQUEST)
        serializer = self.get_serializer(data=data)
        if serializer.is_valid(raise_exception=False):
            super().perform_create(serializer)
            headers = super().get_success_headers(serializer.data)
            return Response(serializer.data, status=status.HTTP_201_CREATED, headers=headers)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

    def update(self, request, *args, **kwargs):
        data, errors = _get_data_and_errors_for_exchange_rate_creation(request.data.dict(), is_partial=True)
        if errors:
            return Response({'errors': errors}, status=status.HTTP_400_BAD_REQUEST)
        serializer = self.get_serializer(self.get_object(), data=data, partial=True)
        if serializer.is_valid(raise_exception=False):
            self.perform_update(serializer)
            return Response(serializer.data, status=status.HTTP_200_OK)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


# def get_exchange_rate_data(source_currency, exchanged_currency, valuation_date, provider)


def get_sorted_provider_list(provider_name):
    first_providers = []
    if provider_name:
        first_providers.append(Provider.objects.get(name=provider_name))
    first_providers.append(StoredDataProvider())
    return first_providers + list(Provider.objects.exclude(name=provider_name)) + [MockProvider()]


def get_rates_dict_from_some_provider(provider_name, source_currency, date_from=None, date_to=None, exchanged_currency=None):
    for provider in get_sorted_provider_list(provider_name):
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
        amount = float(data.get('amount') or '1')
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
        amount = float(data.get('amount') or '1')
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