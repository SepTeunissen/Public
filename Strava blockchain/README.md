used: https://www.geeksforgeeks.org/python/create-simple-blockchain-using-python/ to start


install requirements through requirements.txt

Use dockercompose -d --build to create a container. 

NGrok is used to create a tunnel to the docker environment so the Strava Webhook can send activities 

The refreshtoken is writen in RefreshToken.txt, because when getting the access_token from strava, the token can change.

necessary variables are defined in config.py 
DESIGNATED_OWNER_ID is the id of the strava user of wich i get activities from strava, and is used to filter incomming activities

storage.py is used to get and save the chain
chain.py is used for chain actions
strava_api.py is used to contact the strava api
flask_api.py is used to expose endpoints for this project 
