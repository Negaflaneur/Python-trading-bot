from cProfile import label
from email import header
from lib2to3.pgen2.token import PERCENT
from turtle import update
from binance.client import Client
from binance import ThreadedWebsocketManager
import time
from datetime import datetime
import os
from numpy import sign
import pandas as pd
from binance.enums import *
import btalib
import numpy as np
import requests

btc_prices = {'error': False}
closes=[]

def get_historical_price(symbol, interval, lookback):
    #getting price data candles since the timestamp
    klines = client.get_historical_klines(symbol, interval, lookback, limit=5000)
    #deleting unnecessary price data, leaving only 6 lines
    for line in klines:
        del line[6:]
    btc_historical_price_df = pd.DataFrame(klines, columns=['date','open', 'high', 'low', 'close', 'volume'])
    btc_historical_price_df['date'] = pd.to_datetime(btc_historical_price_df['date'], unit='ms') 
    btc_historical_price_df.to_csv('historical_price.csv')
    return btc_historical_price_df

def create_order_book():
    trades = client.get_all_orders(symbol='BTCUSDT')
    trades = list(trades)
    print("YOur orders are ...", trades)
    orders_book = pd.DataFrame(trades)
    orders_book['time'] = pd.to_datetime(orders_book['time'], unit='ms')
    orders_book.set_index('time', inplace=True)
    orders_book = orders_book.drop(columns=['orderListId', 'clientOrderId', 'price', 'status', 'timeInForce', 'type', 'stopPrice', 'icebergQty', 'updateTime', 'isWorking', 'origQuoteOrderQty'])
    orders_book.to_csv('orderbook.csv')
    return orders_book

def read_order_book():
    order_book_coll= create_order_book()
    order_book = pd.read_csv('orderbook.csv', index_col=0)
    #print(order_book)
    print(order_book_coll)

def get_indicators(df):
    macd = btalib.macd(df, pfast=12, pslow=26, psignal=9)
    df = df.join([macd.df])

    df['AF'] = 0.02
    df['PSAR'] = df['low']
    df['EP'] = df['high']
    df['PSARdir'] = 'bull'

    #calculating SAR value
    for a in range(1, len(df)):
        if df.loc[df.index[a-1], 'PSARdir'] == 'bull':
            #calculating SAR value in the bull market
            df.loc[df.index[a], 'PSAR'] = df.loc[df.index[a-1], 'PSAR'] + df.loc[df.index[a-1], 'AF']*(df.loc[df.index[a-1], 'EP']-df.loc[df.index[a-1], 'PSAR'])        

            df.loc[df.index[a], 'PSARdir'] = "bull"
            #checking if the market has reversed to a bear trend
            if df.loc[df.index[a], 'low'] < df.loc[df.index[a-1], 'PSAR']:
                df.loc[df.index[a], 'PSARdir'] = "bear"
                df.loc[df.index[a], 'PSAR'] = df.loc[df.index[a-1], 'EP']
                df.loc[df.index[a], 'EP'] = df.loc[df.index[a-1], 'low']
                df.loc[df.index[a], 'AF'] = .02

            else:
                #calculating a new extreme point and adjusting the acceleration factor
                if df.loc[df.index[a], 'high'] > df.loc[df.index[a-1], 'EP']:
                    df.loc[df.index[a], 'EP'] = df.loc[df.index[a], 'high']
                    if df.loc[df.index[a-1], 'AF'] <= 0.18:
                        df.loc[df.index[a], 'AF'] =df.loc[df.index[a-1], 'AF'] + 0.02
                    else:
                        #if the acceleration factor reaches the maximum value of 0.2 we reasign it
                        df.loc[df.index[a], 'AF'] = df.loc[df.index[a-1], 'AF']
                elif df.loc[df.index[a], 'high'] <= df.loc[df.index[a-1], 'EP']:
                    df.loc[df.index[a], 'AF'] = df.loc[df.index[a-1], 'AF']
                    df.loc[df.index[a], 'EP'] = df.loc[df.index[a-1], 'EP']               


        #calculating SAR in a bear market
        elif df.loc[df.index[a-1], 'PSARdir'] == 'bear':

            df.loc[df.index[a], 'PSAR'] = df.loc[df.index[a-1], 'PSAR'] - df.loc[df.index[a-1], 'AF']*(df.loc[df.index[a-1], 'PSAR']-df.loc[df.index[a-1], 'EP'])

            df.loc[df.index[a], 'PSARdir'] = "bear"
            #checking if the market has reversed to a bull market
            if df.loc[df.index[a], 'high'] > df.loc[df.index[a-1], 'PSAR']:
                df.loc[df.index[a], 'PSARdir'] = "bull"
                df.loc[df.index[a], 'PSAR'] = df.loc[df.index[a-1], 'EP']
                df.loc[df.index[a], 'EP'] = df.loc[df.index[a-1], 'high']
                df.loc[df.index[a], 'AF'] = .02

            else:
                #otherwise, calculating a new extreme point and adjusting the acceleration factor
                if df.loc[df.index[a], 'low'] < df.loc[df.index[a-1], 'EP']:
                    df.loc[df.index[a], 'EP'] = df.loc[df.index[a], 'low']
                    if df.loc[df.index[a-1], 'AF'] <= 0.18:
                        df.loc[df.index[a], 'AF'] = df.loc[df.index[a-1], 'AF'] + 0.02
                    else:
                        #if the acceleration factor reaches the maximum value of 0.2 we reasign it
                        df.loc[df.index[a], 'AF'] = df.loc[df.index[a-1], 'AF']
                        #otherwise, calculating new extreme point
                elif df.loc[df.index[a], 'low'] >= df.loc[df.index[a-1], 'EP']:
                    df.loc[df.index[a], 'AF'] = df.loc[df.index[a-1], 'AF']
                    df.loc[df.index[a], 'EP'] = df.loc[df.index[a-1], 'EP']           
    return df

class Trading_Strategy:

    def __init__(self,signal):
        self.signal = signal

    def signals(self):
        buy = []
        sell = []
        flag = -1

        for i in range(0, len(self.signal)):
            if (self.signal ['histogram'][i] > 0) and (self.signal ['histogram'][i] > self.signal ['histogram'][i-1]) and (self.signal['macd'][i] < -10.0) and (self.signal['PSARdir'][i] == 'bull'):
                #if the trend is bull and the histogram value is higher than 0, we append the order to the buy list
                sell.append(np.nan)
                if flag != 1:
                    buy.append(self.signal['close'][i])
                    #the flag is set to 1 to indicate that we have already opened a trade
                    flag = 1
                else:
                    buy.append(np.nan)
            elif (self.signal['histogram'][i] < 0) and (self.signal['histogram'][i] < self.signal['histogram'][i-1]) and (self.signal['macd'][i] > 10.0) and (self.signal['PSARdir'][i] == 'bear'):
                #if the trend is bearish and the histogram value is below 0, we append the order to the sell list
                #append value NaN to the buy list in this case
                buy.append(np.nan)
                if flag != 0:
                    sell.append(self.signal['close'][i])
                    #the flag is set to 1 to indicate that we have already opened a trade
                    flag = 0
                else:
                    #otherwise, append NaN value to the sell list
                    sell.append(np.nan)
            else:
                #if all the conditions fail, we append NaN value to both lists
                buy.append(np.nan)
                sell.append(np.nan)
        return (buy, sell)
    
    def Get_orders_dataframe(self):
        signals_instant = self.signals()
        order_df = pd.DataFrame()
        order_df = self.signal
        order_df = order_df.drop(columns=['volume', 'AF'])
        order_df['buy'] = signals_instant[0]
        order_df['sell'] = signals_instant[1]
        return order_df

def Combine_all_strategies():
    btc_price_frame = get_historical_price('BTCUSDT', '1m', '1 hours GMT')

    #reading the price file we have created and setting the index to represent dates
    indicator_frame = pd.read_csv('historical_price.csv', index_col=0)
    indicator_frame.set_index('date', inplace=True)

    #calling the get_indicators function and printing the result
    indicators = get_indicators(indicator_frame)

    signals_inst = Trading_Strategy(indicators)
    signals_inst = signals_inst.Get_orders_dataframe()
    
    return signals_inst

def create_price_log(df):
    entry_prices = df
    entry_prices.to_csv('lastprice.csv')
    entry_prices = pd.read_csv('lastprice.csv')
    entry_prices.reset_index(drop=True, inplace=True)
    return entry_prices

def Place_Order(df, pair, btc_balance, usdt_balance, open_postion_buy=False, open_position_sell=False):

    btc_trade_quantity = float(btc_balance) *(1.0/100.0)
    usdt_trade_quantity = float(usdt_balance) * (1.0/100.0)
    btc_trade_quantity = round(btc_trade_quantity, 6)
    usdt_trade_quantity = round(usdt_trade_quantity, 6)
    btc_balance = float(btc_balance)
    usdt_balance = float(usdt_balance)
    print("BTC trade quantity is ", btc_trade_quantity)
    print("Usdt trade quantity is", usdt_trade_quantity)

    prices_df = pd.DataFrame()

    if (open_postion_buy == False) or (open_position_sell == False):
        df = Combine_all_strategies()
        df = df.drop(columns=['PSAR', 'EP'])
        btc_usdt_postion_size = round(usdt_trade_quantity/float(df['close'].iloc[-1]), 6) # usdt position size
        print(f'The current close price is ' + str(df['close'].iloc[-1]))
        print(df.tail())
        #if we have a buy signal and our balance does not equal 0, we open a buy trade
    if (df['buy'].iloc[-1] == df['close'].iloc[-1]) and (open_position_sell == False) and (open_postion_buy == False) and (usdt_balance != 0):
        order = client.create_order(symbol=pair, side='BUY', type='MARKET', quantity=btc_usdt_postion_size)
        open_postion_buy = True
        open_position_sell = False
        buy_pos_quantity = btc_usdt_postion_size #record the postion size in btc
        read_order_book()
        
        prices_df['buy_entry_price'] = order['fills'][0]['price']
        create_price_log(prices_df)

        print(order)
        buy_price = float(order['fills'][0]['price'])
        print(buy_price)
        print("Position size is ", buy_pos_quantity)
        # setting a stop loss
        stop_loss_price = buy_price - 100.0
        take_profit_price = buy_price + 40.0
    while (open_postion_buy) and (open_position_sell != True):
        #while we have a buy trade open, we update the price
        time.sleep(3)
        df = Combine_all_strategies()
        df['entry_b_p'] = order['fills'][0]['price']
        print('The stop price is ', stop_loss_price)
        print('The take profit price is ', take_profit_price)
        print('The buy price is ', str(order['fills'][0]['price'] ))
            
        print(f'Buy trade open')
        print(df.tail())
        # if we have a signal for selling, we close the buy order
        if (float(df['histogram'].iloc[-1]) < -2.0) or (float(df['close'].iloc[-1]) > take_profit_price) or (float(df['close'].iloc[-1]) <stop_loss_price) and(open_postion_buy):
            order = client.create_order(symbol = pair, side='SELL', type='MARKET', quantity=buy_pos_quantity)
            read_order_book()

            prices_df['buy_close_price'] = order['fills'][0]['price']
            create_price_log(prices_df)

            print('You have closed the order', order)
            open_postion_buy = False
            #printing the close price
            df['close__b_p'] = order['fills'][0]['price']
            print(df.tail())
            break
    #otherwise, if we get a sell signal, we place a sell order at a market price
    if (df['sell'].iloc[-1] == df['close'].iloc[-1]) and (open_position_sell == False) and (open_postion_buy == False) and (btc_balance != 0):
        order = client.create_order(symbol=pair, side='SELL', type='MARKET', quantity=btc_trade_quantity)
        read_order_book()

        prices_df['sell_entry_price'] = order['fills'][0]['price']
        create_price_log(prices_df)

        open_position_sell = True
        open_postion_buy = False
        #printing out the details of the order
        print(order)
        buy_price = float(order['fills'][0]['price'])
        print(buy_price)
        #setting the stop loss 
        stop_loss_price = buy_price + 100.0
        take_profit_price = buy_price - 40.0
    while (open_position_sell) and (open_postion_buy != True):
        time.sleep(5)
        df = Combine_all_strategies()
        df['entry_s_p'] = order['fills'][0]['price']
        print("The sell stop loss is ", stop_loss_price)
        print('The take profit price is ', take_profit_price)
        print('The order price is ', str(order['fills'][0]['price']))
            
        print(f'You have entered a sell order, ,the current close price is  ' + str(df['close'].iloc[-1]))
        print(df.tail())
        #if we get a signal to close the sell order or if the price hits the stop loss, we close it
        if (float(df['histogram'].iloc[-1]) > 2.0) or (float(df['close'].iloc[-1]) < take_profit_price) or  (float(df['close'].iloc[-1]) > stop_loss_price) and(open_position_sell):
            order = client.create_order(symbol = pair, side='BUY', type='MARKET', quantity=btc_trade_quantity)
            read_order_book()

            prices_df['sell_close_price'] = order['fills'][0]['price']
            create_price_log(prices_df)


            print('You have closed the order', order)
            open_position_sell = False
            #printing the close price
            df['close_s_p'] = order['fills'][0]['price']
            print(df.tail())
            break 

#initialising API keys and creating an object client
api_key = os.environ.get('binance_key')
api_secret = os.environ.get('binance_secret')
client = Client(api_key, api_secret, testnet=True, requests_params={"timeout": 5})

#initialising the websocket
bsm = ThreadedWebsocketManager(api_key, api_secret, testnet=True)
bsm.start()

#subscribing to a stream of data
#bsm.start_symbol_ticker_socket(callback=current_btc_price, symbol='BTCUSDT')


#printing the BTC balance
btc_balance = client.get_asset_balance(asset='BTC')
usdt_balance = client.get_asset_balance(asset="USDT")
print("Your BTC balance is " + str(btc_balance))
print('Your USDT balance is ' + str(usdt_balance))

#getting the earliest timestap
timestamp = client._get_earliest_valid_timestamp('BTCUSDT', '15m')
print(timestamp)

combine_strategies = Combine_all_strategies()
print(combine_strategies)

#defining the BTC and USDT balances
btc_trade_balance = btc_balance['free']
usdt_trade_balance = usdt_balance['free']
#calling the function for a test
place_order = Place_Order(combine_strategies, 'BTCUSDT', btc_trade_balance, usdt_trade_balance)
print(place_order)

read_order_book()

while True:
    #calling a function in a continuous loop to execute trades with 5 seconds delay update
    try:
        Place_Order(combine_strategies, 'BTCUSDT', btc_trade_balance, usdt_trade_balance)
        time.sleep(3)
    except requests.exceptions.ReadTimeout:
        time.sleep(5)
        print("time out occured")
        pass


