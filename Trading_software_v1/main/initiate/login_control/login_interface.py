
##########  Python IMPORTs  ############################################################
from PyQt6.QtWidgets import QMessageBox
import sqlite3
########################################################################################

##########  Created files IMPORTS  #####################################################
from initiate.login_control.utils.cryptography_helper import Login_Cryptography 
# UIs
from initiate.login_control.gui.login import Login
from initiate.login_control.gui.create_account import Create_Account
########################################################################################

class LoginWindow(Login):
    """
    This handles the login window functionality
    from the pyuic6 generated login.ui
    
    Ultimately returns: accept()
    
    else: None
    
    Thread: Main Thread
    """
    def __init__(self, logger):
        super().__init__()
        self.setupUi(self)
        self.setWindowTitle("Login Window")
        self.log = logger
        
        # 1. This connects to Log_connect database
        self.conn = sqlite3.connect('Log_connect.db')
        self._initializer()
        self.pushButton_login.clicked.connect(self.login)
        self.pushButton_create_account.clicked.connect(self._creating_account)
    
    def _initializer(self):
        # application will not close as long as this is 0
        self.button_close_event = 0
        # 2. Creates Table if it does not exist
        cursor = self.conn.execute("CREATE TABLE IF NOT EXISTS login (username_key BLOB, username BLOB, password_key BLOB, password BLOB)")
        # 3. Gets database login data
        cursor = self.conn.execute("SELECT username_key, username, password_key, password FROM login")
        # Remember for this list username is 0 element, password is 1 element
        self._sql_login_data = cursor.fetchall()
        # 4. Initiate Login_Cryptography 
        self._crypto = Login_Cryptography()
        if not self._sql_login_data:
            button = QMessageBox.question(self, "No Login Information",
                                 "Welcome! There does not seem to be any login information."
                                 + " This must be your first time using the application.\n\n"
                                 + "Please create a new account."
                                 + " Clicking close will exit the program", 
                                 QMessageBox.StandardButton.Ok | QMessageBox.StandardButton.Close)
            
            if button == QMessageBox.StandardButton.Ok:
                self.button_close_event = 0
                self._creating_account()
            if button == QMessageBox.StandardButton.Close:
                self.conn.close()
                # signals to login_handler to close application
                self.button_close_event = 1
        
    def login(self):
        """"
        Emmitted when Login button is clicked
        Will check if username or password exist
        """
        try:
            for element in self._sql_login_data:
                if self.lineEdit_username.text() == self._crypto.decrypt(element[1], element[0]): 
                    if self.lineEdit_password.text() == self._crypto.decrypt(element[3], element[2]):
                        self.accept()
                        self.conn.close()
                    else:
                        QMessageBox.warning(self, "Wrong username or password",
                                    "Either the username or password is incorrect")
                else: 
                    QMessageBox.warning(self, "Wrong username or password",
                                        "Either the username or password is incorrect")
        except Exception as e:
            self.log.error(e)
            
    def _creating_account(self):
        """
        From the LoginWindow class Create Account Window is called
        """
        self.account_creation = CreateAccount(self.conn, self.log)
        self.account_creation.show()
        self._initializer()
            
class CreateAccount(Create_Account):
    """
    This Window allows the user to create a new account
    with a new password.
    
    Thread: Main Thread
    """
    def __init__(self, sql_connect, logger):
        super().__init__()
        self.setupUi(self)
        self.sql_connection = sql_connect
        self.log = logger
        self._initializer()
        self.pushButton_create.clicked.connect(self.create_account)
    
    def _initializer(self):
        # 1. Initiate Login_Cryptography 
        self._crypto = Login_Cryptography()
        self.setWindowTitle("Create Account")
        self.move(self.pos().x() + 500, self.pos().y() + 200)
        
    def create_account(self):
        """
        Checks and validates user's input for creating a new account.
        If valid returns new username and password to database
        """
        try:
            username = self.lineEdit_username.text() 
            password = self.lineEdit_password.text()
            confirm_password = self.lineEdit_password_2.text()
            
            if username == "":
                # Prevent user from entering blank username 
                QMessageBox.warning(self, "Error",
                                    "Username Cannot Be Empty!")
            elif password == "" or confirm_password == "":
                # Prevent user from entering blank password 
                QMessageBox.warning(self, "Error",
                                    "Password Cannot Be Empty!")
            elif password != confirm_password:
                # Prevent user from misstyping intended password 
                QMessageBox.warning(self, "Error",
                                    "Confirmation Password does not match Pasword!")
            else: 
                username_key, username = self._crypto.encrypt_it(username)
                password_key, password = self._crypto.encrypt_it(password)
                # Inserting encryption and their key to sql database
                save_user_pass_query = f"""INSERT INTO login (username_key, username, password_key, password)
                    VALUES (?, ?, ?, ?)""" 
                binary_tuple = (memoryview(username_key), memoryview(username), memoryview(password_key), memoryview(password))
                self.sql_connection.execute(save_user_pass_query, binary_tuple)
                # Commit Change
                self.sql_connection.commit()
                q_button = QMessageBox.information(self, "Account Created",
                                    """Welcome! Account has been successfully created!""", 
                                    QMessageBox.StandardButton.Ok)
                if q_button.Ok:
                    self.destroy()
        except Exception as e:
            self.log.error(e)