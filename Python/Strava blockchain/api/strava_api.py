import requests
import config
import time

class Class_StravaAuth:
    def __init__(self):
        self.client_id = config.CLIENT_ID
        self.client_secret = config.CLIENT_SECRET
        self.refresh_token = config.get_refresh_token()

    def get_access_token(self):
        get_token = requests.post(
            'https://www.strava.com/oauth/token',
            params={
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'grant_type': 'refresh_token',
                'refresh_token': self.refresh_token
            }
        )

        if get_token.status_code != 200:
            print("Statuscode:", get_token.status_code)
            print("Error:", get_token.text)
            return None

        else:
            get_token = get_token.json()
            access_token = get_token['access_token']
            GottenRefreshToken = get_token['refresh_token']

            if (GottenRefreshToken != self.refresh_token):
                print("Gotten RefreshToken differs from Used token, changing Refreshtoken.txt")
                config.set_refresh_token(GottenRefreshToken)

            return access_token


class Class_StravaClient:
    def __init__(self):
        self.auth = Class_StravaAuth()
        self.access_token = self.auth.get_access_token()

    def get_all_activities(self):
        get_activities = requests.get(
            'https://www.strava.com/api/v3/athlete/activities',
            params={
                'access_token': self.access_token
                }
        )
        if get_activities.status_code != 200:
            print("Statuscode:", get_activities.status_code)
            print("Error:", get_activities.text)
            return None

        else:
            return get_activities.json()
    
    def get_activity_by_id(self, activity_id):
        get_activity = requests.get(
            f'https://www.strava.com/api/v3/activities/{activity_id}',
            params={
                'access_token': self.access_token
                }
        )
        if get_activity.status_code != 200:
            print("Statuscode:", get_activity.status_code)
            print("Error:", get_activity.text)
            return None

        else:
            return get_activity.json()

class Class_WebHook:
    def __init__(self):
        self.verify_token = config.VERIFY_TOKEN
        self.client_id = config.CLIENT_ID
        self.client_secret = config.CLIENT_SECRET

    def get_ngrok_url(self):
        print("Getting ngrok URL")
        response = requests.get("http://ngrok:4040/api/tunnels")
        if response.status_code == 200:
            tunnels = response.json().get("tunnels", [])
            if tunnels:
                public_url = tunnels[0].get("public_url")
                if public_url and public_url.startswith("https://"):
                    print("Public URL:", public_url)
                    return public_url
                else:
                    print("No HTTPS tunnel found")
        return None

    def subscribe_webhook(self):
        print("Subscribing to Strava webhook")
        print("trying to subscribe with url:", self.get_ngrok_url())

        subscribe = requests.post(
            'https://www.strava.com/api/v3/push_subscriptions',
            params={
                'client_id': self.client_id,
                'client_secret': self.client_secret,
                'callback_url': self.get_ngrok_url(),
                'verify_token': self.verify_token
                }
        )
        if subscribe.status_code == 201:
            print("Webhook subscribed successfully.")
            return True

        elif subscribe.status_code == 400:
            response_json = subscribe.json()
            errors = response_json.get("errors", [])
            for error in errors:
                if error.get("code") == "already exists":
                    print("Webhook subscription already exists.")
                    return True

            print(f"Bad request error: {response_json}")
            return False
        else:
            print("Statuscode:", subscribe.status_code)
            print("Error:", subscribe.text)
            return False

    def get_webhook_subscriptions(self):
        response = requests.get(
            'https://www.strava.com/api/v3/push_subscriptions',
            params={
                'client_id': self.client_id,
                'client_secret': self.client_secret
            }
        )
        if response.status_code == 200:
            return response.json()
        else:
            print("Error fetching subscriptions:", response.text)
            return None

    def unsubscribe_webhook(self, subscription_id):
        response = requests.delete(
            f'https://www.strava.com/api/v3/push_subscriptions/{subscription_id}',
            params={
                'client_id': self.client_id,
                'client_secret': self.client_secret
            }
        )
        if response.status_code == 204:
            print("Webhook unsubscribed successfully.")
            return True
        else:
            print("Error unsubscribing webhook:", response.text)
            return False
