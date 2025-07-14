from api.flask_api import flask_api_app
from api.strava_api import Class_WebHook
from blockchain.chain import Class_Blockchain
from threading import Thread
import config

webHook = Class_WebHook()
blockchain = Class_Blockchain()

print("start Flask API")
def run_flask_app():
    flask_api_app.run(host=config.API_IP_ADDRESS, port=config.API_PORT)

flask_thread = Thread(target=run_flask_app)
flask_thread.start()

print("start Strava Webhook")
subscriptions = webHook.get_webhook_subscriptions()
if not subscriptions:
    print("No webhook subscriptions found, subscribing now")
else:
    print("Webhook subscriptions found, removing")
    subscription_id = subscriptions[0]['id']
    webHook.unsubscribe_webhook(subscription_id=subscription_id)

webHook.subscribe_webhook()