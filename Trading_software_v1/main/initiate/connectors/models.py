##########  Python IMPORTs  ############################################################
import typing
########################################################################################

class PairData:
    """
    Storage for data on a pair in
    Exchange\n
    Ex. Data - \n
    symbol: STORJUSD\n
    base_asset: STORJ\n
    quote_asset: USD\n
    price_decimal: 8\n
    quantity_decimals: 8\n
    tick_sizes: 1e-08\n
    lot_size: 1e-08\n
    exchange: binance_us
    """
    def __init__(self, pair_info, exchange: str):
        self.symbol = pair_info["symbol"]
        self.base_asset = pair_info["baseAsset"]
        self.quote_asset = pair_info["quoteAsset"]
        self.price_decimal = pair_info["baseAssetPrecision"]
        self.quantity_decimals = pair_info["quotePrecision"]
        self.tick_size = 1 / pow(10, pair_info['baseAssetPrecision'])
        self.lot_size = 1 / pow(10, pair_info['quotePrecision'])
        self.exchange = exchange
        
class Balance:
    """
    Storage for data on your balance in Exchange\n
    Ex. Data - \n
    free_balance: 10.0\n
    locked_balance: 20.0
    """
    def __init__(self, info):
        self.free_balance = float(info["free"])
        self.locked_balance = float(info["locked"])
  
class Trade: 
    """
    Storage for data on your Trades on Exchange\n
    Ex. Data - \n
    """
    def __init__(self, trade_info) -> None:
        self.time: int = trade_info["time"]
        self.pair: PairData = trade_info["pair"]
        self.strategy: str = trade_info["strategy"]
        self.side: str = trade_info["side"]
        self.entry_price: float = trade_info["entry_price"]
        self.status: str = trade_info["status"]
        self.pnl: float = trade_info["pnl"]
        self.quantity: int = trade_info["quantity"]
        self.entry_id: int = trade_info["entry_id"]

class Candle:
    """
    Storage for data on Candles from
    the Exchange\n
    """
    def __init__(self, candle_info, exchange):
        if exchange == 'binance_us':
            self.timestamp = candle_info[0]
            self.open = float(candle_info[1])
            self.high = float(candle_info[2])
            self.low = float(candle_info[3])
            self.close = float(candle_info[4])
            self.volume = float(candle_info[5])
        
        elif exchange == 'parse_trade':
            self.timestamp = candle_info['ts']
            self.open = float(candle_info['open'])
            self.high = float(candle_info['high'])
            self.low = float(candle_info['low'])
            self.close = float(candle_info['close'])
            self.volume = float(candle_info['volume'])
        
    def tick_todecimals(tick_size: float) -> int:
        tick_size_str = "{0:.8f}".format(tick_size)
        while tick_size_str[-1] == "0":
            tick_size_str = tick_size_str[:-1]
            
        split_tick = tick_size_str.split(".")
        
        if len(split_tick) > 1:
            return len(split_tick[1])
        else:
            return 0
        
class OrderStatus:
    """
    Storage for order information sent to
    the exchange
    """
    def __init__(self, order_info):
        self.order_id = order_info["orderId"]
        self.status = order_info["status"].lower()
        self.price = order_info["price"]
        
class Backtestresults:
    def __init__(self):
        self.pnl: float = 0.0
        self.max_dd: float = 0.0
        self.parameters: typing.Dict = dict()
        self.dominated_by: int = 0
        self.dominates: typing.List[int] = []
        self.rank: int = 0
        self.crowding_distance: float = 0.0
        
    def __repr__(self):
        return f"PNL = {round(self.pnl, 2)} Max. Drawdown = {round(self.max_dd, 2)} Parameters = {self.parameters} " \
            f"Rank = {self.rank} Crowding Distance = {self.crowding_distance}"
        
    def reset_results(self):
        self.dominated_by = 0
        self.dominates.clear()
        self.rank = 0
        self.crowding_distance = 0.0