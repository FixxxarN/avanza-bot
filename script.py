import os
import json

from bot.bot import Bot
from bot.prediction import Prediction

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

stock_information = bot.get_stock_information("1296604")

chartData = bot.get_stock_chart_data("1296604", "today")["ohlc"]

print(chartData)

# prediction = Prediction()

# print(f'Close {prediction.Predict([d["close"] for d in chartData], stock_information["name"])}')