import pyalgotrade.strategy as strategy
import pyalgotrade.technical.ma as ma

#moving average model
class MovingAverageStrategy(strategy.BacktestingStrategy):

    def __init__(self,feed,instrument,nfast):
        super(MovingAverageStrategy,self).__init__(feed)
        self.feed=feed
        #we can track the position: long or short positions
        #if it is None we know we can open one
        self.position = None
        #the given stock (for example AAPL)
        self.instrument = instrument
        #fast moving average indicator (short-term trend) period is smaller
        self.fastMA = ma.SMA(feed[instrument].getPriceDataSeries(),nfast)
        self.stop_loss=0
        self.fill_price=0
        self.risk_percent=2
        self.BUDGET_USE=0
        self.INITIAL_BUDGET=0
        self.printInfo=False
        self.fastMASlope=0
        
        
    def getFastMA(self):
        return self.fastMA
    
    def initBackTestStrategy(self,initialBudget):
        strategy.BacktestingStrategy.__init__(self, self.feed, initialBudget)
        
    def setBudgetUse(self,budgetUse):
        self.BUDGET_USE=budgetUse
    
    def setRiskPercent(self,risk_percent):
        self.risk_percent=risk_percent
        
    def setInfoOutput(self,printInfo):
        self.printInfo=printInfo
        
    #this is where the MA strategy is implemented
    #this method is called when new bars are available
    #when fast > slow MA -> open a long position 
    #when fast < slow MA -> close the long position
    def onBars(self,bars):
        bar = bars[self.instrument]
        equity = self.getBroker().getCash()
        equity_use = equity*self.BUDGET_USE
        max_risk=self.risk_percent*equity_use*.01
        #MA with period p needs p previous values ... if not available then return (for the first p-1 bars the value is NULL)
        
        if self.fastMA[-1] is None:
            return
        #if we have not opened a long position so far then we open one
        if self.position is None:
            #When Price Action is above sma 9 buy, else sell
            if self.fastMA[-1] < bar.getPrice():
                shares=int(equity_use//bar.getPrice())
                risk_per_share = max_risk/shares
                self.stop_loss=bar.getPrice()-risk_per_share
                self.fill_price=bar.getPrice()
                self.position = self.enterLong(self.instrument,shares,True)
        
        elif self.fastMA[-1] >  bar.getPrice() or bar.getPrice()<=self.stop_loss:
            #exit the long position
            self.position.exitMarket()
            self.position = None
        

    
    #when we open a long position this function is called
    def onEnterOk(self,position):
        if self.printInfo:
            trade_info = position.getEntryOrder().getExecutionInfo()
            shares= position.getShares()
            self.info("Buy stock at $%.2f"%(trade_info.getPrice()))

            
        
    #when we close the long position this function is called
    def onExitOk(self,position):
        if self.printInfo:
            trade_info = position.getExitOrder().getExecutionInfo()
            self.info("Sell stock at $%.2f"%(trade_info.getPrice()))
    
