import pandas as pd
import numpy as np
import backtrader as bt
import yfinance as yf
import matplotlib.pyplot as plt

# Define the ticker symbol
df = yf.download('EURUSD=X', start='2010-01-01', end='2023-06-06', interval='1d')


def trading_strategy(df):
    # Calculate Bollinger Bands
    df['upper_band'], df['middle_band'], df['lower_band'] = bt.BBANDS(df['close'], timeperiod=20)

    # Calculate RSI
    df['rsi'] = bt.RSI(df['close'], timeperiod=14)

    # Calculate momentum oscillator
    df['momentum'] = bt.MOM(df['close'], timeperiod=14)

    # Define prediction window
    prediction_window = 10

    # Calculate future returns
    df['future_returns'] = (df['close'].shift(-prediction_window) - df['close']) / df['close']

    # Define trading signals
    df['long_signal'] = ((df['close'] < df['lower_band']) & (df['rsi'] < 30) & (df['momentum'] > 0)).astype(int)
    df['short_signal'] = ((df['close'] > df['upper_band']) & (df['rsi'] > 70) & (df['momentum'] < 0)).astype(int)

    # Define trading positions
    df['position'] = df['long_signal'] - df['short_signal']

    # Calculate returns
    df['returns'] = df['position'].shift(1) * df['future_returns']

    # Calculate cumulative returns
    df['cumulative_returns'] = (1 + df['returns']).cumprod()

    # Calculate Sharpe ratio
    sharpe_ratio = np.sqrt(252) * df['returns'].mean() / df['returns'].std()

    # Return Sharpe ratio
    return sharpe_ratio


results = pd.DataFrame(df)
print(results)

for timeperiod in range(10, 30):
    df_optimized = df.copy()
    df_optimized['sharpe_ratio'] = df_optimized['close'].rolling(timeperiod).apply(trading_strategy, raw=False)
    max_sharpe_ratio = df_optimized['sharpe_ratio'].max()
    row = df_optimized[df_optimized['sharpe_ratio'] == max_sharpe_ratio].iloc[0]
    results = results.append(row)

# Select the optimal parameters
optimal_timeperiod = results['upper_band'].astype(int).mode()[0]

# Implement the trading strategy with the optimal parameters
df['upper_band'], df['middle_band'], df['lower_band'] = bt.BBANDS(df['close'], timeperiod=optimal_timeperiod)
df['rsi'] = bt.RSI(df['close'], timeperiod=14)
df['momentum'] = bt.MOM(df['close'], timeperiod=14)
df['future_returns'] = (df['close'].shift(-prediction_window) - df['close']) / df['close']
df['long_signal'] = ((df['close'] < df['lower_band']) & (df['rsi'] < 30) & (df['momentum'] > 0)).astype(int)
df['short_signal'] = ((df['close'] > df['upper_band']) & (df['rsi'] > 70) & (df['momentum'] < 0)).astype(int)
df['position'] = df['long_signal'] - df['short_signal']
df['returns'] = df['position'].shift(1) * df['future_returns']
df['cumulative_returns'] = (1 + df['returns']).cumprod()

# calculate daily returns
df['Returns'] = df['Close'].pct_change() * df['Position'].shift(1)

fig, (ax1, ax2) = plt.subplots(nrows=2, ncols=1, figsize=(12, 8))
df['Close'].plot(ax=ax1)
ax1.set(title='EURUSD Close Price', ylabel='Price')
df['Returns'].cumsum().plot(ax=ax2)
ax2.set(title='EURUSD Trading Strategy', ylabel='Cumulative Returns')
plt.tight_layout()
plt.show()
