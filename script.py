import os
import json
import asyncio
from datetime import date, timedelta

from bot.bot import Bot
from bot.bot_socket import BotSocket
from bot.prediction import Prediction

import random as rnd
import matplotlib.pyplot as plt
from itertools import count
from matplotlib.animation import FuncAnimation

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