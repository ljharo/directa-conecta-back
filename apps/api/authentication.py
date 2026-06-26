import hmac
from django.conf import settings
from rest_framework.authentication import BaseAuthentication
from rest_framework.exceptions import AuthenticationFailed


class APIKeyAuthentication(BaseAuthentication):
    def authenticate(self, request):
        auth_header = request.META.get('HTTP_AUTHORIZATION', '')
        if not auth_header.startswith('Bearer '):
            raise AuthenticationFailed('API key requerida. Header: Authorization: Bearer <key>')

        key = auth_header.split(' ', 1)[1].strip()
        expected = settings.API_KEY_BOT

        if not expected:
            raise AuthenticationFailed('API key no configurada en el servidor.')

        if not hmac.compare_digest(key, expected):
            raise AuthenticationFailed('API key inválida.')

        # Retornamos un objeto mínimo como "usuario autenticado"
        return (_BotUser(), None)


class _BotUser:
    """Usuario sintético para el bot — no es un User de Django."""
    is_authenticated = True
    is_anonymous = False
    pk = None
