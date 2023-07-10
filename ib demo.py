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
                if price > high:
                    self.execute_trade('BUY', price)
                elif price < low:
                    self.execute_trade('SELL', price)


    def nextValidId(self, orderId: int):
        super().nextValidId(orderId)
        self.start()

    def start(self):
        contract = Contract()
        contract.symbol = "EUR"
        contract.secType = "CASH"
        contract.exchange = "IDEALPRO"
        contract.currency = "USD"

        self.reqMarketDataType(3) # Set market data type to "Delayed"
        self.reqMktData(1, contract, "", False, False, []) # Request real-time market data
        self.reqHistoricalData(2, contract, "", "1 D", "1 min", "MIDPOINT", 0, 1, False, []) # Request historical data

    def stop(self):
        self.done = True
        self.disconnect()

    def execute_trade(self, action, price):
        contract = Contract()
        contract.symbol = 'EUR'
        contract.exchange = 'IDDEALPRO'
        contract.currency = 'USD'

        order = Order()
        order.action = action
        order.totalQuantity = 1000
        order.orderType = 'MKT'
        order.transmit = True

        self.placeOrder(self.nextOrderId(), contract, order)    #replace with the next valid order ID
        print(f'{action} order submitted for {contract.symbol}{contract.currency} at {price}')

        self.trade_executed = True





while True:

    app = IBapi()
    app.connect("127.0.0.1", 7497, 0)  # Port number may vary depending on your setup
    app.run()

