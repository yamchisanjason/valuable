import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
import yfinance as yf
import tensorflow
from keras.layers import Dense, LSTM
from keras.models import Sequential
from sklearn.preprocessing import MinMaxScaler

df = yf.download('EURUSD=X', start='2005-01-01', end='2023-06-09')


def SMA(values, window):
    return pd.Series(values).rolling(window=window).mean().values


def RSI(values, window):
    delta = pd.Series(values).diff()
    loss = delta.where(delta < 0, 0)
    gain = -delta.where(delta > 0, 0)
    avg_loss = loss.rolling(window=window).mean()
    avg_gain = gain.rolling(window=window).mean()
    rs = avg_gain / avg_loss
    return 100 - (100 / (1 + rs)).values


df['SMA'] = SMA(df['Close'].values, window=10)
df['RSI'] = RSI(df['Close'].values, window=14)
df = df.dropna()


def create_dataset(X, y, time_steps=1):
    Xs, ys = [], []
    for i in range(len(X) - time_steps):
        v = X.iloc[i: (i + time_steps)].values
        Xs.append(v)
        ys.append(y.iloc[i + time_steps])
    return np.array(Xs), np.array(ys)


# Define the lookback period
time_steps = 10

# Features and target
X = df[['Close', 'SMA', 'RSI']]
y = df['Close']

# Scaling
scaler_X = MinMaxScaler()
X = pd.DataFrame(scaler_X.fit_transform(X), columns=X.columns)

scaler_y = MinMaxScaler()
y = pd.Series(scaler_y.fit_transform(y.values.reshape(-1, 1)).flatten())

# Create the dataset with the lookback
X, y = create_dataset(X, y, time_steps)

# Train-test split
train_size = int(len(X) * 0.8)
X_train, X_test = X[0:train_size], X[train_size:len(X)]
y_train, y_test = y[0:train_size], y[train_size:len(y)]

# LSTM model
model = Sequential()
model.add(LSTM(4, input_shape=(X_train.shape[1], X_train.shape[2])))
model.add(Dense(1))
model.compile(loss='mean_squared_error', optimizer='adam')
model.fit(X_train, y_train, epochs=5, batch_size=1, verbose=2)

# Predictions
train_predict = model.predict(X_train)
test_predict = model.predict(X_test)

# Inverse scaling
train_predict = scaler_y.inverse_transform(train_predict)
y_train = scaler_y.inverse_transform(y_train.reshape(-1, 1))
test_predict = scaler_y.inverse_transform(test_predict)
y_test = scaler_y.inverse_transform(y_test.reshape(-1, 1))

# Plotting the predictions
plt.figure(figsize=(15, 5))
plt.plot(y_test, label='True Prices')
plt.plot(test_predict, label='Predicted Prices')
plt.xlabel('Time')
plt.ylabel('Price')
plt.title('Price Prediction')
plt.legend()
plt.show()

# Simple Trading Strategy
# Simple Trading Strategy
holdings = 0
bp_winnings = 0
bp_winnings_history = []

for i in range(1, len(test_predict)):
    tomorrow_pred = test_predict[i]
    today_pred = test_predict[i - 1]

    if tomorrow_pred < today_pred:
        if holdings == 0:
            # Buy the EUR with USD
            holdings = 1 / y_test[i - 1][0]
    elif tomorrow_pred > today_pred:
        if holdings > 0:
            # Sell the EUR for USD and calculate the difference in price in basis points
            bp_winnings += (y_test[i - 1][0] - y_test[i - 2][0]) * holdings
            holdings = 0

    # Append the current winnings to the history
    bp_winnings_history.append(bp_winnings)

# Include the final day, if still holding
if holdings > 0:
    bp_winnings += (y_test[-1][0] - y_test[-2][0]) * holdings

bp_winnings_history.append(bp_winnings)
print(f'Total basis points won: {bp_winnings:.2f}')

# Plotting the basis points won over time
plt.figure(figsize=(15, 5))
plt.plot(bp_winnings_history, label='Basis Points Won')
plt.xlabel('Time')
plt.ylabel('Basis Points')
plt.title('Cumulative Basis Points Won Over Time')
plt.legend()
plt.show()