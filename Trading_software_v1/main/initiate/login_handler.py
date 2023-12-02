# This interface will handle access between the login platform/window
# and the actual application. if positive response is not received
# it will not allow access to the application 

##########  Python IMPORTs  ############################################################
from PyQt6.QtWidgets import QApplication
import sys
########################################################################################

##########  Created files IMPORTS  #####################################################
from initiate.login_control.login_interface import LoginWindow
from initiate.root_handler import Root_Handler
########################################################################################

class Login:
    """
    logger -> main logger that was created at the start of the application
    
    This class actually handles access to the application. Access is only
    given if a positive response is given, i.e. login.exec() == 1
    login.exec() is initilly 0. It will change when receiving an
    accept() signal
    
    Thread: Main Thread
    """
    def __init__(self, logger):
        app = QApplication(sys.argv)
        self.log = logger
        self.login = LoginWindow(self.log)
        
        if self.login.button_close_event == 0:
            self.login.show()
            
        if self.login.exec() == 1:
            root_h = Root_Handler(self.log)
            
        else:
            self.login.reject()
            return
        
        # Stops application from closing upon initialization    
        sys.exit(app.exec()) 