from django.contrib import admin
from .models import CurrencyExchangeRate, Currency, Provider


class CurrencyExchangeRateModelAdmin(admin.ModelAdmin):
    pass

class CurrencyModelAdmin(admin.ModelAdmin):
    pass

class ProviderModelAdmin(admin.ModelAdmin):
    pass

admin.site.register(CurrencyExchangeRate, CurrencyExchangeRateModelAdmin)
admin.site.register(Currency, CurrencyModelAdmin)
admin.site.register(Provider, ProviderModelAdmin)