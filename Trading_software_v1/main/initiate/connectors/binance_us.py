##########  Python IMPORTs  ############################################################
import logging
import requests
import pprint
import time
import typing
from urllib.parse import urlencode
import hmac
import hashlib
import websocket
import json
import threading 
from typing import Optional
########################################################################################

##########  Python THIRD PARTY IMPORTs  ################################################
from PyQt6 import QtTest
########################################################################################

##########  Created files IMPORTS  #####################################################
from initiate.connectors.models import *
from initiate.root_component.strategies.strategies import (TechnicalStrategy, 
                                                           BreakoutStrategy)
########################################################################################

logger = logging.getLogger()

class BinanceUSClient():
    """
    This Client handles all communiction with the 
    Binance US Spot API service\n
    Thread: Main_Thread \n
    Websocket Thread: Websocket_Thread 
    """
    
    def __init__(self, public_key: str, secret_key: str, tld='us'):
        # Initiate Binance US Rest API
        self._tld = tld
        self._base_url = f"https://www.binance.{self._tld}"
        
        # Initiate Binance US Websocket API
        self._wss_url = f"wss://stream.binance.{self._tld}:9443/ws"
        self._public_key = public_key
        self._secret_key = secret_key
        self._headers = {'X-MBX-APIKEY': self._public_key}
        
        # Initiate pairs on Binance US exchange and 
        # your current balance
        self.pairs = self.get_pairs() 
        self.balances = self.get_balance()
        
        # Initiate dictionary for prices on Binance US
        self.prices = dict()
        
        self.strategies: typing.Dict[int, typing.Union[TechnicalStrategy, BreakoutStrategy]] = dict()
        
        # Initiate websocket for Binance US
        self._ws_id = 1
        self.ws: websocket.WebSocketApp
        self.reconnect = True
        
        # Logs that will be stored and sent to logging frame after some time
        self.logs = []
        
        # Initiate thread for websocket
        t = threading.Thread(target=self._start_ws)
        t.setName("Websocket_Thread")
        t.start() # Start thread
        
        # Let's user know that binance us connection worked properly
        logger.info("Binance US Client successfully initialized")
        
    def _add_log(self, msg: str):
        """
        Adds information to a psuedo log that will yet to 
        be display until some time has passed. log is stored
        in the meantime\n
        Thread: update_ui
        """
        
        logger.info("%s", msg)
        self.logs.append({"log": msg, "displayed": False})
        
    def _generate_signature(self, data: typing.Dict) -> str:
        """
        Signature generator using hashlib sha256
        """
        
        return hmac.new(self._secret_key.encode(), urlencode(data).encode(), hashlib.sha256).hexdigest()
    
    def _make_request(self, method: str, endpoint: str, data: typing.Dict):
        """
        Main function for making a request\n
        Can send either: "GET", "POST", or "DELETE" request
        """
        
        # For GET request
        if method == "GET":
            try:
                response = requests.get(self._base_url + endpoint, params=data, headers=self._headers)
            except Exception as e:
                logger.error(f"Connection error while making {method} request to {endpoint}: {e}")   
                return None 
              
        # For POST request
        elif method == 'POST':
            try:
                response = requests.post(self._base_url + endpoint, params=data, headers=self._headers)
            except Exception as e:
                logger.error(f"Connection error while making {method} request to {endpoint}: {e}")
                return None 
            
        # For DELETE request    
        elif method == 'DELETE':
            try:
                response = requests.delete(self._base_url + endpoint, params=data, headers=self._headers)
            except Exception as e:
                logger.error(f"Connection error while making {method} request to {endpoint}: {e}") 
                return None
            
        else: # if an error has occurred from the request
            raise ValueError()
        
        # 200 status code given from binance US. This is a good signal. Can
        # Safely send response
        if response.status_code == 200:
            return response.json()
        else: # If a different error occurred other than 200
            logger.error(f"Error while making {method} request to {endpoint}: {response.json()} (error code {response.status_code})")
            return None
        
    def get_pairs(self) -> typing.Dict[str, PairData]:
        """
        Gets all of the pairs from Biannce US and returns it as a dictionary\n
        Example -\n
        Returns: {\n
            'BTCUSD4': <initiate.connectors.models.PairData object at 0x00000226B8612EE0>,\n
            'ETHUSD4': <initiate.connectors.models.PairData object at 0x00000226B8616280>,\n
            'XRPUSD': <initiate.connectors.models.PairData object at 0x00000226B86162B0>,\n
            etc...,}
        """
        
        # send request to binance to get all pairs as a json dictionary
        exchange_info = self._make_request("GET", "/api/v3/exchangeInfo", dict())
        
        # Initiate dictionary for pair data
        exchange_pair = dict()
        
        # Append pair get response to exchange pair dictionary
        if exchange_info is not None:
            for pair_data in exchange_info["symbols"]:
                exchange_pair[pair_data["symbol"]] = PairData(pair_data, "binance_us")
                
        return exchange_pair
    
    def get_historical_candles(self, 
                               symbol: PairData, 
                               interval: str, 
                               limit=1000, 
                               start_time: Optional[int] = None, 
                               end_time: Optional[int] = None) -> typing.List[Candle]:
        """
        returns: candles - models.Candles list
        """
        
        data = dict()
        data['symbol'] = symbol.symbol
        data['interval'] = interval
        data['limit'] = limit
        if start_time is not None:
            data["startTime"] = start_time
        if end_time is not None:
            data["endTime"] = end_time
            
        # Send request with data dictionary
        raw_candles = self._make_request("GET", "/api/v3/klines", data)
        
        # Make list to turn hsitorical data into model.Candle data
        candles = []
        
        # convert raw_candles in models.Candle data
        if raw_candles is not None:
            for c in raw_candles:
                candles.append(Candle(c, 'binance_us'))
                
        return candles
    
    def get_bid_ask(self, symbol: PairData) -> typing.Dict[str, float]:
        """
        Get the Bid and ask price that will be used for the watchlist
        component. update_ui thread use this from main_root.py\n
        Thread: update_ui
        """
        
        # Initialize dictionary for storing bid and ask prices
        data = dict()
        data["symbol"] = symbol.symbol
        ob_data = self._make_request("GET", "/api/v3/ticker/bookTicker", data)
        
        # If data is received from bookTicker it will continue
        # Not all pairs will send back ask and bid prices
        if ob_data is not None:
            if symbol.symbol not in self.prices:
                # In case a pair was missed
                self.prices[symbol.symbol] = {'bid': float(ob_data['bidPrice']), 'ask': float(ob_data['askPrice'])}
            else:
                self.prices[symbol.symbol]['bid'] = float(ob_data['bidPrice'])
                self.prices[symbol.symbol]['ask'] = float(ob_data['askPrice'])  
                                              
            return self.prices[symbol.symbol]
    
    def get_balance(self) -> typing.Dict[str, Balance]:
        """
        Gets all of the balance from Biannce US and returns it as a dictionary\n
        Example -\n
        Returns: {\n
            'BTC': <initiate.connectors.models.Balance object at 0x0000026C1F344E50>,\n
            'ETH': <initiate.connectors.models.Balance object at 0x0000026C1F344EE0>,\n
            'USD4': <initiate.connectors.models.Balance object at 0x0000026C1F344F40>,\n
            etc...,}
        """
        
        # Need signature and timestamp to send proper request
        # to Binance Us for balance information
        data = dict()
        data['timestamp'] = int(time.time() * 1000)
        data['signature'] = self._generate_signature(data)
        
        # Initiate dictionary to store balance data
        balances = dict()
        
        # GET request for balance data
        account_data = self._make_request("GET", "/api/v3/account", data)
        
        # Store response into balances dictionary 
        if account_data is not None:
            for a in account_data['balances']:
                balances[a['asset']] = Balance(a)
                
        return balances
    
    def place_order(self, symbol: PairData, order_type: str, quantity: float, side: str, price=None, tif=None) -> OrderStatus:
        """
        Strategies.py will utilize this function to tell Binance
        that you want to place an order. This is a "POST" request 
        """
        
        # Organize the data to send to Binance
        # The way the REST API ask
        data = dict()
        data['symbol'] = symbol.symbol
        data['side'] = side
        data['quantity'] = round(round(quantity / symbol.lot_size) * symbol.lot_size, 8)
        data['type'] = order_type
        
        # If you specified a price to buy at
        if price is not None:
            data['price'] = round(round(price / symbol.tick_size) * symbol.tick_size, 8)
        if tif is not None:    
            data['timeInForce'] = tif
        data['timestamp'] = int(time.time() * 1000)    
        data['signature'] = self._generate_signature(data)
        
        # send request in the form of dictionary
        order_status = self._make_request("POST", "/api/v3/order", data)
        
        # If sending order was successful
        if order_status is not None:
            order_status = OrderStatus(order_status)
            
        return order_status
    
    # def cancel_order(self, symbol: PairData, order_id: int) -> OrderStatus:
    #     data = dict()
    #     data['symbol'] = symbol.symbol
    #     data['orderId'] = order_id
        
    #     data['timestamp'] = int(time.time() * 1000)    
    #     data['signature'] = self._generate_signature(data)
        
    #     order_status = self._make_request("DELETE", "/api/v3/order", data)
        
    #     if order_status is not None:
    #         order_status = OrderStatus(order_status)
        
    #     return order_status
    
    def get_order_status(self, symbol: PairData, order_id: int) -> OrderStatus:
        """
        Pass the PairData and order_id and receive
        the status of your order. This is a "GET" request\n
        return: order_status (model.OrderStatus) 
        """
        
        # Initialize data to send to Binance
        data = dict()
        data['timestamp'] = int(time.time() * 1000)
        data['symbol'] = symbol.symbol
        data['orderId'] = order_id
        data['signature'] = self._generate_signature(data)
        
        # Send request
        order_status = self._make_request("GET", "/api/v3/order", data)
        
        # if order data was received and not []
        if order_status is not None:
            
            # Parse data to an object we can use
            order_status = OrderStatus(order_status)
            
        return order_status # Return model.OrderStatus object
    
    def _start_ws(self):
        """
        Thread: Websocket_Thread
        """
        
        self.ws = websocket.WebSocketApp(self._wss_url, on_open=self._on_open, on_close=self._on_close, on_error=self._on_error, on_message=self._on_message)
        
        while True:
            try:
                if self.reconnect:
                    self.ws.run_forever()
                else:
                    logger.info("Websocket disconnected")
                    break
            except Exception as e:
                logger.error(f"Binance error in run_forever() method: {e}")
            
            QtTest.QTest.qWait(2000)
        
    def _on_open(self, ws):
        """
        Thread: Websocket_Thread
        """
        
        logger.info("Binance connection opened")
        self.subscribe_channel(list(self.pairs.values()), 'bookTicker')
        
    def _on_close(self, ws):
        """
        Thread: Websocket_Thread
        """
        
        logger.warning("Binance Websocket connection closed")
        
    def _on_error(self, ws, msg: str):
        """
        Thread: Websocket_Thread
        """
        
        logger.error(f"Binance connection error {msg}")
        
    def _on_message(self, ws, msg: str):
        """
        Thread: Websocket_Thread
        """
        
        data = json.loads(msg)
        if "e" in data and "e" == "aggTrade":
            symbol = data['s']
            
            for key, strat in self.strategies.item():
                if strat.pair.symbol == symbol:
                    res = strat.parse_trades(float(data['p']), float(data['q']), data['T'])
                    strat.check_trade(res)
                
            logger.info("step not setup yet")
             
        elif "u" in data:
            symbol = data['s']
            if symbol not in self.prices:
                self.prices[symbol] = {'bid': float(data['b']), 'ask': float(data['a'])}
                # Example: 2023-05-24 12:48:24,989 - INFO :: {'bid': 1.177, 'ask': 1.182}
            else:
                self.prices[symbol]['bid'] = float(data['b'])
                self.prices[symbol]['ask'] = float(data['a'])   
                # Example: 2023-05-24 12:48:24,989 - INFO :: {'bid': 1.177, 'ask': 1.182}
                
            # PNL Calculations
            try:
                for b_index, strat in self.strategies.items():
                    # From Technical/Breakout -> PairData
                    # -> symbol == symbol
                    if strat.pair.symbol == symbol:
                        # From Technical/Breakout -> Strategy
                        # -> model.Trade
                        for trade in strat.trades:
                            if trade.status == "open" and trade.entry_price is not None:
                                if trade.side == "long":
                                    trade.pnl = (self.prices[symbol]["bid"] - trade.entry_price) * trade.quantity
                                elif trade.side == "short":
                                    trade.pnl = (trade.entry_price - self.prices[symbol]["ask"]) * trade.quantity
                                    
            except RuntimeError as e:
                logger.error(f"Error while looping through the Binance strategies: {e}")
                self._add_log(f"Error while looping through the Binance strategies: {e}")
        
    def subscribe_channel(self, symbol: typing.List[PairData], channel: str):
        """
        Subscribe to all the pair channels on Binance US\n
        Thread: Websocket_Thread
        """
        
        data = dict()
        data['method'] = 'SUBSCRIBE'
        data['params'] = []
        pair_subscribe = 0
        
        # subscribe to only 20 channels at a time
        # to many will overload the program and not work
        iterator = 20
        while pair_subscribe < len(symbol) and self.reconnect == True:
            if iterator > len(symbol):
                for pairs in symbol[pair_subscribe:]: 
                    data['params'].append(pairs.symbol.lower() + "@" + channel)
                data['id'] = self._ws_id
            else:
                for pairs in symbol[pair_subscribe:iterator]: 
                    data['params'].append(pairs.symbol.lower() + "@" + channel)
                data['id'] = self._ws_id
            
            try:
                self.ws.send(json.dumps(data))
                time.sleep(0.5)
                pair_subscribe += 20
                iterator += 20
            except Exception as e:
                logger.error(f"Websocket error while subscribing to {len(symbol)} {channel}: {e}")
            
        self._ws_id += 1
        
    def get_trade_size(self, pair: PairData, price: float, balance_percent:float):
        """
        Get size of the trade that you need to make. This will be based
        on your wallet balance\n
        returns: the size of the trade
        """
        
        balance = self.get_balances()
        if balance is not None:
############# Will need to change after testing ######################################################
            if 'USDT' in balance:
                balance = balance['USDT'].free_balance
            else:
                return None
        else:
            return None
        # Get trade size
        trade_size = (balance * balance_percent / 100) / price
        trade_size = round(round(trade_size / pair.lot_size) * pair.lot_size)
        # Sends info to logger
        logger.info(f"Binance US current USDT balance = {balance}, trade size = {trade_size}")
        self._add_log
        # return size of trade 
        return trade_size