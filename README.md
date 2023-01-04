# avanza-bot

This project takes inspiration from: https://github.com/Qluxzz/avanza

### Strategies
My first ever strategy was to buy when a SMA 12 crosses over a SMA 26 and to sell when the SMA 12 goes under the SMA 26.
This didn't really work out. 

After that i added RSI. The bot was supposed to buy when the first strategy gave a buy signal or if the RSI was below 30%. The bot was selling stocks if the first strategy gave a sell signal or if the RSI was above 70%.
This didn't really work either.

The bot now uses RSI, EMA and MACD to create buy signals. If the RSI is above 50% and the price of the stock is above the EMA 150 and the MACD line crosses over the MACD signal line then the bot would buy a certain stock. If the SMA 12 crosses under the SMA 26 the bot would sell the stock.

## Journal

### 2022-12-29
First day of using the bot the entire day
<details>
  <summary>Result image</summary>
  
  ![image](https://user-images.githubusercontent.com/26044858/209981507-83d99808-e592-44ca-aa7c-aad490af4cbf.png)
</details>

Thoughts: The bot is currently buying and selling at weird times due to logic issues. Will try to fix this tomorrow


### 2023-01-02
<details>
  <summary>Result image</summary>
  
  ![image](https://user-images.githubusercontent.com/26044858/210257652-49256bed-b6c7-42c8-977b-4177f14510b9.png)
</details>

The results are getting better and better with everyday. Hoping for + tomorrow


### 2023-01-04
<details>
  <summary>Result image</summary>
  
  ![image](https://user-images.githubusercontent.com/26044858/210625244-9fbde2ab-2553-43a0-8a2d-88ad3839276f.png)
</details>

Changed the strategy so the bot won much better trades
