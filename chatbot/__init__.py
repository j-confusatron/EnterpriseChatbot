import numpy as np
import chatbot.intentclassifier as intentclassifier
import chatbot.nerclassifier as nerclassifier
from chatbot.usersession import UserSession
from transformers import pipeline, AutoModelForCausalLM, AutoTokenizer
import torch

from chatbot.ir_nlg_alarm import setAlarm
from chatbot.ir_nlg_weather import getWeather
from chatbot.ir_nlg_cscatalog import getCseCatalogInfo
from chatbot.ir_nlg_joke import getJoke
from chatbot.ir_nlg_names import whatIsBotName, setUserName, repeatUserName

class Chatbot:
  def __init__(self, debug=True):
    # Load up necessary things like models/classifiers
    self.intentClassifier = intentclassifier.IntentClassifier()
    self.nerclassifier = nerclassifier.NerClassifier()
    self.sentimentAnalysis = pipeline('sentiment-analysis')
    self.chat_tokenizer = AutoTokenizer.from_pretrained("microsoft/DialoGPT-medium")
    self.chat_model = AutoModelForCausalLM.from_pretrained("microsoft/DialoGPT-medium")
    self.debug = debug
    self.intent_confidence_threshold = 0.6

    # Setup a factory to direct intents to the appropriate handler.
    self.ir_nlg_handlers = {
      'cancel': self.do_cancel,
      'weather': getWeather,
      'tell_joke': getJoke,
      'greeting': self.do_greeting,
      'alarm': setAlarm,
      'cse_course_content': getCseCatalogInfo,
      'cse_course_prerequisites': getCseCatalogInfo,
      'cse_course_id': getCseCatalogInfo,
      'change_user_name': setUserName,
      'what_is_your_name': whatIsBotName,
      'user_name': repeatUserName,
      'what_can_i_ask_you': self.what_can_bot_do,
      'get_intent_clarity': self.clarifyIntent
    }

  def delegate_by_intent(self, prompt, userSession: UserSession, ignoreIntentConfidence=False):
    # Hardcode a mechanism for setting the confidence threshold.
    if prompt.lower().startswith("set threshold"):
      prompt_parts = prompt.split()
      if prompt_parts[-1].isnumeric():
        self.intent_confidence_threshold = float(prompt_parts[-1]) / 100
        return "intent_confidence_threshold=%.2f" % (self.intent_confidence_threshold)

    # If the prompt is empty, set the intent to greeting.
    c = 1.0
    if not prompt or len(prompt.strip()) == 0:
      prompt = ''
      intent = 'greeting'
    # Otherwise, classify it intelligently.
    else:
      intent, c = self.intentClassifier.getIntent(prompt)
    
    # If the previous interaction was complete, we set the new intent as the current interaction.
    # Otherwise, the implication is that we need to continue with the prior intent and not let the new intent direct handler delegation.
    if userSession.isIntentComplete():
      if not ignoreIntentConfidence and c < self.intent_confidence_threshold:
        userSession.setCurrentIntent('get_intent_clarity')
      else:
        userSession.setCurrentIntent(intent)

    # Extract utterance entities.
    entities = self.nerclassifier.getEntities(prompt)

    # Classify the sentiment of the user prompt and record it in the user session.
    sentiment = self.sentimentAnalysis(prompt)[0]
    if intent != 'cancel': # cancel comes across as negative, but the user is likely just trying to get out of a continuing intent.
      if sentiment['label'] == 'NEGATIVE':
        userSession.addSentimentToMood(-1 * sentiment['score'])
      else:
        userSession.addSentimentToMood(sentiment['score'])

    # Route the prompt to the correct handler, per intent.
    response = ''
    if intent == 'cancel':
      response = self.do_cancel(userSession)
    elif userSession.getCurrentIntent() in self.ir_nlg_handlers:
      response = self.ir_nlg_handlers[userSession.getCurrentIntent()](prompt, intent, entities, self.nerclassifier, userSession)
    else:
      response = self.handle_unknown(intent, prompt, userSession)
    
    # Print out debug data.
    if self.debug:
      debug_statement = "\n### NLU Debug ###\nIntent: %s, Confidence: %.4f\nEntities: %s\nSentiment: %s\nUser Mood: %.4f" \
        % (intent, c, str(entities), str(sentiment), userSession.getUserMood())
      debug_statement += userSession.toString()
      print(debug_statement)

    return response
  

  def do_cancel(self, userSession: UserSession):
    userSession.setIntentComplete()
    userSession.setFrame({})
    response = "Got it. What else can I help you with?" if userSession.getUserMood() >= 0 else "I'm really sorry, can I do anything else for you?"
    return response


  def do_greeting(self, prompt, intent, entities, nerclassifier, userSession: UserSession):
    positive_greetings = ["Hello%s.", "Hi%s.", "Welcome%s.", "Good day%s.", "Well hello%s.", "Hi there%s."]
    negative_greetings = ["...hi...%s.", "Are you doing ok%s", "What's got you down%s?"]
    greetings = positive_greetings if userSession.getUserMood() >= 0 else negative_greetings
    name = ' '+userSession.getName() if userSession.getName() else ''
    response = np.random.choice(greetings, 1)[0] % (name)
    return response
  

  def what_can_bot_do(self, prompt, intent, entities, nerclassifier, userSession: UserSession):
    response = "I can perform the following tasks:"
    for kIntent in self.ir_nlg_handlers.keys():
      response += "\n"+kIntent.replace('_', ' ')
    return response
  
  def clarifyIntent(self, prompt, intent, entities, nerclassifier, userSession: UserSession):
    # Setup some session tracking.
    frame = userSession.getFrame() if not userSession.isIntentComplete() else userSession.setFrame({'PROMPT': prompt})

    # If the user replied affirmatively or negatively, record it.
    if intent == 'yes':
        frame['CONFIRMED'] = True
    elif intent == 'no':
        frame['CONFIRMED'] = False

    # Build the response, based on frame state.
    if 'CONFIRMED' in frame:
      userSession.setIntentComplete()
      userSession.setFrame({})
      if frame['CONFIRMED']:
        return self.delegate_by_intent(frame['PROMPT'], userSession, ignoreIntentConfidence=True)
      else: 
        return "Try restating your question more clearly."
    else:
      userSession.setIntentComplete(intentComplete=False)
      frame['CONFIRMED'] = False
      return "Are you talking about %s?" % (intent.replace('_', ' '))


  def handle_unknown(self, intent, prompt, userSession):
    #response = "I'm afraid I don't know how to support %s. I can perform the following tasks:" % (intent.replace('_', ' '))
    #for kIntent in self.ir_nlg_handlers.keys():
    #  response += "\n"+kIntent.replace('_', ' ')
    
    # Run the user prompt through DialoGPT.
    new_user_input_ids = self.chat_tokenizer.encode(prompt + self.chat_tokenizer.eos_token, return_tensors='pt')
    bot_input_ids = torch.cat([userSession.chat_history_ids, new_user_input_ids], dim=-1) if userSession.chat_started else new_user_input_ids
    userSession.chat_history_ids = self.chat_model.generate(bot_input_ids, max_length=1000, pad_token_id=self.chat_tokenizer.eos_token_id, do_sample=True, top_k=0, top_p=0.5)
    response = self.chat_tokenizer.decode(userSession.chat_history_ids[:, bot_input_ids.shape[-1]:][0], skip_special_tokens=True)
    userSession.chat_started = True

    return response