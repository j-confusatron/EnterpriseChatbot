#!/usr/bin/env python3
"""api.py

Provides an API into the chatbot implementation
"""
from chatbot.usersession import SessionManager
import chatbot

chatbot = chatbot.Chatbot()
sessionManager = SessionManager()

def start_session():
  """start_session
  FUTURE: Returns a token that indicates a chat session.

  You do not not need to implement this unless your chatbot supports keeping
  working memory of different chats. This
  """
  # You do not need to implement this for assignment 4
  return sessionManager.addSession().getToken()


def end_session(token):
  """end_session
  FUTURE: Discards a token terminating a chat session.

  You do not not need to implement this unless your chatbot supports keeping
  working memory of different chats.
  """
  # You do not need to implement this for assignment 4
  sessionManager.removeSession(token)

def respond(token, prompt):
  """respond
  Given a token and an utterance string, your chatbot should return with a 
  string response.
  
  If sessions are not supported, this method should ignore the token provided.
  If the prompt is an empty string, it indicates that the bot should initiate
  a conversation.

  :param token: A session token to associate the prompt to
  :param prompt: A string indicating text from a user
  :return: A string response from the chatbot
  """
  response = chatbot.delegate_by_intent(prompt, sessionManager.getSession(token))
  return response

if __name__ == '__main__':
  print('This file should not be run directly. ' + \
    'To try out your chatbot, please use debugserver.py.')
  exit(1)
