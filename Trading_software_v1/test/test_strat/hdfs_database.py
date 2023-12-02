import os
import logging
from typing import *
import h5py
import numpy as np
import pandas as pd
import time
from models import Candle

logger = logging.getLogger()

class Hdf5Client:
    """
    This class handles connection and interaction with HDF5
    database. This will store ticker data tht can be used later 
    """
    def __init__(self, exchange: str, backtest_widget):
        file_path = os.path.join(os.path.dirname(__file__), ".." , "..", "main", "initiate", "root_component", "components", "helper","data", f"{exchange}.h5")
        
        if not os.path.isfile(file_path):
            # Creating a file at specified location
            with open(file_path, 'w') as fp:
                pass

        # this will create a .h5 file for the backtester to use
        self.hf = h5py.File(file_path, "a")
        self.backtest_widget = backtest_widget
        
        # Get rids of buffers
        self.hf.flush()

    def create_dataset(self, symbol: str):
        """
        Pass a symbol to the HDF5 database and it will 
        create a dataset for it inside the exchange database
        """
        if symbol not in self.hf.keys():
            # if this symbol's dataset has not been created before it will be created here
            self.hf.create_dataset(symbol, shape=(0, 6), maxshape=(None, 6), dtype="float64")
            
            # Get rids of buffers
            self.hf.flush()
    
    def write_data(self, symbol: str, data: List[Candle]):
        """
        adds data to the HDF5 database
        """
        # Get the timestamp first to know where to begin
        min_ts, max_ts = self.get_first_last_timestamp(symbol)
        
        # If no data was return:
        if min_ts is None:
            min_ts = float("inf")
            max_ts = 0
            
        # Start a list to filter data later
        filtered_data = []
        
        # check to see if there is data available to insert into the database
        for d in data:
            
            if d.timestamp < min_ts:
                filtered_data.append(d)
                
            elif d.timestamp > max_ts:
                filtered_data.append(d)
                
        if len(filtered_data) == 0:
            logger.warning("%s: No data to insert", symbol)
            
        # Convert model.Candle data into data
        # writable in HDF5 database
        data_hdf5 = []
        for d in data:
            model_candle_data = []
            model_candle_data.append(d.timestamp)
            model_candle_data.append(d.open)
            model_candle_data.append(d.high)
            model_candle_data.append(d.low)
            model_candle_data.append(d.close)
            model_candle_data.append(d.volume)
            data_hdf5.append(model_candle_data)
            
        # Convert data into a mp.array
        data_array = np.array(data_hdf5)
        
        # Make sure hdf5 symbol dataset has room to insert data correctly  
        self.hf[symbol].resize(self.hf[symbol].shape[0] + data_array.shape[0], axis=0)
        self.hf[symbol][-data_array.shape[0]:] = data_array
        
        # Get rids of buffers
        self.hf.flush()

    def get_data(self, symbol: str, from_time: int, to_time: int) -> Union[None, pd.DataFrame]:
        """
        This function will gather data and pack it as a pd.DataFrame
        returns: None | pd.DataFrame
        """
        # Get time to see how long it takes to get all of the data
        start_query = time.time()
        
        # Grab what dataset already exist for you 
        existing_data = self.hf[symbol][:]
        
        # If you have no data, then no data will be returned
        if len(existing_data) == 0:
            return None
        
        # Sort data by timestamp
        data = sorted(existing_data, key=lambda x: x[0])
        data = np.array(data)
        
        # Convert data into a pandas dataframe
        df = pd.DataFrame(data, columns=["timestamp", "open", "high", "low", "close", "volume"])
        df = df[(df["timestamp"] >= from_time) & (df["timestamp"] <= to_time)]
        
        # convert timestamp column into milliseconds
        df["timestamp"] = pd.to_datetime(df["timestamp"].values.astype(np.int64), unit="ms")
        df.set_index("timestamp", drop=True, inplace=True)
        
        # End time to get all of the data
        query_time = round((time.time() - start_query), 2)
        
        # send time to the ui
        logger.info("Retrieved %s %s data from database in %s seconds", len(df.index), symbol, query_time)
        self.backtest_widget._add_log(f"Retrieved {len(df.index)} {symbol} data from database in {query_time} seconds\n")
        
        # returns a pandas DataFrame
        return df

    def get_first_last_timestamp(self, symbol: str) -> Union[Tuple[None, None], Tuple[float, float]]:
        """
        get timestamps from the database that relates to the
        symbol of your choosing. This will look to see
        at what's the latest timestamp dataset you collected
        and what's the earliest timestamp\n
        returns: first_ts, last_ts
        """
        # First grab what dataset you have so far
        existing_data = self.hf[symbol][:]
        
        # If you have no data for thissymbol so far you
        # will return None
        if len(existing_data) == 0:
            return None, None
        
        # if you have some data you will get the first and last
        first_ts = min(existing_data, key=lambda x: x[0])[0]
        last_ts = max(existing_data, key=lambda x: x[0])[0]
        
        # Returns two variables
        return first_ts, last_ts