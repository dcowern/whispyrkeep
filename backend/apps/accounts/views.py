"""
Account views - Registration and profile management.

Endpoints:
- POST /api/auth/register/ - Create new user account
- GET /api/auth/me/ - Get current user profile
- PUT/PATCH /api/auth/me/ - Update user profile
"""

from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

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
