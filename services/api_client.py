import requests
import os
import json

class LesJoursAPI:
    def __init__(self, base_url):
        self.base_url = base_url.rstrip('/')
        self.tokens = {}  # telegram_user_id -> jwt token
        self.api_user_ids = {}  # telegram_user_id -> api user_id
        self._load_user_ids()

    def _get_headers(self, user_id=None):
        headers = {}
        token = self.tokens.get(user_id)
        if token:
            headers['Authorization'] = f'Bearer {token}'
        return headers

    def _user_ids_path(self):
        return os.path.join(os.path.dirname(__file__), 'user_ids.json')

    def _save_user_ids(self):
        try:
            with open(self._user_ids_path(), 'w', encoding='utf-8') as f:
                json.dump(self.api_user_ids, f)
        except Exception as e:
            print('Ошибка при сохранении user_ids:', e)

    def _load_user_ids(self):
        try:
            with open(self._user_ids_path(), 'r', encoding='utf-8') as f:
                self.api_user_ids = json.load(f)
        except Exception:
            self.api_user_ids = {}

    def register(self, telegram_user_id, first_name='', last_name=''):
        url = f"{self.base_url}/api/user/register/"
        email = f"telegram_{telegram_user_id}@telegram.com"
        data = {
            "username": email,
            "password": str(telegram_user_id),
            "phone": str(telegram_user_id),
            "gender": "male",  # по умолчанию
            "is_mailing_list": False,
            "first_name": first_name,
            "last_name": last_name
        }
        print("REGISTER DATA:", data)
        resp = requests.post(url, json=data)
        print("REGISTER RESPONSE:", resp.status_code, resp.text)
        resp.raise_for_status()
        api_user_id = resp.json().get('user_id')
        if api_user_id:
            self.api_user_ids[telegram_user_id] = api_user_id
            self._save_user_ids()
        return resp.json()

    def login(self, telegram_user_id):
        url = f"{self.base_url}/api/token/"
        email = f"telegram_{telegram_user_id}@telegram.com"
        data = {
            "email": email,
            "password": str(telegram_user_id)
        }
        print("LOGIN DATA:", data)
        resp = requests.post(url, json=data)
        print("LOGIN RESPONSE:", resp.status_code, resp.text)
        resp.raise_for_status()
        token = resp.json().get('access')
        api_user_id = resp.json().get('user_id')
        if token:
            self.tokens[telegram_user_id] = token
        if api_user_id:
            self.api_user_ids[telegram_user_id] = api_user_id
            self._save_user_ids()
        return token

    def ensure_auth(self, user_id, first_name='', last_name=''):
        try:
            return self.login(user_id)
        except requests.HTTPError as e:
            if e.response.status_code == 401:
                self.register(user_id, first_name, last_name)
                return self.login(user_id)
            raise

    def list_masterclasses(self, user_id, page=1, page_size=5):
        url = f"{self.base_url}/api/masterclasses/events/"
        params = {"page": page, "page_size": page_size}
        resp = requests.get(url, params=params, headers=self._get_headers(user_id))
        resp.raise_for_status()
        return resp.json()

    def get_masterclass(self, user_id, mc_id):
        url = f"{self.base_url}/api/masterclasses/masterclasses/{mc_id}/"
        resp = requests.get(url, headers=self._get_headers(user_id))
        resp.raise_for_status()
        return resp.json()

    def book_masterclass(self, user_id, event_id, data):
        url = f"{self.base_url}/api/masterclasses/events/{event_id}/book/"
        resp = requests.post(url, json=data, headers=self._get_headers(user_id))
        resp.raise_for_status()
        return resp.json()

    def list_certificates(self, user_id):
        url = f"{self.base_url}/api/certificates/certificates/"
        resp = requests.get(url, headers=self._get_headers(user_id))
        resp.raise_for_status()
        return resp.json()

    def buy_certificate(self, user_id, data):
        url = f"{self.base_url}/api/certificates/buy/"
        resp = requests.post(url, json=data, headers=self._get_headers(user_id))
        resp.raise_for_status()
        return resp.json()

    def list_all_masterclasses(self, user_id):
        url = f"{self.base_url}/api/masterclasses/masterclasses/"
        headers = self._get_headers(user_id)
        all_results = []
        next_url = url
        while next_url:
            resp = requests.get(next_url, headers=headers)
            resp.raise_for_status()
            data = resp.json()
            all_results.extend(data.get('results', []))
            next_url = data.get('next')
        return {'results': all_results}

    def add_to_cart(self, user_id, product_unit_id, guests_amount=1):
        url = f"{self.base_url}/api/order/cart/{user_id}/{product_unit_id}/{guests_amount}/"
        resp = requests.post(url, headers=self._get_headers(user_id))
        resp.raise_for_status()
        return resp.json()

    def checkout(self, user_id, data):
        url = f"{self.base_url}/api/order/checkout/{user_id}/"
        resp = requests.post(url, json=data, headers=self._get_headers(user_id))
        resp.raise_for_status()
        return resp.json()

    def get_api_user_id(self, telegram_user_id):
        print('API USER IDS:', self.api_user_ids)
        print('Запрошен user_id для:', telegram_user_id)
        api_user_id = self.api_user_ids.get(telegram_user_id)
        if api_user_id:
            return api_user_id
        # Если не найдено — пробуем получить профиль пользователя через API
        token = self.tokens.get(telegram_user_id)
        if not token:
            return None
        url = f"{self.base_url}/api/user/profile/"
        headers = {'Authorization': f'Bearer {token}'}
        try:
            resp = requests.get(url, headers=headers)
            resp.raise_for_status()
            api_user_id = resp.json().get('id') or resp.json().get('user_id')
            if api_user_id:
                self.api_user_ids[telegram_user_id] = api_user_id
                self._save_user_ids()
                return api_user_id
        except Exception as e:
            print('Ошибка при получении user_id из профиля:', e)
        return None 