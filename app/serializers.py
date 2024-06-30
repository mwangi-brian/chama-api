from rest_framework import serializers

from .models import Chama
class LoginSerializer(serializers.Serializer):
    phone_number = serializers.CharField()
    password = serializers.CharField(write_only=True)

class StkPushSerializer(serializers.Serializer):
    amount = serializers.DecimalField(max_digits=10, decimal_places=2)

class DashboardSerializer(serializers.Serializer):
    chama_name = serializers.CharField()
    chama_account = serializers.IntegerField()
    balance = serializers.DecimalField(max_digits=10, decimal_places=2)

    class Meta:
        model = Chama
        fields = ['chama_name', 'chama_account', 'balance']