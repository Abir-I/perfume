from rest_framework import serializers
from .models import User
from django.utils import timezone
import bcrypt

class RegisterSerializer(serializers.Serializer):
    first_name = serializers.CharField(max_length=100)
    last_name  = serializers.CharField(max_length=100)
    email      = serializers.EmailField()
    password   = serializers.CharField(write_only=True, min_length=8)
    phone      = serializers.CharField(max_length=20, required=False)

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("An account with this email already exists.")
        return value

    def create(self, validated_data):
        raw_password = validated_data['password']
        hashed = bcrypt.hashpw(raw_password.encode('utf-8'), bcrypt.gensalt())

        user = User.objects.create(
            first_name    = validated_data['first_name'],
            last_name     = validated_data['last_name'],
            email         = validated_data['email'],
            phone         = validated_data.get('phone', ''),
            password_hash = hashed.decode('utf-8'),
            role_id       = 2,
            is_active     = 1,
            created_at    = timezone.now(),
        )
        return user