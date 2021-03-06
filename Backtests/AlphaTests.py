#!/usr/bin/env python
# coding: utf-8

# In[23]:


import pandas as pd
from matplotlib.pyplot import *
from statistics import mean


# In[1]:


class AlphaBacktest:
    def __init__(self,options,prices):
        self.options = pd.read_csv(options)
        self.prices = pd.read_csv(prices)
        self.construct_features()
        try:
            self.batch = options.split("-")[3].split(".")[0]
            stk = options.split("-")[0]
            if "PE" in options:
                self.result_name = stk+"-options-CE-"+self.batch+".csv"
            else:
                self.result_name = stk+"-options-PE-"+self.batch+".csv"
        except:
            pass
    
    def construct_features(self):
        self.options["Alpha"] = (self.prices["Close"] - self.options["Strike Price"]) / self.options["Close"]
        self.prices["Change"] = ((self.prices["Close"] - self.prices["Open"]) / self.prices["Close"])*100
        # options["Alpha-Prev"] = options.Alpha.shift(1)
        self.options["Alpha-Change"] = ((self.options["Alpha"] - self.options.Alpha.shift(1)) / self.options["Alpha"])*100
        self.options["Alpha-Mean"] = (self.options.Alpha.shift(1)+self.options.Alpha.shift(2)+self.options.Alpha.shift(3)) / 3
        self.options["Change"] = ((self.options["Close"] - self.options["Open"]) / self.options["Open"])*100
        
        for index,row in self.options.iterrows():
            if row["Change"] == "inf":
                row["Change"] = 0
        
    def find_optimal_threshold(self,toPrint=False):
        threshold = 0.3
        max_profit = 0
        optimal_thresh = 0
        while(threshold <= 2):
            net_result = 0
            threshold += 0.01
            for index,rows in self.options.iterrows():
                if index == 0 or rows["LTP"] == 0 or self.options["LTP"][index-1] == 0:
                    continue
                if (rows["Alpha"] / rows["Alpha-Mean"]) > threshold:
        #             print("Buy!")
                    if index+1 < len(self.options.index):
                        result = 0
                            
                        #Take profit -> 30%
                        if self.options["High"][index+1] >= self.options["Open"][index+1]*1.3:
                            result = 30
                        
                        #Stop loss -> -10%
                        elif self.options["Low"][index+1] <= self.options["Open"][index+1] * 0.9:
                            result = -10
                        
                        #Square off position
                        else:
                            result = self.options["Change"][index+1]
                        
                        net_result += result
            if net_result >= max_profit:
                max_profit = net_result
                optimal_thresh = threshold
        
        if toPrint:
            print("Net profit : " + str(max_profit))
            print("Optimal Threshold: " + str(optimal_thresh))
            print("")
        return optimal_thresh
    
    def find_net_returns(self,thresh,toPrint=False,verbose=False):
        net_result = 0
        wins = 0
        losses = 0
        total_trades = 0
        max_drawdown = 0
        compound_result = 1
        total_loss = 0
        total_profit = 0
        for index,rows in self.options.iterrows():
                if index == 0 or rows["LTP"] == 0 or self.options["LTP"][index-1] == 0:
                    continue
                # Do not execute trade is ratio is double the threshold
                if (rows["Alpha"] / rows["Alpha-Mean"]) > thresh and (rows["Alpha"] / rows["Alpha-Mean"]) < thresh*2:
                    total_trades += 1
        #             print("Buy!")
                    if index+1 < len(self.options.index):
                        result = 0
                            
                        #Take profit -> 30%
                        # Buying on the open of the next day
                        if self.options["High"][index+1] >= self.options["Open"][index+1] * 1.3:
                            result = 30
                        # Take all loss if target is not hit
                        else:
                            result = self.options["Change"][index+1]
                        
                        #Stop loss -> -10%
#                         elif self.options["Low"][index+1] <= self.options["Open"][index+1] * 0.9:
#                             result = -10
                        
#                         #Square off position
#                         else:
#                             result = self.options["Change"][index+1]
                        
                        #Calculate Accuracy
                        if result > 0:
                            wins += 1
                            total_profit += result
                        else:
                            losses += 1
                            total_loss += abs(result)
                            if abs(result) > abs(max_drawdown):
                                max_drawdown = result
                            
                        net_result += result
                        compound_result = compound_result * (1+(result/100))
        if toPrint:
            print("Net Profit: " + str(net_result))
            if total_trades > 0: print("Accuracy: " + str((wins/total_trades)*100) + "%")
            print("Total Trades: " + str(total_trades))
            print("Compunded Result: " + str(compound_result))
            print("")
        if verbose:
            return [net_result,max_drawdown,total_loss,total_profit]
        else:
            return net_result
    
    def get_result(self,index):
        df = pd.read_csv(self.result_name)
        df["Change"] = ((df["Close"] - df["Open"]) / df["Open"]) * 100
        return df["Change"][index]
        
    def plot_scatter(self,threshold,limit=99999,retData=False):
        if limit == 99999:
            limit = threshold*2
        X = []
        Y = []
        output = ""
        for index,rows in self.options.iterrows():
            if index == 0 or rows["Open"] == 0 or rows["LTP"] == 0 or self.options["LTP"][index-1] == 0:
                continue
            ratio = rows["Alpha"] / rows["Alpha-Mean"]
            if ratio >= threshold and ratio < limit:
                if index+1 < len(self.options.index):
#                     result = self.options["Change"][index+1]
                    result = self.get_result(index+1)

                    if result > 0:
                        scatter(index,ratio,color="green")
                    else:
                        scatter(index,ratio,color="red")
                    if retData:
                        ratio = rows["Alpha"] / rows["Alpha-Mean"]
                        output += str(rows["Date"])+","+str(rows["Expiry"])+","+str(rows["Strike Price"])+","+str(result)+","+str(rows["Alpha"])+","+str(rows["Alpha-Mean"])+","+str(rows["Alpha"] / rows["Alpha-Mean"])+"\n"
        if retData:
            return output
                    


# In[10]:


class Loader:
    def __init__(self,options,prices):
        # List of all options and prices files mapped to each other
        self.options = options
        self.options_2 = []
        if "PE" in options[0]:
            for x in options:
                self.options_2.append(x.replace("PE","CE"))
        elif "CE" in options[0]:
             for x in options:
                self.options_2.append(x.replace("CE","PE"))
        self.prices = prices
        self.backtests = []
        for i in range(0,len(options)):
            self.backtests.append(AlphaBacktest(options[i],prices[i]))
    
    def find_individual_optimal_threshold(self):
        thresholds = []
        for test in self.backtests:
            thresholds.append(test.find_optimal_threshold())
        mean_thresh = mean(thresholds)
        print("Mean Threshold : %f"%(mean_thresh))
        return thresholds
    
    def find_net_returns(self,thresh):
        returns = []
        for test in self.backtests:
            test_return = test.find_net_returns(thresh)
            returns.append(test_return)
        return sum(returns)
    
    def maximize_returns(self):
        # Return threshold,returns, max drawdown, total loss, total profit
        returns = 0
        threshold = 0.3
        max_drawdown = 0
        optimal_threshold = 0
        total_loss = 0
        total_profit = 0
        
        while(threshold <= 2):
            threshold += 0.01
            batch_returns = []
            tmp_total_loss = 0
            tmp_total_profit = 0
            batch_drawdowns = []
            for test in self.backtests:
                cur_batch_returns, cur_max_drawdown, cur_total_loss, cur_total_profit = test.find_net_returns(threshold,False,True)
                batch_returns.append(cur_batch_returns)
                batch_drawdowns.append(cur_max_drawdown)
                tmp_total_loss += cur_total_loss
                tmp_total_profit += cur_total_profit
            
            if sum(batch_returns) > returns:
                returns = sum(batch_returns)
                max_drawdown = min(batch_drawdowns)
                total_loss = tmp_total_loss
                total_profit = tmp_total_profit
                optimal_threshold = threshold
        
        return [optimal_threshold,returns,max_drawdown,total_loss,total_profit]
    
    def minimize_losses(self,minimize_drawdown=False):
        # Return threshold,returns,max drawdown,total loss, total profit
        returns = 0
        threshold = 0.3
        max_drawdown = 99999
        drawdown = -999999
        optimal_threshold = 0
        total_loss = 999999
        total_profit = 0
        
        while(threshold <= 2):
            threshold += 0.01
            batch_returns = []
            batch_drawdowns = []
            tmp_total_loss = 0
            tmp_total_profit = 0
            for test in self.backtests:
                cur_batch_returns, cur_max_drawdown, cur_total_loss, cur_total_profit = test.find_net_returns(threshold,False,True)
                batch_returns.append(cur_batch_returns)
                batch_drawdowns.append(cur_max_drawdown)
                tmp_total_loss += cur_total_loss
                tmp_total_profit += cur_total_profit
            
            if minimize_drawdown:
                if abs(min(batch_drawdowns)) < abs(max_drawdown):
                    returns = sum(batch_returns)
                    max_drawdown = min(batch_drawdowns)
                    total_loss = tmp_total_loss
                    total_profit = tmp_total_profit
                    optimal_threshold = threshold
            else:
                if abs(tmp_total_loss) < abs(total_loss):
                    returns = sum(batch_returns)
                    max_drawdown = min(batch_drawdowns)
                    total_loss = tmp_total_loss
                    total_profit = tmp_total_profit
                    optimal_threshold = threshold
            
        return [optimal_threshold,returns,max_drawdown,total_loss,total_profit]
    
    def plot_scatter(self,threshold,limit=999999):
        with open("trades.csv","w") as trades:
            trades.write("Date,Expiry,Strike Price,Returns,Alpha,Alpha-Mean,Ratio"+"\n")
        for test in self.backtests:
            data = test.plot_scatter(threshold,limit,True)
            with open("trades.csv","a") as trades:
                trades.write(data)
        
        self.create_xlsx()
    
    def create_xlsx(self):
        df1 = pd.read_csv("trades.csv")
        options_df = []
        for i in self.options:
            tmp = pd.read_csv(i)
            options_df.append(tmp)

        options_2_df = []
        for i in self.options_2:
            tmp = pd.read_csv(i)
            options_2_df.append(tmp)
        
        prices_df = []
        for i in self.prices:
            tmp = pd.read_csv(i)
            prices_df.append(tmp)
        
        df2 = pd.concat(options_df)
        df3 = pd.concat(options_2_df)
        df4 = pd.concat(prices_df)
        
        df4 = df4[~df4.index.duplicated()]
        df2 = df2[~df2.index.duplicated()]
        df3 = df3[~df3.index.duplicated()]
        
        df2["Alpha"] = (df4["Close"] - df2["Strike Price"]) / df2["Close"]
        df2["Alpha-Change"] = ((df2["Alpha"] - df2.Alpha.shift(1)) / df2["Alpha"])*100
        df2["Alpha-Mean"] = (df2.Alpha.shift(1)+df2.Alpha.shift(2)+df2.Alpha.shift(3)) / 3
        df2["Change"] = ((df2["Close"] - df2["Open"]) / df2["Open"])*100
        df2["Ratio"] = df2["Alpha"] / df2["Alpha-Mean"]
        
        df3["Alpha"] = (df4["Close"] - df3["Strike Price"]) / df3["Close"]
        df3["Alpha-Change"] = ((df3["Alpha"] - df3.Alpha.shift(1)) / df3["Alpha"])*100
        df3["Alpha-Mean"] = (df3.Alpha.shift(1)+df3.Alpha.shift(2)+df3.Alpha.shift(3)) / 3
        df3["Change"] = ((df3["Close"] - df3["Open"]) / df3["Open"])*100
        df3["Ratio"] = df3["Alpha"] / df3["Alpha-Mean"]
        
        df4["Change"] = ((df4["Close"] - df4["Open"]) / df4["Close"])*100
        
        writer = pd.ExcelWriter("results.xlsx",engine='xlsxwriter')
        
        df1.to_excel(writer,sheet_name="trades")
        df2.to_excel(writer,sheet_name="puts chain")
        df3.to_excel(writer,sheet_name="calls chain")
        df4.to_excel(writer,sheet_name="prices")
        
        writer.save()


# In[20]:


# options = ["banknifty-options-1.csv",
#           "banknifty-options-2.csv"]
# prices = ["banknifty-prices-1.csv",
#          "banknifty-prices-2.csv"]


# In[21]:


# loader = Loader(options,prices)


# In[22]:


# loader.plot_scatter(1.5,10)


# In[ ]:





# In[3]:


# a = "banknifty-options-CE-1.csv"


# In[7]:


# a.split("-")[3].split(".")[0]


# In[2]:


# "banknifty-options-PE-1.csv".replace("PE","CE")


# In[ ]:





# In[ ]:




