from dataclasses import dataclass
import pandas as pd
import math
from ta.momentum import KAMAIndicator
from ta.trend import SMAIndicator


def algorithm_calc(ticker='Si', ama_fast = 2, ama_slow = 95, ama_int = 40,\
    ma_period = 8, ma_incline = 0.305, ma_incline_int = 6, c_long = 1,\
    c_short = 1, type='filtered', brief=True):
   
    path = 'forts/' + ticker + '.xlsx'
    data = pd.read_excel(path)
    data = data.drop(columns=['<PER>', 'Пробел'])
    data.rename(columns = {'<DATE>' : 'date', '<TIME>' : 'time',\
    '<OPEN>' : 'open', '<HIGH>' : 'high', '<LOW>' : 'low',\
    '<CLOSE>' : 'close', '<TICKER>' : 'ticker'}, inplace = True)

    data['median'] = (data['high'] + data['low'])/2

    ama = KAMAIndicator(data['median'], ama_int, ama_fast, ama_slow)
    data['ama'] = ama.kama()
    sma = SMAIndicator(data['median'], ma_period)
    data['ma'] = sma.sma_indicator()
    
    data['d1'] = data['median'] - data['ama']
    data['d2'] = data['median'].shift(1) - data['ama'].shift(1)

    data['angle'] = (data['ma'] - data['ma'].shift(ma_incline_int))/data['ma']*100
    
    #Расставляем сигналы и целевые позиции
    signal_list = []
    signal = ''
    tf = 'flat'
    position_virt = 'out'
    position = 'out'
    # пробегаемся по строкам таблицы
    for row in data.index:
        #проверяем сигналы на покупку/продажу
        if data['d1'].loc[row] > 0 and data['d2'].loc[row] > 0:
            signal = 'buy'
        elif data['d1'].loc[row] < 0 and data['d2'].loc[row] < 0:
            signal = 'sell'
        else:
            signal = ''
        #проверяем условие на тренд        
        if abs(data['angle'].loc[row]) <= ma_incline:
            tf='flat'
        else:
            tf='trend'
        #выводим целевую позицию
        if signal == 'buy':
            position_virt = 'long'
        elif signal == 'sell':
            position_virt = 'short'
        elif len(signal_list) > 0:
            position_virt = signal_list[-1][2]
        else:
            position_virt = 'out'
    
        if tf == 'flat':
            position = 'out'
        else:
            position = position_virt
        # создаём кортеж
        item = (signal, tf, position_virt, position) 
        # добавляем кортеж в список
        signal_list.append(item) 
    # создаём вспомогательную таблицу
    signals = pd.DataFrame(
        signal_list,
        columns=['signal', 'tf', 'position_virt', 'position']
    )
    
    data = pd.concat([data, signals], axis=1)
    data = data.drop(columns=['d1', 'd2', 'angle'])
        
    # рассчитываем портфель
    
    if type == 'filtered':
        pos_col = 'position'
    elif type == 'unfiltered':
        pos_col = 'position_virt'
    
    portfolio_list = []
    paper_num = 0.0
    cash = 1000000.0
    portfolio = 0.0
    # пробегаемся по строкам таблицы
    for row in data.index:
        portfolio = paper_num*data['close'].loc[row]+cash
        deal = 0
        #проверяем сигналы на покупку/продажу
        if row > 0 and data[pos_col].loc[row] != data[pos_col].loc[row-1]:
            deal = 1
            if data[pos_col].loc[row] == 'long':
                paper_num = math.floor(portfolio*c_long/data['close'].loc[row])
                cash = portfolio - paper_num*data['close'].loc[row]
            elif data[pos_col].loc[row] == 'short':
                paper_num = -math.floor(portfolio*c_short/data['close'].loc[row])
                cash = portfolio - paper_num*data['close'].loc[row]
            elif data[pos_col].loc[row] == 'out':
                paper_num = 0
                cash = portfolio
        # создаём кортеж
        item = (paper_num, cash, portfolio, deal) 
        # добавляем кортеж в список
        portfolio_list.append(item) 
    # создаём вспомогательную таблицу
    portfolio_df = pd.DataFrame(
        portfolio_list,
        columns=['paper_num', 'cash', 'portfolio', 'deals']
    )
    portfolio_df['portfolio'] = portfolio_df['portfolio']/portfolio_df['portfolio'].loc[0]
    portfolio_df = portfolio_df.drop(columns=['paper_num', 'cash'])  
        
    data = pd.concat([data, portfolio_df], axis=1)
  
    # рассчитываем просадки и максимумы
    dropdown_list = []
    maximum = 0.0
    dropdown = 0.0
    maximum_dropdown = 0.0
    # пробегаемся по строкам таблицы
    for row in data.index:
        if data['portfolio'].loc[row] > maximum:
            maximum = data['portfolio'].loc[row]
        dropdown = -(1 - data['portfolio'].loc[row]/maximum)
        if dropdown < maximum_dropdown:
            maximum_dropdown = dropdown
        # создаём кортеж
        item = (maximum, dropdown, maximum_dropdown) 
        # добавляем кортеж в список
        dropdown_list.append(item) 
    # создаём вспомогательную таблицу
    dropdown_df = pd.DataFrame(
        dropdown_list,
        columns=['maximum', 'dropdown', 'maximum_dropdown']
    )

    data = pd.concat([data, dropdown_df], axis=1)
    
    hist_frame = 14*21*3
    data['m_hist'] = data['portfolio'].diff(hist_frame)/data['portfolio'].shift(hist_frame)*10000/hist_frame
    data['m_fut'] = -data['portfolio'].diff(-hist_frame)/data['portfolio']*10000/hist_frame

    quality = {
        "yr rate": data['portfolio'].iloc[-1]**(14*21*12/data['portfolio'].count())-1 if data['portfolio'].iloc[-1]>0 else 0,
        "dd mean": dropdown_df['dropdown'].mean(),
        "dd max": dropdown_df['dropdown'].min(),
        "correlation": data[['m_hist', 'm_fut']].corr()['m_hist']['m_fut'],
        "deals": data['deals'].sum(),
        "records": data['portfolio'].count(),
        "flat ratio": data['tf'].value_counts(normalize=True)['flat']
    }
            
    if brief:
        return quality
    else:
        return data