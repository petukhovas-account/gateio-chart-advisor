import numpy as np
import pandas as pd
import pandas_ta as ta
import requests
import json
import math
import mplfinance as mpf
import datetime as dt

# Пара валют 
CURRENCY_BASE = 'BLOK'
CURRENCY_QUOTE = 'USDT'
symbol = CURRENCY_BASE + '_' + CURRENCY_QUOTE

#Интервал данных с лимитом
interval = '1d'
limit = 200

#Период эксп.скользящей средней Хала
ehma_period = 33

#Загрузка данных с биржи Binance, преобразование в формат json
root_url = 'https://api.gateio.ws/api/v4/spot/candlesticks'
url = root_url + '?currency_pair=' + symbol + '&interval=' + interval + '&limit=' + str(limit)
candles = requests.get(url)
data = json.loads(candles.text)

#Данные в таблицу
df = pd.DataFrame(data)
df.columns = ['open_time', 'Volume', 'Close', 'High', 'Low', 'Open']
df.index.name = 'DatetimeIndex'
df.index = [dt.datetime.fromtimestamp(int(x)) for x in df.open_time]
df['Open'] = df['Open'].astype(float)
df['High'] = df['High'].astype(float)
df['Low'] = df['Low'].astype(float)
df['Close'] = df['Close'].astype(float)
df['Volume'] = df['Volume'].astype(float)

#Расчёт эксп.скользящей средней Хала 
n2ma = 2 * ta.ema(df['Close'], length = round(ehma_period/2))
nma = ta.ema(df['Close'], length = ehma_period)
diff = n2ma - nma
sqn = round(math.sqrt(ehma_period))
n1 = ta.ema(diff, length = sqn)
n1 = n1.replace(np.nan, 0)
#print(n1)

#Расчёт маркеров сигнала buy
signal_buy = []
preprevious = -1.0; previous = 0.0
for date,value in n1.iteritems():
    if value > previous and previous < preprevious:
       signal_buy.append(df['Close'][date])
    else: 
        signal_buy.append(np.nan)
    preprevious = previous; previous = value
#Расчёт маркеров сигнала sell
signal_sell = []
preprevious = -1.0; previous = 0.0
for date,value in n1.iteritems():
    if value < previous and previous > preprevious:
       signal_sell.append(df['Close'][date])
    else: 
        signal_sell.append(np.nan)
    preprevious = previous; previous = value

#Вывод графика
n1 = n1.replace(0, np.nan)
apdict = [mpf.make_addplot(n1, secondary_y=False),
          mpf.make_addplot(signal_buy,type='scatter', markersize=100, color = 'green', alpha = 0.5, marker='^'),
          mpf.make_addplot(signal_sell,type='scatter', markersize=100, color = 'red', alpha = 0.5, marker='v')         ]
set_title = symbol+' at Gate.io (last '+str(limit)+' days, '+ str(interval) +' timeframe) w/EHMA('+str(ehma_period)+')'
mpf.plot(df, type = 'candle', style = 'yahoo', title = set_title, ylabel = CURRENCY_BASE+', price in '+CURRENCY_QUOTE, addplot = apdict)
mpf.show()