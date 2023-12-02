##########  Python IMPORTs  ############################################################
from ctypes import *
import typing
import sys
import matplotlib
from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.backends.backend_qtagg import (
    NavigationToolbar2QT as NavigationToolbar,
)
import matplotlib.pyplot as plt
import pandas as pd
import numpy as np
########################################################################################
##########  Python THIRD PARTY IMPORTs  ################################################
from PyQt6.QtCore import QDateTime, QRect
from PyQt6.QtWidgets import QLineEdit, QApplication
import mplfinance as mpf
from PyQt6.QtWidgets import QMainWindow, QWidget, QVBoxLayout
########################################################################################
##########  Created files IMPORTS  #####################################################
from hdfs_database import Hdf5Client
import root_variables as r_var
from backtesting import (TechnicalStrategy, 
                        BreakoutStrategy,
                        TraditionalIchimokuStrategy)
########################################################################################

matplotlib.use("QtAgg") 
# # capturing original logger

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

class backtest_widget:
    def __init__(self):
        ...
    
    def _add_log(message: str):
        """ 
        This is a dummy backtest widget logger
        """
        print(f"{message}")
        
class MplCanvas(FigureCanvasQTAgg):
    """
    This object will be responsible for displaying
    chart/graph on the backtest page
    """
    def __init__(self, parent=None, width=20, height=8, dpi=100):
        plt.rcParams.update(r_var.CHART_BINANCE_DARK_STYLE)
        plt.grid(True)
        self.fig, self.ax = plt.subplots(figsize=(width, height), dpi=dpi)
        super().__init__(self.fig)
        self.setParent(parent)
        
def kumo_positive(y1, y2):
    return y1 >= y2

def kumo_negative(y1, y2):
    return y1 <= y2
    

app = QApplication(sys.argv)

form = QMainWindow()
form.resize(1800, 1093)
centralwidget = QWidget(form)
verticalLayout__ = QVBoxLayout(centralwidget)

centralwidget.setLayout(verticalLayout__)
centralwidget.setGeometry(QRect(0, 0, 1800, 1080))
backtest_widgeter = backtest_widget()
matplotlib_chart = MplCanvas(None, width=15, height=8, dpi=100)
matplotlib_chart2 = MplCanvas(None, width=15, height=5, dpi=100) 
verticalLayout__.addWidget(matplotlib_chart)
verticalLayout__.addWidget(matplotlib_chart2)  
form.setCentralWidget(centralwidget) 
         
# Create toolbar, passing canvas as first parameter, parent (self, the MainWindow) as second.
chart_toolbar = NavigationToolbar(matplotlib_chart, centralwidget)  
chart_toolbar2 = NavigationToolbar(matplotlib_chart2, None)      

form.show()

tenkan = QLineEdit("20")
kijun = QLineEdit("60") 
chikou_senko = QLineEdit("30")
senko_b = QLineEdit("120")
parameters  = {
            "Strategy"         : "Traditional Ichimoku",
            "Pair"             : "BTCUSDT",
            "Exchange"         : "BinanceUS",
            "Client"           : "foo",
            "TimeFrame"        : "15m",
            "Balance"          : "5000",
            "Balance_percent"  : "99",
            "Take_Profit"      : "2",
            "Stop_Loss"        : "1",
            "From_Time"        : 1672552800000,
            "To_Time"          : 1682622360000,
            "Extra_Parameters" : {"tenkan"               : tenkan,
                                  "kijun"                : kijun,
                                  "chikou_senkou_span_a" : chikou_senko,
                                  "senkou_span_b"        : senko_b,
                                  }
            }

pnl, max_dd, df = run(backtest_widget, parameters)

"""
Charts results after backtesting strategy
"""
matplotlib_chart.ax.clear()

mc = mpf.make_marketcolors(up='tab:green',
                            down='tab:red', 
                            edge='black', 
                            wick={'up':'green','down':'red'}, 
                            inherit=True)
s  = mpf.make_mpf_style(base_mpf_style='mike', marketcolors=mc)

candle_data = df[["open", "high", "low", "close", "volume"]]

df_copy = df.copy()
for idx, i in enumerate(df_copy.index):
    
    if df_copy.loc[i, "Enter"] == "Enter":
        df_copy.loc[i, "Enter"] = df_copy.loc[i, "open"]
        
    if df_copy.loc[i, "Exit"] == "Exit":
        df_copy.loc[i, "Exit"] = df_copy.loc[i, "close"] 
            
enter = df_copy[["Enter"]]
exit = df_copy[["Exit"]]

mpf.plot(candle_data[:],
        type='candle',
        ax=matplotlib_chart.ax, 
        style=s, 
        ylabel='Price', 
        returnfig=False, 
        axtitle="Plotting")

xpoints = np.arange(len(df))

plot_info = {
    "columnns"            : ["Balance", "PnL", "Enter", "Exit", "tenkan", "kijun", "senkou_span_a", "senkou_span_b", "chikou"],
    "column_colors"       : ["c", "r", "green", "red", "b", "y", "g", "m", "#ab3c10"],
    "markers"             : [None, None, "^", "v", None, None, None, None, None],
    "linestyle"           : ["-", "-.", None, None, "--", "-", "-", "-", "-",],
    "linewidth"           : [5, 5, 5, 5, 2, 3, 2, 2, 1],
    "markersize"          : [10, 10, 10, 10, 10, 10, 10, 10, 10],
    "fill_between"        : True,
    "fill_between_params" : {
        "y1" : "senkou_span_a",
        "y2" : "senkou_span_b",
        "where1" : kumo_positive
    }
}
ax2 = matplotlib_chart2.ax.twinx()
ax3 = matplotlib_chart2.ax.twinx()

for idx, i in enumerate(plot_info["columnns"]):
    if plot_info["columnns"][idx] == "Balance":
        ax2.plot(xpoints,
                df[[i]], 
                color=plot_info["column_colors"][idx], 
                marker=plot_info["markers"][idx], 
                linestyle=plot_info["linestyle"][idx],
                linewidth=plot_info["linewidth"][idx],
                markersize=plot_info["markersize"][idx],
                )
    elif plot_info["columnns"][idx] == "PnL":
        ax3.plot(xpoints,
                df[[i]], 
                color=plot_info["column_colors"][idx], 
                marker=plot_info["markers"][idx], 
                linestyle=plot_info["linestyle"][idx],
                linewidth=plot_info["linewidth"][idx],
                markersize=plot_info["markersize"][idx],
                )
    elif plot_info["columnns"][idx] == "Enter":
        matplotlib_chart.ax.plot(xpoints,
                                enter, 
                                color=plot_info["column_colors"][idx], 
                                marker=plot_info["markers"][idx], 
                                linestyle=plot_info["linestyle"][idx],
                                linewidth=plot_info["linewidth"][idx],
                                markersize=plot_info["markersize"][idx],
                                )
    
    elif plot_info["columnns"][idx] == "Exit":
        matplotlib_chart.ax.plot(xpoints,
                                exit, 
                                color=plot_info["column_colors"][idx], 
                                marker=plot_info["markers"][idx], 
                                linestyle=plot_info["linestyle"][idx],
                                linewidth=plot_info["linewidth"][idx],
                                markersize=plot_info["markersize"][idx],
                                )
        
    else:  
        # Chart entry points
        matplotlib_chart.ax.plot(xpoints,
                                df[[i]], 
                                color=plot_info["column_colors"][idx], 
                                marker=plot_info["markers"][idx], 
                                linestyle=plot_info["linestyle"][idx],
                                linewidth=plot_info["linewidth"][idx],
                                markersize=plot_info["markersize"][idx],
                                )

if plot_info["fill_between"]:
    matplotlib_chart.ax.fill_between(xpoints, 
                                     df[plot_info["fill_between_params"]["y1"]], 
                                     df[plot_info["fill_between_params"]["y2"]], 
                                     where=(df[plot_info["fill_between_params"]["y1"]] >= df[plot_info["fill_between_params"]["y2"]]), 
                                     color='g', 
                                     alpha=0.15,
                                     interpolate=True)
    matplotlib_chart.ax.fill_between(xpoints, 
                                     df[plot_info["fill_between_params"]["y1"]], 
                                     df[plot_info["fill_between_params"]["y2"]], 
                                     where=(df[plot_info["fill_between_params"]["y1"]] <= df[plot_info["fill_between_params"]["y2"]]), 
                                     color='r', 
                                     alpha=0.15,
                                     interpolate=True)
# Plot only 15 x axis ticks at a time
matplotlib_chart.ax.xaxis.set_major_locator(plt.MaxNLocator(15))

# Use all of the canvas that is available
plt.tight_layout()
matplotlib_chart.draw()
matplotlib_chart.flush_events()
print(f"""\n
      PnL          : {pnl}\n
      Max MarkDown : {max_dd}\n
      End Balance  : {df["Balance"][-1]}""")
    
    
sys.exit(app.exec())