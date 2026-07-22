<<<<<<< HEAD
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.permissions import AllowAny
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import RegisterSerializer
from .models import User
import bcrypt

class RegisterView(APIView):
    # Registering an account has to work without being logged in already -
    # explicit here because the project-wide default permission is now
    # IsAuthenticated (see REST_FRAMEWORK settings).
    permission_classes = [AllowAny]

    def post(self, request):
        serializer = RegisterSerializer(data=request.data)
        if serializer.is_valid():
            user = serializer.save()
            return Response(
                {"message": "Account created successfully.", "user_id": user.user_id},
                status=status.HTTP_201_CREATED
            )
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class LoginView(APIView):
    # Same reasoning as RegisterView - logging in has to work while
    # logged out, so it opts out of the project-wide IsAuthenticated default.
    permission_classes = [AllowAny]

    def post(self, request):
        email    = request.data.get('email')
        password = request.data.get('password')

        # make sure both fields were actually sent
        if not email or not password:
            return Response(
                {"error": "Email and password are required."},
                status=status.HTTP_400_BAD_REQUEST
            )

        # look up the user by email in your MySQL user table
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response(
                {"error": "Invalid email or password."},
                status=status.HTTP_401_UNAUTHORIZED
            )

        # stop deactivated accounts from logging in
        if not user.is_active:
            return Response(
                {"error": "This account has been deactivated."},
                status=status.HTTP_403_FORBIDDEN
            )

        # check the password the user typed against
        # the hashed version stored in the database
        password_correct = bcrypt.checkpw(
            password.encode('utf-8'),
            user.password_hash.encode('utf-8')
        )

        if not password_correct:
            return Response(
                {"error": "Invalid email or password."},
                status=status.HTTP_401_UNAUTHORIZED
            )

        # password matched — generate a JWT token
        # we build it manually because we use our own
        # custom user table instead of Django's built-in one
        refresh = RefreshToken()
        refresh['user_id']   = user.user_id
        refresh['email']     = user.email
        refresh['role_id']   = user.role_id
        refresh['full_name'] = f"{user.first_name} {user.last_name}"

        return Response({
            "message"  : "Login successful.",
            "user_id"  : user.user_id,
            "full_name": f"{user.first_name} {user.last_name}",
            "email"    : user.email,
            "role_id"  : user.role_id,
            "access"   : str(refresh.access_token),
            "refresh"  : str(refresh),
        }, status=status.HTTP_200_OK)
=======
from django.db import transaction
from django.utils import timezone
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from accounts.authentication import CustomJWTAuthentication
from accounts.models import Cart, CartItem

from .serializers import AddCartItemSerializer, CartSerializer


def _get_or_create_cart(user):
    """Every customer gets exactly one cart (cart table has a UNIQUE user_id)."""
    now = timezone.now()
    cart, _ = Cart.objects.get_or_create(
        user=user,
        defaults={'created_at': now, 'updated_at': now},
    )
    return cart


class CartView(APIView):
    """GET /api/cart/ - view the logged-in customer's cart and its items."""
    authentication_classes = [CustomJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def get(self, request):
        cart = _get_or_create_cart(request.user)
        return Response(CartSerializer(cart).data, status=status.HTTP_200_OK)


class AddCartItemView(APIView):
    """POST /api/cart/items/ - add a product to the logged-in customer's cart."""
    authentication_classes = [CustomJWTAuthentication]
    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = AddCartItemSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        product = serializer.get_product()
        quantity = serializer.validated_data['quantity']
        cart = _get_or_create_cart(request.user)

        with transaction.atomic():
            item, created = CartItem.objects.get_or_create(
                cart=cart,
                product=product,
                defaults={'quantity': quantity, 'added_at': timezone.now()},
            )
            if not created:
                # already in the cart - top up the quantity instead of
                # erroring out on the unique (cart, product) constraint
                item.quantity += quantity
                item.save(update_fields=['quantity'])

            cart.updated_at = timezone.now()
            cart.save(update_fields=['updated_at'])

        response_status = status.HTTP_201_CREATED if created else status.HTTP_200_OK
        return Response(CartSerializer(cart).data, status=response_status)
>>>>>>> e3386a4d74ddeeb9a881026351c901dd539fa312
