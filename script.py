import os
import json

from bot.bot import Bot

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
CONFIG_PATH = os.path.join(ROOT_DIR, 'config.json')

fileStream = open(CONFIG_PATH)
config = json.load(fileStream)
fileStream.close()

bot = Bot ({ 
  "username": config["username"], 
  "password": config["password"], 
  "secret": config["secret"],
  "accountId": config["accountId"],
  "stockWatchlist": config["stockWatchlist"]
})