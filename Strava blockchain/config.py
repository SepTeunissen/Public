#Joomla, sql, ports, passwords, and other sensitive information should not be stored in this file.

CLIENT_ID = '**Top Secret**'
CLIENT_SECRET = '**Top Secret**'
REFRESH_TOKEN_FILE = 'RefreshToken.txt'
CHAIN_FILE_NAME = 'strava_chain.json'
API_PORT = 5000
API_IP_ADDRESS = '0.0.0.0'
VERIFY_TOKEN = "**Top Secret**"
DESIGNATED_OWNER_ID = 000000


def get_refresh_token():
    with open(REFRESH_TOKEN_FILE, 'r') as file:
        return file.read().strip()

def set_refresh_token(token):
    with open(REFRESH_TOKEN_FILE, 'w') as file:
        file.write(token)
