from django.db.models.signals import pre_save, post_save
from django.dispatch import receiver
from .models import CurrencyExchangeRate
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

@receiver(post_save, sender=CurrencyExchangeRate)
def input_created(instance, created, **kwargs):
    if created:
        channel_layer = get_channel_layer()
        instance_json = {
            'source_currency': instance.source_currency.code,
            'exchanged_currency': instance.exchanged_currency.code,
            'valuation_date': instance.valuation_date.strftime('%Y-%m-%d'),
            'rate_value': str(instance.rate_value)
        }
        async_to_sync(channel_layer.group_send)(
                instance.source_currency.code,
                {
                    'type': 'new_exchange_rate',
                    'new_exchange_rate': instance_json
                }
        )
