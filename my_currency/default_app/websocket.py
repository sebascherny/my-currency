from channels.generic.websocket import AsyncJsonWebsocketConsumer


class GraphConsumer(AsyncJsonWebsocketConsumer):

    async def connect(self):
        if 'base_currency' in self.scope.get('query_string').decode('utf-8'):
            base_currency = self.scope.get('query_string').decode('utf-8').split('=')[1]
            await self.channel_layer.group_add(
                base_currency, self.channel_name
            )
            await self.accept()
        else:
            await self.close()

    async def disconnect(self):
        pass

    async def new_exchange_rate(self, event):
        await self.send_json(
            {
                'new_exchange_rate': event['new_exchange_rate'],
            },
        )

    async def receive(self, text_data):
        if text_data == 'ping':
            await self.send_json({
                'message': 'pong',
            })
