import requests
from django.conf import settings

PAYSTACK_BASE_URL = 'https://api.paystack.co'


class PaystackService:
    def __init__(self):
        self.secret_key = settings.PAYSTACK_SECRET_KEY
        self.headers = {
            'Authorization': f'Bearer {self.secret_key}',
            'Content-Type': 'application/json',
        }

    def initialize_transaction(self, email, amount_kobo, reference, callback_url, metadata=None):
        data = {
            'email': email,
            'amount': amount_kobo,
            'reference': reference,
            'callback_url': callback_url,
            'metadata': metadata or {},
            'currency': 'GHS',
        }
        response = requests.post(
            f'{PAYSTACK_BASE_URL}/transaction/initialize',
            json=data,
            headers=self.headers,
            timeout=30,
        )
        response.raise_for_status()
        return response.json()

    def verify_transaction(self, reference):
        response = requests.get(
            f'{PAYSTACK_BASE_URL}/transaction/verify/{reference}',
            headers=self.headers,
            timeout=30,
        )
        response.raise_for_status()
        return response.json()
