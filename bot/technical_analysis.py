import numpy as np
import pandas as pd

class TechnicalAnalysis:
  def sma(data, window):
    s = pd.Series(data, dtype=pd.Float64Dtype())
    ma = s.rolling(window=window).mean()
    return ma.array

  def rsi(data, window):
    s = pd.Series(data)
    diff = s.diff(1).dropna()

    positive = 0 * diff
    negative = 0 * diff

    positive[diff > 0] = diff[diff > 0]
    negative[diff < 0] = diff[diff < 0]

    average_gain = positive.ewm(com=window-1, min_periods=window).mean()
    average_loss = negative.ewm(com=window-1, min_periods=window).mean()

    relative_strength = abs(average_gain / average_loss)
    RSI = 100 - 100 / (1 + relative_strength)
    return RSI.array

  def macd(data, window1, window2):
    s = pd.Series(data, dtype=pd.Float64Dtype())
    ma1 = s.ewm(span=window1).mean()
    ma2 = s.ewm(span=window2).mean()

    macd_line = ma1 - ma2

    signal_line = macd_line.ewm(span=9, adjust=False).mean()

    histogram = macd_line - signal_line

    return macd_line.array, signal_line.array, histogram.array

  def ema(data, window):
    s = pd.Series(data)
    return s.ewm(span=window, adjust=False).mean().array
