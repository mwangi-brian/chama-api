import requests, base64, json
from django.conf import settings
from django.views import View
from datetime import datetime
from django.http import JsonResponse
from rest_framework.views import APIView
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import status
from rest_framework.response import Response
from django.contrib.auth import authenticate, login, logout
from django.utils.decorators import method_decorator
from django.views.decorators.csrf import csrf_exempt
import logging
from decimal import Decimal

from .models import User
from .serializers import LoginSerializer, StkPushSerializer, DashboardSerializer

logger = logging.getLogger(__name__)

class StkPushView(APIView):
    permission_classes = [IsAuthenticated]

    def get_access_token(self):
        consumer_key = settings.DARAJA_CONSUMER_KEY
        consumer_secret = settings.DARAJA_CONSUMER_SECRET
        api_url = f"{settings.DARAJA_BASE_URL}/oauth/v1/generate?grant_type=client_credentials"
        response = requests.get(api_url, auth=(consumer_key, consumer_secret))

        if response.status_code != 200:
            print(f"Error: {response.status_code} - {response.text}")
            return None

        try:
            json_response = response.json()
        except requests.exceptions.JSONDecodeError:
            print(f"JSONDecodeError: {response.text}")
            return None

        return json_response.get('access_token')

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
        amount = float(serializer.validated_data['amount'])

        user = request.user
        phone_number = user.phone_number
        chama_account = user.chama.chama_account if user.chama else None

        if not phone_number or not chama_account:
            return JsonResponse({'error': 'User is not associated with a chama or phone number is missing'}, status=400)

        formatted_phone_number = self.format_phone_number(phone_number)
        access_token = self.get_access_token()

        if not access_token:
            return JsonResponse({'error': 'Failed to retrieve access token'}, status=500)

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

        if response.status_code != 200:
            print(f"Error: {response.status_code} - {response.text}")
            return JsonResponse({'error': 'Failed to process STK push request'}, status=500)

        try:
            json_response = response.json()
        except requests.exceptions.JSONDecodeError:
            print(f"JSONDecodeError: {response.text}")
            return JsonResponse({'error': 'Failed to decode response from STK push request'}, status=500)

        return JsonResponse(json_response)


@method_decorator(csrf_exempt, name='dispatch')
class StkPushCallbackView(View):
    def post(self, request, *args, **kwargs):
        try:
            data = json.loads(request.body)
            logger.info(f"Callback data received: {json.dumps(data, indent=2)}")

            result_code = data.get("Body", {}).get("stkCallback", {}).get("ResultCode")
            callback_metadata = data.get("Body", {}).get("stkCallback", {}).get("CallbackMetadata", {})

            logger.info(f"Result code: {result_code}")
            logger.info(f"Callback metadata: {json.dumps(callback_metadata, indent=2)}")

            if result_code == 0:  # Transaction was successful
                amount = 0
                phone_number = None

                for item in callback_metadata.get("Item", []):
                    if item.get("Name") == "Amount":
                        amount = Decimal(item.get("Value"))
                    elif item.get("Name") == "PhoneNumber":
                        phone_number = str(item.get("Value"))

                logger.info(f"Extracted amount: {amount}, Phone number: {phone_number}")

                if phone_number is not None:
                    try:
                        user = User.objects.get(phone_number=phone_number)
                        chama = user.chama
                        if chama:
                            logger.info(f"Chama found: {chama}, current balance: {chama.balance}")
                            chama.balance += amount
                            chama.save()
                            logger.info(f"Updated balance: {chama.balance}")
                            return JsonResponse({"ResultCode": 0, "ResultDesc": "Success"})
                        else:
                            logger.error(f"User {user} is not associated with any Chama")
                            return JsonResponse({"ResultCode": 1, "ResultDesc": "User is not associated with any Chama"}, status=404)
                    except User.DoesNotExist:
                        logger.error(f"User with phone number {phone_number} not found")
                        return JsonResponse({"ResultCode": 1, "ResultDesc": "User not found"}, status=404)

            logger.error(f"Transaction failed or invalid, result code: {result_code}")
            return JsonResponse({"ResultCode": 1, "ResultDesc": "Failed or invalid transaction"}, status=400)

        except json.JSONDecodeError as e:
            logger.error(f"JSON decode error: {e}")
            return JsonResponse({"ResultCode": 1, "ResultDesc": "Invalid JSON data"}, status=400)
        except Exception as e:
            logger.error(f"Unexpected error: {e}")
            return JsonResponse({"ResultCode": 1, "ResultDesc": "Internal server error"}, status=500)


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

class UserDashboard(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        chama = user.chama

        if not chama:
            return Response({'error': 'User is not associated with any Chama'}, status=400)

        serializer = DashboardSerializer(chama)
        return Response(serializer.data)
