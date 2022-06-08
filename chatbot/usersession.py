import uuid

class SessionManager:
    def __init__(self):
        self.sessions = {}

    def addSession(self):
        token = str(uuid.uuid4())
        userSession = UserSession(token)
        self.sessions[token] = userSession
        return userSession

    def removeSession(self, token):
        userSession = self.sessions[token]
        self.sessions[token] = None
        return userSession

    def getSession(self, token):
        userSession = self.sessions[token]
        return userSession

class UserSession:

    def __init__(self, token):
        self.token = token
        self.name = None
        self.currentIntent = None
        self.frame = {}
        self.intentComplete = True
        self.botname = None
        self.mood = []
        self.chat_history_ids = None
        self.chat_started = False
    
    def toString(self):
        name = self.name if self.name else ''
        currentIntent = self.currentIntent if self.currentIntent else ''
        botname = self.botname if self.botname else ''
        s = "\n\n### User Session ###\nToken: %s\nName: %s\nCurrent Intent: %s\nFrame: %s\nIntent Complete: %s\nBot Name: %s\nMood: %s" \
            % (self.token, name, currentIntent, str(self.frame), self.intentComplete, botname, str(self.mood))
        return s
    
    def getToken(self):
        return self.token
    
    def getName(self):
        return self.name
    def setName(self, name):
        self.name = name
        return name
    
    def getBotName(self):
        return self.botname
    def setBotName(self, botname):
        self.botname = botname
        return botname
    
    def getCurrentIntent(self):
        return self.currentIntent
    def setCurrentIntent(self, intent):
        self.currentIntent = intent
        return intent

    def getFrame(self):
        return self.frame
    def setFrame(self, frame):
        self.frame = frame
        return frame
    
    def isIntentComplete(self):
        return self.intentComplete
    def setIntentComplete(self, intentComplete=True):
        self.intentComplete = intentComplete

    def getUserMood(self):
        mood = 0
        for i in range(len(self.mood)):
            mood += (1-(1/(i+1))) * self.mood[i]
        return mood
    def addSentimentToMood(self, sentiment):
        self.mood.append(sentiment)
        return sentiment