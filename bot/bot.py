import requests
import pyotp
import hashlib
import asyncio
import os
import math

from typing import Any, Callable
from datetime import date, timedelta, datetime
from bot.bot_socket import BotSocket
from bot.technical_analysis import TechnicalAnalysis


BASE_URL = "https://www.avanza.se"
MAX_INACTIVE_MINUTES = 60 * 24

AUTHENTICATION_PATH = "/_api/authentication/sessions/usercredentials"
TOTP_PATH = "/_api/authentication/sessions/totp"
ACCOUNT_OVERVIEW_PATH = "/_api/account-overview/overview/categorizedAccounts"
STOCK_CHART_DATA_PATH = "/_api/price-chart/stock/{}?from={}&to={}"
STOCK_INFORMATION_PATH = "/_api/market-guide/stock/{}"
PLACE_ORDER_PATH = "/_api/trading-critical/rest/order/new"

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
RESULTS_PATH = os.path.join(ROOT_DIR, 'results')

class Bot:
  def __init__(self, config):
    self.config = config 
    self._authenticationTimeout = MAX_INACTIVE_MINUTES
    self._session = requests.Session()

    response_body, credentials = self.__authenticate(config)

    self._credentials = credentials
    self._authentication_session = response_body["authenticationSession"]
    self._push_subscription_id = response_body["pushSubscriptionId"]
    self._customer_id = response_body["customerId"]

    self._socket = BotSocket(self._push_subscription_id, self._session.cookies.get_dict())

    self.buyingPower = self.get_buying_power(config)
    self.buyingPriceLimit = self.buyingPower * 0.15
    self.stopLossLimit = 0.05

    self.activeStocks = {}

    asyncio.get_event_loop().run_until_complete(self.start(config))
    asyncio.get_event_loop().run_forever()

  def __authenticate(self, config):
    data = {
      "maxInactiveMinutes": self._authenticationTimeout,
      "username": config["username"],
      "password": config["password"]
    }

    response = self._session.post(f"{BASE_URL}{AUTHENTICATION_PATH}", json=data)

    response.raise_for_status()

    return self.__validate_two_factor_authentication(config)

  def __validate_two_factor_authentication(self, config):
    totp = pyotp.TOTP(config["secret"], digest=hashlib.sha1)
    totp_code = totp.now()

    response = self._session.post(f"{BASE_URL}{TOTP_PATH}", json={
      "method": "TOTP",
      "totpCode": totp_code
    })

    response.raise_for_status()

    self._security_token = response.headers.get("X-SecurityToken")

    response_body = response.json()

    return response_body, config

  def get_account_overview(self, options=None, return_content: bool = False):
    data = {}
    data["params"] = options

    response = self._session.get(f"{BASE_URL}{ACCOUNT_OVERVIEW_PATH}", headers={
      "X-AuthenticationSession": self._authentication_session,
      "X-SecurityToken": self._security_token
    }, **data)

    response.raise_for_status()

    if len(response.content) == 0:
      return None
    if return_content:
      return response.content
    return response.json()

  def get_buying_power(self, config):
    categorizedAccounts = self.get_account_overview()
    accounts = [account for account in categorizedAccounts['accounts'] if account['id'] == config['accountId']]
    return accounts[0]['buyingPower']['value']

  def get_stock_chart_data(self, stockId, fromTime, toTime):
    response = self._session.get(f"{BASE_URL}{STOCK_CHART_DATA_PATH.format(stockId, fromTime, toTime)}", headers={
      "X-AuthenticationSession": self._authentication_session,
      "X-SecurityToken": self._security_token
    })

    response.raise_for_status()

    if len(response.content) == 0:
      return None

    return response.json()

  def get_stock_information(self, stockId):
    response = self._session.get(f"{BASE_URL}{STOCK_INFORMATION_PATH.format(stockId)}", headers={
      "X-AuthenticationSession": self._authentication_session,
      "X-SecurityToken": self._security_token
    })

    response.raise_for_status()

    if len(response.content) == 0:
      return None

    return response.json()

  def place_order(self, config, orderbookId, orderType, price, volume):
    data = {
      "json": {
        "accountId": config["accountId"],
        "orderbookId": orderbookId,
        "side": orderType,
        "price": price,
        "volume": volume
      }
    }

    response = self._session.post(f"{BASE_URL}{PLACE_ORDER_PATH}", headers={
      "X-AuthenticationSession": self._authentication_session,
      "X-SecurityToken": self._security_token
    }, **data)

    response.raise_for_status()

    if len(response.content) == 0:
      return None

    return response.json()

  async def subscribe_to_id(self, channel, id, callback: Callable[[str, dict], Any]):
    await self.subscribe_to_ids(channel, [id], callback)

  async def subscribe_to_ids(self, channel, ids, callback: Callable[[str, dict], Any]):
    if not self._socket._connected:
      await self._socket.init()

    await self._socket.subscribe_to_ids(channel, ids, callback)

  def handle_stock(self, data):
    stockData = data['data']

    prevTime = str(self.activeStocks[stockData['orderbookId']]["lastUpdated"])
    prevTimestamp = prevTime[:10] + '.' + prevTime[-3:]

    currentTime = str(stockData['lastUpdated'])
    currentTimestamp = currentTime[:10] + '.' + currentTime[-3:]

    start = datetime.utcfromtimestamp(float(prevTimestamp))
    end = datetime.utcfromtimestamp(float(currentTimestamp))

    delta = end - start
    if delta.total_seconds() < 5:
      return

    self.activeStocks[stockData['orderbookId']]['lastUpdated'] = stockData['lastUpdated']

    # previous_sma_12 = self.activeStocks[stockData['orderbookId']]["SMA_12"][-1]
    # previous_sma_26 = self.activeStocks[stockData['orderbookId']]["SMA_26"][-1]

    previous_macd_line = self.activeStocks[stockData['orderbookId']]["MACD"][-1]
    previous_macd_signal_line = self.activeStocks[stockData['orderbookId']]["MACD_SIGNAL"][-1]

    self.activeStocks[stockData['orderbookId']]["data"].append(stockData["lastPrice"]) 

    self.activeStocks[stockData['orderbookId']]["SMA_26"] = TechnicalAnalysis.sma(self.activeStocks[stockData['orderbookId']]["data"], 26)
    self.activeStocks[stockData['orderbookId']]["SMA_12"] = TechnicalAnalysis.sma(self.activeStocks[stockData['orderbookId']]["data"], 12)
    self.activeStocks[stockData['orderbookId']]["RSI_14"] = TechnicalAnalysis.rsi(self.activeStocks[stockData['orderbookId']]["data"], 14)
    self.activeStocks[stockData['orderbookId']]["EMA_150"] = TechnicalAnalysis.ema(self.activeStocks[stockData['orderbookId']]["data"], 150)

    macd_line, signal_line, histogram = TechnicalAnalysis.macd(self.activeStocks[stockData['orderbookId']]["data"], 12, 26)

    self.activeStocks[stockData['orderbookId']]["MACD"] = macd_line
    self.activeStocks[stockData['orderbookId']]["MACD_SIGNAL"] = signal_line
    self.activeStocks[stockData['orderbookId']]["MACD_HIST"] = histogram

    filename = date.today().strftime('%Y-%m-%d') + '.txt'
    filepath = RESULTS_PATH + f'\{filename}'

    if os.path.exists(filepath):
      append_write = 'a'
    else:
      append_write = 'w'

    # current_sma_12 = 0
    # current_sma_26 = 0
    current_macd_line = 0
    current_macd_signal_line = 0
    
    # current_sma_12 = self.activeStocks[stockData['orderbookId']]["SMA_12"][-1]
    # current_sma_26 = self.activeStocks[stockData['orderbookId']]["SMA_26"][-1]

    current_macd_line = self.activeStocks[stockData['orderbookId']]["MACD"][-1]
    current_macd_signal_line = self.activeStocks[stockData['orderbookId']]["MACD_SIGNAL"][-1]


    # if previous_sma_12 < previous_sma_26 and current_sma_12 > current_sma_26 and self.activeStocks[stockData['orderbookId']]["owned_stocks_count"] == 0:
    #   self.activeStocks[stockData['orderbookId']]["signal"] = "BUY"

    if previous_macd_line < previous_macd_signal_line and current_macd_line > current_macd_signal_line and self.activeStocks[stockData['orderbookId']]["EMA_150"][-1] < stockData["lastPrice"] and self.activeStocks[stockData['orderbookId']]["RSI_14"][-1] >= 50 and self.activeStocks[stockData['orderbookId']]["owned_stocks_count"] == 0:
      self.activeStocks[stockData['orderbookId']]["signal"] = "BUY"
    if previous_macd_line > previous_macd_signal_line and current_macd_line < current_macd_signal_line and self.activeStocks[stockData['orderbookId']]["owned_stocks_count"] > 0:
      self.activeStocks[stockData['orderbookId']]["signal"] = "SELL"

    # if self.activeStocks[stockData['orderbookId']]["RSI_14"][-1] < 30 and self.activeStocks[stockData['orderbookId']]["owned_stocks_count"] == 0:
    #   self.activeStocks[stockData['orderbookId']]["signal"] = "BUY"
    # if self.activeStocks[stockData['orderbookId']]["RSI_14"][-1] > 70 and self.activeStocks[stockData['orderbookId']]["owned_stocks_count"] > 0:
    #   self.activeStocks[stockData['orderbookId']]["signal"] = "SELL"

    amount = math.floor(self.buyingPriceLimit / stockData["sellPrice"])

    if self.activeStocks[stockData['orderbookId']]["signal"] == "BUY":
      if stockData["sellPrice"] <= self.buyingPriceLimit:
        #self.place_order(self.config, stockData['orderbookId'], "BUY", stockData["sellPrice"], amount)
        self.activeStocks[stockData['orderbookId']]['owned_stocks_count'] = amount
        self.activeStocks[stockData['orderbookId']]['stop_loss'] = stockData["sellPrice"] * 0.001
        self.activeStocks[stockData['orderbookId']]["boughtFor"] = stockData['sellPrice'] * amount
        print(f"""Bought {amount} of {self.activeStocks[stockData['orderbookId']]['name']} stocks for {stockData['sellPrice'] * amount} and each stock was worth {stockData['sellPrice']} at {datetime.fromtimestamp(float(currentTimestamp))}.""")
        todays_result = open(filepath, append_write)
        todays_result.write(f"Bought {amount} of {self.activeStocks[stockData['orderbookId']]['name']} stocks for {stockData['sellPrice'] * amount} and each stock was worth {stockData['sellPrice']} at {datetime.fromtimestamp(float(currentTimestamp))}. \n")
        todays_result.close()
        self.activeStocks[stockData['orderbookId']]["signal"] = "WAIT"
        self.buyingPower = self.buyingPower - (stockData['sellPrice'] * amount)
        self.buyingPriceLimit = self.buyingPower * 0.15
    if self.activeStocks[stockData['orderbookId']]["signal"] == "SELL":
      #self.place_order(self.config, stockData['orderbookId'], "SELL", stockData["buyPrice"], self.activeStocks[stockData['orderbookId']]['owned_stocks_count'])
      print(f"""Sold {self.activeStocks[stockData['orderbookId']]['owned_stocks_count']} of {self.activeStocks[stockData['orderbookId']]['name']} stocks for {stockData['buyPrice'] * self.activeStocks[stockData['orderbookId']]['owned_stocks_count']} and each stock was worth {stockData['buyPrice']} at {datetime.fromtimestamp(float(currentTimestamp))}. ({(stockData['buyPrice'] * self.activeStocks[stockData['orderbookId']]['owned_stocks_count']) - self.activeStocks[stockData['orderbookId']]["boughtFor"]})""")
      todays_result = open(filepath, append_write)
      todays_result.write(f"Sold {self.activeStocks[stockData['orderbookId']]['owned_stocks_count']} of {self.activeStocks[stockData['orderbookId']]['name']} stocks for {stockData['buyPrice'] * self.activeStocks[stockData['orderbookId']]['owned_stocks_count']} and each stock was worth {stockData['buyPrice']} at {datetime.fromtimestamp(float(currentTimestamp))}. ({(stockData['buyPrice'] * self.activeStocks[stockData['orderbookId']]['owned_stocks_count']) - self.activeStocks[stockData['orderbookId']]['boughtFor']}) \n")
      todays_result.close()
      self.buyingPower = self.buyingPower + (stockData['buyPrice'] * self.activeStocks[stockData['orderbookId']]['owned_stocks_count'])
      self.buyingPriceLimit = self.buyingPower * 0.15
      self.activeStocks[stockData['orderbookId']]['owned_stocks_count'] = 0
      self.activeStocks[stockData['orderbookId']]["signal"] = "WAIT"
    if stockData["buyPrice"] < self.activeStocks[stockData['orderbookId']]['stop_loss']:
      #self.place_order(self.config, stockData['orderbookId'], "SELL", stockData["buyPrice"], self.activeStocks[stockData['orderbookId']]['owned_stocks_count'])
      print(f"""Sold {self.activeStocks[stockData['orderbookId']]['owned_stocks_count']} of {self.activeStocks[stockData['orderbookId']]['name']} stocks for {stockData['buyPrice'] * self.activeStocks[stockData['orderbookId']]['owned_stocks_count']} and each stock was worth {stockData['buyPrice']} at {datetime.fromtimestamp(float(currentTimestamp))}. ({(stockData['buyPrice'] * self.activeStocks[stockData['orderbookId']]['owned_stocks_count']) - self.activeStocks[stockData['orderbookId']]['boughtFor']})""")
      todays_result = open(filepath, append_write)
      todays_result.write(f"Sold {self.activeStocks[stockData['orderbookId']]['owned_stocks_count']} of {self.activeStocks[stockData['orderbookId']]['name']} stocks due to stop loss for {stockData['buyPrice'] * self.activeStocks[stockData['orderbookId']]['owned_stocks_count']} and each stock was worth {stockData['buyPrice']} at {datetime.fromtimestamp(float(currentTimestamp))}. ({(stockData['buyPrice'] * self.activeStocks[stockData['orderbookId']]['owned_stocks_count']) - self.activeStocks[stockData['orderbookId']]['boughtFor']}) \n")
      todays_result.close()
      self.buyingPower = self.buyingPower + (stockData['buyPrice'] * self.activeStocks[stockData['orderbookId']]['owned_stocks_count'])
      self.buyingPriceLimit = self.buyingPower * 0.15
      self.activeStocks[stockData['orderbookId']]['owned_stocks_count'] = 0
      self.activeStocks[stockData['orderbookId']]["signal"] = "WAIT"

  async def start(self, config):
    today = date.today()
    yesterday = today - timedelta(days=1)

    for stock in config["stockWatchlist"]:
      stockInformation = self.get_stock_information(stock)
      yesterdayData = self.get_stock_chart_data(stock, fromTime=yesterday, toTime=yesterday)["ohlc"]
      todayData = self.get_stock_chart_data(stock, fromTime=today, toTime=today)["ohlc"]
      stockData = yesterdayData + todayData

      SMA_26 = TechnicalAnalysis.sma([d["close"] for d in stockData], 26)
      SMA_12 = TechnicalAnalysis.sma([d["close"] for d in stockData], 12)
      RSI_14 = TechnicalAnalysis.rsi([d["close"] for d in stockData], 14)
      EMA_150 = TechnicalAnalysis.ema([d["close"] for d in stockData], 150)
      macd_line, signal_line, histogram = TechnicalAnalysis.macd([d["close"] for d in stockData], 12, 26)

      now  = datetime.now()
      ts = datetime.timestamp(now)

      self.activeStocks[stock] = { 
        "id": stock, 
        "name": stockInformation['name'], 
        "data": [d["close"] for d in stockData],
        "SMA_26": SMA_26,
        "SMA_12": SMA_12,
        "RSI_14": RSI_14,
        "EMA_150": EMA_150,
        "MACD": macd_line,
        "MACD_SIGNAL": signal_line,
        "MACD_HIST": histogram,
        "owned_stocks_count": 0,
        "stop_loss": 0,
        "signal": "WAIT",
        "lastUpdated": str(ts)[:14]
      }

      print(stockData)

      await self.subscribe_to_id('quotes', stock, self.handle_stock)