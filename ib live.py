from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
from ibapi.order import Order
from datetime import datetime, timedelta
import time

class IBapi(EWrapper, EClient):
    def __init__(self):
        EClient.__init__(self, self)
        self.data = [] # to store the real-time market data
        self.start_time = datetime.utcnow().replace(hour=8, minute=0, second=0, microsecond=0)
        self.trade_executed = False
        self.close_time = datetime.utcnow().replace(hour=17, minute=25, second=0, microsecond=0)
        self.risk_reward_ratio = 2
        self.take_profit_distance = None
        self.stop_loss_distance = None
        self.position_size = None
        self.usd_balance = 0
        self.eur_balance = 0
        self.open_orders = []

    def historicalData(self, reqId, bar):
        super().historicalData(reqId, bar)
        print(bar.date, bar.open, bar.high, bar.low, bar.close, bar.volume)

    def tickPrice(self, reqId, tickType, price, attrib):
        super().tickPrice(reqId, tickType, price, attrib)
        if tickType == 2: # open price
            self.data.append(price)
        elif tickType == 3: # high price
            self.data.append(price)
        elif tickType == 4: # low price
            self.data.append(price)
        elif tickType == 5: # close price
            self.data.append(price)

            if not self.trade_executed and datetime.utcnow() >= self.start_time + timedelta(minute=30):
                high = max(self.data)
                low = min(self.data)

                #calculate the stop loss and take profit levels based on the risk-reward ratio
                distance = abs(high - low)
                self.stop_loss_distance = distance / (1 + self.risk_reward_ratio)
                self.take_profit_distance = self.stop_loss_distance * self.risk_reward_ratio

                #calculate stop loss and take profit levels in price terms
                if price > high:
                    stop_loss = price - self.stop_loss_distance
                    take_profit = price - self.take_profit_distance
                    self.execute_trade('BUY', price, take_profit, stop_loss)

                elif price < low:
                    stop_loss = price + self.stop_loss_distance
                    take_profit = price - self.take_profit_distance
                    self.execute_trade('SELL', price, take_profit, stop_loss)

            #check if the current time has passed the close time and close all open trades
            if datetime.utcnow() >= self.close_time:
                self.close_all_trades()

        print(self.data)

    def orderStatus(self, orderId, status, filled, remaining, avgFillPrice, permId, parentId, lastFillPrice, clientId, whyHeld, mktCapPrice):
        super().orderStatus(orderId, status, filled, remaining, avgFillPrice, permId, parentId, lastFillPrice, clientId,whyHeld, mktCapPrice)

        if status == 'Filled':
            print(f'Order {orderId} has been filled')




    def execDetails(self, reqId, contract, execution):
        super().execDetails(reqId, contract, execution)
        print(f'Trade executed: {execution.side} {execution.shares} shares of {contract.symbol}{contract.currency} at {execution.price}')
        pnl = (execution.price - execution.avgPrice) * execution.shares
        print(f'PnL: {pnl}')

    def nextValidId(self, orderId: int):
        super().nextValidId(orderId)
        self.next_order_id = orderId
        self.start()


    def openOrder(self, orderId, contract, order, orderState):
        super().openOrder(orderId, contract, order, orderState)
        print(f'Order {orderId} has been opened')
        self.open_orders.appennd(order)


    def start(self):
        contract = Contract()
        contract.symbol = "EUR"
        contract.secType = "CASH"
        contract.exchange = "IDEALPRO"
        contract.currency = "USD"

        self.reqMarketDataType(3) # Set market data type to "Delayed"
        self.reqMktData(1, contract, "", False, False, []) # Request real-time market data
        self.reqHistoricalData(2, contract, "", "1 D", "1 min", "MIDPOINT", 0, 1, False, []) # Request historical data

        #request account updates to synchronize the account balance
        self.reqAccountUpdates(True, '')


    def updateAccountValue(self, key: str, val: str, currency:str, accountName: str):
        super().updateAccountValue(key, val, currency, accountName)
        if key == 'CashBalance' and currency == 'USD':
            self.usd_balance = float(val)
        elif key == 'CashBalance'  and currency == 'EUR':
            self.eur_balance = float(val)






    def stop(self):
        self.done = True
        self.disconnect()

    def execute_trade(self, action, price, take_profit, stop_loss):
        contract = Contract()
        contract.symbol = 'EUR'
        contract.exchange = 'IDEALPRO'
        contract.currency = 'USD'

        #calculate the position size based on the risk amount and stop loss distance
        #risk_amount = self.account_balance * self.risk_percentage
        self.position_size = int(self.usd_balance / self.stop_loss_distance)

        order = Order()
        order.action = action
        order.totalQuantity = self.position_size
        order.orderType = 'MKT'
        order.transmit = True
        order.account = 'DU7270972'

        self.placeOrder(self.next_order_id(), contract, order)    #replace with the next valid order ID
        self.next_order_id += 1
        print(f'{action} order submitted for {contract.symbol}{contract.currency} at {price}')

        #update the account balance based on the executed trade
        if action == 'BUY':
            self.usd_balance -= self.position_size
            self.eur_balance += price * self.position_size

        elif action == 'SELL':
            self.usd_balance += self.position_size
            self.eur_balance -= price * self.position_size

        self.trade_executed = True

    def close_all_trades(self):
        self.reqAllOpenOrders()     #request all open orders
        open_orders = self.reqOpenOrders()
        for order in open_orders:
            #execute a trade in the opposite direction of the open trades
            if order.action == 'BUY':
                action = 'SELL'
                price = self.data[-1]   #current market price

            elif order.action == 'SELL':
                action = 'BUY'
                price = self.data[-1]   #current market price

            else:
                #this order is not a trade order, skip it
                continue

            #place the opposite trade at the current market price
            contract = Contract()
            contract.symbol = 'EUR'
            contract.exchange = 'IDEALPRO'
            contract.currency = 'USD'

            order = Order()
            order.action = action
            order.totalQuantity = self.position_size
            order.orderType = 'MKT'
            order.transmit = True
            order.account = 'DU7270972'

            self.placeOrder(self.nextValidId(), contract, order)
            print(f'{action} order submitted for {contract.symbol}{contract.currency} at {price}')

            #update the account balance based on the executed trade
            if action == 'BUY':
                self.usd_balance -= self.position_size
                self.eur_balance += price * self.position_size

            elif action == 'SELL':
                self.usd_balance += self.position_size
                self.eur_balance -= price * self.position_size

            print(f'Updated account balance: USD {self.usd_balance:.2f}, EUR {self.eur_balance:.2f}')

        self.open_orders = []
        self.trade_executed = False

        self.trade_executed = False




app = IBapi()
app.connect("127.0.0.1", 7497, 0)
app.start()

while True:
    app.run()

