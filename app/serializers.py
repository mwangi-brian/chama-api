from rest_framework import serializers

from .models import User

class LoginSerializer(serializers.Serializer):
    phone_number = serializers.CharField()
    password = serializers.CharField(write_only=True)


class StkPushSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)