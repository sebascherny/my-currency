from django.contrib import admin
from .models import CurrencyExchangeRate, Currency, Provider, SiteConfiguration


class CurrencyExchangeRateModelAdmin(admin.ModelAdmin):
    autocomplete_fields = ('source_currency', 'exchanged_currency')
    list_display = ('source_currency', 'exchanged_currency', 'valuation_date', 'rate_value')

class CurrencyModelAdmin(admin.ModelAdmin):
    search_fields = ['code']

class ProviderModelAdmin(admin.ModelAdmin):
    pass

admin.site.register(CurrencyExchangeRate, CurrencyExchangeRateModelAdmin)
admin.site.register(Currency, CurrencyModelAdmin)
admin.site.register(Provider, ProviderModelAdmin)
admin.site.register(SiteConfiguration)