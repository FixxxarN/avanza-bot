import numpy as np
import matplotlib.pyplot as plt
import pandas as pd

from sklearn.preprocessing import MinMaxScaler
from tensorflow.python.keras.models import Sequential
from tensorflow.python.keras.layers import Dense, Dropout, LSTM

class Prediction:
  def Predict(self, data, stockName):
    self.data = data
    self.actual_prices = data

    scaler = MinMaxScaler(feature_range=(0,1))
    scaled_data = scaler.fit_transform(pd.Series(self.data).values.reshape(-1, 1))

    prediction_days = 100

    x_train = []
    y_train = []

    for x in range(prediction_days, len(scaled_data)):
      x_train.append(scaled_data[x-prediction_days:x, 0])
      y_train.append(scaled_data[x, 0])

    x_train, y_train = np.array(x_train), np.array(y_train)
    x_train = np.reshape(x_train, (x_train.shape[0], x_train.shape[1], 1))

    model = Sequential()

    model.add(LSTM(units=50, return_sequences=True, input_shape=(x_train.shape[1], 1)))
    model.add(Dropout(0.1))
    model.add(LSTM(units=50, return_sequences=True))
    model.add(Dropout(0.1))
    model.add(LSTM(units=50))
    model.add(Dropout(0.1))
    model.add(Dense(units=1))

    model.compile(optimizer="adam", loss="mean_squared_error")

    model.fit(x_train, y_train, epochs=25, batch_size=32)

    total_dataset = pd.concat((pd.Series(self.data), pd.Series(self.actual_prices)), axis=0)
    model_inputs = total_dataset[len(total_dataset) - len(self.actual_prices) - prediction_days:]
    model_inputs = model_inputs.values.reshape(-1, 1)
    model_inputs = scaler.transform(model_inputs)

    x_test = []

    for x in range(prediction_days, len(model_inputs)+1):
      x_test.append(model_inputs[x-prediction_days:x, 0])

    x_test = np.array(x_test)
    x_test = np.reshape(x_test, (x_test.shape[0], x_test.shape[1], 1))

    predicted_prices = model.predict(x_test)
    predicted_prices = scaler.inverse_transform(predicted_prices)

    plt.plot(self.actual_prices, color="black", label=f"Actual {stockName} Price")
    plt.plot(predicted_prices, color="green", label=f"Predicted {stockName} Price")
    plt.plot(pd.Series(self.actual_prices).rolling(window=26).mean() , color="yellow", label=f"SMA 26", linestyle="--")
    plt.plot(pd.Series(self.actual_prices).rolling(window=12).mean() , color="orange", label=f"SMA 12", linestyle="--")
    plt.title(f"{stockName} Share Price")
    plt.xlabel("Time")
    plt.ylabel(f"{stockName} Share Price")
    plt.legend()
    plt.show()

    real_data = [model_inputs[len(model_inputs) + 1 - prediction_days:len(model_inputs+1), 0]]
    real_data = np.array(real_data)
    real_data = np.reshape(real_data, (real_data.shape[0], real_data.shape[1], 1))

    prediction = model.predict(real_data)
    prediction = scaler.inverse_transform(prediction)
    return prediction

