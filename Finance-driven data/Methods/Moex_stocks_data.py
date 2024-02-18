def get_stock_prices(stock_lst,start_date,end_date):
    #импортируем библиотеки для работы и АПИ Мосбиржи для парсинга цен
    import apimoex
    import requests
    import pandas as pd

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