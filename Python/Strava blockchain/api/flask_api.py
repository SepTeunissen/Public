from flask import Flask, jsonify, request
from blockchain.chain import Class_Blockchain
from api.strava_api import Class_StravaClient
import config

blockchain = Class_Blockchain()

flask_api_app = Flask(__name__)

@flask_api_app.route('/get_chain', methods=['GET'])
def display_chain():
    response = {'chain': blockchain.chain,
                'length': len(blockchain.chain)}
    return jsonify(response), 200


@flask_api_app.route('/valid', methods=['GET'])
def valid():
    valid = blockchain.chain_valid(blockchain.chain)

    if valid:
        response = {'message': 'The Blockchain is valid.'}
    else:
        response = {'message': 'The Blockchain is not valid.'}
    return jsonify(response), 200

@flask_api_app.route('/get_last_activity', methods=['GET'])
def get_last_activity():
    response = Class_StravaClient().get_last_activity()

    return jsonify(response), 200

@flask_api_app.route("/", methods=["GET", "POST"])
def strava_webhook():
    print("Incoming GET:", request.args)
    print("Headers:", request.headers)

    if request.method == "GET":
        mode = request.args.get("hub.mode")
        challenge = request.args.get("hub.challenge")
        token = request.args.get("hub.verify_token")

        print(mode, challenge, token)

        if mode == "subscribe" and token == config.VERIFY_TOKEN:
            return jsonify({"hub.challenge": challenge}), 200
        else:
            return "verification failed", 403

    if request.method == "POST":
        data = request.get_json()
        print("incomming event:", data)

        if config.DESIGNATED_OWNER_ID == data.get('owner_id'):
            print("Owner ID matches, processing event")

            activity_data = Class_StravaClient().get_activity_by_id(data['object_id'])

            if activity_data is None:
                return jsonify({"error": "Failed to fetch activity data"}), 500

            response, status_code = blockchain.mine_block(activity_data)
            return response, status_code

        # If owner ID doesn't match, just return 200 OK to acknowledge webhook
        return "", 200
