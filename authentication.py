from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import AuthenticationFailed, InvalidToken

from .models import User


class CustomJWTAuthentication(JWTAuthentication):
    """
    LoginView (accounts/views.py) issues access tokens carrying a 'user_id'
    claim that points at our own `user` table (accounts.models.User), NOT at
    Django's built-in auth.User. The default JWTAuthentication.get_user()
    looks the token up against django.contrib.auth's user model instead, so
    request.user would resolve to the wrong table (or fail entirely).

    This subclass resolves the token against accounts.models.User instead,
    so anything using this authentication class gets the real logged-in
    customer on request.user.
    """

    def get_user(self, validated_token):
        user_id = validated_token.get('user_id')
        if user_id is None:
            raise InvalidToken('Token contained no recognizable user identification.')

        try:
            user = User.objects.get(user_id=user_id)
        except User.DoesNotExist:
            raise AuthenticationFailed('User not found.', code='user_not_found')

        if not user.is_active:
            raise AuthenticationFailed('This account has been deactivated.', code='user_inactive')

        # accounts.models.User is a plain (non-auth) model, so it doesn't
        # have the is_authenticated attribute DRF's IsAuthenticated permission
        # checks for. Set it here rather than on the model itself.
        user.is_authenticated = True
        return user
