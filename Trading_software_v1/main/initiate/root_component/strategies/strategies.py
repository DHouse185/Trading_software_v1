##########  Python IMPORTs  ############################################################
import logging
import typing
import pandas as pd
import numpy as np
import time
from threading import Timer
########################################################################################
##########  Created files IMPORTS  #####################################################
from initiate.connectors.models import *
import initiate.root_component.util.root_variables as r_var
if typing.TYPE_CHECKING:
    from initiate.connectors.binance_us import BinanceUSClient
########################################################################################
# capturing original logger
logger = logging.getLogger()

# timeframe dictionary
TF_EQUIV = {"1m" : 60, 
            "5m" : 300, 
            "15m": 900, 
            "30m": 1800, 
            "1h" : 3600, 
            "4h" : 14400}
    
class Strategy:
    """
    Class that will manage all strategies and their
    properties
    """
    def __init__(self, client: "BinanceUSClient", pair: PairData, exchange: str, timeframe: str, balance_percentage: float,
                 take_profit: float, stop_loss: float, strat_name):
        # Initiate from passed values
        self.client = client
        self.pair = pair
        self.exchange = exchange
        self.timeframe = timeframe
        self.tf_equiv = TF_EQUIV[timeframe] * 100 
        self.balance_percentage = balance_percentage
        self.take_profit = take_profit
        self.stop_loss = stop_loss
        self.strat_name = strat_name
        
        # when this is initlized, positions are not
        # initialized
        self.ongoing_position = False
        
        # Initializing strategies properties 
        self.candles: typing.List[Candle] = []
        self.trades: typing.List[Trade] = []
        self.logs = []
        
    def _add_log(self, message: str):
        """ 
        Send information to logger frame to be displayed
        later
        """
        logger.info(f"{message}")
        self.logs.append({"log": message, "displayed": False})
        
    def parse_trades(self, price: float, size: float, timestamp: int) -> str:
        """
        This function checks on the ongoing position
        and checks if this is the same candle, there are
        missing candles, or there is a new candle\n
        returns: "same candle" or "new candle"
        """
        
        # First see if there is a significant difference from
        # data's time to the actual time.
        timestamp_diff = int(time.time()) * 1000 - timestamp
        
        # if data is off by 2 secs. you get warned
        if timestamp_diff >= 2000:
            logger.warning(f"{self.exchange} {self.pair.symbol}: {timestamp_diff} \
                           milliseconds of difference between the current time and the trade time")
            self._add_log(f"{self.exchange} {self.pair.symbol}: {timestamp_diff} \
                          milliseconds of difference between the current time and the trade time")
        
        # Get the last candles properties
        last_candle = self.candles[-1]
        
        # SAME CANDLE: This means this is the same Candle
        if timestamp < last_candle.timestamp + self.tf_equiv:
            
            last_candle.close = price
            last_candle.volume += size
            
            # Update highs and lows if changed
            if price > last_candle.high:
                last_candle.high = price
                
            elif price < last_candle.low:
                last_candle.low = price
                
            # Check Take profit / Stop Loss 
            for trade in self.trades:
                
                if trade.status == "open" and trade.entry_price is not None:
                    self._check_tp_sl(trade)
                    
            # let's you know the candle is the same if all is well
            return "same_candle"       
        
        # MISSING CANDLE(s): This means some candles are missing
        elif timestamp >= last_candle.timestamp + 2 * self.tf_equiv:
            
            missing_candle = int((timestamp - last_candle.timestamp) / self.tf_equiv) - 1
            
            logger.info(f"{self.exchange} missing {missing_candle} candles for {self.pair.symbol} \
                        {self.timeframe} ({timestamp} {last_candle.timestamp})")
            
            for missing in range(missing_candle):
                
                new_timestamp = last_candle.timestamp + self.tf_equiv
                
                candle_info = {'ts'    : new_timestamp, 
                               'open'  : last_candle.close, 
                               'high'  : last_candle.close, 
                               'low'   : last_candle.close, 
                               'close' : last_candle.close, 
                               'volume': 0}
                
                new_candle = Candle(candle_info, 'parse_trade')
                
                self.candles.append(new_candle)
                
                last_candle = new_candle
                
            new_timestamp = last_candle.timestamp + self.tf_equiv
            candle_info = {'ts': new_timestamp, 
                           'open'  : price, 
                           'high'  : price, 
                           'low'   : price, 
                           'close' : price, 
                           'volume': size}
            
            new_candle = Candle(candle_info, 'parse_trade')
            
            self.candles.append(new_candle)
            
            return "new_candle"
            
        # New Candle
        elif timestamp >= last_candle.timestamp + self.tf_equiv:
            new_timestamp = last_candle.timestamp + self.tf_equiv
            candle_info = {'ts': new_timestamp, 
                           'open'  : price, 
                           'high'  : price, 
                           'low'   : price, 
                           'close' : price, 
                           'volume': size}
            
            new_candle = Candle(candle_info, 'parse_trade')
            
            self.candles.append(new_candle)
            
            logger.info(f"{self.exchange} New candle for {self.pair.symbol} {self.timeframe}")
            
            return "new_candle"
        
    def _check_order_status(self, order_id):
        """
        Get updates on the orders you submitted
        """
        # Send request to exchange and get order status
        order_status = self.client.get_order_status(self.pair, order_id)
        
        # Again, if order_status variable is not []
        if order_status is not None:
            
            logger.info(f"{self.exchange} order status {order_status.status}")
            self._add_log(f"{self.exchange} order status {order_status.status}")
            
            # If order has been bought/sold by exchange
            if order_status.status == "filled":
                
                for trade in self.trades:
                    
                    if trade.entry_id == order_id:
                        trade.entry_price = order_status.price
                        break
                    
                return
            
        # Check order status every 2 seconds until filled.
        t = Timer(2.0, lambda: self._check_order_status(order_id))
        t.start()
    
    def _open_position(self, signal_result: int):
        """"
        Attempts to open a new position when signal is
        triggered
        """
        trade_size = self.client.get_trade_size(self.pair, 
                                                self.candles[-1].close, 
                                                self.balance_percentage)
        
        if trade_size is None:
            return
        
        order_side = "buy" if signal_result == 1 else "sell"
        position_side = "long" if signal_result == 1 else "short"
        
        self._add_log(f"{position_side} signal on {self.pair.symbol} {self.timeframe}")
        
        order_status = self.client.place_order(self.pair, "MARKET", trade_size, order_side, trade_size)
        
        if order_status is not None:
            self._add_log(f"{order_side.capitalize()} order placed on {self.exchange} | Status: {order_status.status}")
        
            self.ongoing_position = True
            average_fill_price = None
            
            if order_status.status == "filled":
                average_fill_price = order_status.price
                
            else:
                t = Timer(2.0, lambda: self._check_order_status(order_status.order_id))
                t.start()
                
            new_trade = Trade({"time"       : int(time.time() * 1000), 
                               "entry_price": average_fill_price, 
                               "pair"       : self.pair, 
                               "strategy"   : self.strat_name, 
                               "side"       : position_side,
                               "status"     : "open", 
                               "pnl"        : 0, 
                               "quantity"   : trade_size, 
                               "entry_id"   : order_status.order_id})
            
        self.trades.append(new_trade)
        
    def _check_tp_sl(self, trade: Trade):
        """
        Checks if stop_loss or take profit
        has been hit\n
        return: void
        """
        tp_triggered = False
        sl_triggered = False
        
        # Checks closing price of last candle
        price = self.candles[-1].close
        
        # First check if you are long or short
        # For long trades 
        if trade.side == "long":
            
            if self.stop_loss is not None:
                
                if price <= trade.entry_price * (1 - self.stop_loss / 100):
                    sl_triggered = True
                    
            if self.take_profit is not None:
                
                if price >= trade.entry_price * (1 + self.take_profit / 100):
                    tp_triggered = True
                    
        # For short trades            
        elif trade.side == "short":
            
            if self.stop_loss is not None:
                
                if price >= trade.entry_price * (1 + self.stop_loss / 100):
                    sl_triggered = True
                    
            if self.take_profit is not None:
                
                if price <= trade.entry_price * (1 - self.take_profit / 100):
                    tp_triggered = True
                    
        # If either take profit or stop loss is triggered            
        if tp_triggered or sl_triggered:
            
            # Sends message to log to be displayed on ui
            self._add_log(f"{'Stop loss' if sl_triggered else 'Take profit'} for {self.pair.symbol} {self.timeframe}")
            
            # Tells exchange you want to exit trade with "MARKET" order
            order_side = "SELL" if trade.side == "long" else "BUY"
            order_status = self.client.place_order(self.pair, "MARKET", trade.quantity, order_side)
            
            if order_status is not None:
                self._add_log(f"Exit order on {self.pair.symbol} {self.timeframe} has been placed successfully")
                trade.status = "closed"
                self.ongoing_position = False    
        
class TechnicalStrategy(Strategy):
    """
    Properties of strategies tht are categorized as technical\n
    Takes in Strategy component, initiates it and get all of its
    properties. 
    """
    def __init__(self, 
                 client: "BinanceUSClient", 
                 pair: PairData, 
                 exchange: str, 
                 timeframe: str,
                 balance_percentage: float, 
                 take_profit: float, 
                 stop_loss: float, 
                 other_params: typing.Dict):
        
        super().__init__(client, pair, exchange, timeframe, balance_percentage,
                 take_profit, stop_loss, "Technical") 
        
        # Initiate parameters for technical strategies
        self._ema_fast = other_params['ema_fast']
        self._slow_ema = other_params['ema_slow']
        self._ema_signal = other_params['ema_signal']
        self._rsi_length = other_params['rsi_length']
            
    def _rsi(self):
        """
        Get rsi data based on candle info\n
        returns: rsi[-2] candle
        """
        
        # initiate list for closed candles
        close_list = []
        
        for candle in self.candles:
            close_list.append(candle.close)
            
        # Turn close candle list to a pandas Series          
        closes = pd.Series(close_list)
        
        # returns None for missing closed candles
        delta = closes.diff().dropna()
        
        # Get two copies of close candle Series
        up, down = delta.copy(), delta.copy()
        
        # All values less than 0 become 0
        up[up < 0] = 0
        
        # All values more than 0 become 0
        down[down > 0] = 0
        
        # Get mean for up and down series
        avg_gain = up.ewm(com=(self._rsi_length - 1), min_periods=self._rsi_length).mean()
        avg_loss = down.abs().ewm(com=(self._rsi_length - 1), min_periods=self._rsi_length).mean()
        
        # rs calculation based on average gain and losses
        rs = avg_gain / avg_loss
        
        # Formula for rsi
        rsi = 100 - 100 / (1 + rs)
        rsi = rsi.round(2)
        
        # returns rsi for candle that has guaranteed been closed
        return rsi.iloc[-2]
    
    def _macd(self) -> typing.Tuple[float, float]:
        """
        Calculation for macd\n
        returns: macd_line[-2] candle and macd_signal[-2] candle
        """
        # initiate list for closed candles
        close_list = []
        
        for candle in self.candles:
            close_list.append(candle.close)
            
        # Turn close candle list to a pandas Series            
        closes = pd.Series(close_list)
        
        # Get mean for fast and slow ema of close candle Series
        ema_fast = closes.ewm(span=self._ema_fast).mean()
        ema_slow = closes.ewm(span=self._slow_ema).mean()
        
        # Formula for macd
        macd_line = ema_fast - ema_slow
        macd_signal = macd_line.ewm(self._ema_signal).mean()
        
        return macd_line.iloc[-2], macd_signal.iloc[-2]
    
    def _check_signal(self):
        """How signal is checked for Technical Strategy\n
        returns: 0, 1, or -1"""
        
        # Get macd
        macd_line, macd_signal = self._macd()
        
        # Get rsi
        rsi = self._rsi()
        
        # Check if rsi and macd are giving long signal
        if rsi < 30 \
        and macd_line > macd_signal:
            return 1
        
        # Check if rsi and macd are giving short signal
        elif rsi > 70 \
        and macd_line < macd_signal:
            return -1
        
        # No signal was received
        else: 
            return 0
        
    def check_trade(self, tick_type: str):
        """"
        If trade is ongoing\n
        functions activated: self._open_position\n
        return: void
        """
        # Check if strategy triggered once new candle has started
        if tick_type == "new_candle" and self.ongoing_position == False:
            
            signal_result = self._check_signal()
            
            # open position
            if self.exchange != "BinanceUS":
                
                if signal_result in [-1, 1]:
                    self._open_position(signal_result)
                
            else:
                if signal_result in [1]:
                    self._open_position(signal_result)
                
        return

    
class BreakoutStrategy(Strategy):
    """
    Properties of strategies that are categorized as Breakout\n
    Takes in Strategy component, initiates it and get all of its
    properties. 
    """
    def __init__(self, client, pair: PairData, exchange: str, timeframe: str, balance_percentage: float,
                 take_profit: float, stop_loss: float, other_params: typing.Dict):
        
        super().__init__(client, pair, exchange, timeframe, balance_percentage,
                 take_profit, stop_loss, "Breakout") 
        
        # Gets minimum volume for activation
        self._min_volume = other_params['min_volume']
        
    def _check_signal(self) -> int:
        """How signal is checked for Breakout Strategy\n
        returns: 0, 1, or -1
        """
        
        if self.candles[-1].close > self.candles[-2].high \
        and self.candles[-1].volume > self._min_volume:
            return 1
        
        elif self.candles[-1].close < self.candles[-2].low \
        and self.candles[-1].volume > self._min_volume:
            return -1
        
        else:
            return 0

    def check_trade(self, tick_type: str):
        """"
        If trade is ongoing\n
        functions activated: self._open_position\n
        return: void
        """
        
        # Check if strategy triggered once new candle has started
        if not self.ongoing_position:
            
            signal_result = self._check_signal()
            
            # open position
            if self.exchange != "BinanceUS":
                
                if signal_result in [-1, 1]:
                    self._open_position(signal_result)
                
            else:
                if signal_result in [1]:
                    self._open_position(signal_result)
                    
        return
    
class TraditionalIchimokuStrategy(Strategy):
    """
    Properties of strategies that are categorized as Traditional
    Ichimoku\n
    Takes in Strategy component, initiates it and get all of its
    properties. 
    """
    def __init__(self, client, pair: PairData, exchange: str, timeframe: str, balance_percentage: float,
                 take_profit: float, stop_loss: float, other_params: typing.Dict):
        
        super().__init__(client, pair, exchange, timeframe, balance_percentage,
                 take_profit, stop_loss, "Breakout") 
        
        # Initiate parameters for ichimoku strategy
        self._tenkan_period = other_params['tenkan']
        self._kijun_period = other_params['kijun']
        self._chikou_senkou_span_a_period = other_params['chikou_senkou_span_a']
        self._senkou_span_b_period = other_params['senkou_span_b']
            
    def _tenkan(self):
        """
        Get tenkan data based on candle info\n
        returns: tenkan[-2] candle
        """
        
        # initiate list for low and high candles
        low_list = []
        high_list = []
        
        for candle in self.candles:
            low_list.append(candle.low)
            high_list.append(candle.high)
            
        # Turn low and high candle list to a pandas Series          
        lows = pd.Series(low_list)
        highs = pd.Series(high_list)
        
        # Get lowest and highest candle within period
        lows = lows.rolling(window=self._tenkan_period).min()
        highs = highs.rolling(window=self._tenkan_period).max()
        
        # Get two copies of close candle Series
        self.tenkan = (lows + highs) / 2
        
        # returns tenkan for candle that has guaranteed been closed
        return self.tenkan.iloc[-2]
    
    def _kijun(self):
        """
        Get kijun data based on candle info\n
        returns: kijun[-2] candle
        """
        
        # initiate list for low and high candles
        low_list = []
        high_list = []
        
        for candle in self.candles:
            low_list.append(candle.low)
            high_list.append(candle.high)
            
        # Turn low and high candle list to a pandas Series          
        lows = pd.Series(low_list)
        highs = pd.Series(high_list)
        
        # Get lowest and highest candle within period
        lows = lows.rolling(window=self._kijun_period).min()
        highs = highs.rolling(window=self._kijun_period).max()
        
        # Get two copies of close candle Series
        self.kijun = (lows + highs) / 2
        
        # returns kijun for candle that has guaranteed been closed
        return self.kijun.iloc[-2]
    
    def _chikou(self):
        """
        Get Chikou data based on candle info\n
        returns: chikou[-self._kijun_period-2], 
        closes[-self._kijun_period-2] candle
        """
        
        # initiate list for close candles
        close_list = []
        
        for candle in self.candles:
            close_list.append(candle.close)
            
        # Turn close candle list to a pandas Series            
        closes = pd.Series(close_list)
        
        chikou = closes.shift(-self._chikou_senkou_span_a_period)
        
        return chikou[-self._chikou_senkou_span_a_period-2], closes[-self._chikou_senkou_span_a_period-2]
    
    def _senkou_span_a(self) -> typing.Tuple[float, float]:
        """
        Get Senkou Span A data based on candle info\n
        returns: senkou_span_a.iloc[-self._kijun_period-2], 
                 senkou_span_a.iloc[-2] candle
        """
        
        senkou_span_a = ((self.tenkan + self.kijun) / 2).shift(self._chikou_senkou_span_a_period)
        
        return senkou_span_a.iloc[-self._chikou_senkou_span_a_period-2], senkou_span_a.iloc[-2]
    
    def _senkou_span_b(self):
        """
        Get Senkou Span B data based on candle info\n
        returns: senkou_span_b.iloc[-self._kijun_period-2], 
                 senkou_span_b.iloc[-2] candle
        """
        
        # initiate list for low and high candles
        low_list = []
        high_list = []
        
        for candle in self.candles:
            low_list.append(candle.low)
            high_list.append(candle.high)
            
        # Turn low and high candle list to a pandas Series          
        lows = pd.Series(low_list)
        highs = pd.Series(high_list)
        
        # Get lowest and highest candle within period
        lows = lows.rolling(window=(self._senkou_span_b_period)).min()
        highs = highs.rolling(window=(self._senkou_span_b_period)).max()
        
        # Get two copies of close candle Series
        senkou_span_b = ((lows + highs) / 2).shift(self._chikou_senkou_span_a_period)
        
        # returns tenkan for candle that has guaranteed been closed
        return senkou_span_b.iloc[-self._chikou_senkou_span_a_period-2], senkou_span_b.iloc[-2]
    
    def _check_signal(self):
        """How signal is checked for Technical Strategy\n
        returns: 0, 1, or -1"""
        
        # Get tenkan
        tenkan = self._tenkan()
        
        # Get kijun
        kijun = self._kijun()
        
        # Get senkou span A
        current_senkou_a, future_senkou_a = self._senkou_span_a()
        
        # Get senkou span B
        current_senkou_b, future_senkou_b = self._senkou_span_b()
        
        # Get chikou
        chikou, close_to_chikou = self._chikou()
        
        # Check if ichimoku are giving long signal
        if tenkan            > kijun \
        and kijun            > current_senkou_a \
        and current_senkou_a > current_senkou_b \
        and future_senkou_a  > future_senkou_b \
        and chikou           > close_to_chikou:
            return 1
        
        # Check if ichimoku are giving short signal
        elif tenkan          < kijun \
        and kijun            < current_senkou_a \
        and current_senkou_a < current_senkou_b \
        and future_senkou_a  < future_senkou_b \
        and chikou           < close_to_chikou:
            return -1
        
        # No signal was received
        else: 
            return 0
        
    def check_trade(self, tick_type: str):
        """"
        If trade is ongoing\n
        functions activated: self._open_position\n
        return: void
        """
        # Check if strategy triggered once new candle has started
        if tick_type == "new_candle" and self.ongoing_position == False:
            
            signal_result = self._check_signal()
            
            # open position
            if self.exchange != "BinanceUS":
                
                if signal_result in [-1, 1]:
                    self._open_position(signal_result)
                
            else:
                if signal_result in [1]:
                    self._open_position(signal_result)
                
        return
    