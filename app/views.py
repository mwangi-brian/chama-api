from django.shortcuts import render
import requests, base64, json
from django.conf import settings
from django.http import JsonResponse
from django.views import View
from django.views.decorators.csrf import csrf_exempt
from django.utils import timezone
from django.utils.decorators import method_decorator
from datetime import datetime
from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import status
from rest_framework.response import Response
from django.contrib.auth import authenticate, login, logout

from .serializers import LoginSerializer, StkPushSerializer

@method_decorator(csrf_exempt, name='dispatch')
class StkPushView(APIView):
    permission_classes = [IsAuthenticated]

    def get_access_token(self):
        consumer_key = settings.DARAJA_CONSUMER_KEY
        consumer_secret = settings.DARAJA_CONSUMER_SECRET
        api_url = f"{settings.DARAJA_BASE_URL}/oauth/v1/generate?grant_type=client_credentials"
        response = requests.get(api_url, auth=(consumer_key, consumer_secret))
        json_response = response.json()
        return json_response['access_token']

    def format_phone_number(self, phone_number):
        if phone_number.startswith('0'):
            return '254' + phone_number[1:]
        elif phone_number.startswith('+'):
            return phone_number[1:]
        else:
            return phone_number

    def post(self, request, *args, **kwargs):
        serializer = StkPushSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        amount = serializer.validated_data['amount']

        user = request.user
        phone_number = user.phone_number
        chama_account = user.chama.chama_account if user.chama else None

        if not phone_number or not chama_account:
            return JsonResponse({'error': 'User is not associated with a chama or phone number is missing'}, status=400)

        formatted_phone_number = self.format_phone_number(phone_number)
        access_token = self.get_access_token()
        api_url = f"{settings.DARAJA_BASE_URL}/mpesa/stkpush/v1/processrequest"
        headers = {
            'Authorization': f'Bearer {access_token}',
            'Content-Type': 'application/json'
        }

        timestamp = datetime.now().strftime('%Y%m%d%H%M%S')
        password = base64.b64encode(f"{settings.DARAJA_SHORTCODE}{settings.DARAJA_PASSKEY}{timestamp}".encode()).decode('utf-8')

        payload = {
            "BusinessShortCode": settings.DARAJA_SHORTCODE,
            "Password": password,
            "Timestamp": timestamp,
            "TransactionType": "CustomerPayBillOnline",
            "Amount": amount,
            "PartyA": formatted_phone_number,
            "PartyB": settings.DARAJA_SHORTCODE,
            "PhoneNumber": formatted_phone_number,
            "CallBackURL": settings.CALLBACK_URL,
            "AccountReference": chama_account,
            "TransactionDesc": "Payment for Chama"
        }

        response = requests.post(api_url, json=payload, headers=headers)
        return JsonResponse(response.json())

@method_decorator(csrf_exempt, name='dispatch')
class StkPushCallbackView(View):
    def post(self, request, *args, **kwargs):
        data = json.loads(request.body)
        # Handle the callback data here
        # You can parse the data and update the database as needed

        return JsonResponse({"ResultCode": 0, "ResultDesc": "Success"})


@method_decorator(csrf_exempt, name='dispatch')
class LoginView(APIView):
    def post(self, request, *args, **kwargs):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        phone_number = serializer.validated_data['phone_number']
        password = serializer.validated_data['password']
        
        user = authenticate(request, phone_number=phone_number, password=password)
            
        if user is not None:
            login(request, user)
            refresh = RefreshToken.for_user(user)
            token = str(refresh.access_token)
            return Response({"message": "User login successful", 'token': token}, status=status.HTTP_200_OK)
        else:
            return Response({'detail': 'Invalid credentials'}, status=status.HTTP_401_UNAUTHORIZED)


class LogoutView(APIView):
    permission_classes = [IsAuthenticated]
    
    def post(self, request, format=None):
        logout(request)
        return Response({"message": "Logout successful"}, status=status.HTTP_200_OK)