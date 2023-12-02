##########  Python IMPORTs  ############################################################
import json
from pathlib import Path
import logging
########################################################################################
##########  Python THIRD PARTY IMPORTs  ################################################
from PyQt6.QtWidgets import (QVBoxLayout,
                            QWidget,
                            QGridLayout,
                            QPushButton,
                            QLabel,
                            QComboBox, 
                            QLineEdit,
                            QScrollArea,
                            QMessageBox)
from PyQt6.QtCore import (Qt, 
                          QRect,
                          QRegularExpression)
from PyQt6.QtGui import (QIntValidator,
                         QRegularExpressionValidator)
########################################################################################
##########  Created files IMPORTS  #####################################################
from initiate.connectors.models import *
from initiate.connectors.binance_us import BinanceUSClient
from initiate.root_component.components.logging_component import Logging
import initiate.root_component.util.root_variables as r_var
from initiate.root_component.util.custom_label import Top_Notification
from initiate.root_component.strategies.strategies import (TechnicalStrategy, 
                                                           BreakoutStrategy,
                                                           TraditionalIchimokuStrategy)
########################################################################################
# capturing original logger
logger = logging.getLogger()
# from database import Workspace
            
class StrategyEditor:
    def __init__(self, strategy_page: QWidget, binance_pairs, binance: BinanceUSClient, notification: Top_Notification): #: typing.Dict[str, PairData]):
        """
        Responsible for handeling strategies conducted on the strategy page
        """
        super().__init__()
        
        # self.db = Workspace()
        
        # Initialize
        self.strategy_page = strategy_page
        self._valid_integer = QIntValidator()
        self._valid_float = QRegularExpressionValidator(QRegularExpression(r'[0-9].+'))
        self.logs = []
        self.binance_symbols = list(binance_pairs.keys())
        self.notification = notification
        
        # Adds "_BinanceUS" to all symbols from Binance for list 
        for idx, symbol in enumerate(self.binance_symbols):
            self.binance_symbols[idx] = symbol + "_BinanceUS"
            
        # Initiate exchanges
        self._exchanges = {"BinanceUS": binance}
        
        # Intiate timeframes
        self._all_timeframes = ["1m", "5m", "15m", "30m", "1h", "4h"]
        
        # Create a widget that will contain all things related
        # to the Strategy Page
        # Mainwindow -> central widget -> StackWidget -> Strategy Page
        # -> strategy_widget
        self.strategy_widget = QWidget(self.strategy_page)
        self.strategy_widget.setObjectName(u"strategy_widget")
        self.strategy_widget.setGeometry(QRect(30, 130, 1860, 706))
        
        # Scroll Area is needed for going through list of strategies
        # Mainwindow -> central widget -> StackWidget -> Strategy Page
        # -> strategy_widget -> strategies_scrollArea
        self.strategies_scrollArea = QScrollArea(self.strategy_widget)
        self.strategies_scrollArea.setObjectName("Strategies_scrollArea")
        self.strategies_scrollArea.setWidgetResizable(True)
        self.strategies_scrollArea.setMaximumSize(1840, 500)
        self.strategies_scrollArea.setGeometry(QRect(10, 100, 1840, 596))
        
        # strategies will be the displayed in here
        # Mainwindow -> central widget -> StackWidget -> Strategy Page
        # -> strategy_widget -> strategies_scrollArea
        # -> scrollAreaWidgetContents
        self.scrollAreaWidgetContents = QWidget()
        self.scrollAreaWidgetContents.setObjectName("strategy_scrollAreaWidgetContents")
        
        # Strategies will show up in this frame
        # Mainwindow -> central widget -> StackWidget -> Strategy Page
        # -> strategy_widget -> strategies_scrollArea
        # -> scrollAreaWidgetContents -> _headers_frame
        self._headers_frame = QGridLayout(self.scrollAreaWidgetContents)
        self._headers_frame.setObjectName("Strategy_Headers_frame")
        self._headers_frame.setSpacing(0)
        
        # Push widgets up in watchlist_widget
        self._headers_frame.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        # Add button to strategy_widget. Outside of scroll area
        self.add_button = QPushButton("Add Strategy", self.strategy_widget)
        self.add_button.setObjectName("Add_strategy")
        self.add_button.setMaximumWidth(250)
        self.add_button.setGeometry(QRect(10, 50, 250, 40))
        self.add_button.clicked.connect(self._add_strategy_row)
        
        # Creating headers for scrollAreaWidgetContents
        self._headers = ["Strategy", "Pair", "TimeFrame", "Balance %", "TP %", "SL %"]
        
        # Create a list of QLabels for the number of headers 
        self._headers_labels = [QLabel() for _ in range(len(self._headers))]
        
        # Initiate body widget dictionary
        self.body_widgets = dict()
        
        # If extra parameters are needed for certain strategies
        self._additional_parameters = dict()
        self._extra_input = dict()
        
        # list for constructing strategy parameters
        self._base_params = [
            {"code_name": "strategy_type", 
             "widget"   : QComboBox, 
             "data_type": str, 
             "values"   : r_var.STRATEGIES, 
             "width"    : 10},
            
            {"code_name": "pairs", 
             "widget"   : QComboBox, 
             "data_type": str, 
             "values"   : self.binance_symbols, 
             "width"    : 15},
            
            {"code_name": "timeframe", 
             "widget"   : QComboBox, 
             "data_type": str, 
             "values"   : self._all_timeframes, 
             "width"    : 7},
            
            {"code_name": "balance_percentage", 
             "widget"   : QLineEdit, 
             "data_type": float, 
             "width"    : 7},
            
            {"code_name": "take_profit", 
             "widget"   : QLineEdit, 
             "data_type": float, 
             "width"    : 7},
            
            {"code_name": "stop_loss", 
             "widget"   : QLineEdit, 
             "data_type": float, 
             "width"    : 7},
            
            {"code_name": "parameters", 
             "widget"   : QPushButton, 
             "data_type": float, 
             "text"     : "Parameters", 
             "style"    : "Blue_button", 
             "command"  : self._show_popup},
            
            {"code_name": "activation", 
             "widget"   : QPushButton, 
             "data_type": float, 
             "text"     : "ON", 
             "style"    : "Activation", 
             "command"  : self._switch_strategy},
            
            {"code_name": "delete", 
             "widget"   : QPushButton, 
             "data_type": float, 
             "text"     : "X", 
             "style"    : "remove_button_watchlist", 
             "command"  : self._delete_row}
        ]
        
        # Create labels for headers
        for idx, h in enumerate(self._headers_labels):
            h.setObjectName(f"label_{self._headers[idx]}")
            h.setText(f"{self._headers[idx]}")
            h.setMinimumWidth(200)
            self._headers_frame.addWidget(h, 0, idx)
            
        # changing values in "code_name" into dictionary
        # Ex. "strategy_type" = dict() inside body widget    
        for h in self._base_params:
            self.body_widgets[h['code_name']] = dict()
            
        # Important for where to add pair data in Scroll area
        # self._body_index = 0 is the header area          
        self._body_index = 1
        
        # self._load_workspace()
        
        # Now we add the scrollAreaWidgetContents to trades_scrollArea
        self.strategies_scrollArea.setWidget(self.scrollAreaWidgetContents)
    
    def _add_log(self, message: str):
        """ 
        Send information to logger frame to be displayed
        later
        """
        logger.info(f"{message}")
        self.logs.append({"log": message, "displayed": False})
            
    def _add_strategy_row(self):
        """
        Add strategy to _headers_frame
        """
        
        b_index = self._body_index
        
        # Enumerates over dictionaries in base_params list
        for col, base_params in enumerate(self._base_params):
            code_name = base_params['code_name']
            
            # Create combo boxes 
            if base_params['widget'] == QComboBox:
                self.body_widgets[code_name][b_index] = QComboBox()
                self.body_widgets[code_name][b_index].addItem("")
                self.body_widgets[code_name][b_index].setItemText(0, "")
                self.body_widgets[code_name][b_index].addItems(base_params['values'])
                self.body_widgets[code_name][b_index].setMinimumWidth(base_params['width'])  
                    
            # Create combo line edits     
            elif base_params['widget'] == QLineEdit:
                
                self.body_widgets[code_name][b_index] = QLineEdit()
                
                # limit wht can be entered into the line edits
                if base_params['data_type'] == int:
                    self.body_widgets[code_name][b_index].setValidator(self._valid_integer)
                    
                if base_params['data_type'] == float:
                    self.body_widgets[code_name][b_index].setValidator(self._valid_float)
                    
            # Create buttons     
            elif base_params['widget'] == QPushButton:
                self.body_widgets[code_name][b_index] = QPushButton()
                self.body_widgets[code_name][b_index].setText(base_params['text'])
                self.body_widgets[code_name][b_index].setObjectName(base_params['style'])
                self.body_widgets[code_name][b_index].clicked.connect(lambda state, x = (base_params['command']): x(b_index))  
                  
            else:
                continue
            
            #  add specified widget to its location
            self._headers_frame.addWidget(self.body_widgets[code_name][b_index], b_index, col)
            
        # Create dictionary for additional parameters    
        self._additional_parameters[b_index] = dict()
        
        # Turns the code names of the strategy types None
        # Ex. "ema_fast" = None
        for strat, params in r_var.EXTRA_PARAMETERS.items():
            
            for param in params:
                self._additional_parameters[b_index][param['code_name']] = None
                
        # Have to update to go to next line
        self._body_index += 1
        
    def _delete_row(self, b_index: int):
        """
        Permanently removes the specified row from the ui
        """
        for element in range(len(self._base_params)):
            # Delete items from their position
            del_widget = self._headers_frame.itemAtPosition(b_index, element).widget()
            del_widget.deleteLater()
            
        # Delete items completely from ui    
        for element in self._base_params:
            del self.body_widgets[element['code_name']][b_index]
            
    class Popup_window(QWidget):
        """
        This "window" is a QWidget. If it has no parent, it
        will appear as a free-floating window as we want.
        """
        def __init__(self, position):
            super().__init__()
            
            # Create new widget for popup window
            self.pop_window = QWidget()
            self.pop_window.setObjectName("Parameters_Window")
            self.pop_window.resize(500, 300)
            self.pop_window.setWindowTitle("Parameters")
            self.pop_window.setStyleSheet(Path(r_var.DARK_MODE).read_text())
            self.pop_window.setGeometry(QRect(position.x(), position.y() + 500, 500, 300))
            
            # Add a widget to this pop_up window
            self.popup_widget = QWidget(self.pop_window)
            self.popup_widget.setObjectName("pop_up_widget")
            self.popup_widget.setGeometry(QRect(10, 1, 490, 290))
            
            # Give it a vertical layout
            self.vertical_pop_up = QVBoxLayout(self.popup_widget)
            self.vertical_pop_up.setObjectName("Vertical_Layout_popup_window")
            self.vertical_pop_up.setSpacing(0)
            
            # Now add a grid to the Vertical layout
            self.grid_frame = QGridLayout()
            self.grid_frame.setObjectName("Grid_frame_popup")
            self.grid_frame.setSpacing(5)
            self.vertical_pop_up.addLayout(self.grid_frame)
            self.vertical_pop_up.setAlignment(Qt.AlignmentFlag.AlignTop)
            
        def adding_widget_popup_grid(self, widget, row: int, column: int):
            """
            This will add a widget to the grid of the popup window
            """
            self.grid_frame.addWidget(widget, row, column)
            
        def adding_widget_popup_main(self, widget):
            """
            This will add a widget to the vertical layout 
            of the popup window
            """
            self.vertical_pop_up.addWidget(widget)
            
    def _show_popup(self, b_index: int):
        """
        This will make the pop up window appear and
        controls what fills it.
        """
        
        # Get the Startegy that was selected so 
        strat_selected = self.body_widgets['strategy_type'][b_index].currentText()
        
        if strat_selected == "": 
            QMessageBox.warning(self.strategy_widget, "Strategy Missing",
                                    "Please select a strategy type first")
            return
        
        # Get the position of the button to specify where the pop
        # up window should show up at
        position = self.body_widgets['parameters'][b_index].pos()
        
        # Initiate Popup Window
        self._show_popup_window = self.Popup_window(position)
        
        # Start at row number 1
        row_nb = 0
        
        # Add extra parameters to the Popup Window
        for param in r_var.EXTRA_PARAMETERS[strat_selected]:
            
            # Inside strategy list that was selected
            code_name = param['code_name']
            
            # Create labels for line edits
            temp_label = QLabel() 
            temp_label.setObjectName("Parameter_" + param['name'])
            temp_label.setText(param['name'])
            temp_label.setMaximumWidth(200)
            temp_label.setIndent(10)
            self._show_popup_window.adding_widget_popup_grid(temp_label,
                                                             row_nb,
                                                             0)
            
            # Create line edits next to the QLabels
            if param['widget'] == QLineEdit:
                self._extra_input[code_name] = QLineEdit()
                self._extra_input[code_name].setAlignment(Qt.AlignmentFlag.AlignCenter)
                self._extra_input[code_name].setMaximumWidth(200)
                self._show_popup_window.adding_widget_popup_grid(self._extra_input[code_name],
                                                             row_nb,
                                                             1)
                
                # Limit what is entered into these line edits
                if param['data_type'] == int:
                    self._extra_input[code_name].setValidator(self._valid_integer)
                    
                if param['data_type'] == float:
                    self._extra_input[code_name].setValidator(self._valid_float)
                    
                # Makes sure that the parameters stay when you exit the window
                if self._additional_parameters[b_index][code_name] is not None:
                    self._extra_input[code_name].setText(str(self._additional_parameters[b_index][code_name]))
                    
            else:
                continue
            
            row_nb += 1
            
        # Validation Button
        validation_button = QPushButton("Validate")
        validation_button.setObjectName("Add_strategy")
        validation_button.setMaximumWidth(150)
        validation_button.clicked.connect(lambda: self._validate_parameters(b_index))
        self._show_popup_window.adding_widget_popup_main(validation_button)
        
        # Now show pop up window upon setting it up
        self._show_popup_window.pop_window.show()
        
        return
        
    def _switch_strategy(self, b_index: int):
        """
        Activates or deactivates the strategy
        """
        
        # This prevents you from setting up a strategy with 
        # missing parameters
        for param in ["balance_percentage", "take_profit", "stop_loss"]:
            
            if self.body_widgets[param][b_index].text() == "":
                self._add_log(f"Missing {param} parameter")
                self.notification.notify(f"Missing {param} parameter")
                return
            
        # Get the strategy selected    
        strat_selected = self.body_widgets['strategy_type'][b_index].currentText()
        for param in r_var.EXTRA_PARAMETERS[strat_selected]:
            
            if self._additional_parameters[b_index][param['code_name']] is None:
                self._add_log(f"Missing {param['code_name']} parameter")
                self.notification.notify(f"Missing {param} parameter")
                return
            
        # Removes the _ from the symbol from the QComboBox
        # Ex. BTCUSDT_BinanceUS = BTCUSDT    
        symbol = self.body_widgets['pairs'][b_index].currentText().split("_")[0]
        timeframe = self.body_widgets['timeframe'][b_index].currentText()
        
        # Removes the _ from the symbol from the QComboBox
        # Ex. BTCUSDT_Binance_US = BinanceUS 
        exchange = self.body_widgets['pairs'][b_index].currentText().split("_")[1]
        
        # Gets binanceclient class then gets its pairs PairData symbol
        pair = self._exchanges[exchange].pairs[symbol]
        
        # Get Text from QLineEdits
        balance_percent = float(self.body_widgets['balance_percentage'][b_index].text()) 
        take_profit = float(self.body_widgets['take_profit'][b_index].text())
        stop_loss = float(self.body_widgets['stop_loss'][b_index].text())
        
        # If activation is off and you want to start strategy
        if self.body_widgets['activation'][b_index].text() == "ON":
            
############ This will continously be expanded as the program develops ######################################  
            if strat_selected == 'Technical':
                new_strategy = TechnicalStrategy(self._exchanges[exchange], pair, exchange, timeframe,
                                                 balance_percent,take_profit, stop_loss,
                                                 self._additional_parameters[b_index])  
                
            elif strat_selected == 'Breakout':
                new_strategy = BreakoutStrategy(self._exchanges[exchange],pair, exchange, timeframe, 
                                                balance_percent, take_profit, stop_loss, 
                                                self._additional_parameters[b_index])
                
            elif strat_selected == 'Traditional Ichimoku':
                new_strategy = TraditionalIchimokuStrategy(self._exchanges[exchange],pair, exchange, timeframe, 
                                                           balance_percent, take_profit, stop_loss, 
                                                           self._additional_parameters[b_index])  
                
            else:
                return
#############################################################################################################    
 
            # Get historical candle data. returns models.Candle data        
            new_strategy.candles = self._exchanges[exchange].get_historical_candles(pair, timeframe)
            
            # if no candle data was sent
            if len(new_strategy.candles) == 0:
                self._add_log(f"No historical data retrieved for {pair.symbol}")
                return 
            
############ This will continously be expanded as the program develops #######################################              
            if exchange == "BinanceUS":
                self._exchanges[exchange].subscribe_channel([pair], "aggTrade")
##############################################################################################################

            # Adds a new object to exchangeclient.strategies              
            self._exchanges[exchange].strategies[b_index] = new_strategy
            
            # loop through list of _base_params widgets
            for param in self._base_params:
                
                code_name = param["code_name"]
                # Disable all buttons if strategy is activated
                
                if code_name != "activation":
                    self.body_widgets[code_name][b_index].setEnabled(False) 
                    self.body_widgets['activation'][b_index].setText("OFF")
                    self.body_widgets['activation'][b_index].setStyleSheet(Path(r_var.DISABLE_STYLE).read_text())
                    self.body_widgets[code_name][b_index].setStyleSheet(Path(r_var.DISABLE_STYLE).read_text())
            
            self._add_log(f"{strat_selected} strategy on {symbol} / {timeframe} started")
            self.notification.notify(f"{strat_selected} strategy on {symbol} / {timeframe} started")
            
        # if activation is "ON" and you want to disable
        else:
            
            # Stops strategy
            del self._exchanges[exchange].strategies[b_index]
            
            # loop through list of _base_params widgets
            for param in self._base_params:
                
                code_name = param["code_name"]
                
                # Enbles all buttons if strategy is activated
                if code_name != "activation":
                    self.body_widgets[code_name][b_index].setEnabled(True)
                    self.body_widgets['activation'][b_index].setText("ON")
                    self.body_widgets['activation'][b_index].setStyleSheet(Path(r_var.DARK_MODE).read_text())
                    self.body_widgets[code_name][b_index].setStyleSheet(Path(r_var.DARK_MODE).read_text())

            self._add_log(f"{strat_selected} strategy on {symbol} / {timeframe} stoppped")
            self.notification.notify(f"{strat_selected} strategy on {symbol} / {timeframe} stoppped")
            
    def _validate_parameters(self, b_index: int):
        """
        Adds the extra parameters to a dictionary
        """
        
        strat_selected = self.body_widgets['strategy_type'][b_index].currentText()
        
        # Goes through the extra parameters
        for param in r_var.EXTRA_PARAMETERS[strat_selected]:
            
            code_name = param['code_name']
            
            # If a parameter is left blank, change it to none
            if self._extra_input[code_name].text() == "":
                self._additional_parameters[b_index][code_name] = None
                
            else:
                # Else we add everything to _additional parameter dictionary for strategy
                self._additional_parameters[b_index][code_name] = param['data_type'](self._extra_input[code_name].text())
                
        # Close Pop up window upon clicking button
        self._show_popup_window.pop_window.close()
        
    # def _load_workspace(self):
    #     data = self.db.get("strategies")
    #     for row in data:
    #         self._add_strategy_row()
            
    #         b_index = self._body_index - 1
           
    #         for base_param in self._base_params:
    #             code_name = base_param['code_name']
                
    #             if base_param['widget'] == QComboBox and row[code_name] is not None:
    #                 self.body_widgets[code_name][b_index].setCurrentText(row[code_name])
                    
    #             elif base_param['widget'] == QLineEdit and row[code_name] is not None:
    #                 self.body_widgets[code_name][b_index].setText(str(row[code_name]))
                    
    #         extra_params = json.loads(row['extra_params'])
                    
    #         for param, value in extra_params.items():
    #             if value is not None:
    #                 self._additional_parameters[b_index][param] = value     