# avanza-bot

This is not meant to be used by anyone. This repository is just a fun experiment and a way for me to learn more about tensorflow and neural networks.

This project takes inspiration from these repositories: https://github.com/Qluxzz/avanza & https://github.com/fhqvst/avanza

List of modules used:
- tensorflow (Skipping for now since it is really hard to predict accurately. Will keep the prediction files in the bot folder)
- numpy
- pandas
- matplotlib
- pyotp
- hashlib
- requests
- datetime
- asyncio
- logging
- json
- websockets

#### TODO

- [x] Create a class for the bot
- [x] Create a function that creates and returns the avanza credentials
- [x] Create a function that validates the user
- [x] Create a function that validates totpSecret or totpCode
- [x] Create a function that fetches account overview
- [ ] Create constants for time periods, gateways
- [x] Create a function that fetches chart data within specified time interval
- [x] Create a function that fetches stock information
- [ ] Use websockets to fetch stock data everytime the stock updates
- [ ] Use websockets to fetch stock data everytime the stock updates for multiple stocks
- [ ] Draw the websocket data in a plot in real time
- [ ] Implement a way for the bot to signal time for buy and time for sell
- [ ] Add SMA
- [ ] Add RSI
- [ ] Create a function that fetches chart data for a specified interval and resolution
- [ ] Add a list of stocks the bot should keep in mind when day trading
- [ ] Save all trades to a json file with buyTimestamp, sellTimestamp, profit, loss, stock, buyPrice, sellPrice.
- [ ] Test bot with fake money and fake functions that uses realtime data but uses fake buy and sell functions instead of real ones.




