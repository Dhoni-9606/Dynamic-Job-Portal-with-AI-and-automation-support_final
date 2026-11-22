import random
import string

import dns.resolver
from django.conf import settings
from django.contrib.auth import authenticate, get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.cache import cache
from django.core.mail import send_mail
from rest_framework import serializers
from rest_framework_simplejwt.tokens import RefreshToken


User = get_user_model()


def is_real_email_domain(email):
    domain = email.split('@')[-1]
    try:
        dns.resolver.resolve(domain, 'MX')
        return True
    except:
        return False
class UserSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = ('id', 'email', 'first_name', 'last_name', 'role')

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True, validators=[validate_password])
    confirm_password = serializers.CharField(write_only=True, required=True)

    class Meta:
        model = User
        fields = ('email', 'first_name', 'last_name', 'role', 'password', 'confirm_password')

    def validate(self, attrs):
        if attrs['password'] != attrs['confirm_password']:
            raise serializers.ValidationError({"confirm_password": "Password fields didn't match."})
        return attrs

    def create(self, validated_data):
        validated_data.pop('confirm_password')
        user = User.objects.create_user(**validated_data)
        return user
    def validate_email(self, value):
        if not is_real_email_domain(value):
            raise serializers.ValidationError("Please use a valid email address (real domain).")
        return value 

class LoginSerializer(serializers.Serializer):
    email = serializers.EmailField()
    password = serializers.CharField(write_only=True)

    def validate(self, data):
        user = authenticate(email=data['email'], password=data['password'])
        if not user:
            raise serializers.ValidationError("Invalid email or password.")
        if not user.is_active:
            raise serializers.ValidationError("User account is disabled.")
        refresh = RefreshToken.for_user(user)
        return {
            'refresh': str(refresh),
            'access': str(refresh.access_token),
            'user': {
                'id': user.id,
                'email': user.email,
                'first_name': user.first_name,
                'last_name': user.last_name,
                'role': user.role,
            }
        }
def reset_otp_cache_key(email):
    return f"reset_otp_{email.strip().lower()}"


def send_password_reset_otp(email, otp):
    send_mail(
        "Password Reset OTP",
        f"Your OTP for password reset is: {otp}",
        settings.DEFAULT_FROM_EMAIL,
        [email],
        fail_silently=False,
    )

class ForgotPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()

    def validate_email(self, value):
        if not User.objects.filter(email__iexact=value).exists():
            raise serializers.ValidationError("No user with this email address.")
        return value.strip().lower()

    def save(self):
        email = self.validated_data['email']
        otp = ''.join(random.choices(string.digits, k=6))
        cache.set(reset_otp_cache_key(email), otp, timeout=600)   # store OTP for 10 min

        send_password_reset_otp(email, otp)
        return otp

class ResetPasswordSerializer(serializers.Serializer):
    email = serializers.EmailField()
    otp = serializers.CharField(max_length=6, required=True)
    new_password = serializers.CharField(write_only=True, validators=[validate_password])
    confirm_new_password = serializers.CharField(write_only=True)

    def validate(self, attrs):
        if attrs['new_password'] != attrs['confirm_new_password']:
            raise serializers.ValidationError({"confirm_new_password": "Passwords do not match."})
        cached_otp = cache.get(reset_otp_cache_key(attrs['email']))
        if not cached_otp or cached_otp != attrs['otp']:
            raise serializers.ValidationError({"otp": "Invalid or expired OTP."})
        return attrs

    def save(self):
        email = self.validated_data['email'].strip().lower()
        new_password = self.validated_data['new_password']
        
        try:
            user = User.objects.get(email__iexact=email)
            user.set_password(new_password)   # This is CRITICAL
            user.save()
            cache.delete(reset_otp_cache_key(email))
            return user
        except User.DoesNotExist:
            raise serializers.ValidationError("User not found.")
