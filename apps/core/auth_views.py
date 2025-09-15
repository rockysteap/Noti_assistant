"""
Authentication views for the Noti project.
"""

from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.authtoken.models import Token
from rest_framework.authtoken.serializers import AuthTokenSerializer
from django.contrib.auth import authenticate, login, logout
from django.contrib.auth.models import User
from django.utils import timezone
from .models import UserProfile, AuditLog
from .serializers import UserSerializer, UserProfileSerializer
import json


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def login_view(request):
    """
    User login endpoint.
    """
    serializer = AuthTokenSerializer(data=request.data)
    if serializer.is_valid():
        user = serializer.validated_data['user']
        token, created = Token.objects.get_or_create(user=user)
        
        # Log the login
        AuditLog.objects.create(
            user=user,
            action='login',
            resource='auth',
            ip_address=request.META.get('REMOTE_ADDR'),
            user_agent=request.META.get('HTTP_USER_AGENT', ''),
        )
        
        return Response({
            'token': token.key,
            'user': UserSerializer(user).data,
            'profile': UserProfileSerializer(
                user.profile, 
                context={'request': request}
            ).data if hasattr(user, 'profile') else None
        })
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def logout_view(request):
    """
    User logout endpoint.
    """
    # Log the logout
    AuditLog.objects.create(
        user=request.user,
        action='logout',
        resource='auth',
        ip_address=request.META.get('REMOTE_ADDR'),
        user_agent=request.META.get('HTTP_USER_AGENT', ''),
    )
    
    # Delete the token
    try:
        request.user.auth_token.delete()
    except:
        pass
    
    return Response({'message': 'Successfully logged out'})


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def register_view(request):
    """
    User registration endpoint.
    """
    data = request.data
    
    # Validate required fields
    required_fields = ['username', 'email', 'password']
    for field in required_fields:
        if field not in data:
            return Response(
                {field: ['This field is required.']}, 
                status=status.HTTP_400_BAD_REQUEST
            )
    
    # Check if user already exists
    if User.objects.filter(username=data['username']).exists():
        return Response(
            {'username': ['A user with this username already exists.']},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    if User.objects.filter(email=data['email']).exists():
        return Response(
            {'email': ['A user with this email already exists.']},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Create user
    user = User.objects.create_user(
        username=data['username'],
        email=data['email'],
        password=data['password'],
        first_name=data.get('first_name', ''),
        last_name=data.get('last_name', ''),
    )
    
    # Create user profile
    UserProfile.objects.create(
        user=user,
        timezone=data.get('timezone', 'UTC'),
        language=data.get('language', 'en'),
    )
    
    # Create token
    token = Token.objects.create(user=user)
    
    # Log the registration
    AuditLog.objects.create(
        user=user,
        action='create',
        resource='user',
        ip_address=request.META.get('REMOTE_ADDR'),
        user_agent=request.META.get('HTTP_USER_AGENT', ''),
    )
    
    return Response({
        'token': token.key,
        'user': UserSerializer(user).data,
        'profile': UserProfileSerializer(
            user.profile, 
            context={'request': request}
        ).data
    }, status=status.HTTP_201_CREATED)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def change_password_view(request):
    """
    Change password endpoint.
    """
    data = request.data
    
    if 'old_password' not in data or 'new_password' not in data:
        return Response(
            {'error': 'old_password and new_password are required.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Verify old password
    if not request.user.check_password(data['old_password']):
        return Response(
            {'old_password': ['Incorrect password.']},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Set new password
    request.user.set_password(data['new_password'])
    request.user.save()
    
    # Log the password change
    AuditLog.objects.create(
        user=request.user,
        action='update',
        resource='password',
        ip_address=request.META.get('REMOTE_ADDR'),
        user_agent=request.META.get('HTTP_USER_AGENT', ''),
    )
    
    return Response({'message': 'Password changed successfully'})


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def telegram_auth_view(request):
    """
    Telegram authentication endpoint.
    """
    telegram_data = request.data.get('telegram_data')
    if not telegram_data:
        return Response(
            {'error': 'telegram_data is required.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # This would typically be handled by the TelegramAuthentication class
    # For now, we'll create a simple implementation
    telegram_id = telegram_data.get('id')
    if not telegram_id:
        return Response(
            {'error': 'Telegram ID is required.'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Get or create Telegram user
    from apps.telegram_bot.models import TelegramUser
    
    try:
        telegram_user = TelegramUser.objects.get(telegram_id=telegram_id)
        user = telegram_user.user
    except TelegramUser.DoesNotExist:
        # Create new user and Telegram user
        username = telegram_data.get('username', f'telegram_{telegram_id}')
        user = User.objects.create_user(
            username=username,
            first_name=telegram_data.get('first_name', ''),
            last_name=telegram_data.get('last_name', ''),
        )
        
        # Create user profile
        UserProfile.objects.create(
            user=user,
            timezone=telegram_data.get('timezone', 'UTC'),
            language=telegram_data.get('language_code', 'en'),
        )
        
        # Create Telegram user
        telegram_user = TelegramUser.objects.create(
            user=user,
            telegram_id=telegram_id,
            username=telegram_data.get('username', ''),
            first_name=telegram_data.get('first_name', ''),
            last_name=telegram_data.get('last_name', ''),
            language_code=telegram_data.get('language_code', 'en'),
        )
    
    # Create or get token
    token, created = Token.objects.get_or_create(user=user)
    
    # Log the Telegram authentication
    AuditLog.objects.create(
        user=user,
        action='login',
        resource='telegram_auth',
        details={'telegram_id': telegram_id},
        ip_address=request.META.get('REMOTE_ADDR'),
        user_agent=request.META.get('HTTP_USER_AGENT', ''),
    )
    
    return Response({
        'token': token.key,
        'user': UserSerializer(user).data,
        'profile': UserProfileSerializer(
            user.profile, 
            context={'request': request}
        ).data if hasattr(user, 'profile') else None,
        'telegram_user': {
            'telegram_id': telegram_user.telegram_id,
            'username': telegram_user.username,
            'is_verified': telegram_user.is_verified,
        }
    })


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def user_info_view(request):
    """
    Get current user information.
    """
    user_data = UserSerializer(request.user).data
    profile_data = None
    
    if hasattr(request.user, 'profile'):
        profile_data = UserProfileSerializer(
            request.user.profile, 
            context={'request': request}
        ).data
    
    telegram_data = None
    if hasattr(request.user, 'telegram_user'):
        telegram_user = request.user.telegram_user
        telegram_data = {
            'telegram_id': telegram_user.telegram_id,
            'username': telegram_user.username,
            'is_verified': telegram_user.is_verified,
        }
    
    return Response({
        'user': user_data,
        'profile': profile_data,
        'telegram': telegram_data,
    })
