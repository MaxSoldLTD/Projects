#Импортируем нужные библиотеки
import apimoex
import requests
import pandas as pd
import yfinance as yf
import datetime as dt
import matplotlib.pyplot as plt
import numpy as np

def get_stock_prices(stock_lst,start_date,end_date):

    #Задаём пустой список, куда будем размещать индекс Мосбиржи, чтобы прогнать его отдельным методом
    indexes = []

    #Отдельно выносим из общего списка индекс Мосбиржи, если его указали в списке
    try:
        for i in stock_lst:
            if i == 'IMOEX':
                indexes.append(i)
                stock_lst.remove(i)
            else:
                pass
    except:
        pass

    dataframe = pd.DataFrame()

    with requests.Session() as session:
        #Получаем данные по историческим ценам акций
        try:
            for t in stock_lst:
                prices = apimoex.get_board_history(session,t)
                prices = pd.DataFrame(prices)
                prices.set_index('TRADEDATE', inplace=True)
                prices = prices['CLOSE']
                prices = prices.rename(t)
                dataframe = pd.concat([dataframe,prices], axis = 1)
        except:
            pass
        #Получаем данные по историческим ценам индекса, если такой тикер указан
        try:
            for i in indexes:
                prices = apimoex.get_board_history(session,i,engine='stock',market='index',board = 'SNDX')
                prices = pd.DataFrame(prices)
                prices.set_index('TRADEDATE', inplace=True)
                prices = prices['CLOSE']
                prices = prices.rename(i)
                dataframe = pd.concat([dataframe,prices], axis = 1)
        except:
            pass

    dataframe.index.name = 'Date'
    dataframe = dataframe.sort_index(ascending=False)
    dataframe = dataframe.loc[(dataframe.index >= start_date) & (dataframe.index <= end_date)]

    return dataframe

def analyse_stock_price(stock_lst, start_date, end_date, type = 'IMOEX', const = -1):
    # Добавляем к списку
    stock_lst.append('IMOEX')
    # Импортируем котировки цен на нефть, стоимость доллара и евро к рублю
    brent = yf.download('BZ=F', '2010-01-01', dt.datetime.now())['Adj Close'].sort_index(ascending=False)
    brent = brent.rename('Brent')
    usdrub = yf.download('RUB=X', '2010-01-01', dt.datetime.now())['Adj Close'].sort_index(ascending=False)
    usdrub.rename('USD', inplace=True)
    eurrub = yf.download('EURRUB=X', '2010-01-01', dt.datetime.now())['Adj Close'].sort_index(ascending=False)
    eurrub.rename('EUR', inplace=True)
    futures_currency_data = pd.concat([brent, usdrub], axis=1)
    futures_currency_data = pd.concat([futures_currency_data, eurrub], axis=1)
    futures_currency_data = futures_currency_data.sort_index(ascending=False)
    futures_currency_data.index = futures_currency_data.index.astype(str)

    #С помощью функции get_stock_prices забираем данные о ценах акций
    dataframe = get_stock_prices(stock_lst,start_date,end_date)

    # Соединяем данные нефти и валют с осноным датафреймом
    dataframe = pd.merge(dataframe, futures_currency_data[futures_currency_data.index.isin(list(dataframe.index))],
                         left_index=True, right_index=True)

    # Рассчитываем корреляционные матрицы, логарифмические доходности, меру риска VAR по каждой бумаге
    try:
        #Считаем среднюю доходность за период
        returns = dataframe[(dataframe.index >= start_date) & (dataframe.index <= end_date)]
        returns = returns.sort_index(ascending=True)
        returns = returns.pct_change()
        returns = returns.dropna(how='all')
        returns = returns.dropna(how='all', axis=1)
        returns = round(returns, 4) * 100
        returns = returns.sort_index(ascending=False)

        mean_returns = returns.median()
        mean_returns = round(mean_returns, 2)

        #Волатильность бумаги за выбранный период
        min_periods = 7
        data_tickers = list(dataframe.columns)
        empty_dict = dict()
        for i in data_tickers:
            vol = dataframe[i].rolling(min_periods).std() * np.sqrt(min_periods)
            vol = vol.median()
            empty_dict[i] = vol
        volatility = pd.DataFrame.from_dict(empty_dict, orient='index')
        volatility[0] = round(volatility[0], 2)
        volatility = volatility.rename(columns={0: f'{min_periods} volatility'})

        # Формируем датасеты с корреляцией по разным периодам
        corr = dataframe[(dataframe.index >= start_date) & (dataframe.index <= end_date)].dropna(axis=1).corr()

        # Ищем наибольшие корреляции с выбранном параметром Type за нужный период

        #Рисуем столбчатую диаграмму для наглядной оценки корреляции
        corr = corr[abs(corr[type]) >= const]
        corr = corr.sort_values(by=type, ascending=True)

        groups = list(corr.index)
        fig, ax = plt.subplots(figsize=(8, 8))

        bars = plt.barh(groups, corr[type])

        ax.bar_label(bars)

        #plt.show()

        #Создаём финальный датафрейм с результатом расчётов всех параметров
        #Удаляем лишние колонки из датафрейма
        deleting_external_values = ['EUR', 'USD', 'IMOEX', 'Brent']

        final = corr[[type]]
        final.rename(columns={f'{type}': f'Correl {type}'})

        final = f'Расчёты за период с {dataframe.dropna(axis=1).index.min()} по {dataframe.dropna(axis=1).index.max()} \n' \
                f'{final[~final.index.isin(deleting_external_values)].round(2)}'
    except:
        final = f'Введённого значения {type} нет в списке. \n' \
                f'Вы можете выбрать значение среди {list(corr.index)}'

    return final
