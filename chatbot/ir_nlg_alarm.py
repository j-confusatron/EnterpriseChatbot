from chatbot.usersession import UserSession

def setAlarm(prompt, intent, entities, nerclassifier, userSession: UserSession):
    # Setup some session tracking.
    frame = userSession.getFrame() if not userSession.isIntentComplete() else userSession.setFrame({'ASKED': None})

    # Extract entities from the utterance.
    if 'DATE' in entities:
        frame['DATE'] = entities['DATE'][0]
    if 'TIME' in entities:
        frame['TIME'] = entities['TIME'][0]

    # if we're asking for confirmation and we gto a yes or no, record it.
    if frame['ASKED'] == 'CONFIRMED':
        if intent == 'yes':
            frame['CONFIRMED'] = True
        elif intent == 'no':
            frame['CONFIRMED'] = False

    # Do some frame analysis to determine the response.
    response = ''

    # If we don't have a date yet, ask for one. If the user doesn't reply with one, set one anyway and roll with it.
    if 'DATE' not in frame:
        userSession.setIntentComplete(intentComplete=False)
        if frame['ASKED'] == 'DATE':
            frame['DATE'] = "every single day"
            response = "I'll set it for every day.\n"+setAlarm(prompt, intent, entities, nerclassifier, userSession)
        else:
            frame['ASKED'] = 'DATE'
            response = "What day do you want the alarm for?"

    # Ask the user for a time. If they don't provide one, wake them up at 4am!
    elif 'TIME' not in frame:
        userSession.setIntentComplete(intentComplete=False)
        if frame['ASKED'] == 'TIME':
            frame['TIME'] = "6am"
            response = "Let's try 6am.\n"+setAlarm(prompt, intent, entities, nerclassifier, userSession)
        else:
            frame['ASKED'] = 'TIME'
            response = "What time should I set the alarm for?"

    # Ground the statement with the user, confirm the details.
    elif 'CONFIRMED' not in frame:
        userSession.setIntentComplete(intentComplete=False)
        frame['ASKED'] = 'CONFIRMED'
        response = "Ok, I'll set an alarm for you %s at %s. Sound good?" % (frame['DATE'], frame['TIME'])

    # If the user disagrees with the alarm, ask them why. They can respond back with new dates and times.
    elif frame['CONFIRMED'] == False:
        userSession.setIntentComplete(intentComplete=False)
        del frame['CONFIRMED']
        response = "Did I get something wrong?"

    # Otherwise set the alarm and mark the intent as complete.
    else:
        userSession.setIntentComplete()
        response = "Your alarm is all set for %s at %s!" % (frame['DATE'], frame['TIME'])
        userSession.setFrame({})

    # Return the response.
    return response