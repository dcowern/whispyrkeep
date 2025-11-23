"""
Account views - Registration, authentication, and profile management.

Endpoints:
- POST /api/auth/register/ - Create new user account
- POST /api/auth/login/ - Login and get JWT tokens
- POST /api/auth/logout/ - Logout and blacklist refresh token
- GET /api/auth/me/ - Get current user profile
- PUT/PATCH /api/auth/me/ - Update user profile
"""

from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.views import TokenObtainPairView

from apps.accounts.models import User
from apps.accounts.serializers import (
    UserProfileSerializer,
    UserRegistrationSerializer,
)


class RegisterView(generics.CreateAPIView):
    """
    POST /api/auth/register - Create new user account.

    Request body:
    {
        "email": "user@example.com",
        "username": "username",
        "password": "securepassword",
        "password_confirm": "securepassword",
        "display_name": "Display Name" (optional)
    }

    Returns:
    - 201: User created successfully
    - 400: Validation errors
    """

    permission_classes = [AllowAny]
    serializer_class = UserRegistrationSerializer
    queryset = User.objects.all()

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()

        return Response(
            {
                "id": str(user.id),
                "email": user.email,
                "username": user.username,
                "display_name": user.display_name,
                "message": "User registered successfully.",
            },
            status=status.HTTP_201_CREATED,
        )


class UserProfileView(generics.RetrieveUpdateAPIView):
    """
    GET/PUT/PATCH /api/auth/me - Current user profile.

    GET returns the current user's profile information.
    PUT/PATCH updates the user's profile (display_name, settings_json).
    """

    permission_classes = [IsAuthenticated]
    serializer_class = UserProfileSerializer

    def get_object(self):
        return self.request.user


class LoginView(TokenObtainPairView):
    """
    POST /api/auth/login - Login and get JWT tokens.

    Request body:
    {
        "email": "user@example.com",
        "password": "password"
    }

    Returns:
    - 200: Login successful with access and refresh tokens
    - 401: Invalid credentials
    """

    permission_classes = [AllowAny]


class LogoutView(APIView):
    """
    POST /api/auth/logout - Logout by blacklisting refresh token.

    Request body:
    {
        "refresh": "refresh_token_string"
    }

    Returns:
    - 200: Logout successful
    - 400: Invalid or missing refresh token
    """

    permission_classes = [IsAuthenticated]

    def post(self, request, *args, **kwargs):
        refresh_token = request.data.get("refresh")

        if not refresh_token:
            return Response(
                {"detail": "Refresh token is required."},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
            return Response(
                {"message": "Logout successful."},
                status=status.HTTP_200_OK,
            )
        except TokenError as e:
            return Response(
                {"detail": str(e)},
                status=status.HTTP_400_BAD_REQUEST,
            )
