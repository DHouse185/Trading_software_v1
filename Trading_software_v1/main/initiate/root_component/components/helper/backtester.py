##########  Python IMPORTs  ############################################################
from ctypes import *
import typing
########################################################################################
##########  Python THIRD PARTY IMPORTs  ################################################
from PyQt6.QtCore import QDateTime
########################################################################################
##########  Created files IMPORTS  #####################################################
from initiate.root_component.components.helper.hdfs_database import Hdf5Client
import initiate.root_component.util.root_variables as r_var
from initiate.root_component.strategies.backtesting import (TechnicalStrategy, 
                                                           BreakoutStrategy,
                                                           TraditionalIchimokuStrategy)
########################################################################################

def run(backtest_widget, 
        parameters: typing.Dict):
    """
    Return strategies parameters as a dictionary list
    backtest_widget
    ---------------
    used for backtest_widget._add_log:
    This is so information can be sent to the ui.\n
    Example : backtest_widget._add_log(str(message))\n
    Example
    ---------
    Technical_strategy = [{rsi}]\n
    
    Here strategies have their own function in the form 
    of a dictionary.\n
    Example
    ---------
    strategies = {Technical: strategy.technical.backtest,
    Breakout: strategy.breakout.backtest,
    Ichimoku: strategy.breakout.backtest
    MACD_and_Breakout: strategy.macd_and_breakout.backtest}\n
    You will also pass the strategy function a dictionary of the
    parameters needed for backtesting\n
    Example
    ----------
    strategy.technical.backtest(data: pd.DataFrame, parameter: List[Dict])
    where parameters:
    parameters = [{
        "Balance": 2500,
        "Balance_percent" : 0.02,
        "Take_Profit": 0.02,
        "Stop_Loss": 0.005
        },
                  # Extra Parameters
                  {"rsi_signal": 30,
                   "macd_signal": 50,
                   "macd_fast": 12,
                   "macd_slow": 25,
                   "volume": 400}]
                   
    - Make dictionary of strategy types with their function
    strategy_types = {"Technical": technical.backtest,
                       "Breakout": breakout.backtest}
    - Don't forget to update this with r_var.STRTEGIES
    - Go into data history and retrieve data
    h5_db = Hdf5Client(exchange, backtest_widget)
    
    data = h5_db.get_data(symbol=symbol, from_time=from_time, to_time=to_time)
    - from_time and to_time are QDateTime objects, so they need to be converted to 
    - from_time.toSecsSinceEpoch() * 1000 and 
    - to_time.toSecsSinceEpoch() * 1000
    The output for this data will be a pandas DataFrame
    
    - Before running the next line, we will make that the data is available
    
    if data is not None:
            # converts the data timeframe into what you want 
            data = r_var.resample_timeframe(data=data, tf=timeframe)
            
            pnl, max_drawdown = strategy_type[strategies](data, ma_period=params["ma_period"])
            return pnl, max_drawdown
    else: 
        backtest_widget._add_log(str(no data was received))
        return
    
    Return
    ----------
    pnl
    max_drawdown
    dataframe results
    """ 
    # Make dictionary of strategy types with their function
    # Don't forget to update this with r_var.STRTEGIES
    strategies_backtest = {"Technical"            : True,
                           "Breakout"             : BreakoutStrategy,
                           "Traditional Ichimoku" : TraditionalIchimokuStrategy, 
                           "Test_Strat"           : True}
    
    # Go into data history and retrieve data
    h5_db = Hdf5Client(parameters["Exchange"], backtest_widget)
    data = h5_db.get_data(symbol=parameters["Pair"], 
                          from_time=parameters["From_Time"], 
                          to_time=parameters["To_Time"])
    # data order: columns=["timestamp", "open", "high", "low", "close", "volume"]
    
    if data is not None:
            # converts the data timeframe into what you want 
            data = r_var.resample_timeframe(data=data, tf=parameters["TimeFrame"])
            
    else: 
        backtest_widget._add_log(str("No data was received"))
        return

    strategy = strategies_backtest[parameters["Strategy"]](data=data, parameters=parameters)        
    pnl, max_drawdown, df_results = strategy.run()
    
    return pnl, max_drawdown, df_results