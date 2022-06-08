from chatbot.usersession import UserSession
import numpy as np
import requests

JOKES = [
  "How do you know someone is a cross fitter? They tell you.",
  "Why couldn't the bicycle stand up by itself? It was two tired!",
  "Did you hear the rumor about butter? Well, I'm not going to spread it!"
]

def getJoke(prompt, intent, entities, nerclassifier, userSession: UserSession):
    try:
        response = requests.get('https://icanhazdadjoke.com/', headers={'Accept': 'application/json'})
        return response.json()['joke']
    except ConnectionError:
        return np.random.choice(JOKES, 1)[0]