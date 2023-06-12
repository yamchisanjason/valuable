import pandas as pd
import numpy as np
import yfinance as yf

# Define the ticker symbol and the time frame
ticker = "AAPL"
start_date = "2022-01-01"
end_date = "2022-06-01"

# Get the stock data from Yahoo Finance API
data = yf.download(ticker, start=start_date, end=end_date)

# Define the buy and sell signals based on the moving averages
data["MA10"] = data["Close"].rolling(window=10).mean()
data["MA50"] = data["Close"].rolling(window=50).mean()

data["Signal"] = np.where(data["MA10"] > data["MA50"], 1, 0)
data["Position"] = data["Signal"].diff()

# Define the risk-reward ratio
risk_reward_ratio = 2

# Define the initial capital and position size
initial_capital = 10000
position_size = initial_capital / len(data)

# Define the trading strategy
for i, row in enumerate(data.iterrows()):
    if i == 0:
        data.at[i, "Shares"] = 0
        data.at[i, "Cash"] = initial_capital
    else:
        if data.at[i, "Position"] == 1:
            data.at[i, "Shares"] = position_size / data.at[i, "Close"]
            data.at[i, "Cash"] = data.at[i-1, "Cash"] - (data.at[i, "Shares"] * data.at[i, "Close"])
        elif data.at[i, "Position"] == -1:
            data.at[i, "Shares"] = 0
            data.at[i, "Cash"] = data.at[i-1, "Cash"] + (data.at[i-1, "Shares"] * data.at[i, "Close"])
        else:
            data.at[i, "Shares"] = data.at[i-1, "Shares"]
            data.at[i, "Cash"] = data.at[i-1, "Cash"]

    # Calculate the unrealized P&L
    data.at[i, "Unrealized P&L"] = data.at[i, "Shares"] * (data.at[i, "Close"] - data.at[i-1, "Close"])

    # Calculate the maximum loss allowed for each trade
    max_loss = position_size * (1 - 1/risk_reward_ratio)

    # Calculate the stop loss and take profit levels
    data.at[i, "Stop Loss"] = data.at[i, "Close"] - max_loss
    data.at[i, "Take Profit"] = data.at[i, "Close"] + max_loss

    # Check for stop loss and take profit levels
    if data.at[i, "Position"] == 1:
        if data.at[i, "Low"] < data.at[i, "Stop Loss"]:
            data.at[i, "Position"] = -1
        elif data.at[i, "High"] > data.at[i, "Take Profit"]:
            data.at[i, "Position"] = -1

# Calculate the realized P&L
data["Realized P&L"] = data["Shares"].diff() * data["Close"]

# Calculate the total P&L
data["Total P&L"] = data["Realized P&L"] + data["Unrealized P&L"]

# Print the final portfolio value
print("Final Portfolio Value: ${:.2f}".format(data.tail(1)["Cash"].values[0] + (data.tail(1)["Shares"].values[0] * data.tail(1)["Close"].values[0])))
