import requests

class LesJoursAPI:
    def __init__(self, base_url):
        self.base_url = base_url.rstrip('/')
        self.tokens = {}  # user_id -> jwt token

    def _get_headers(self, user_id=None):
        headers = {}
        token = self.tokens.get(user_id)
        if token:
            headers['Authorization'] = f'Bearer {token}'
        return headers

    def register(self, user_id, first_name='', last_name=''):
        url = f"{self.base_url}/api/user/register/"
        email = f"telegram_{user_id}@telegram.com"
        data = {
            "username": email,
            "password": str(user_id),
            "phone": str(user_id),
            "gender": "male",  # по умолчанию
            "is_mailing_list": False,
            "first_name": first_name,
            "last_name": last_name
        }
        print("REGISTER DATA:", data)
        resp = requests.post(url, json=data)
        print("REGISTER RESPONSE:", resp.status_code, resp.text)
        resp.raise_for_status()
        return resp.json()

    def login(self, user_id):
        url = f"{self.base_url}/api/token/"
        email = f"telegram_{user_id}@telegram.com"
        data = {
            "email": email,
            "password": str(user_id)
        }
        print("LOGIN DATA:", data)
        resp = requests.post(url, json=data)
        print("LOGIN RESPONSE:", resp.status_code, resp.text)
        resp.raise_for_status()
        token = resp.json().get('access')
        if token:
            self.tokens[user_id] = token
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