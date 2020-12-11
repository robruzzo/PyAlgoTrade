'''
This script is employed to run a simple strategy on a list of tickers

TODO: More documentation 
      Exception handling for bad data
      Get Better Data
'''

import tickerdatautil as td
import sma_9_strategy_backtest as sma_9
import pyalgotrade.plotter as plotter
import pyalgotrade.barfeed.csvfeed as csvfeed
import pyalgotrade.bar as bar
import pyalgotrade.stratanalyzer.returns as ret
import pyalgotrade.stratanalyzer.sharpe as sharpe
import pyalgotrade.stratanalyzer.trades as trades
from pyalgotrade.broker import backtesting
import os
import pickle
import sys
import pandas as pd




#settings for updating the ticker data
period ="1y" #Default Initial Yahoo Finance Download Period
delay=0.5	 #Default Delay between downloads in seconds
data_directory='E:/Datasets/Stocks/' #Include the trailing '/'
fileName ="MyWatchList.pickle" #Default File Name For updating
ticker_sub_directory ='MyWatchList'
start_date='2020-01-01'
end_date='2020-06-29'
interval='1d'

#Update or redownload ticker data, uncomment to do so
#Update Tickers
#td.update_ticker_prices_fromLast(data_directory,ticker_sub_directory,fileName,delay)


#Purge Tickers and Redownload
#td.add_ticker_to_pickle(data_directory,pickleFile=fileName,tickerName='AMD')
#td.get_data_from_yahoo(data_directory, ticker_sub_directory, fileName, period, False, True, delay)


#Set the initial portfolio size
INITIAL_BUDGET = 1600
#How much of our budget will we use on this instrument for buying shares
BUDGET_USE = 0.50
#How Much we want to risk, to set a stop
RISK_PERCENT=2
#Stock List File
pickle_file ='MyWatchList.pickle'
#The Data directory
pickle_directory ="E:\\Datasets\\stocks\\"
tickerFile=pickle_directory+pickle_file
data_directory='E:\\Datasets\\stocks\\MyWatchList\\'
save_plots=True
plot_dpi=200
outputInfo=False
save_results=True
save_errors=True
results_directory='C:\\Users\\robru\\Documents\\Python Scripts\\PyAlgoTrade\\Strategies\\Results\\'
plots_directory=results_directory+'plots\\'
results_filename='WatchListsma9_5y'

if __name__ == "__main__":
    
    results = pd.DataFrame(columns=['Ticker', 'Initial Equity', 'Net P/L', 'Annualized Sharpe', 'Trades Made',
                                    'Avg P/L', 'Max Profit', 'Max Loss', 'Annual Ret', 'Final Equity'])
    
    errors = pd.DataFrame(columns=['Ticker', 'Section', 'Error'])
    
    if not os.path.exists(tickerFile):
        print(tickerFile+" Not Found! Check Path and File Name! Exiting!")
        sys.exit()
    with open(tickerFile,"rb") as f:
        tickers=pickle.load(f)
    if not os.path.exists(plots_directory):
        os.makedirs(plots_directory)
    for ticker in tickers:
        try:

            file_name=data_directory+ticker+'.csv'
            #we want to predict the S&P500 (^GSPC index)
            #second MA indicator tracks the fast trend with period 9
            fastPeriod = 9
    
            #the data is in the CSV file (one row per day)
            feed = csvfeed.GenericBarFeed(bar.Frequency.DAY)
            feed.addBarsFromCSV(ticker,file_name)
    
            #this is where we define the time for the moving average models (slow and fast)
            movingAverageStrategy = sma_9.MovingAverageStrategy(feed,ticker,fastPeriod)
            #Set Initial Budget
            movingAverageStrategy.initBackTestStrategy(INITIAL_BUDGET)
            #Set Risk Percent, default is 2
            movingAverageStrategy.setRiskPercent(RISK_PERCENT)
            #Set budget useage
            movingAverageStrategy.setBudgetUse(BUDGET_USE)
            #we can define the cost of trading (cost pre trade)
            movingAverageStrategy.getBroker().setCommission(backtesting.FixedPerTrade(0.1))
            #Turn on or off the trade print output
            movingAverageStrategy.setInfoOutput(outputInfo)
        
            #Prepare plots
            plot = plotter.StrategyPlotter(movingAverageStrategy,plotAllInstruments=True,plotBuySell=True,plotPortfolio=True)
            plot.getInstrumentSubplot(ticker).addDataSeries('Fast SMA',movingAverageStrategy.getFastMA())
        
            #we can analyze the returns during the backtest
            returnAnalyzer = ret.Returns()
            movingAverageStrategy.attachAnalyzer(returnAnalyzer)
    
            #we can analyze the Sharpe ratio during backtest
            sharpeRatioAnalyzer = sharpe.SharpeRatio()
            movingAverageStrategy.attachAnalyzer(sharpeRatioAnalyzer)
    
            #we can analyze the trades (maximum profit or loss etc.)
            tradesAnalyzer = trades.Trades()
            movingAverageStrategy.attachAnalyzer(tradesAnalyzer)
    
            #let's run the strategy on the data (CSV file) so let's backtest the algorithm
            movingAverageStrategy.run()
        
            tradesProfits = tradesAnalyzer.getAll()
        except:
            e = sys.exc_info()[0]
            #print("Ticker: ", ticker," Error: %s" % e)
            errors = errors.append({'Ticker':ticker,'Section':'Trades','Error':e}, ignore_index=True)
        
        try:
            results = results.append({'Ticker':ticker , 'Initial Equity':INITIAL_BUDGET, 'Net P/L':tradesAnalyzer.getAll().sum(),
                                  'Annualized Sharpe':sharpeRatioAnalyzer.getSharpeRatio(0.0), 
                                  'Trades Made':tradesAnalyzer.getCount(),'Avg P/L':tradesProfits.mean(),
                                     'Max Profit':tradesProfits.max(), 'Max Loss':tradesProfits.min(), 
                                     'Annual Ret':returnAnalyzer.getCumulativeReturns()[-1]*100,
                                     'Final Equity':movingAverageStrategy.getBroker().getEquity()},ignore_index=True)
        except:
            e = sys.exc_info()[0]
            #print("Error in results, Ticker: ", ticker," Error: %s" % e)
            errors = errors.append({'Ticker':ticker,'Section':'Results','Error':e},ignore_index=True)
       
        if save_plots:
            #we want to plot the stock (instrument) with the buy/sell orders
            plot.savePlot(plots_directory+ticker+'.png', dpi=plot_dpi, format='png')
        
        
        
    if save_results:
        print("Saving Results.....")
        results=results.sort_values(by=['Annual Ret'], ascending=False)
        results.to_csv(results_directory+results_filename+'.csv', index=False)
    
    if save_results:
        print("Saving Exception Log.....")
        errors.to_csv(results_directory+results_filename+'errors'+'.csv', index=False)

    print(results)
        