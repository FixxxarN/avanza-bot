import requests
import pyotp
import hashlib

BASE_URL = "https://www.avanza.se"
MAX_INACTIVE_MINUTES = 60 * 24

AUTHENTICATION_PATH = "/_api/authentication/sessions/usercredentials"
TOTP_PATH = "/_api/authentication/sessions/totp"
ACCOUNT_OVERVIEW_PATH = "/_api/account-overview/overview/categorizedAccounts"
STOCK_CHART_DATA_PATH = "/_api/price-chart/stock/{}?timePeriod={}"
STOCK_INFORMATION_PATH = "/_api/market-guide/stock/{}"

class Bot:
  def __init__(self, credentials): 
    self._authenticationTimeout = MAX_INACTIVE_MINUTES
    self._session = requests.Session()

    response_body, credentials = self.__authenticate(credentials)

    self._credentials = credentials
    self._authentication_session = response_body["authenticationSession"]
    self._push_subscription_id = response_body["pushSubscriptionId"]
    self._customer_id = response_body["customerId"]

    self.balance = self.get_account_overview()["accountsSummary"]["buyingPower"]["value"]
    self.print_account_information()

  def __authenticate(self, credentials):
    data = {
      "maxInactiveMinutes": self._authenticationTimeout,
      "username": credentials["username"],
      "password": credentials["password"]
    }

    response = self._session.post(f"{BASE_URL}{AUTHENTICATION_PATH}", json=data)

    response.raise_for_status()

    return self.__validate_two_factor_authentication(credentials)

  def __validate_two_factor_authentication(self, credentials):
    totp = pyotp.TOTP(credentials["secret"], digest=hashlib.sha1)
    totp_code = totp.now()

    response = self._session.post(f"{BASE_URL}{TOTP_PATH}", json={
      "method": "TOTP",
      "totpCode": totp_code
    })

    response.raise_for_status()

    self._security_token = response.headers.get("X-SecurityToken")

    response_body = response.json()

    return response_body, credentials

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

  def get_stock_chart_data(self, stockId, timePeriod):
    response = self._session.get(f"{BASE_URL}{STOCK_CHART_DATA_PATH.format(stockId, timePeriod)}", headers={
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

  def print_account_information(self):
    print(self.balance)



