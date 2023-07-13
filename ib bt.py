from ibapi.client import EClient
from ibapi.wrapper import EWrapper
from ibapi.contract import Contract
from ibapi.common import BarData
from datetime import datetime

class MyWrapper(EWrapper):
    def historicalData(self, reqId, date, open, high, low, close, volume, barCount, WAP, hasGaps):
        print(f'{date} {open} {high} {low} {close} {volume}')

    def historicalDataEnd(self, reqId, start, end):
        print('Historical data request completed')

    def connected(self):
        print('Connection established')

    def disconnected(self):
        print('Connection closed')

class MyClient(EClient):
    def __init__(self, wrapper):
        EClient.__init__(self, wrapper)

    def request_historical_data(self):
        contract = Contract()
        contract.symbol = 'AAPL'
        contract.secType = 'STK'
        contract.currency = 'USD'
        contract.exchange = 'SMART'

        end_time = datetime(2023, 6, 30, 23, 59, 59).strftime('%Y%m%d %H:%M:%S')
        duration = '3 M'
        bar_size = '1 day'

        self.reqHistoricalData(1, contract, end_time, duration, bar_size, 'MIDPOINT', 1, 1, False, [])

    def run(self):
        self.reqMarketDataType(4)
        super().run()
        print('Disconnected')

def main():
    wrapper = MyWrapper()
    client = MyClient(wrapper)

    client.connect('127.0.0.1', 7497, 0)

    client.request_historical_data()

    client.run()

    client.disconnect()

if __name__ == '__main__':
    main()