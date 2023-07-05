##已经把pendingcancel的订单都实现取消后重新下单

from ib_insync import *
import tkinter as tk
import asyncio
import threading
import time
from datetime import datetime, timezone


# -*- coding: utf-8 -*-
class ForexApp:
    def __init__(self, root):
        self.root = root
        self.root.title("外汇交易应用程序")
        self.forex_contracts = ['EURUSD', 'USDJPY', 'USDCNH', 'AUDUSD', 'GBPUSD', 'USDCAD', 'USDHKD']
        self.high_prices = []
        self.low_prices = []
        self.tasks = [None] * len(self.forex_contracts)
        self.stop_flags = [False] * len(self.forex_contracts)
        self.disconnection_as_except= [False] * len(self.forex_contracts)
        self.forex_contracts_var = []
        self.text_box = []
        self.amounts = []
        self.total_usd = [0.0]*len(self.forex_contracts)
        self.position_tasks = [None] * len(self.forex_contracts)
        self.total_position_label = tk.Label(root)
        self.total_position_label.pack(side='right', fill='x')
        self.update_position_label()
        self.total_account =[0.0]*len(self.forex_contracts)
        self.currency_balance = [0.0]*len(self.forex_contracts)
        self.currency_hkd_rate = [0.0]*len(self.forex_contracts)
        self.usd_hkd_rate = (0.0)
        



        total_position_button = tk.Button(root, text="查看总仓位")
        total_position_button.pack(side='right', fill='y')

        # 创建一个 Canvas 容器
        canvas = tk.Canvas(self.root, scrollregion=(0, 0, 2000, 1500))
        canvas.pack(side="left", fill="both", expand=True)

        # 创建一个 PanedWindow 容器，用于将窗口内容分为左右两部分
        paned_window = tk.PanedWindow(canvas, orient='horizontal', sashwidth=10, sashrelief='raised')
        # 创建左侧子 Frame，放置货币选择、订单价格和下单金额等控件
        left_frame = tk.Frame(paned_window)
        # 创建右侧子 Frame，放置执行情况的文本框
        right_frame = tk.Frame(paned_window)
        # 将左右两个子 Frame 添加到 PanedWindow 容器中
        paned_window.add(left_frame, minsize=500)
        paned_window.add(right_frame, minsize=400)
        # 将 PanedWindow 放置在 Canvas 容器中
        canvas.create_window((0, 0), window=paned_window, anchor='nw')
        # 创建一个垂直滚动条
        scrollbar = tk.Scrollbar(self.root, orient="vertical", command=canvas.yview) 
        canvas.configure(yscrollcommand=scrollbar.set)
        # 将 Canvas 和滚动条放置在主窗口中
        canvas.pack(side='left', fill='both', expand=True)
        scrollbar.pack(side='right', fill='y')

        # 循环遍历每个货币
        for i, forex in enumerate(self.forex_contracts):
            # 创建一个 Frame 容器，用于放置每个货币的控件
            sub_frame = tk.Frame(left_frame, bd=5)
            sub_frame.pack(side='top', fill='y')
            #sub_frame.grid(row=i*7, column=0, padx=10, pady=10, sticky='w')
            print(i, forex)
            # 显示货币名称
            label = tk.Label(sub_frame, text=f"{forex}合约：")
            label.pack(side="left")

            # 用于存储货币选择的 StringVar 对象
            forex_var = tk.StringVar(value=forex)
            self.forex_contracts_var.append(forex_var)

            # 显示高价触发的订单价格标签和输入框
            high_label = tk.Label(sub_frame, text="高价触发订单价格：")
            high_label.pack(side='top')
            high_entry = tk.Entry(sub_frame, width=80)
            high_entry.pack()
            self.high_prices.append(high_entry)

            # 显示低价触发的订单价格标签和输入框
            low_label = tk.Label(sub_frame, text="低价触发订单价格：")
            low_label.pack()
            low_entry = tk.Entry(sub_frame, width=80)
            low_entry.pack()
            self.low_prices.append(low_entry)

            # 显示下单金额
            amount_label = tk.Label(sub_frame, text="下单金额：")
            amount_label.pack()
            amount_var = tk.StringVar(value="10000") # 初始化为 100000
            amount_entry = tk.Entry(sub_frame, width=80, textvariable=amount_var)
            amount_entry.pack()
            self.amounts.append(amount_entry)

            sub_frame2 = tk.Frame(right_frame, bd=7) ##bd可以调整sub_frame2的间距
            sub_frame2.pack(side='top', fill='x')
            #sub_frame2.grid(row=i+100, column=1, padx=10, pady=10, sticky='e')

            # 创建用于放置订单的按钮
            place_button = tk.Button(sub_frame, text="放置订单", 
                                    command=lambda i=i: threading.Thread(target=self.threaded, args=(i,)).start()) 
            place_button.pack(side="left")

            # 创建用于停止订单的按钮
            stop_button = tk.Button(sub_frame, text="停止碰撞并取消订单",
                                    command=lambda i=i: self.stop_order(i))
            stop_button.pack(side="left")

         
            # 在遇到非连接报错时，用这个按钮断开连接并退出碰撞
            disconnection_as_except_button = tk.Button(sub_frame, text="出现非连接错误",
                                        command=lambda i=i: self.disconnection(i))
            disconnection_as_except_button.pack(side="left")
            # 创建用于查看现在仓位的按钮
            position_button = tk.Button(sub_frame, text="查看仓位及汇率",
                                        command=lambda i=i: threading.Thread(target=self.threaded2, args=(i,)).start())
            position_button.pack(side="left")
            #执行情况
            text_label = tk.Label(sub_frame2, text="执行情况：")
            text_label.pack()
            text_box = tk.Text(sub_frame2, height=9.45, width=60)
            text_box.pack()
            self.text_box.append(text_box)

   
        #添加对总仓位的显示
        # 连接到 IB 账户
    def update_position_label(self):   
            try:
                ib = IB()
                ib.connect('127.0.0.1', 7497, clientId=12345)
                self.total_position_label.destroy() #每次更新前先删除原来的label
                self.total_position_label = tk.Label(root)
                self.total_position_label.pack(side='right', fill='x')

                # 获取总仓位
                total_usd = 0
                total_position = 0
                global total_usd_list
                total_usd_list = [0.0]*len(self.forex_contracts)
                i=0
                for forex in enumerate(self.forex_contracts):
                    forex = Forex(forex[1])
                    total_execution_trades = [f for f in ib.fills() if f.contract.symbol == forex.symbol and f.contract.currency == forex.currency and f.execution.avgPrice is not None ]
                    print(len(total_execution_trades))
                    #print(total_execution_trades[0])
                    

                    for fill in total_execution_trades:
                                        currency = forex.currency
                                        print(forex.symbol,forex.currency)
                                        if currency == 'USD':
                                                    #forex_quote = ib.reqMktData(forex)    
                                                    #forex_rate = forex_quote.last #先不用市场利率了，先用当时成交的利率
                                            if fill.execution.side == 'BOT':
                                                total_usd =- fill.execution.shares * fill.execution.price
                                                print(total_usd,fill.execution.price,fill.execution.side,fill.execution.time)
                                            else:
                                                total_usd = fill.execution.shares * fill.execution.price
                                                print (total_usd,fill.execution.price,fill.execution.side,fill.execution.time)
                                        else:
                                            if fill.execution.side == 'BOT':
                                                total_usd = fill.execution.shares
                                                print(total_usd,fill.execution.price,fill.execution.side,fill.execution.time)
                                            else:
                                                total_usd =- fill.execution.shares
                                                print (total_usd,fill.execution.price,fill.execution.side,fill.execution.time)
                                        total_position += total_usd
                                        print('total_position',total_position)
                                        total_usd_list[i] += total_usd
                                        print('total_usd_list[i]',total_usd_list[i])

                    i+=1

                total_account = 0
                b = ib.accountValues(account='DU7270972')

                #计算公式：sumary_in_usd = total in hkd/exchangerate(usd/hkd) - total in hkd_usd

                global exchange_rate_list
                exchange_rate_list = [0.0]*len(self.forex_contracts)
                global cashbalance_inusd
                cashbalance_inusd =[0.0]*len(self.forex_contracts)
                i=0     
                for forex in enumerate(self.forex_contracts):
                        print(forex[1])
                        forex = Forex(forex[1])
                        if forex.currency == 'USD':
                            item_currency = forex.symbol
                        else:
                            item_currency = forex.currency 
                        print(item_currency)
                        ticker = ib.reqTickers(forex)[0]
                        print(ticker)
                        exchange_rate_list[i] = float(ticker.bid)
                        print(exchange_rate_list[i])
                                
                        for item in b:
                            if item.tag =='TotalCashBalance' and item.currency== item_currency :
                                print('yes')
                                cashbalance = float(item.value)
                                print(cashbalance)
                                
                                if forex.currency == 'USD':
                                    cashbalance_inusd[i] = cashbalance*exchange_rate_list[i]
                                if forex.symbol == 'USD':
                                    cashbalance_inusd[i] = cashbalance/exchange_rate_list[i] ####主货币是美元
                        if item_currency != 'HKD' :
                                total_account += cashbalance_inusd[i] 
                                print('total_account',total_account)        
                        i += 1            

                print(total_account)
                self.total_position_label.config(text=f"Daily net USD transaction ($): \n{round(total_position,1)} \nTotal Cach balance in USD($)\nexcept USD&HKD: \n{round(total_account,1)}")
                ib.disconnect()


            #except ConnectionRefusedError or TimeoutError or asyncio.exceptions.CancelledError or ConnectionError or asyncio.exceptions.TimeoutError as e: 
            except Exception as e:
                self.total_position_label.destroy() #每次更新前先删除原来的label
                self.total_position_label = tk.Label(root)
                self.total_position_label.pack(side='right', fill='x')
                print('This is position exception:',e)
                self.total_position_label.config(text = 'check position error, \nplease wait a few seconds to reconnect')

            root.after(50000, self.update_position_label)

        
    def threaded2(self, i):
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        self.position_tasks[i] = loop.create_task(self.get_position_async(i))
        loop.run_until_complete(self.position_tasks[i])


    #查看仓位
    async def get_position_async(self, i):
        try:
            text_box = self.text_box[i]
            text_box.delete('1.0', tk.END)
            text_box.insert(tk.END, '查看仓位')
            total_usd = total_usd_list[i]


            total_account = self.total_account[i]
            total_account = cashbalance_inusd[i]   
            exchange_rate = exchange_rate_list[i]
            print(total_account)
            text_box = self.text_box[i]
            text_box.insert(tk.END, '\n当日总成交美金:' + str(round(total_usd)) + '\ncash balance in usd:'+str(round(total_account))+'\nexchange rate:'+str(round(exchange_rate,4)))   
            #在上面添加一个await，使得查看仓位和下单的窗口不要互相干扰，可以同时进行

        except Exception as e: ##如果异步函数在执行过程中出现异常，就会跳转到except代码块中，输出异常信息并关闭与IB的连接。这样可以保证在出现异常时及时关闭连接，防止出现问题#
                print(e)
                self.position_tasks[i] is None
                text_box = self.text_box[i]
                text_box.delete(2.0, tk.END)
                text_box.insert(tk.END, '\n查看仓位出错,已断开连接')


    #创建了一个新的事件循环，并将任务添加到其中
    def threaded(self, i):
        #下单
            text_box = self.text_box[i]
            text_box.delete(1.0, tk.END)
            text_box.insert(tk.END, '碰撞已开始')

            self.stop_flags[i] = False
            self.disconnection_as_except[i] = False

            loop = asyncio.new_event_loop()
            asyncio.set_event_loop(loop)
            self.tasks[i] = loop.create_task(self.place_order_async(i))
            loop.run_until_complete(self.tasks[i])


    async def place_order_async(self, i):
        account = 0
        while True:
            account += 1
            forex_contract = self.forex_contracts_var[i].get()
            print("place order",forex_contract)
            # 获取货币对，高触发价，低触发价           
            if forex_contract == 'EURUSD':
                client_id = 1013
            elif forex_contract == 'USDJPY':
                client_id = 1014
            elif forex_contract == 'USDCNH':
                client_id = 1015        
            elif forex_contract == 'AUDUSD':
                client_id = 1016
            elif forex_contract == 'GBPUSD':
                client_id = 1017
            elif forex_contract == 'USDCAD':
                client_id = 1018
            elif forex_contract == 'USDHKD':
                client_id = 1019
            
            # 根据货币对不同设置不同的客户端ID
            print('place order for', forex_contract, 'with client id', client_id)
            forex = Forex(forex_contract)       
            # 不再需要连接IB TWS   
            
            # 将货币对合约资格设置为qualify，并下单
            ib = IB()
            #ib.setTimeout(950) ###设置超时时间,期望能够让TWS的重启在60秒内完成所有操作，如果超过60秒，就会抛出异常，程序就会停止运行#目前还没有用处
            try:
                await ib.connectAsync('127.0.0.1', 7497, client_id)  # 连接IB TWS######################################
                await asyncio.sleep(2)
                a = time.time()
                orderId = int(a)
                orderId_buy=int(a)+1
                if account == 1:
                    print('place order for', forex_contract, 'with client id', client_id, 'first time','order id',orderId)
                    high_trigger_price = float(self.high_prices[i].get())
                    low_trigger_price = float(self.low_prices[i].get())
                else:
                    print('place order for', forex_contract, 'with client id', client_id, 'again','order id',orderId)
                    high_trigger_price = high_trigger_price
                    low_trigger_price = low_trigger_price

                high_trigger_order = LimitOrder('SELL', float(self.amounts[i].get()) , high_trigger_price, orderId=orderId)
                low_trigger_order = LimitOrder('BUY',float(self.amounts[i].get()) , low_trigger_price, orderId=orderId_buy)
                high_trigger_order.tif='GTC'
                low_trigger_order.tif='GTC'
                if self.stop_flags[i] == True:
                    open_orders = ib.openOrders()
                    open_orders = [t for t in open_orders if t.orderId == orderId or t.orderId == orderId_buy]
                    for order in open_orders:
                        ib.cancelOrder(order)
                    text_box = self.text_box[i]    
                    text_box.delete(1.0, tk.END)
                    text_box.insert(tk.END, '订单已取消\n')
                    ib.disconnect()
                    self.tasks[i] = None
                    break

                #加一个先决条件：下单的价格一定是相对于当前市场价格的低买高卖，否则就不下单，取消连接并退出循环
                if high_trigger_price <  exchange_rate_list[i] or low_trigger_price > exchange_rate_list[i]:
                    text_box = self.text_box[i]    
                    text_box.delete(1.0, tk.END)
                    text_box.insert(tk.END, '当前制定的trigger price和当前的exchange rate存在冲突\n')
                    ib.disconnect()
                    self.tasks[i] = None
                    break        

                ib.placeOrder(forex, high_trigger_order)
                ib.placeOrder(forex, low_trigger_order)
                # 如果停止标志被设置，则取消订单并断开连接
                print ('place order',i,'done')

            except Exception as e:
                print('while true 1 exception:','order'+str(i))
                text_box = self.text_box[i]
                text_box.insert(tk.END,str(i)+'不能进行这个操作噢,即将取消这次操作,exception:')
                print ()
                break

            while True:
                try:    
                    if self.stop_flags[i] == True:
                        print ('stop order',i)
                        open_orders = ib.openOrders()
                        open_orders = [t for t in open_orders if t.orderId == orderId or t.orderId == orderId_buy]
                        for order in open_orders:
                            ib.cancelOrder(order)
                        text_box.delete(1.0, tk.END)
                        text_box.insert(tk.END, '订单已取消')
                        ib.disconnect()
                        self.tasks[i] = None
                        break
                    print('wait for order',i,' to be filled') 
                    await ib.reqCurrentTimeAsync() ###使得程序向TWS请求数据，从而及时发现TWS的断开连接
                    

                    total_usd = total_usd_list[i]
                    total_account = self.total_account[i]
                    total_account = cashbalance_inusd[i]   
                    exchange_rate = exchange_rate_list[i]
                    print(total_account)                    
                    text_box = self.text_box[i]
                    text_box.delete(2.0, tk.END)
                    text_box.insert(tk.END, '\n当日总成交美金:' + str(round(total_usd)) + '\ncash balance in usd:'+str(round(total_account))+'\nexchange rate:'+str(round((exchange_rate),4))) 


                    open_trades = ib.openTrades()
                    #### 使得可以不用手动改订单，就可以再次下pair trade
                    open_trades = [t for t in open_trades if t.order.orderId == orderId or t.order.orderId == orderId_buy] 
                    if len(open_trades) == 0:
                        print(str(i)+'no open trade now, place new pair')
                        await asyncio.sleep(2)
                        executions = ib.executions()
                        last_high_trade = [e for e in executions if e.orderId == orderId]
                        last_low_trade = [e for e in executions if e.orderId == orderId_buy]
                        last_trend = executions[0].side
                        print('last trend: ', last_trend)
                        print ('last high trade: ', last_high_trade)
                        print ('last low trade: ', last_low_trade)
                        last_high_price = last_high_trade[0].price
                        last_low_price = last_low_trade[0].price
                        print('last high price: ', last_high_price)
                        print('last low price: ', last_low_price)
                        move_step = abs(high_trigger_price - low_trigger_price)/2 ########
                        print('move step: ', move_step)
                        if last_trend == 'SLD':
                            print('last trend is SLD')
                            high_trigger_price =  last_high_price + move_step
                            low_trigger_price = last_low_price + move_step
                        elif last_trend == 'BOT':
                            high_trigger_price =  last_high_price - move_step
                            low_trigger_price = last_low_price - move_step   
                        text_box.insert(tk.END,'\nno open trade now, place new pair')    
                        break
                    # 如果只有一个交易，则等待另一个交易
                    if len(open_trades) == 1:
                        print(str(i)+'one trade filled, wait for another one')
                        for trade in open_trades:
                            order_status = trade.orderStatus.status
                            text_box = self.text_box[i]
                            print(str(i)+'order action:',trade.order.action,'order status: ', order_status)
                            text_box.insert(tk.END,'\none trade filled, wait for another one')
                            current_move_step = abs(high_trigger_price - low_trigger_price)/2
                            another_trade = ib.executions()
                            if trade.order.action == 'SELL':
                                    another_trade= [e for e in another_trade if e.orderId == orderId_buy]
                                    another_trade_price = another_trade[0].price
                                    text_box.insert(tk.END,'\norder action:'+str(trade.order.action)+
                                                    '\norder status: '+ str(order_status)+
                                                    '\ncurrent trigger_price: '+str(round(trade.order.lmtPrice,4))+
                                                    '\ncurrent move step: '+str(round(current_move_step,4))+
                                                    '\nnext trigger price pair would like to be:'+str(round((another_trade_price+current_move_step),4))+','+str(round((trade.order.lmtPrice+current_move_step),4)))
                            if trade.order.action == 'BUY':
                                    another_trade = [e for e in another_trade if e.orderId == orderId]
                                    another_trade_price = another_trade[0].price
                                    text_box.insert(tk.END,'\norder action:'+str(trade.order.action)+
                                                    '\norder status: '+ str(order_status)+
                                                    '\ncurrent trigger_price: '+str(round(trade.order.lmtPrice,4))+
                                                    '\ncurrent move step: '+str(round(current_move_step,4))+
                                                     '\nnext trigger price pair would like to be:'+str(round((trade.order.lmtPrice-current_move_step),4))+','+str(round((another_trade_price-current_move_step),4)))
                                
                        
                    # 如果两个订单都没有被填充，则等待两个订单都被填充
                    if len(open_trades) == 2:
                        print(str(i)+'no trade filled, wait for both trades to be filled')
                        text_box = self.text_box[i]
                        text_box.insert(tk.END,'\nno trade filled, wait for both trades to be filled')
                        for trade in open_trades:
                                order_status = trade.orderStatus.status
                                print(str(i)+'\norder action:',trade.order.action,'\norder status: ', order_status)
                                text_box = self.text_box[i]
                                text_box.insert(tk.END,'\norder action:'+trade.order.action+'\norder status: '+ order_status+'\ncurrent trigger_price: '+str(round(trade.order.lmtPrice,4)))

                    await asyncio.sleep(3)                

                except Exception as e:
                            retry = True
                            while retry:
                                try:
                                    if self.disconnection_as_except[i] == True:
                                        print ('disconnection_as_except',i)
                                        text_box = self.text_box[i]
                                        text_box.insert(tk.END, 'Decide to disconnect because this unexpected exceptions.')
                                        ib.disconnect()
                                        self.tasks[i] = None
                                        break
                                    print('while true 3 exception:','order',str(i),e)
                                    text_box = self.text_box[i]
                                    text_box.delete(1.0, tk.END)
                                    text_box.insert(tk.END, str(i)+',while true 3 exception')
                                    time.sleep(60)   
                                    print('already, start re-connecting..',str(i))
                                    #只有当re-start断开连接时，才需要重新连接，如果是其他的异常，就不需要重新连接
                                    is_connected = ib.client.isConnected()
                                    print('is_connected',str(is_connected),str(i))
                                    if is_connected == False: #设置筛选，使得只在断开连接（restart）时才重新连接
                                        print ('re-connected',str(i))
                                        await ib.connectAsync('127.0.0.1', 7497, client_id)  # 连接IB TWS#
                                    else:
                                        print ('Good morning, the connection is not lost, just wait please.')
                                        text_box = self.text_box[i]
                                        text_box.insert(tk.END, 'Good morning, the connection is not lost, just wait please.')
                                        pass
                                    text_box = self.text_box[i]
                                    text_box.insert(tk.END, '\n3: already wait for 60 seconds, reconnecting...碰撞已开始'+str(i))
                                    retry = False
                                except:
                                    print('order'+str(i)+'re-connecting failed, try again')
                                    retry = True


                # 断开IB TWS连接
            ib.disconnect()
            
    def stop_order(self, i):
        self.stop_flags[i] = True
        print(i)
        print(f"Stop flag set for {self.forex_contracts[i]}  order.")

    def disconnection(self,i):
        self.disconnection_as_except[i] = True
        print('disconnection_as_except set for',self.forex_contracts[i],'order')




if __name__ == '__main__':
    root = tk.Tk()
    app = ForexApp(root)
    root.mainloop()
    

