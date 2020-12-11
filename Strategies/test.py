# -*- coding: utf-8 -*-
"""
Created on Tue Jun 30 16:31:15 2020

@author: robru
"""

data_directory = "E:/Datasets/Stocks/"
ticker_sub_directory="SP500/"
fileName ="MyWatchList.csv"
delay = 0.5
period="1y"
start="2019-01-01"
end="2020-01-01"
interval="1d"
tickerName="IFSX"


import tickerdatautil_InProg
#tickerdatautil_InProg.save_sp_500_tickers("E:/Datasets/Stocks/")
#tickerdatautil_InProg.update_ticker_prices_fromLast(data_directory, ticker_sub_directory, fileName, delay)
#tickerdatautil_InProg.get_data_from_yahoo(data_directory,ticker_sub_directory,fileName,period,True,False,delay)
#tickerdatautil_InProg.get_data_from_yahoo(data_directory,ticker_sub_directory,fileName,period,False,True,delay)
#tickerdatautil_InProg.get_data_from_yahoo_specific(data_directory,ticker_sub_directory,fileName,start,end,interval, False, True, delay)
#tickerdatautil_InProg.add_ticker_to_csv(data_directory,fileName,tickerName)
#tickerdatautil_InProg.remove_ticker_from_csv(data_directory,fileName, tickerName)