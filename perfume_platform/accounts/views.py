from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import RegisterSerializer
from .models import User
import bcrypt

class RegisterView(APIView):
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
    