# -*- coding: utf-8 -*-
"""
Created on Sun Feb  9 22:18:41 2020

@author: Robert E. Ruzzo III

The object of this script is to perform the following tasks:
1. Grab the current List of S&P 500 Company Tickers
2. Using the Yahoo Finance API, Download all the data for a given time period
   and save them to a csv. (open, high, low, close,volume, dividends, stock splits)
3. Update the data when called. In this case the update period will be calculated.
   If the data has not been updated in greater than 3 months, the data should be 
   refreshed using the original grab function, as opposed to the update function.
4. Using any pickle list of stock tickers, download or update the data accordingly.

5. Read a CSV with stock tickers and import them into a pickle file for use as above.

Notes:

Yahoo Finance acceptable time periods:
valid periods: 1d,5d,1mo,3mo,6mo,1y,2y,5y,10y,ytd,max
Valid intervals: 1m,2m,5m,15m,30m,60m,90m,1h,1d,5d,1wk,1mo,3mo
                Intraday data cannot extend last 60 days
"""

#imports

import bs4 as bs
import pickle
import requests
import os
import time
import yfinance as yf
import pandas as pd
from datetime import datetime
import glob as g
import sys

'''
Function Name: save_sp_500_tickers(data_directory)
Function Purpose: To get the current list of S&P500 ticker Symbols from wikipedia
                  and save them to a file tickers.pickle.
Arguments: data_directory: A string representing the data directory where pickle files containing tickers are stored
Output: sp500tickers.pickle
'''
def save_sp_500_tickers(data_directory):
    resp=requests.get('https://en.wikipedia.org/wiki/List_of_S%26P_500_companies')
    soup=bs.BeautifulSoup(resp.text, 'lxml')
    table=soup.find('table',{'class': 'wikitable sortable'})
    tickers=[]
    for row in table.findAll('tr')[1:]:
        ticker = row.findAll('td')[0].text.replace('.','-')
        ticker = ticker[:-1]
        tickers.append(ticker)
    if os.path.exists(data_directory+'sp500tickers.pickle'):
        os.remove(data_directory+'sp500tickers.pickle')
    with open(data_directory + "sp500tickers.pickle","wb") as f:
        pickle.dump(tickers,f)



'''
Function Name: update_ticker_prices_fromLast(data_directory,ticker_sub_directory,fileName)
Function Purpose: When given a pickle file with a list of ticker names, if a csv file exists in the ticker subdirectory,
                  then the function will check the last date in the file, download the data in a valid increment,
                  and update the file.
Arguments:  data_directory: A string representing the data directory where pickle files containing tickers are stored
            ticker_sub_directory: The sub folder that the csv files for each ticker will be stored
            fileName: A string representing name of the pickle file that contains the tickers, .pickle should be included
            delay: float - The delay time in seconds between ticker info downloads, 0.5 works well, not to anger the yahoo server
'''
def update_ticker_prices_fromLast(data_directory,ticker_sub_directory,fileName,delay):
    with open(data_directory + fileName,"rb") as f:
            tickers=pickle.load(f)
    for ticker in tickers:
        print("Updating Ticker: {}".format(ticker))
        if not os.path.exists(data_directory+ticker_sub_directory+'/{}.csv'.format(ticker)):
            print("Ticker File Not Found, Check directory, ticker name, or run get_data_from_yahoo()")
        else:
            delta, last_date=get_update_date_delta(data_directory,ticker_sub_directory,'{}'.format(ticker))
            if delta==0:
                print("No Update Needed for {}".format(ticker))
                continue
            if delta==1:
                update_period = "1d"
            if delta > 1 and delta < 32:
                update_period ="1mo"
            if delta > 31 and delta < 94:
                update_period ="3mo"
            if delta > 93: 
                print("It has been more than 3 Months since update, it would be more efficient to get new data. \nUse get_data_from_yahoo") 
                print("\nDays Since Last Update: {}  ".format(delta)) 
                continue
            with open(data_directory+ticker_sub_directory+'/{}.csv'.format(ticker),"a",newline='') as f:
                tick=yf.Ticker(ticker)
                df=tick.history(update_period)
                df['Adj Close'] = df['Close']
                df.index.name ="Date Time"
                df.drop(columns=['Dividends','Stock Splits'],axis=1, inplace=True)
                df.reset_index(inplace=True)
                #Depedent on Update Time, Get aftermarket volume info
                if update_period =="1d":
                    df.drop(df.index[1], inplace=True)  
                f.write(df.to_csv(date_format='%s',header=False, index=False))
                time.sleep(delay)
    

'''
Function Name: get_data_from_yahoo(data_directory,ticker_sub_directory,fileName,period,refresh,purge)
Purpose:  This function will take as an input a pickle file
          which it will open, take in all of the ticker names
          and download the information using the Yahoo Finance API.
Arguments:    data_directory: Data parent directory - this is where the pickle files should be stored
            ticker_sub_directory: String, data sub directory, this is where a csv for each of the tickers history will be stored
            fileName: String, file name of the pickle file that resides in the data_directory to read tickers from. The
                      default is sp500tickers.pickle, other pickle files in the same format can be used.
            period: This is the length of the history that you wish to download.
                    The following values are allowed for the Yahoo Finance API: 1d,5d,1mo,3mo,6mo,1y,2y,5y,10y,ytd,max
                    The default period is set to 1y or 1 year. The input is a string.
            refresh: Bool, if set to True, it will delete the file for each ticker, and re-download the data for the desired period.
            purge:   Bool, if set to True, ALL data files in the directory will be deleted, and then the data will be downloaded. This
                     function serves to delete old data that is in the directory that is no longer in use. IE after a watch list has changed.
            delay:   float - The delay time in seconds between ticker info downloads, 0.5 works well, not to anger the yahoo server
'''
def get_data_from_yahoo(data_directory,ticker_sub_directory,fileName,period,refresh,purge,delay):
    if not os.path.exists(data_directory+fileName):
        print(data_directory+fileName+" Not Found! Check Path and File Name! Exiting!")
        sys.exit()
    with open(data_directory + fileName,"rb") as f:
        tickers=pickle.load(f)
    if purge:
        files=g.glob(data_directory+ticker_sub_directory+'/*')
        print("Purging all files for a fresh clean start")
        for f in files:
            os.remove(f)
    if not os.path.exists(data_directory+ticker_sub_directory):
        os.makedirs(data_directory+ticker_sub_directory)
    for ticker in tickers:
        if not os.path.exists(data_directory+ticker_sub_directory+'/{}.csv'.format(ticker)):
            print("Getting Ticker: {}".format(ticker))
            tick=yf.Ticker(ticker)
            df=tick.history(period=period)
            df['Adj Close'] = df['Close']
            df.index.name ="Date Time"
            df.reset_index(inplace=True)
            df["Date Time"]=pd.to_datetime(df["Date Time"])
            df.drop(columns=['Dividends','Stock Splits'],axis=1, inplace=True)
            df.to_csv(data_directory+ticker_sub_directory+'/{}.csv'.format(ticker),date_format='%s', index=False)
            time.sleep(delay)
            continue
        if os.path.exists(data_directory+ticker_sub_directory+'/{}.csv'.format(ticker)) and refresh:
            print("Refreshing data for {}".format(ticker))
            os.remove(data_directory+ticker_sub_directory+'/{}.csv'.format(ticker))
            tick=yf.Ticker(ticker)
            df=tick.history(period)
            df['Adj Close'] = df['Close']
            df.index.name ="Date Time"
            df.reset_index(inplace=True)
            df["Date Time"]=pd.to_datetime(df["Date Time"])
            df.drop(columns=['Dividends','Stock Splits'],axis=1, inplace=True)
            df.to_csv(data_directory+ticker_sub_directory+'/{}.csv'.format(ticker),date_format='%s', index=False)
            time.sleep(delay)

'''
Function Name: get_data_from_yahoo_specific(data_directory,ticker_sub_directory,fileName,start,end,interval, refresh, purge)
Purpose:  This function will take as an input a pickle file
          which it will open, take in all of the ticker names
          and download the information using the Yahoo Finance API.
Arguments:    data_directory: Data parent directory - this is where the pickle files should be stored
            ticker_sub_directory: String, data sub directory, this is where a csv for each of the tickers history will be stored
            fileName: String, file name of the pickle file that resides in the data_directory to read tickers from. The
                      default is sp500tickers.pickle, other pickle files in the same format can be used.
            start:    A string in the format yyyy-mm-dd representing the desired start date
            end:      A string in the format yyyy-mm-dd representing the desired end date
            interval: A string representing the interval period for each data point. 
                      Valid intervals: 1m,2m,5m,15m,30m,60m,90m,1h,1d,5d,1wk,1mo,3mo
                      Intraday data cannot extend last 60 days
            refresh:  Bool, if set to True, it will delete the file for each ticker, and re-download the data for the desired period.
            purge:    Bool, if set to True, ALL data files in the directory will be deleted, and then the data will be downloaded. This
                      function serves to delete old data that is in the directory that is no longer in use. IE after a watch list has changed.
            delay:   float - The delay time in seconds between ticker info downloads, 0.5 works well, not to anger the yahoo server
'''
def get_data_from_yahoo_specific(data_directory,ticker_sub_directory,fileName,start,end,interval, refresh, purge, delay):
    if not os.path.exists(data_directory+fileName):
        print(data_directory+fileName+" Not Found! Check Path and File Name! Exiting!")
        sys.exit()
    with open(data_directory + fileName,"rb") as f:
        tickers=pickle.load(f)
    if purge:
        files=g.glob(data_directory+ticker_sub_directory+'/*')
        print("Purging all files for a fresh clean start")
        for f in files:
            os.remove(f)
    if not os.path.exists(data_directory+ticker_sub_directory):
        os.makedirs(data_directory+ticker_sub_directory)
    for ticker in tickers:
        if not os.path.exists(data_directory+ticker_sub_directory+'/{}.csv'.format(ticker)):
            print("Getting Ticker: {}".format(ticker))
            tick=yf.Ticker(ticker)
            df=tick.history(start=start,end=end,interval=interval)
            df['Adj Close'] = df['Close']
            df.index.name ="Date Time"
            df.reset_index(inplace=True)
            df["Date Time"]=pd.to_datetime(df["Date Time"])
            df.drop(columns=['Dividends','Stock Splits'],axis=1, inplace=True)
            df.to_csv(data_directory+ticker_sub_directory+'/{}.csv'.format(ticker),date_format='%s', index=False)
            time.sleep(delay)
            continue
        if os.path.exists(data_directory+ticker_sub_directory+'/{}.csv'.format(ticker)) and refresh:
            print("Refreshing data for {}".format(ticker))
            os.remove(data_directory+ticker_sub_directory+'/{}.csv'.format(ticker))
            tick=yf.Ticker(ticker)
            df=tick.history(start=start,end=end,interval=interval)
            df['Adj Close'] = df['Close']
            df.index.name ="Date Time"
            df.reset_index(inplace=True)
            df["Date Time"]=pd.to_datetime(df["Date Time"])
            df.drop(columns=['Dividends','Stock Splits'],axis=1, inplace=True)
            df.to_csv(data_directory+ticker_sub_directory+'/{}.csv'.format(ticker),date_format='%s', index=False)
            time.sleep(delay)
'''
Function Name: get_update_date_delta(data_directory,ticker_sub_directory,ticker)
Purpose: This function takes a ticker name string as an input and will open
         the appropriate csv file, and will return the time in days since last
         update as well as the date of the last update.
Arguments: data_directory: Data parent directory - this is where the pickle files should be stored
           ticker_sub_directory: String, data sub directory, this is where a csv for each of the tickers history will be stored
           ticker: String, the ticker symbol, ex Apple = 'AAPL'
Returns: int days, pandas datetime last_date yyyy-mm-dd
'''

def get_update_date_delta(data_directory,ticker_sub_directory,ticker):
    if not os.path.exists(data_directory+ticker_sub_directory+'/{}.csv'.format(ticker)):
            print("Ticker File Not Found, Run get_data_from_yahoo()")
    else:   
            today=datetime.now()
            df=pd.read_csv(data_directory+ticker_sub_directory+'/{}.csv'.format(ticker))
            df["Date Time"]=pd.to_datetime(df["Date Time"])
            last_date=df.tail(1)["Date Time"]
            difference = today - last_date
            return int(difference.astype('timedelta64[D]')), last_date


'''
Function Name: convert_tickers_csv_to_pickle(data_directory,csv_file)
Purpose: This function takes a csv file of one column with ticker names and creates a pickle
         file with the same name.
Arguments:  data_directory: String, Data parent directory - this is where the pickle files should be stored
            csv_file: String, name of the csv file to conver to pickle, include .csv in string, place file in the data_directory
                      The csv file should have the header of Ticker
Output: A pickle file containing the tickers
'''
def convert_tickers_csv_to_pickle(data_directory,csv_file):
    df=pd.read_csv(data_directory+csv_file)
    pickle_name=csv_file[:-4]+".pickle"
    tickers=df['Ticker']
    with open(data_directory + pickle_name,"wb") as f:
        pickle.dump(tickers,f)

'''
Function Name: add_ticker_to_pickle(data_directory,pickleFile,tickerName)
Purpose: This function allows you to add a ticker to a pickle file. Ex myWatchList.
Arguments: data_directory: String, Data parent directory - this is where the pickle files should be stored
           pickleFile: String, this is the name of the pickle file that contains tickers, that you will be adding a ticker to
           tickerName: String, the ticker symbol you wish to add to the pickle file
Note: This does not update the data, you should run get_data_from_yahoo() to do so
'''

def add_ticker_to_pickle(data_directory,pickleFile,tickerName):
    if os.path.exists(data_directory+pickleFile):
        with open(data_directory + pickleFile,"rb") as f:
            tickers=pickle.load(f) 
        tickers[len(tickers)]=tickerName
        os.remove(data_directory+pickleFile)
        with open(data_directory + pickleFile,"wb") as f:
            pickle.dump(tickers,f)
        print("{} ".format(tickerName)+ "Added to {}".format(pickleFile))

'''
Function Name: remove_ticker_from_pickle(data_directory,pickleFile, tickerName)
Purpose: This function is used to remove a ticker from a pickle file.
Arguments: data_directory: String, Data parent directory - this is where the pickle files should be stored
           pickleFile: String, this is the name of the pickle file that contains tickers, that you will be removing a ticker from
           tickerName: String, the ticker symbol you wish to remove from the pickle file
Note: This does not update the data, only the pickle, you should run
      get_data_from_yahoo() to do so. If you dont use the purge option while
      doing so, the old data will remain for tickers that no longer exist.
'''

def remove_ticker_from_pickle(data_directory,pickleFile, tickerName):
    if os.path.exists(data_directory+pickleFile):
        with open(data_directory + pickleFile,"rb") as f:
            tickers=pickle.load(f)
        for i in range (0,len(tickers)):
            if tickers[i]==tickerName:
                print("Removing ticker: {}".format(tickers[i]))
                tickers.drop(labels=i,inplace=True)
        os.remove(data_directory+pickleFile)
        with open(data_directory + pickleFile,"wb") as f:
            pickle.dump(tickers,f)



'''
Function Name: convert_tickers_df_to_pickle(data_directory,output_file,ticker_df)
Purpose: This function takes a pandas dataframe list of tickers with the column header Ticker and creates a pickle file
Arguments:  data_directory: String, Data parent directory - this is where the pickle files should be stored
            output_file: String, name of the output file, .pickle will be added, dont include
            ticker_df: a pandas dataframe that contains a list of tickers, with a Column name of Ticker          
Output: A pickle file containing the tickers
Example:  df = pd.DataFrame(data=['AAPL','IBM','OLED'], columns=['Ticker']) 
          convert_tickers_df_to_pickle('E:/Datasets/Stocks/','mythree',df)
'''
def convert_tickers_df_to_pickle(data_directory,output_file,ticker_df):
    pickle_name=output_file+".pickle"
    with open(data_directory + pickle_name,"wb") as f:
        pickle.dump(ticker_df['Ticker'],f)


