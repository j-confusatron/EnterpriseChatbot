from chatbot.usersession import UserSession
from datetime import datetime
import requests

OPEN_WEATHER_API_KEY = '32b9b1f26d874c9c8fe4bf4a9ee3b40c'
DEFAULT_LOC = "Seattle"

def getWeather(prompt, intent, entities, nerclassifier, userSession: UserSession):
    weather = {}
    response = ''
    try:
        # Retrieve the weather.
        weather, loc, citySpecified = retrieveWeatherFromAPI(entities, userSession)

        # Generate a natural language response.
        temp = weather['main']['temp']
        tempHigh = weather['main']['temp_max']
        tempLow = weather['main']['temp_min']
        humidity = weather['main']['humidity']
        desc = weather['weather'][0]['description']
        sunrise = datetime.fromtimestamp(weather['sys']['sunrise'])
        sunset = datetime.fromtimestamp(weather['sys']['sunset'])
        response = "Here's the weather for %s.\n" % (loc)
        if not citySpecified:
            response = "Querying for weather without specifying a city is currently unsupported. Here's the weather for %s.\n" % (loc)
        response += "The current weather is %d degrees and %s. Humidity is at %d%%.\nThe high temperature today is %d, low is %d.\nSunrise is at %s, sunset at %s." % (temp, desc, humidity, tempHigh, tempLow, sunrise.strftime("%H:%M"), sunset.strftime("%H:%M"))

    # If the connection to OpenWeather failed or there was a payload error, it'll be caught here.
    except Exception as err:
        print("OpenWeatherAPI Exception")
        print(err)
        response = "Hmm... Something went wrong and I'm not able to get the weather for %s currently.\nIf you were asking about %s, odds are it is grey, wet, and mild." % (loc, DEFAULT_LOC)
    
    # Return the weather.
    return response

def retrieveWeatherFromAPI(entities, userSession):
    loc = ''
    citySpecified = True
    weather = {}

    # If the entities provide a location, use it.
    if 'GPE' in entities:
        for l in entities['GPE']:
            loc += ",%s" % (l) if len(loc) > 0 else l
    # Otherwise, fallback on the default location.
    else:
        loc = DEFAULT_LOC
        citySpecified = False

    # Hit the OpenWeather API.
    endpoint = 'https://api.openweathermap.org/data/2.5/weather?q=%s&appid=%s&units=imperial' % (loc, OPEN_WEATHER_API_KEY)
    response = requests.get(endpoint)
    weather = response.json()
    if weather['cod'] != 200:
        raise ValueError(weather['message'])

    # Return the weather.
    return weather, loc, citySpecified