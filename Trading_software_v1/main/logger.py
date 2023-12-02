# Logger function and functionality that will be used throughout 
# the application

##########  Python IMPORTs  ############################################################
import logging
import os
########################################################################################
print(os.getcwd())

def main():
    """
    Logger that will be used throught the application\n
    format: %(asctime)s - %(levelname)s :: %(message)s\n
    example: 2023-05-22 13:01:11,309 - INFO :: Binance US Client
    successfully initialized\n
    can do: logger.debug logger.info logger.error logger.warning  
    """
    
    logger = logging.getLogger()
    logger.setLevel(logging.INFO)
    
    stream_handler = logging.StreamHandler()
    formatter = logging.Formatter("%(asctime)s %(threadName)12s - %(levelname)s :: %(lineno)-4d %(message)s")
    stream_handler.setFormatter(formatter)
    stream_handler.setLevel(logging.INFO)

    file_dir = os.path.join("main", "initiate", "root_component", "util", "info.log")
    file_handler = logging.FileHandler("." + "\\" + file_dir)
    file_handler.setFormatter(formatter)
    file_handler.setLevel(logging.DEBUG)

    logger.addHandler(stream_handler)
    logger.addHandler(file_handler)
    
    return logger