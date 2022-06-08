from chatbot.usersession import UserSession
import numpy as np
import requests

NAMES = ['Han', 'Luke', 'Leia', 'Chewbacca', 'Obi Wan Kenobi', 'Darth Vader', 'Emperor Palpatine']
RESPONSES = [
    "You can call me %s.",
    "I go by %s.",
    "%s, and don't you forget it!",
    "Officially, %s, but you can call me whatever you want."
]

def whatIsBotName(prompt, intent, entities, nerclassifier, userSession: UserSession):
    # Come up with the botname. If one is already defined, used that. Otherwise, grab a random one.
    botname = userSession.getBotName()
    if not botname:
        try:
            response = requests.get('https://api.namefake.com/', headers={'Accept': 'application/json'})
            botname = response.json()['name']
        except ConnectionError:
            botname = np.random.choice(NAMES, 1)[0]
        userSession.setBotName(botname)

    # Build and return the response.
    response = np.random.choice(RESPONSES, 1)[0] % (botname)
    return response

def setUserName(prompt, intent, entities, nerclassifier, userSession: UserSession):
    # Pull the name from the user utterance, if it is available.
    name = entities['PERSON'][0] if 'PERSON' in entities else None

    # Check to see if the user already had a name.
    nameChanged = userSession.getName()

    # If the user gave us a name, set it. Otherwise, ask for it and mark the intent is incomplete.
    response = ''
    if name:
        userSession.setName(name)
        userSession.setIntentComplete()
        userSession.setFrame({})
        if nameChanged:
            response = "Sounds good %s, er, I mean, %s." % (nameChanged, name)
        else:
            response = "Nice to meet you, %s!" % (name)
    else:
        response = "Ok, what should I call you?"
        userSession.setIntentComplete(intentComplete=False)
    return response

def repeatUserName(prompt, intent, entities, nerclassifier, userSession: UserSession):
    name = userSession.getName()
    if name:
        return "Your name is %s." % (name)
    else:
        name = np.random.choice(NAMES, 1)[0]
        userSession.setName(name)
        return "You never told me what your name is. I'll call you %s." % (name)