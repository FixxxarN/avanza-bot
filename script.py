import os
import json

from bot.bot import Bot

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
CREDENTIALS_PATH = os.path.join(ROOT_DIR, 'credentials.json')

fileStream = open(CREDENTIALS_PATH)
credentials = json.load(fileStream)
fileStream.close()

bot = Bot ({ 
  "username": credentials["username"], 
  "password": credentials["password"], 
  "secret": credentials["secret"] 
})

print(bot.get_account_overview())