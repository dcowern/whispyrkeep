"""Account views - Registration and profile management."""

from rest_framework import generics, status
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework.response import Response

from apps.accounts.models import User


class RegisterView(generics.CreateAPIView):
    """POST /api/auth/register - Create new user account."""

    permission_classes = [AllowAny]
    queryset = User.objects.all()

    def create(self, request, *args, **kwargs):
        # Placeholder - will be implemented in ticket 1.1.2
        return Response(
            {"detail": "Registration endpoint - to be implemented"},
            status=status.HTTP_501_NOT_IMPLEMENTED,
        )


class UserProfileView(generics.RetrieveUpdateAPIView):
    """GET/PUT /api/auth/me - Current user profile."""

    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

    def retrieve(self, request, *args, **kwargs):
        # Placeholder - will be implemented in ticket 1.1.3
        return Response(
            {"detail": "Profile endpoint - to be implemented"},
            status=status.HTTP_501_NOT_IMPLEMENTED,
        )
