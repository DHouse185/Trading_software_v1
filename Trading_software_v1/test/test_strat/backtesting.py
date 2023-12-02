##########  Python IMPORTs  ############################################################
import typing
import pandas as pd
import numpy as np
import os
########################################################################################
##########  Created files IMPORTS  #####################################################
import root_variables as r_var
########################################################################################

class BackTest:
    """
    parameters example: {'Strategy': 'Breakout',
                        'Pair': 'SUSHIUSDT', 
                        'Exchange': 'BinanceUS', 
                        'Client': <initiate.connectors.binance_us.BinanceUSClient object at 0x00000216B896E9D0>, 
                        'TimeFrame': '15m', 
                        'Balance_percent': '100', 
                        'Take_Profit': '2', 
                        'Stop_Loss': '1', 
                        'From_Time': 1682920800000, 
                        'To_Time': 1684562400000, 
                        'Extra_Parameters': {'min_volume': <PyQt6.QtWidgets.QLineEdit object at 0x00000216C1524D30>}}
    """
    def __init__(self, data: pd.DataFrame, parameters: typing.Dict):
        base_default_params = r_var.DEFAULT_BACKTEST_PARAMETERS
        self.balance = base_default_params["Balance"]["Default"]
        self.balance_percentage = base_default_params["Balance_percent"]["Default"]
        self.take_profit = base_default_params["Take_Profit"]["Default"]
        self.stop_loss = base_default_params["Stop_Loss"]["Default"]
         
        for params in parameters:
            if params == "Balance":
                self.balance = round(float(parameters[params]), 2)
            if params == "Balance_percent":
                self.balance_perc = round(float(parameters[params]), 2)
            if params == "Take_Profit":
                self.take_profit = round(float(parameters[params]), 3)
            if params == "Stop_Loss":
                self.stop_loss = round(float(parameters[params]), 3) 

        test_dataframe = []
        test_dataframe = pd.DataFrame(test_dataframe, columns=['Enter',
                                                               'Exit',
                                                               'Signal / No Signal',
                                                               'Entry Price',
                                                               'Side',
                                                               'Balance',
                                                               'Shares',
                                                               'PnL'], index=data.index)      
        self.testing_dataframe = pd.concat([data, test_dataframe], axis=1) 
        
        # get data float length:
        max_float_length = 0
        
        for i, j in data["close"].iteritems():
            try:
                num_float_length = len(str(j).split(".")[1])
                
                max_float_length = max(max_float_length, num_float_length)
                
            except IndexError:
                num_float_length = 0
                
                max_float_length = max(max_float_length, num_float_length)
        
        self.rounding = max_float_length
        self.rounding_exp = 10**(int(-max_float_length + 1))
        print(self.rounding_exp)
            
        

    def take_profit_calc(self, entry_price=None, side=None) -> float:
        """ Calculation for take profit based on trade side and entry price"""
        if side == 1:
            take_profit = round(float(entry_price + (entry_price * (self.take_profit / 100))), self.rounding)
            return take_profit
        
        elif side == -1:
            take_profit = round(float(entry_price - (entry_price * (self.take_profit / 100))), self.rounding)
            return take_profit
        
        else:
            return None

    def stop_loss_cal(self, entry_price=None, side=None) -> float:
        """ Calculation for stop loss based on trade side and entry price"""
        if side == 1:
            stop_loss = round(float(entry_price - (entry_price * (self.stop_loss / 100))), self.rounding)
            return stop_loss
        
        elif side == -1:
            stop_loss = round(float(entry_price + (entry_price * (self.stop_loss / 100))), self.rounding)
            return stop_loss
        
        else:
            return None
        
        
    def enter_exit_trade(self):
        take_profit_value = 0
        stop_loss_value = 0
        self.pnl = 0
        current_trade_pnl = 0
        prev_candle_pnl = 0
        max_pnl = 0
        self.max_drawdown = 0 
        
        for idx, i in enumerate(self.testing_dataframe.index):
            prev_index = self.testing_dataframe.index[idx - 1] 
            
            if i == self.testing_dataframe.index[0]:
                self.testing_dataframe.loc[i, "Balance"] = self.balance
                
            else:
                
                check = self.testing_dataframe.loc[i, 'close']
                if not pd.isna(check):
                    # LONG Stop Loss hit          
                    if self.testing_dataframe.loc[prev_index, 'Side'] == 1 \
                    and (stop_loss_value in np.arange(self.testing_dataframe.loc[i, 'low'], self.testing_dataframe.loc[i, 'high'], self.rounding_exp)
                    or self.testing_dataframe.loc[i, 'open'] <= stop_loss_value):
                        
                        # Exit LONG Trade
                        self.testing_dataframe.loc[i, "Exit"] = "Exit"
                        self.testing_dataframe.loc[i, "Side"] = 0
                        
                        # Update Balance
                        self.testing_dataframe.loc[i, "Shares"] = 0 
                        self.testing_dataframe.loc[i, "Balance"] = self.testing_dataframe.loc[prev_index, "Balance"] \
                                                                + ((self.testing_dataframe.loc[prev_index, 'Entry Price'] \
                                                                - (self.testing_dataframe.loc[prev_index, 'Entry Price'] \
                                                                * (self.stop_loss / 100))) \
                                                                * self.testing_dataframe.loc[prev_index, "Shares"]) 
                                                                
                        invested_balance = self.testing_dataframe.loc[prev_index, "Shares"] * self.testing_dataframe.loc[prev_index, 'Entry Price']
                        # Calc PnL
                        current_trade_pnl = float((((stop_loss_value 
                                                    - self.testing_dataframe.loc[prev_index, "Entry Price"]) 
                                                    * self.testing_dataframe.loc[prev_index, "Shares"]) 
                                                    / invested_balance) * 100)
                        
                        prev_candle_pnl = float((((self.testing_dataframe.loc[prev_index, "close"]
                                                - self.testing_dataframe.loc[prev_index, "Entry Price"]) 
                                                * self.testing_dataframe.loc[prev_index, "Shares"]) 
                                                / invested_balance) * 100)
                        
                        if np.isnan(prev_candle_pnl):
                            prev_candle_pnl = 0
                            
                        diff = round(current_trade_pnl - prev_candle_pnl, 4)
                        self.pnl += diff
                        self.testing_dataframe.loc[i, "PnL"] = self.pnl

                    # LONG Take Profit hit
                    elif self.testing_dataframe.loc[prev_index, 'Side'] == 1 \
                    and (take_profit_value in np.arange(self.testing_dataframe.loc[i, 'low'], self.testing_dataframe.loc[i, 'high'], self.rounding_exp)
                    or self.testing_dataframe.loc[i, 'open'] >= take_profit_value):
                        
                        # Exit LONG Trade
                        self.testing_dataframe.loc[i, "Exit"] = "Exit"
                        self.testing_dataframe.loc[i, "Side"] = 0
                        
                        # Update Balance
                        self.testing_dataframe.loc[i, "Shares"] = 0 
                        self.testing_dataframe.loc[i, "Balance"] = self.testing_dataframe.loc[prev_index, "Balance"] \
                                                                    + ((self.testing_dataframe.loc[prev_index, 'Entry Price'] \
                                                                    + (self.testing_dataframe.loc[prev_index, 'Entry Price'] \
                                                                    * (self.take_profit / 100))) \
                                                                    * self.testing_dataframe.loc[prev_index, "Shares"])  
                                                                    
                        invested_balance = self.testing_dataframe.loc[prev_index, "Shares"] * self.testing_dataframe.loc[prev_index, 'Entry Price']                                            
                        # Calc PnL
                        current_trade_pnl = float((((take_profit_value
                                                    - self.testing_dataframe.loc[prev_index, "Entry Price"]) 
                                                    * self.testing_dataframe.loc[prev_index, "Shares"]) 
                                                    / invested_balance) * 100)
                        
                        prev_candle_pnl = float((((self.testing_dataframe.loc[prev_index, "close"]
                                                - self.testing_dataframe.loc[prev_index, "Entry Price"]) 
                                                * self.testing_dataframe.loc[prev_index, "Shares"]) 
                                                / invested_balance) * 100)
                        
                        if np.isnan(prev_candle_pnl):
                            prev_candle_pnl = 0
                            
                        diff = round(current_trade_pnl - prev_candle_pnl, 4)
                        self.pnl += diff
                        self.testing_dataframe.loc[i, "PnL"] = self.pnl
                
                    # SHORT Stop Loss hit         
                    elif self.testing_dataframe.loc[prev_index, 'Side'] == -1 and (stop_loss_value \
                    and self.testing_dataframe.loc[i, 'close'] != None \
                    in np.arange(self.testing_dataframe.loc[i, 'low'], self.testing_dataframe.loc[i, 'high'], self.rounding_exp)
                    or self.testing_dataframe.loc[i, 'open'] >= stop_loss_value):
                        
                        # Exit SHORT Trade
                        self.testing_dataframe.loc[i, "Exit"] = "Exit"
                        self.testing_dataframe.loc[i, "Side"] = 0
                        
                        # Update Balance
                        self.testing_dataframe.loc[i, "Shares"] = 0 
                        self.testing_dataframe.loc[i, "Balance"] = self.testing_dataframe.loc[prev_index, "Balance"] \
                                                                - ((self.testing_dataframe.loc[prev_index, 'Entry Price'] \
                                                                + (self.testing_dataframe.loc[prev_index, 'Entry Price'] \
                                                                * (self.stop_loss / 100))) \
                                                                * self.testing_dataframe.loc[prev_index, "Shares"]) 
                        
                        invested_balance = self.testing_dataframe.loc[prev_index, "Shares"] * self.testing_dataframe.loc[prev_index, 'Entry Price']  
                        # Calc PnL
                        current_trade_pnl = float((((self.testing_dataframe.loc[prev_index, "Entry Price"]
                                                    - stop_loss_value)
                                                    * self.testing_dataframe.loc[prev_index, "Shares"]) 
                                                    / invested_balance) * 100)
                        
                        prev_candle_pnl = float((((self.testing_dataframe.loc[prev_index, "Entry Price"] 
                                                - self.testing_dataframe.loc[prev_index, "close"])
                                                * self.testing_dataframe.loc[prev_index, "Shares"]) 
                                                / invested_balance) * 100)
                        
                        if np.isnan(prev_candle_pnl):
                            prev_candle_pnl = 0
                            
                        diff = round(current_trade_pnl - prev_candle_pnl, 4)
                        self.pnl += diff
                        self.testing_dataframe.loc[i, "PnL"] = self.pnl
                                
                    # SHORT Take Profit hit
                    elif self.testing_dataframe.loc[prev_index, 'Side'] == -1 and (take_profit_value \
                    and self.testing_dataframe.loc[i, 'close'] != None \
                    in np.arange(self.testing_dataframe.loc[i, 'low'], self.testing_dataframe.loc[i, 'high'], self.rounding_exp) 
                    or self.testing_dataframe.loc[i, 'open'] <= take_profit_value):
                        
                        # Exit SHORT Trade
                        self.testing_dataframe.loc[i, "Exit"] = "Exit"
                        self.testing_dataframe.loc[i, "Side"] = 0
                        
                        # Update Balance
                        self.testing_dataframe.loc[i, "Shares"] = 0 
                        self.testing_dataframe.loc[i, "Balance"] = self.testing_dataframe.loc[prev_index, "Balance"] \
                                                                - ((self.testing_dataframe.loc[prev_index, 'Entry Price'] \
                                                                - (self.testing_dataframe.loc[prev_index, 'Entry Price'] \
                                                                * (self.take_profit / 100))) \
                                                                * self.testing_dataframe.loc[prev_index, "Shares"])
                                                                
                        invested_balance = self.testing_dataframe.loc[prev_index, "Shares"] * self.testing_dataframe.loc[prev_index, 'Entry Price'] 
                        # Calc PnL
                        current_trade_pnl = float((((self.testing_dataframe.loc[prev_index, "Entry Price"]
                                                    - take_profit_value)
                                                    * self.testing_dataframe.loc[prev_index, "Shares"]) 
                                                    / invested_balance) * 100)

                        prev_candle_pnl = float((((self.testing_dataframe.loc[prev_index, "Entry Price"] 
                                                - self.testing_dataframe.loc[prev_index, "close"])
                                                * self.testing_dataframe.loc[prev_index, "Shares"]) 
                                                / invested_balance) * 100)
                        
                        if np.isnan(prev_candle_pnl):
                            prev_candle_pnl = 0
                            
                        diff = round(current_trade_pnl - prev_candle_pnl, 4)
                        self.pnl += diff
                        self.testing_dataframe.loc[i, "PnL"] = self.pnl
                           
                    # If currently in a LONG position but no need to Exit
                    elif self.testing_dataframe.loc[prev_index, 'Side'] == 1:
                        
                        # Stay in LONG Trade
                        self.testing_dataframe.loc[i, "Side"] = 1
                        self.testing_dataframe.loc[i, 'Entry Price'] = self.testing_dataframe.loc[prev_index, 'Entry Price']
                        
                        # Update Balance
                        self.testing_dataframe.loc[i, "Shares"] = self.testing_dataframe.loc[prev_index, "Shares"]
                        self.testing_dataframe.loc[i, "Balance"] = self.testing_dataframe.loc[prev_index, "Balance"] 
                        
                        invested_balance = self.testing_dataframe.loc[i, "Shares"] * self.testing_dataframe.loc[i, 'Entry Price'] 
                        # Calc PnL
                        current_trade_pnl = float((((self.testing_dataframe.loc[i, "close"] 
                                                    - self.testing_dataframe.loc[i, "Entry Price"]) 
                                                    * self.testing_dataframe.loc[i, "Shares"]) 
                                                    / invested_balance) * 100)
                        
                        prev_candle_pnl = float((((self.testing_dataframe.loc[prev_index, "close"]
                                                - self.testing_dataframe.loc[prev_index, "Entry Price"]) 
                                                * self.testing_dataframe.loc[prev_index, "Shares"]) 
                                                / invested_balance) * 100)
                        
                        if np.isnan(prev_candle_pnl):
                            prev_candle_pnl = 0
                            
                        diff = round(current_trade_pnl - prev_candle_pnl, 4)
                        self.pnl += diff
                        self.testing_dataframe.loc[i, "PnL"] = self.pnl
                        
                    # If currently in a SHORT position but no need to Exit
                    elif self.testing_dataframe.loc[prev_index, 'Side'] == -1:
                        
                        # Stay in LONG Trade
                        self.testing_dataframe.loc[i, "Side"] = -1
                        self.testing_dataframe.loc[i, 'Entry Price'] = self.testing_dataframe.loc[prev_index, 'Entry Price']
                        
                        # Update Balance
                        self.testing_dataframe.loc[i, "Shares"] = self.testing_dataframe.loc[prev_index, "Shares"]
                        self.testing_dataframe.loc[i, "Balance"] = self.testing_dataframe.loc[prev_index, "Balance"] 
                        
                        invested_balance = self.testing_dataframe.loc[i, "Shares"] * self.testing_dataframe.loc[i, 'Entry Price']
                        # Calc PnL
                        current_trade_pnl = float((((self.testing_dataframe.loc[i, "Entry Price"]  
                                                    - self.testing_dataframe.loc[i, "close"]) 
                                                    * self.testing_dataframe.loc[i, "Shares"]) 
                                                    / invested_balance) * 100)
                        
                        prev_candle_pnl = float((((self.testing_dataframe.loc[prev_index, "Entry Price"] 
                                                - self.testing_dataframe.loc[prev_index, "close"]) 
                                                * self.testing_dataframe.loc[prev_index, "Shares"]) 
                                                / invested_balance) * 100)
                        
                        if np.isnan(prev_candle_pnl):
                            prev_candle_pnl = 0
                            
                        diff = round(current_trade_pnl - prev_candle_pnl, 4)
                        self.pnl += diff
                        self.testing_dataframe.loc[i, "PnL"] = self.pnl
                        
                    # For LONG Trades
                    elif self.testing_dataframe.loc[prev_index, 'Side'] == 0 and \
                    self.testing_dataframe.loc[i, "Signal / No Signal"] == "Signal" and \
                    self.testing_dataframe.loc[prev_index, "Signal / No Signal"] == "Signal" and \
                    self.testing_dataframe.loc[i, "close"] > self.testing_dataframe.loc[prev_index, "high"]:
                        
                        # Enter LONG Trade
                        self.testing_dataframe.loc[i, "Enter"] = "Enter"
                        self.testing_dataframe.loc[i, 'Side'] = 1
                        self.testing_dataframe.loc[i, 'Entry Price'] = self.testing_dataframe.loc[i, "open"]
                        
                        # Update take profit and stop Loss
                        take_profit_value = self.take_profit_calc(self.testing_dataframe.loc[i, 'Entry Price'], self.testing_dataframe.loc[i, 'Side'])
                        stop_loss_value = self.stop_loss_cal(self.testing_dataframe.loc[i, 'Entry Price'], self.testing_dataframe.loc[i, 'Side'])
                        
                        # Purchase Shares
                        self.testing_dataframe.loc[i, "Shares"] = round(float((self.testing_dataframe.loc[prev_index, "Balance"]
                                                                        * (self.balance_perc / 100))
                                                                        / (self.testing_dataframe.loc[i, "Entry Price"])), 2)
                        
                        # Update Balance
                        self.testing_dataframe.loc[i, "Balance"] = self.testing_dataframe.loc[prev_index, "Balance"] \
                                                                - (self.testing_dataframe.loc[i, "open"] \
                                                                * self.testing_dataframe.loc[i, "Shares"])
                                                                
                        invested_balance = self.testing_dataframe.loc[i, "Shares"] * self.testing_dataframe.loc[i, 'Entry Price']
                        # Calc PnL
                        current_trade_pnl = float((((self.testing_dataframe.loc[i, "close"]
                                                    - self.testing_dataframe.loc[i, "Entry Price"]) 
                                                    * self.testing_dataframe.loc[i, "Shares"]) 
                                                    / invested_balance) * 100)

                        self.pnl += current_trade_pnl
                        self.testing_dataframe.loc[i, "PnL"] = self.pnl
                            
                    # For SHORT Trades
                    elif self.testing_dataframe.loc[prev_index, 'Side'] == 0 and \
                    self.testing_dataframe.loc[i, "Signal / No Signal"] == "Signal" and \
                    self.testing_dataframe.loc[prev_index, "Signal / No Signal"] == "Signal" and \
                    self.testing_dataframe.loc[i, "close"] < self.testing_dataframe.loc[prev_index, "low"]:
                        
                        # Enter SHORT Trade
                        self.testing_dataframe.loc[i, "Enter"] = "Enter"
                        self.testing_dataframe.loc[i, 'Side'] = -1
                        self.testing_dataframe.loc[i, 'Entry Price'] = self.testing_dataframe.loc[i, "open"]
                        
                        # Update take profit and stop Loss
                        take_profit_value = self.take_profit_calc(self.testing_dataframe.loc[i, 'Entry Price'], self.testing_dataframe.loc[i, 'Side'])
                        stop_loss_value = self.stop_loss_cal(self.testing_dataframe.loc[i, 'Entry Price'], self.testing_dataframe.loc[i, 'Side'])
                        
                        # Purchase Shares
                        self.testing_dataframe.loc[i, "Shares"] = round(float((self.testing_dataframe.loc[prev_index, "Balance"]
                                                                        * (self.balance_perc / 100))
                                                                        / (self.testing_dataframe.loc[i, "Entry Price"])), 2)
                        # Update Balance
                        self.testing_dataframe.loc[i, "Balance"] = self.testing_dataframe.loc[self.testing_dataframe.index[idx - 1], "Balance"] \
                                                                    + (self.testing_dataframe.loc[i, "open"] \
                                                                    * self.testing_dataframe.loc[i, "Shares"])
                                                                    
                        invested_balance = self.testing_dataframe.loc[i, "Shares"] * self.testing_dataframe.loc[i, 'Entry Price']
                        # Calc PnL
                        current_trade_pnl = float((((self.testing_dataframe.loc[i, "Entry Price"]  
                                                    - self.testing_dataframe.loc[i, "close"]) 
                                                    * self.testing_dataframe.loc[i, "Shares"]) 
                                                    / invested_balance) * 100)
                        
                        self.pnl += current_trade_pnl
                        self.testing_dataframe.loc[i, "PnL"] = self.pnl
                        
                        
                    else:
                        self.testing_dataframe.loc[i, 'Side'] = 0
                        # Update Balance
                        self.testing_dataframe.loc[i, "Shares"] = self.testing_dataframe.loc[prev_index, "Shares"]
                        self.testing_dataframe.loc[i, "Balance"] = self.testing_dataframe.loc[prev_index, "Balance"] 
                        # Calc PnL
                        self.testing_dataframe.loc[i, "PnL"] = self.pnl
                        
                else:
                    # If currently in a LONG position but no need to Exit
                    if self.testing_dataframe.loc[prev_index, 'Side'] == 1:
                        
                        # Stay in LONG Trade
                        self.testing_dataframe.loc[i, "Side"] = 1
                        self.testing_dataframe.loc[i, 'Entry Price'] = self.testing_dataframe.loc[prev_index, 'Entry Price']
                        
                        # Update Balance
                        self.testing_dataframe.loc[i, "Shares"] = self.testing_dataframe.loc[prev_index, "Shares"]
                        self.testing_dataframe.loc[i, "Balance"] = self.testing_dataframe.loc[prev_index, "Balance"] 
                        # Calc PnL
                        self.testing_dataframe.loc[i, "PnL"] = self.pnl
                        
                    # If currently in a SHORT position but no need to Exit
                    elif self.testing_dataframe.loc[prev_index, 'Side'] == -1:
                        
                        # Stay in LONG Trade
                        self.testing_dataframe.loc[i, "Side"] = -1
                        self.testing_dataframe.loc[i, 'Entry Price'] = self.testing_dataframe.loc[prev_index, 'Entry Price']
                        
                        # Update Balance
                        self.testing_dataframe.loc[i, "Shares"] = self.testing_dataframe.loc[prev_index, "Shares"]
                        self.testing_dataframe.loc[i, "Balance"] = self.testing_dataframe.loc[prev_index, "Balance"] 
                        # Calc PnL
                        self.testing_dataframe.loc[i, "PnL"] = self.pnl
                        
                    else:
                        self.testing_dataframe.loc[i, 'Side'] = 0
                        # Update Balance
                        self.testing_dataframe.loc[i, "Shares"] = self.testing_dataframe.loc[prev_index, "Shares"]
                        self.testing_dataframe.loc[i, "Balance"] = self.testing_dataframe.loc[prev_index, "Balance"] 
                        # Calc PnL
                        self.testing_dataframe.loc[i, "PnL"] = self.pnl
                    
                max_pnl = max(max_pnl, self.pnl)
                self.max_drawdown = min(self.max_drawdown, self.pnl) 
                    
class BreakoutStrategy(BackTest):
    """
    This strategy uses volume to enter trades if there is a signal for 
    two candels, then it enters into the trade
    """
    def __init__(self, data: pd.DataFrame, parameters: typing.List[typing.Dict]):
        super().__init__(data, parameters) 
        self.min_volume = float(parameters['Extra_Parameters']["min_volume"].text())
    
    def run(self):
        # First apply when this strategy's signal is received
        self.apply_signal()
        
        # Second, apply when you enter a trade and when you exit
        # Also, do pnl and max_drawdown calculation
        self.enter_exit_trade()
        
        # Third, Save dataframe to a csv file
        self.testing_dataframe.to_csv(os.path.dirname(__file__) + "\\" + "test2.csv", index=False)
        
        # Fourth, return pnl, max_drawdown, and dataframe
        return self.pnl, self.max_drawdown, self.testing_dataframe 
            
    def apply_signal(self):
        """
        Fill the "Signal / No Signal" column of the dataframe
        with "Signal" or "No Signal" depending on the conditions
        """
        self.testing_dataframe["Signal / No Signal"] = np.where(
            self.testing_dataframe["volume"] >= self.min_volume,
            "Signal",
            "No Signal"
            )  
                 
class TechnicalStrategy(BackTest):
    def __init__(self, data: pd.DataFrame, parameters: typing.List[typing.Dict]):
        super().__init__(data, parameters) 
        
class TraditionalIchimokuStrategy(BackTest):
    """
    This strategy uses the Traditional Ichimoku 
    strategy to enter trades. If there is a signal for 
    two candels, then it enters into the trade
    """
    def __init__(self, data: pd.DataFrame, parameters: typing.List[typing.Dict]):
        
        # Initiate Backtest class
        super().__init__(data, parameters) 
        
        # Initiate parameters periods from user input
        self.tenkan_period = int(parameters['Extra_Parameters']["tenkan"].text())
        self.kijun_period = int(parameters['Extra_Parameters']["kijun"].text())
        self.chikou_senkou_period = int(parameters['Extra_Parameters']["chikou_senkou_span_a"].text())
        self.senkou_span_b_period = int(parameters['Extra_Parameters']["senkou_span_b"].text())
    
    def run(self):
        # First apply when this strategy's signal is received
        self.apply_signal()
        
        # Second, apply when you enter a trade and when you exit
        # Also, do pnl and max_drawdown calculation
        self.enter_exit_trade()
        
        # Third, Save dataframe to a csv file
        self.testing_dataframe.to_csv(os.path.dirname(__file__) + "\\" + "ichimoku_test.csv", index=True)
        
        # Fourth, return pnl, max_drawdown, and dataframe
        return self.pnl, self.max_drawdown, self.testing_dataframe 
    
    def apply_signal(self):
        """
        Fill the "Signal / No Signal" column of the dataframe
        with "Signal" or "No Signal" depending on the conditions
        """
        
        # Get tenkan
        tenkan = self._tenkan()
        
        # Get kijun
        kijun = self._kijun()
        
        # Get senkou span A
        senkou_span_a = self._senkou_span_a(tenkan=tenkan, kijun=kijun)
        non_shift_senkou_span_a = (senkou_span_a.shift(-self.chikou_senkou_period, pd.infer_freq(self.testing_dataframe.index))).copy()
        non_shift_senkou_span_a.rename(columns = {'senkou_span_a':'senkou_span_a_no_shift'}, inplace = True)
        
        # Get senkou span B
        senkou_span_b = self._senkou_span_b()
        non_shift_senkou_span_b = (senkou_span_b.shift(-self.chikou_senkou_period, pd.infer_freq(self.testing_dataframe.index))).copy()
        non_shift_senkou_span_b.rename(columns = {'senkou_span_b':'senkou_span_b_no_shift'}, inplace = True)
        
        # Get chikou
        chikou = self._chikou()
        shifted_close = pd.DataFrame([], columns=["close_shifted"], index=self.testing_dataframe.index)
        shifted_close["close_shifted"] = self.testing_dataframe['close'].copy()
        shifted_close["close_shifted"] = chikou["chikou"].shift(self.chikou_senkou_period, fill_value=0, axis = 0, freq=pd.infer_freq(self.testing_dataframe.index))
        
        ichimoku_df = pd.concat([tenkan, kijun, senkou_span_a, senkou_span_b, chikou, shifted_close, non_shift_senkou_span_a, non_shift_senkou_span_b], 
                                   axis=1)
        
        # Add series to testing_dataframe
        self.testing_dataframe = pd.concat([self.testing_dataframe, 
                                            ichimoku_df], 
                                           axis=1) 
        
        self.testing_dataframe.to_csv(os.path.dirname(__file__) + "\\" + "ichimoku_test.csv", index=True)
        
        #print(shifted_close.tail(30))
        
        for idx, i in enumerate(self.testing_dataframe.index):
            
            if idx < 30:
                pass
            
            else:
                chikou_index = self.testing_dataframe.index[idx - self.chikou_senkou_period] 
                
                if (self.testing_dataframe.loc[i, 'close']                  > self.testing_dataframe.loc[i, 'tenkan'] \
                and self.testing_dataframe.loc[i, 'tenkan']                 > self.testing_dataframe.loc[i, 'kijun'] \
                and self.testing_dataframe.loc[i, 'kijun']                  > self.testing_dataframe.loc[i, 'senkou_span_a'] \
                and self.testing_dataframe.loc[i, 'senkou_span_a']          > self.testing_dataframe.loc[i, 'senkou_span_b'] \
                and self.testing_dataframe.loc[i, 'senkou_span_a_no_shift'] > self.testing_dataframe.loc[i, 'senkou_span_b_no_shift'] \
                and self.testing_dataframe.loc[chikou_index, 'chikou']      > self.testing_dataframe.loc[chikou_index, 'close']) \
                or \
                (self.testing_dataframe.loc[i, 'close']                     < self.testing_dataframe.loc[i, 'tenkan'] \
                and self.testing_dataframe.loc[i, 'tenkan']                 < self.testing_dataframe.loc[i, 'kijun'] \
                and self.testing_dataframe.loc[i, 'kijun']                  < self.testing_dataframe.loc[i, 'senkou_span_a'] \
                and self.testing_dataframe.loc[i, 'senkou_span_a']          < self.testing_dataframe.loc[i, 'senkou_span_b'] \
                and self.testing_dataframe.loc[i, 'senkou_span_a_no_shift'] < self.testing_dataframe.loc[i, 'senkou_span_b_no_shift'] \
                and self.testing_dataframe.loc[chikou_index, 'chikou']      < self.testing_dataframe.loc[chikou_index, 'close']):
                    
                    self.testing_dataframe.loc[i, "Signal / No Signal"] = "Signal"
                    
                else:
                    self.testing_dataframe.loc[i, "Signal / No Signal"] = "No Signal"
        
    def _tenkan(self) -> pd.DataFrame:
        """
        Get tenkan data based on candle info\n
        returns: tenkan
        """
        
        # Turn low and high candle list to a pandas Series          
        lows = self.testing_dataframe['low'].rolling(window=self.tenkan_period).min()
        highs = self.testing_dataframe['high'].rolling(window=self.tenkan_period).max()
        
        # Get two copies of close candle Series
        tenkan = pd.DataFrame(((lows + highs) / 2), columns=["tenkan"])
        
        # returns tenkan for candle that has guaranteed been closed
        return tenkan
    
    def _kijun(self) -> pd.DataFrame:
        """
        Get kijun data based on candle info\n
        returns: kijun
        """
        
        # Get lowest and highest candle within period
        lows = self.testing_dataframe['low'].rolling(window=self.kijun_period).min()
        highs = self.testing_dataframe['high'].rolling(window=self.kijun_period).max()
        
        # Get two copies of close candle Series
        kijun =  pd.DataFrame(((lows + highs) / 2), columns=["kijun"])
        
        # returns kijun for candle that has guaranteed been closed
        return kijun
    
    def _chikou(self) -> pd.DataFrame:
        """
        Get Chikou data based on candle info\n
        returns: chikou
        """
        
        # Chikou will be candle closes shift back
        chikou = pd.DataFrame([], columns=["chikou"], index=self.testing_dataframe.index)
        chikou["chikou"] = self.testing_dataframe['close'].copy()
        chikou["chikou"] = chikou["chikou"].shift(-self.chikou_senkou_period, axis=0)
        return chikou
    
    def _senkou_span_a(self, tenkan: pd.DataFrame, kijun: pd.DataFrame) -> pd.Series:
        """
        Get Senkou Span A data based on candle info\n
        returns: senkou_span_a
        """
        
        # Calculate senkou span A from tenkan and kijun
        senkou_span_a = pd.DataFrame(((tenkan["tenkan"] + kijun["kijun"]) / 2), columns=["senkou_span_a"]).shift(self.chikou_senkou_period, axis = 0, freq=pd.infer_freq(self.testing_dataframe.index))
        
        return senkou_span_a
    
    def _senkou_span_b(self) -> pd.DataFrame:
        """
        Get Senkou Span B data based on candle info\n
        returns: senkou_span_b
        """
        
        # Get lowest and highest candle within period
        lows = self.testing_dataframe['low'].rolling(window=(self.senkou_span_b_period)).min()
        highs = self.testing_dataframe['high'].rolling(window=(self.senkou_span_b_period)).max()
        
        # Get two copies of close candle Series
        senkou_span_b = pd.DataFrame((((lows + highs) / 2).shift(self.chikou_senkou_period, freq=pd.infer_freq(self.testing_dataframe.index))), columns=["senkou_span_b"])
        
        # Returns tenkan for candle that has guaranteed been closed
        return senkou_span_b