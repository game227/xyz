"""WebSocket consumers: WebRTC signaling + live chat."""
import json

from asgiref.sync import sync_to_async
from channels.generic.websocket import AsyncWebsocketConsumer

from .models import LiveChatMessage, LiveSession


class LiveConsumer(AsyncWebsocketConsumer):
    async def connect(self):
        self.user = self.scope.get('user')
        if not self.user or not self.user.is_authenticated:
            await self.close()
            return

        self.session_id = self.scope['url_route']['kwargs']['session_id']
        self.room_group = f'live_{self.session_id}'
        await self.channel_layer.group_add(self.room_group, self.channel_name)
        await self.accept()
        await self.channel_layer.group_send(
            self.room_group,
            {
                'type': 'signal.message',
                'payload': {
                    'type': 'peer-join',
                    'from': self.channel_name,
                    'user': self._username(),
                },
                'exclude': self.channel_name,
            },
        )

    async def disconnect(self, close_code):
        if not getattr(self, 'room_group', None):
            return
        await self.channel_layer.group_send(
            self.room_group,
            {
                'type': 'signal.message',
                'payload': {
                    'type': 'peer-leave',
                    'from': self.channel_name,
                },
                'exclude': self.channel_name,
            },
        )
        await self.channel_layer.group_discard(self.room_group, self.channel_name)

    async def receive(self, text_data=None, bytes_data=None):
        if not text_data:
            return
        try:
            data = json.loads(text_data)
        except json.JSONDecodeError:
            return

        msg_type = data.get('type')
        if msg_type == 'chat':
            text = (data.get('text') or '').strip()[:500]
            if not text or not self.user or not self.user.is_authenticated:
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': 'Chat uchun tizimga kiring.',
                }))
                return
            saved = await self._save_chat(text)
            if not saved:
                await self.send(text_data=json.dumps({
                    'type': 'error',
                    'message': 'Efir jonli emas — chat yopiq.',
                }))
                return
            await self.channel_layer.group_send(
                self.room_group,
                {
                    'type': 'signal.message',
                    'payload': {
                        'type': 'chat',
                        'user': saved['user'],
                        'text': saved['text'],
                        'is_teacher': saved['is_teacher'],
                        'created': saved['created'],
                    },
                },
            )
            return

        if msg_type in {'offer', 'answer', 'ice', 'host-ready', 'viewer-ready'}:
            data['from'] = self.channel_name
            target = data.get('to')
            await self.channel_layer.group_send(
                self.room_group,
                {
                    'type': 'signal.message',
                    'payload': data,
                    'exclude': None if target else self.channel_name,
                    'only': target,
                },
            )

    async def signal_message(self, event):
        payload = event['payload']
        only = event.get('only')
        exclude = event.get('exclude')
        if only and only != self.channel_name:
            return
        if exclude and exclude == self.channel_name:
            return
        await self.send(text_data=json.dumps(payload))

    def _username(self):
        if self.user and self.user.is_authenticated:
            return self.user.get_full_name() or self.user.username
        return 'Mehmon'

    @sync_to_async
    def _save_chat(self, text):
        session = LiveSession.objects.filter(pk=self.session_id).first()
        if not session or session.status != LiveSession.Status.LIVE:
            return None
        is_teacher = (
            self.user.pk == session.host_id
            or getattr(self.user, 'can_manage_content', False)
        )
        msg = LiveChatMessage.objects.create(
            session=session,
            user=self.user,
            text=text,
            is_from_teacher=is_teacher,
        )
        return {
            'user': self.user.get_full_name() or self.user.username,
            'text': msg.text,
            'is_teacher': msg.is_from_teacher,
            'created': msg.created_at.strftime('%H:%M'),
        }
