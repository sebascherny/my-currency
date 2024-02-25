"""
URL configuration for my_currency project.

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/4.2/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  path('', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  path('', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.urls import include, path
    2. Add a URL to urlpatterns:  path('blog/', include('blog.urls'))
"""
from django.contrib import admin
from django.urls import path, re_path, include
from rest_framework.routers import DefaultRouter
from default_app.views import CurrencyViewSet, CurrencyExchangeRateViewSet, \
    get_list_of_rates_for_time_period, currency_converter, get_time_weighted_exchange, currency_converter_for_all_currencies, \
        history_conversion_graph_view, current_conversion_view


router = DefaultRouter()
router.register(r'currencies', CurrencyViewSet)
router.register(r'currency_exchange_rates', CurrencyExchangeRateViewSet)

urlpatterns = [
    path('', include(router.urls)),
]


urlpatterns = [
    path("admin/", admin.site.urls),
    path('', include(router.urls)),
    path('history-graph/', history_conversion_graph_view, name='history_conversion_graph'),
    path('current-conversion/', current_conversion_view, name='current_conversion'),
    re_path(r'^v1/rates-for-time-period/', get_list_of_rates_for_time_period),
    re_path(r'^v1/calculate-exchange/', currency_converter),
    re_path(r'^v1/calculate-exchange-twrr/', get_time_weighted_exchange),
    re_path(r'^v1/current-rate-conversion/', currency_converter_for_all_currencies),
]
