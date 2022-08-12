import pandas as pd
import numpy as np
import ta
import time
from binance import Client
import config

client = Client(config.API_KEY, config.SECRET_KEY)

RSI_PERIOD = 14
RSI_treshold = 50
OVERBOUGHT = 80
OVERSOLD = 20
TRADE_SYMBOL = 'ETHUSDT'
TRADE_QUANTITY = 0.01
LOOKBACK = 100
K_LINE_WINDOW = 14
K_LINE_SMOOTH = 3


def get_minute_data(symbol, interval, lookback):
    frame = pd.DataFrame(client.get_historical_klines(symbol,
                                                      interval,
                                                      str(lookback) + ' min ago UTC'))
    frame = frame.iloc[:, :6]
    frame.columns = ['Time', 'Open', 'High', 'Low', 'Close', 'Volume']
    frame.index = pd.to_datetime(frame['Time'], unit='ms')
    frame = frame.drop('Time', axis=1)
    frame = frame.astype(float)

    return frame


def apply_technicals(df):
    df['%K'] = ta.momentum.stoch(df.High, df.Low, df.Close, window=K_LINE_WINDOW, smooth_window=K_LINE_SMOOTH)
    df['%D'] = df['%K'].rolling(K_LINE_SMOOTH).mean()
    df['rsi'] = ta.momentum.rsi(df.Close, window=RSI_PERIOD)
    df['macd'] = ta.trend.macd_diff(df.Close)
    df = df.dropna()
    return df


class Signals:
    def __init__(self, df, lags):
        self.df = df
        self.lags = lags

    def gettrigger(self):
        dfx = pd.DataFrame()
        for i in range(self.lags + 1):
            mask = (self.df['%K'].shift(i) < OVERSOLD) & (self.df['%D'].shift(i) < OVERSOLD)
            dfx = pd.concat([dfx, mask], axis=1, ignore_index=True)
        return dfx.T.sum(axis=0)

    def decide(self):
        self.df['trigger'] = np.where(self.gettrigger(), 1, 0)

        self.df['Buy'] = np.where((self.df['trigger']) &
                                  (self.df['%K'].between(OVERSOLD, OVERBOUGHT)) &
                                  (self.df['%D'].between(OVERSOLD, OVERBOUGHT)) &
                                  (self.df['rsi'] > RSI_treshold) &
                                  (self.df['macd'] > 0), 1, 0)


def strategy(pair, qty, open_position=False):
    df = get_minute_data(pair, '1m', LOOKBACK)
    df = apply_technicals(df)
    inst = Signals(df, 5)
    inst.decide()
    print(f'Current Close is ' + str(df['Close'].iloc[-1]))
    if df['Buy'].iloc[-1]:
        order = client.create_order(symbol=pair,
                                    side='BUY',
                                    type='MARKET',
                                    quantity=qty)
        print(order)
        buyprice = float(order['fills'][0]['price'])
        open_position = True
        while open_position:
            time.sleep(0.5)
            df = get_minute_data(pair, '1m', '2')
            print(f'Current Close is ' + str(df['Close'].iloc[-1]))
            print(f'Current Target is ' + str(buyprice * 1.005))
            print(f'Current Stop is ' + str(buyprice * 0.995))
            if df['Close'][-1] <= buyprice * 0.995 or df['Close'][-1] >= 1.005 * buyprice:
                order = client.create_order(symbol=pair,
                                            side='SELL',
                                            type='MARKET',
                                            quantity=qty)
                print(order)
                break


while True:
    strategy(TRADE_SYMBOL, TRADE_QUANTITY)
    time.sleep(0.5)
