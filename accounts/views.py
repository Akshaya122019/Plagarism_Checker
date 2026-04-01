from django.contrib.auth.models import User
from django.contrib.auth import logout, login, authenticate
from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from rest_framework import generics, status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import RegisterSerializer, UserSerializer, CustomTokenSerializer
from .models import UserProfile


# ── API: Register ────────────────────────────────────────────
class RegisterAPIView(generics.CreateAPIView):
    queryset = User.objects.all()
    serializer_class = RegisterSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        # Create Django session too
        login(request, user)
        refresh = RefreshToken.for_user(user)
        return Response({
            'message': 'Registration successful.',
            'user': UserSerializer(user).data,
            'access': str(refresh.access_token),
            'refresh': str(refresh),
        }, status=status.HTTP_201_CREATED)


# ── API: Login (JWT + Session) — FIXED ───────────────────────
class LoginAPIView(APIView):
    permission_classes = [AllowAny]

    def post(self, request):
        username = request.data.get('username', '').strip()
        password = request.data.get('password', '').strip()

        if not username or not password:
            return Response(
                {'detail': 'Username and password are required.'},
                status=status.HTTP_400_BAD_REQUEST
            )

        # Authenticate user
        user = authenticate(request, username=username, password=password)

        if user is None:
            return Response(
                {'detail': 'Invalid username or password.'},
                status=status.HTTP_401_UNAUTHORIZED
            )

        if not user.is_active:
            return Response(
                {'detail': 'This account has been disabled.'},
                status=status.HTTP_403_FORBIDDEN
            )

        # Create Django session (fixes @login_required)
        login(request, user)

        # Generate JWT tokens
        refresh = RefreshToken.for_user(user)

        return Response({
            'access': str(refresh.access_token),
            'refresh': str(refresh),
            'username': user.username,
            'email': user.email,
            'is_staff': user.is_staff,
        }, status=status.HTTP_200_OK)


# ── API: Logout ──────────────────────────────────────────────
class LogoutAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get('refresh')
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
        except Exception:
            pass
        logout(request)
        return Response({'message': 'Logged out successfully.'})


# ── API: Profile ─────────────────────────────────────────────
class ProfileAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)

    def put(self, request):
        user = request.user
        data = request.data
        user.first_name = data.get('first_name', user.first_name)
        user.last_name = data.get('last_name', user.last_name)
        user.save()
        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile.organization = data.get('organization', profile.organization)
        profile.phone = data.get('phone', profile.phone)
        profile.save()
        return Response({'message': 'Profile updated successfully.'})


# ── Template views ───────────────────────────────────────────
def login_page(request):
    if request.user.is_authenticated:
        return redirect('/checker/')
    return render(request, 'accounts/login.html')


def register_page(request):
    if request.user.is_authenticated:
        return redirect('/checker/')
    return render(request, 'accounts/register.html')


def logout_view(request):
    # Blacklist JWT token if provided
    refresh_token = request.COOKIES.get('refresh_token')
    if refresh_token:
        try:
            token = RefreshToken(refresh_token)
            token.blacklist()
        except Exception:
            pass
    logout(request)
    return redirect('/accounts/login/')


@login_required
def profile_page(request):
    return render(request, 'accounts/profile.html')