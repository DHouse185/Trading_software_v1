##########  Python IMPORTs  ############################################################
from typing import *
import time
import logging
########################################################################################
##########  Python THIRD PARTY IMPORTs  ################################################
from PyQt6 import QtTest
from PyQt6.QtCore import QDateTime
########################################################################################
##########  Created files IMPORTS  #####################################################
import initiate.root_component.util.root_variables as r_var
from initiate.root_component.components.helper.hdfs_database import Hdf5Client
from initiate.connectors.binance_us import BinanceUSClient
########################################################################################

logger = logging.getLogger()

def collect_all(backtest_widget,
                client: BinanceUSClient, 
                exchange: str,
                symbol: str, 
                timeframe: str, 
                from_time: QDateTime, 
                to_time: QDateTime,
                stop_thread):
    """
    This will first collect data that is already in the database
    Then whatever is missing, it will be collected from the exchange
    and stored in a HDF5 file that is specific to that exchange
    and dataset that is specific to that symbol/pair
    Interval is capped at 1m to stop error from pull data
    requests\n
    Notes
    -----
    60000 = 1 minute (60 * 1000)\n
    * 1000 converts seconds into milliseconds,
    exchanges read timstmps in milliseconds
    """
    
    try:
        # Initiate HDF5 client class
        h5_db = Hdf5Client(exchange, backtest_widget=backtest_widget)
        
        # It's important to make sure there is an available dataset for the 
        # Pair that you want
        h5_db.create_dataset(symbol=symbol)
        
        # Get a pandas dataframe of data that is already in the 
        # hdf5 database that you may have 
        data = h5_db.get_data(symbol, from_time=0, to_time=int(time.time() * 1000))
        
        if data is not None:
            # converts the data timeframe into what you want 
            data = r_var.resample_timeframe(data=data, tf=timeframe)
            
        # Sends what data you already have to the ui
        backtest_widget._add_log(f'{data}\n')
        
        # Get the first and last timestamps to know where to strat
        # When collecting data
        oldest_ts, most_recent_ts = h5_db.get_first_last_timestamp(symbol)
        
        # Send this info to the ui
        backtest_widget._add_log(f'The oldest timestmp is: {oldest_ts}\nThe most recent Timestep is: {most_recent_ts}\n')
        
        if stop_thread():
            return
        
        # If you already have the necessary data that you're trying to pull
        if oldest_ts and most_recent_ts is not None:
            
            # If you already have the requested data:
            if oldest_ts < ((from_time.toSecsSinceEpoch() * 1000) - 60000) and \
            most_recent_ts > ((to_time.toSecsSinceEpoch() * 1000) - 60000):
                logging.info(f"For {exchange} pair {symbol}: You've already collected data from \
                            {r_var.ms_to_dt(data[0].timestamp)} to {r_var.ms_to_dt(data[-1].timestamp)}")
                backtest_widget._add_log(f"{exchange} {symbol}: Collected {len(data)} recent data from \
                    {r_var.ms_to_dt(data[0].timestamp)} to {r_var.ms_to_dt(data[-1].timestamp)}")
                return
            
            # If you requested to get older data than what you have available
            if oldest_ts > ((from_time.toSecsSinceEpoch() * 1000) - 60000):
                oldest_ts = ((from_time.toSecsSinceEpoch() * 1000) - 60000)
                
        if stop_thread():
            return
        
        # Initial request
        # If you have no data at all
        if oldest_ts is None:
            # data is a list of models.Candle data
            data = client.get_historical_candles(client.pairs[symbol],
                                                interval=timeframe,
                                                end_time=((to_time.toSecsSinceEpoch() * 1000) - 60000),
                                                start_time=((from_time.toSecsSinceEpoch() * 1000) - 60000))
            
            # If no data was return you will be notified
            if len(data) == 0:
                logger.warning("%s %s: no initial data found", exchange, symbol)
                backtest_widget._add_log(f"{exchange} {symbol}: no initial data found")
                return
            
            else:
                logger.info("%s %s: Collected %s initial data from %s to %s", exchange, symbol, len(data),
                r_var.ms_to_dt(data[0].timestamp), r_var.ms_to_dt(data[-1].timestamp))
                backtest_widget._add_log(f"{exchange} {symbol}: Collected {len(data)} initial data from \
                                         {r_var.ms_to_dt(data[0].timestamp)} to {r_var.ms_to_dt(data[-1].timestamp)}")
                
            # Prepre to write data into hdf5 file
            oldest_ts = data[0].timestamp
            most_recent_ts = data[-1].timestamp
            
            # Write data into HDF5 database Needed data is collected
            h5_db.write_data(symbol=symbol, data=data)
            
        # Preparing to add additional requested data
        data_to_insert = []
        
        if stop_thread():
            return
        
        # Most recent data to see what you are missing
        # If you request to get newer data than what you have available
        if most_recent_ts < ((to_time.toSecsSinceEpoch() * 1000) - 60000):
            
            while True:
                
                data = client.get_historical_candles(client.pairs[symbol], 
                                                    interval=timeframe,
                                                    start_time=int(most_recent_ts + 60000),
                                                    end_time=((to_time.toSecsSinceEpoch() * 1000) - 60000)) 
                
                # if no data was received
                if data is None:
                    QtTest.QTest.qWait(4000) # Pause in case an error occurs during the request
                    continue
                
                # if you were only missing data point 
                if len(data) < 2:
                    break
                
                # data = everything except last data point
                data = data[:-1]
                # combine the two list 
                data_to_insert = data_to_insert + data
                
                if len(data_to_insert) > 10000:
                    h5_db.write_data(symbol=symbol, data=data_to_insert)
                    data_to_insert.clear()
                    
                # change new recent data to most recent
                if data[-1].timestamp > most_recent_ts:
                    most_recent_ts = data[-1].timestamp
                    
                # Notify the ui on data that was collected
                logging.info("%s %s: Collected %s recent data from %s to %s", exchange, symbol, 
                len(data), r_var.ms_to_dt(data[0].timestamp), r_var.ms_to_dt(data[-1].timestamp))
                backtest_widget._add_log(f"{exchange} {symbol}: Collected {len(data)} recent data from \
                                         {r_var.ms_to_dt(data[0].timestamp)} to {r_var.ms_to_dt(data[-1].timestamp)}")
                
                # Give some waiting time before continuing
                QtTest.QTest.qWait(1100)
                
                # write data in hdf5 database
                h5_db.write_data(symbol=symbol, data=data_to_insert)
                data_to_insert.clear()
                
                if stop_thread():
                    break
                
        if stop_thread():
            return
        
        # Older data
        # If you requested to get older data than what you have available
        if oldest_ts > ((from_time.toSecsSinceEpoch() * 1000) - 60000):
            
            while True:
                
                data = client.get_historical_candles(client.pairs[symbol],
                                                    interval=timeframe,
                                                    start_time=((from_time.toSecsSinceEpoch() * 1000) + 60000),
                                                    end_time=int(oldest_ts - 60000)) 
                
                # if no data was received
                if data is None:
                    QtTest.QTest.qWait(4000) # Pause in case an error occurs during the request
                    continue
                
                # if you have all old data available on exchange
                if len(data) == 0:
                    logger.info("%s %s: Stopped older data collection because no data was found before %s", exchange,
                    symbol, r_var.ms_to_dt(oldest_ts))
                    backtest_widget._add_log(f"{exchange} {symbol}: Stopped older data collection because \
                                             no data was found before {r_var.ms_to_dt(oldest_ts)}")
                    break
                
                # combine the two list, what you have and collected 
                data_to_insert = data_to_insert + data
                
                if len(data_to_insert) > 10000:
                    h5_db.write_data(symbol=symbol, data=data_to_insert)
                    data_to_insert.clear()
                    
                # change old data to oldest
                if data[0].timestamp < oldest_ts:
                    oldest_ts = data[0].timestamp
                    
                # Notify the ui on data that was collected
                logging.info("%s %s: Collected %s older data from %s to %s", exchange, symbol,
                len(data), r_var.ms_to_dt(data[0].timestamp), r_var.ms_to_dt(data[-1].timestamp))
                backtest_widget._add_log(f"{exchange} {symbol}%s %s: Collected {len(data)} older data from \
                    {r_var.ms_to_dt(data[0].timestamp)} to {r_var.ms_to_dt(data[-1].timestamp)}")
                
                # write data in hdf5 database
                h5_db.write_data(symbol=symbol, data=data)
                
                # Give some waiting time before continuing
                QtTest.QTest.qWait(1100)
                
                if stop_thread():
                    break
                
        if stop_thread():
            return
        
        # h5_db.write_data(symbol=symbol, data=data_to_insert)
    except Exception as e:
        logging.error(f"Error: {e}")
        backtest_widget._add_log(f"Error: {e}")