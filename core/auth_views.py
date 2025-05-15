# core/auth_views.py
from rest_framework.permissions import AllowAny
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from rest_framework.authtoken.models import Token
from django.contrib.auth import authenticate
from .models import User
from .serializers import UserSerializer
from .email_utils import send_verification_code
import uuid


class LoginView(APIView):
    permission_classes = [AllowAny]
    def post(self, request):
        username = request.data.get('username')
        password = request.data.get('password')

        user = authenticate(username=username, password=password)

        if not user:
            return Response({'error': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)

        # Check if email is verified
        if not user.email_verified:
            return Response({
                'error': 'Email not verified',
                'user_id': user.id
            }, status=status.HTTP_403_FORBIDDEN)

        token, _ = Token.objects.get_or_create(user=user)
        return Response({
            'token': token.key,
            'user': UserSerializer(user).data
        })


class RegisterView(APIView):
    def post(self, request):
        username = request.data.get('username')
        email = request.data.get('email')
        password = request.data.get('password')
        first_name = request.data.get('first_name', '')
        last_name = request.data.get('last_name', '')

        # Verifica se username o email esistono già
        if User.objects.filter(username=username).exists():
            return Response({'error': 'Username already exists'}, status=status.HTTP_400_BAD_REQUEST)

        if User.objects.filter(email=email).exists():
            return Response({'error': 'Email already exists'}, status=status.HTTP_400_BAD_REQUEST)

        # Crea l'utente ma con is_active=False
        user = User.objects.create_user(
            username=username,
            email=email,
            password=password,
            first_name=first_name,
            last_name=last_name,
            email_verified=False,
            is_active=False  # Importante: disattiva l'utente finché non verifica l'email
        )

        # Genera codice di verifica
        user.set_verification_code()

        # Invia email di verifica
        try:
            send_verification_code(user)
        except Exception as e:
            print(f"Failed to send verification email: {str(e)}")
            # Non fallire completamente se l'invio dell'email fallisce

        return Response({
            'message': 'Registration successful. Please check your email to verify your account.',
            'user_id': user.id
        }, status=status.HTTP_201_CREATED)


class ResendVerificationView(APIView):
    def post(self, request):
        email = request.data.get('email')

        try:
            user = User.objects.get(email=email)

            # Only resend if not already verified
            if not user.email_verified:
                user.set_verification_token()
                send_verification_code(user)

            return Response({
                'message': 'If your email is registered, a verification link has been sent.'
            })

        except User.DoesNotExist:
            # Return the same message as success for security reasons
            return Response({
                'message': 'If your email is registered, a verification link has been sent.'
            })


class VerifyEmailView(APIView):
    def get(self, request, token):
        try:
            token_uuid = uuid.UUID(token)
            user = User.objects.get(verification_token=token_uuid)

            if not user.is_token_valid():
                return Response({
                    'error': 'Verification link has expired. Please request a new one.'
                }, status=status.HTTP_400_BAD_REQUEST)

            user.verify_email()

            return Response({
                'message': 'Email verified successfully. You can now log in.'
            })

        except (ValueError, User.DoesNotExist):
            return Response({
                'error': 'Invalid verification link.'
            }, status=status.HTTP_400_BAD_REQUEST)


class VerifyCodeView(APIView):
    def post(self, request):
        user_id = request.data.get('user_id')
        code = request.data.get('code')

        try:
            user = User.objects.get(id=user_id)
            if user.verify_with_code(code):
                token, _ = Token.objects.get_or_create(user=user)
                return Response({
                    'message': 'Email verificata con successo!',
                    'token': token.key,
                    'user': UserSerializer(user).data
                })
            else:
                return Response({
                    'error': 'Codice non valido o scaduto.'
                }, status=status.HTTP_400_BAD_REQUEST)
        except User.DoesNotExist:
            return Response({
                'error': 'Utente non trovato.'
            }, status=status.HTTP_404_NOT_FOUND)


# core/auth_views.py
class VerifyOTPView(APIView):
    def post(self, request, userId):
        code = request.data.get('code')

        if not code:
            return Response({'error': 'Codice richiesto'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            user = User.objects.get(id=userId)

            # Controlla se l'utente è già verificato
            if user.email_verified:
                # Se già verificato, genera comunque un token per il login
                token, _ = Token.objects.get_or_create(user=user)
                return Response({
                    'message': 'Email già verificata',
                    'token': token.key,
                    'user': UserSerializer(user).data
                })

            # Verifica il codice
            if user.verify_with_code(code):
                # Genera token per login automatico
                token, _ = Token.objects.get_or_create(user=user)

                return Response({
                    'message': 'Email verificata con successo',
                    'token': token.key,
                    'user': UserSerializer(user).data
                })
            else:
                return Response({
                    'error': 'Codice non valido o scaduto'
                }, status=status.HTTP_400_BAD_REQUEST)

        except User.DoesNotExist:
            return Response({
                'error': 'Utente non trovato'
            }, status=status.HTTP_404_NOT_FOUND)