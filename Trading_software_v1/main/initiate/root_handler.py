##########  Python IMPORTs  ############################################################
from PyQt6.QtWidgets import QMainWindow
########################################################################################

##########  Created files IMPORTS  #####################################################
from initiate.root_component.main_root import Root
from initiate.connectors.binance_us import BinanceUSClient
import initiate.root_component.util.root_variables as r_var
########################################################################################

class Root_Handler:
    """
    This class is responsible for handling files and directories
    to other components that may not have access to certain
    files directly for the main application
    
    Thread: Main Thread
    """
    def __init__(self, logger):
        super().__init__()
        self.root_h_log = logger
        self.Form = QMainWindow()
        self.ui = Root(self.Form, 
                       self.root_h_log,
                       BinanceUSClient(r_var.API_KEY, r_var.API_SECRET_KEY))
        self.Form.show()