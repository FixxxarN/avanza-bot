import os
import json
import asyncio

from bot.bot import Bot
from bot.bot_socket import BotSocket
from bot.prediction import Prediction

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
CREDENTIALS_PATH = os.path.join(ROOT_DIR, 'credentials.json')

fileStream = open(CREDENTIALS_PATH)
credentials = json.load(fileStream)
fileStream.close()

def callback(data):
  print(data)

async def subscribe_to_channel(bot: Bot):
  await bot.subscribe_to_id('quotes', '5269', callback)
  await bot.subscribe_to_id('quotes', '5447', callback)

bot = Bot ({ 
  "username": credentials["username"], 
  "password": credentials["password"], 
  "secret": credentials["secret"] 
})

asyncio.get_event_loop().run_until_complete(subscribe_to_channel(bot))
asyncio.get_event_loop().run_forever()

# stock_information = bot.get_stock_information("1296604")

# chartData = bot.get_stock_chart_data("1296604", "today")["ohlc"]

# print(chartData)

# prediction = Prediction()

# print(f'Close {prediction.Predict([d["close"] for d in chartData], stock_information["name"])}')