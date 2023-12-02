# Variable, dictionaries, list, ect. will be contained here 
# for the root file to use

##########  Python IMPORTs  ############################################################
from pathlib import Path
import datetime
import pandas as pd
import os
########################################################################################

##########  Python THIRD PARTY IMPORTs  ################################################
from PyQt6.QtWidgets import (QLineEdit)
########################################################################################

root_util_directory = os.path.dirname(__file__)
DARK_MODE = os.path.join(root_util_directory, "style", "darkmode_style.qss")
NOTIFICATION_STYLE = os.path.join(root_util_directory, "style", "notification.qss")
DISABLE_STYLE = os.path.join(root_util_directory, "style", "disable_style.qss") 

# Upon completion this will turn into an sql query 
# key and secret key will store value
# Will also need to encrypt then decrpyt 
API_KEY = "mgbrPUL0wOMSPaWZPjkmFfV5afSpn1g3JKH3DuER3cwkRlkBfgHP95ytyJRHXS5a"
API_SECRET_KEY ="yf23rs2uEZe1PdhVoSiqLFyJBNyUjCUKOEDv5rceI70eO1q44THi0ezvyNfJgSJM"

binance_dark = {
    "base_mpl_style": "dark_background",
    "marketcolors"  : {
        "candle"    : {"up": "#3dc985", "down": "#ef4f60"},  
        "edge"      : {"up": "#3dc985", "down": "#ef4f60"},  
        "wick"      : {"up": "#3dc985", "down": "#ef4f60"},  
        "ohlc"      : {"up": "green", "down": "red"},
        "volume"    : {"up": "#247252", "down": "#82333f"},  
        "vcedge"    : {"up": "green", "down": "red"},  
        "vcdopcod"  : False,
        "alpha"     : 1,
    },
    "mavcolors" : ("#ad7739", "#a63ab2", "#62b8ba"),
    "facecolor" : "#1b1f24",
    "gridcolor" : "#2c2e31",
    "gridstyle" : "--",
    "y_on_right": True,
    "rc"        : {
        "axes.grid"         : True,
        "axes.grid.axis"    : "y",
        "axes.edgecolor"    : "#474d56",
        "axes.titlecolor"   : "red",
        "figure.facecolor"  : "#161a1e",
        "figure.titlesize"  : "x-large",
        "figure.titleweight": "semibold",
    },
    "base_mpf_style"          : "binance-dark",
    "path.simplify"           : True,
    "path.simplify_threshold" : 0.6,
    "agg.path.chunksize"      : 10000,
}
TIME_FRAMES = ["1m", "5m", "15m", "30m", "1h", "4h"]

TF_EQUIV = {"1m" : "1Min", 
            "5m" : "5Min", 
            "15m": "15Min", 
            "30m": "30Min",
            "1h" : "1H",
            "4h" : "4H",
            "12h": "12H",
            "1d" :"D"}
EXCHANGES = ["BinanceUS"]

STRATEGIES = ["Technical", "Breakout", "Traditional Ichimoku"] 

EXTRA_PARAMETERS = {
    "Technical": [
        {"code_name": "rsi_length", 
         "name"     : "RSI Periods", 
         "widget"   : QLineEdit, 
         "data_type": int, 
         "min"      : 2, 
         "max"      : 200},
        
        {"code_name": "ema_fast", 
         "name"     : "MACD Fast Length", 
         "widget"   : QLineEdit, 
         "data_type": int, 
         "min"      : 2, 
         "max"      : 200},
        
        {"code_name": "ema_slow", 
         "name"     : "MACD Slow Length", 
         "widget"   : QLineEdit, 
         "data_type": int, 
         "min"      : 2,
         "max"      : 200},
        
        {"code_name": "ema_signal", 
         "name"     : "MACD Signal Length", 
         "widget"   : QLineEdit, 
         "data_type": int, 
         "min"      : 2, 
         "max"      : 200},
        ],
    
    "Breakout": [
        {"code_name": "min_volume", 
         "name"     : "Minimum Volume", 
         "widget"   : QLineEdit, 
         "data_type": float, 
         "min"      : 0.1, 
         "max"      : 10000000, 
         "decimals" : 2},
        ],
    
    "Traditional Ichimoku": [
        {"code_name": "tenkan", 
         "name"     : "Tenkan Period", 
         "widget"   : QLineEdit, 
         "data_type": int, 
         "min"      : 2, 
         "max"      : 200},
        
        {"code_name": "kijun", 
         "name"     : "Kijun Period", 
         "widget"   : QLineEdit, 
         "data_type": int, 
         "min"      : 4, 
         "max"      : 250},
        
        {"code_name": "chikou_senkou_span_a", 
         "name"     : "Chikou / +Senkou Span A Period", 
         "widget"   : QLineEdit, 
         "data_type": int, 
         "min"      : 2,
         "max"      : 250},
        
        {"code_name": "senkou_span_b", 
         "name"     : "Senkou Span B Period", 
         "widget"   : QLineEdit, 
         "data_type": int, 
         "min"      : 10, 
         "max"      : 300},
        ],
    }

DEFAULT_BACKTEST_PARAMETERS = {
    "Balance"         : { 'Default'     : 3000},
    "Balance_percent" : { 'Default'     : 99},
    "Take_Profit"     : { 'Default'     : 2},
    "Stop_Loss"       : { 'Default'     : 1},
    }

CHART_BINANCE_DARK_STYLE = {
            "lines.color"      : "white",
            "patch.edgecolor"  : "white",
            "text.color"       : "black",
            "axes.facecolor"   : "#1b1f24",
            "axes.edgecolor"   : "#474d56",
            "axes.labelcolor"  : "white",
            "axes.titlecolor"  : "red",
            "xtick.color"      : "white",
            "xtick.labeltop"   : False,   # draw label on the top
            "xtick.major.pad"  : 1.2,     # distance to major tick label in points
            "xtick.minor.pad"  : 1.1,     # distance to the minor tick label in points
            "ytick.color"      : "white",
            "grid.color"       : "#2c2e31",
            "figure.facecolor" : "#161a1e",
            "figure.edgecolor" : "#161a1e",
            "savefig.facecolor": "#161a1e",
            "savefig.edgecolor": "#161a1e"}

def ms_to_dt(ms: int):
    """
    Converts milliseconds into a datetime object in 
    normal seconds
    """
    return datetime.datetime.utcfromtimestamp(ms / 1000)

def resample_timeframe(data: pd.DataFrame, tf: str) -> pd.DataFrame:
    """
    Aggregates a pandas Dataframe time to the 
    available timeframes of your choosing
    """
    return data.resample(TF_EQUIV[tf]).agg(
        {"open"  : "first", 
         "high"  : "max", 
         "low"   : "min", 
         "close" : "last", 
         "volume": "sum"}
    )