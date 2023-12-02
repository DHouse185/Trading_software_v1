##########  Python IMPORTs  ############################################################
import logging
import matplotlib
from matplotlib.figure import Figure
from matplotlib.backends.backend_qtagg import FigureCanvasQTAgg
from matplotlib.backends.backend_qtagg import (
    NavigationToolbar2QT as NavigationToolbar,
)
import matplotlib.pyplot as plt
import threading 
import pandas as pd
import numpy as np
########################################################################################

##########  Python THIRD PARTY IMPORTs  ################################################
from PyQt6.QtWidgets import (QVBoxLayout,
                             QWidget,
                             QGridLayout,
                             QDateEdit,
                             QPushButton,
                             QLabel,
                             QComboBox, 
                             QLineEdit,
                             QMessageBox)
from PyQt6.QtCore import (Qt, 
                          QRect,
                          QRegularExpression,
                          QDateTime,
                          QDate,
                          QTime)
from PyQt6.QtGui import (QIntValidator,
                         QRegularExpressionValidator)
import mplfinance as mpf
########################################################################################

##########  Created files IMPORTS  #####################################################
from initiate.connectors.models import *
from initiate.connectors.binance_us import BinanceUSClient
import initiate.root_component.components.helper.data_collector as data_collector
import initiate.root_component.components.helper.backtester as backtest_helper 
import initiate.root_component.components.helper.optimizer as optimizer_helper 
from initiate.root_component.components.helper.hdfs_database import Hdf5Client
import initiate.root_component.util.root_variables as r_var
########################################################################################

matplotlib.use("QtAgg") 
# # capturing original logger

logger = logging.getLogger()
# # from database import Workspace

class MplCanvas(FigureCanvasQTAgg):
    """
    This object will be responsible for displaying
    chart/graph on the backtest page
    """
    def __init__(self, parent=None, width=20, height=8, dpi=100):
        plt.rcParams.update(r_var.CHART_BINANCE_DARK_STYLE)
        plt.grid(True)
        self.fig, self.ax = plt.subplots(figsize=(width, height), dpi=dpi)
        super().__init__(self.fig)
        self.setParent(parent)
              
class BacktestLab:
    def __init__(self, 
                 backtest_page: QWidget, 
                 binance_pairs: PairData, 
                 binance: BinanceUSClient): #, notification: Top_Notification): #: typing.Dict[str, PairData]):
        """
        Responsible for handeling strategies conducted on the strategy page
        """
        super().__init__()
        
#         # self.db = Workspace()

        # Initialize
        self.backtest_page = backtest_page
        self._valid_integer = QIntValidator()
        self._valid_float = QRegularExpressionValidator(QRegularExpression(r'[0-9].+'))
        self.logs = []
        self.binance_symbols = list(binance_pairs.keys())
        
#         self.notification = notification

        # Adds "_BinanceUS" to all symbols from Binance for list 
        for idx, symbol in enumerate(self.binance_symbols):
            self.binance_symbols[idx] = symbol + "_BinanceUS"
            
        # Initiate exchanges
        self._exchanges = {"BinanceUS": binance}
        
        # Create a widget that will contain all things related
        # to the Backtesting Page
        # Mainwindow -> central widget -> StackWidget -> Backtest Page
        # -> strategy_widget
        self.backtest_widget = QWidget(self.backtest_page)
        self.backtest_widget.setObjectName(u"strategy_widget")
        self.backtest_widget.setGeometry(QRect(30, 130, 1860, 706))
        
        ################ Chart ################
        # Charting activity will occur here
        # Mainwindow -> central widget -> StackWidget 
        # -> Backtest Page -> chart_area
        self.chart_area = QWidget(self.backtest_page)
        self.chart_area.setObjectName(u"chart_area_widget")
        self.chart_area.setGeometry(QRect(5, 70, 1850, 506))
        
        # Chart area layout organizer
        # Mainwindow -> central widget -> StackWidget 
        # -> Backtest Page -> chart_area -> chart_area_VBox
        self.chart_area_VBox = QVBoxLayout(self.chart_area)
        
        # matplotlib Chart object
        self.matplotlib_chart = MplCanvas(self.chart_area, width=30, height=8, dpi=100)    
         
        # Create toolbar, passing canvas as first parameter, parent (self, the MainWindow) as second.
        self.chart_toolbar = NavigationToolbar(self.matplotlib_chart, self.chart_area)
        self.chart_toolbar.move(400, 0)
        self.chart_area_VBox.addWidget(self.chart_toolbar)
        self.chart_area_VBox.addWidget(self.matplotlib_chart)
        self.chart_area.setLayout(self.chart_area_VBox)
        
        ################ Chart Editor ################
        # Backtesting control will occcur here. 
        # This will interact with the chart as well 
        # Mainwindow -> central widget -> StackWidget 
        # -> Backtest Page -> backtesting_area
        self.backtesting_area = QWidget(self.backtest_page)
        self.backtesting_area.setObjectName(u"backtesting_area_widget")
        self.backtesting_area.setGeometry(QRect(5, 586, 1850, 273))
        
        # Strategy finder will show up in this frame
        # Mainwindow -> central widget -> StackWidget 
        # -> Backtest Page -> backtesting_area
        # -> _headers_frame
        self._headers_frame = QGridLayout(self.backtesting_area)
        self._headers_frame.setObjectName("Backtesting_Headers_frame")
        self._headers_frame.setSpacing(0)
        
        # Push widgets up in backtesting_area
        self._headers_frame.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        # Add QCombobox to _headers_frame to start off 
        pick_strategy_label = QLabel("Start By Picking a Strategy:")
        pick_strategy_label.setMaximumWidth(250)
        
        self.initialize_strategy = QComboBox()
        self.initialize_strategy.setObjectName("Add_strategy_combobox")
        self.initialize_strategy.addItem("")
        self.initialize_strategy.setItemText(0, "")
        self.initialize_strategy.addItems(r_var.STRATEGIES)
        self.initialize_strategy.addItem("Collect Data")
        self.initialize_strategy.setMaximumWidth(150) 
        
        self._headers_frame.addWidget(pick_strategy_label, 0, 0)
        self._headers_frame.addWidget(self.initialize_strategy, 0, 1)
        
        # Initiate body widget dictionary
        self.body_widgets = dict()   
             
        # If extra parameters are needed for certain strategies
        self._additional_parameters = dict()
        self._extra_input = dict()
        
        # list for constructing strategy parameters
        # Creating headers for base parameters strategy
        self._headers_strategy = ["Pair",            "TimeFrame",       "Balance", 
                                  "Balance %",       "TP %",            "SL %", 
                                  "Population Size", "Generation Size", "From Time", 
                                  "To Time"
                                  ] 
        
        # Creating headers for base parameters data collector   
        self._base_params_strategy = [
            {"code_name": "pairs", "widget": QComboBox, "data_type": str, "values": self.binance_symbols, "width": 250},
            {"code_name": "timeframe", "widget": QComboBox, "data_type": str, "values": r_var.TIME_FRAMES, "width": 150},
            {"code_name": "balance", "widget": QLineEdit, "data_type": float, "width": 150},
            {"code_name": "balance_percentage", "widget": QLineEdit, "data_type": float, "width": 150},
            {"code_name": "take_profit", "widget": QLineEdit, "data_type": float, "width": 150},
            {"code_name": "stop_loss", "widget": QLineEdit, "data_type": float, "width": 150},
            {"code_name": "population_size", "widget": QLineEdit, "data_type": int, "width": 150},
            {"code_name": "generation_size", "widget": QLineEdit, "data_type": int, "width": 150},
            {"code_name": "from_time", "widget": QDateEdit, "data_type": QDate, "width": 150},
            {"code_name": "to_time", "widget": QDateEdit, "data_type": QDate, "width": 150},
        ]
        
        # list for constructing backtesting parameters
        self._headers_data_collect = ["Exchange", "Pair", "Time Frame", "From Time", "To Time"]   
        
        # Creating headers for base parameters data collector   
        self._base_params_data_collect = [
            {"code_name": "exchange", "widget": QComboBox, "data_type": str, "values": r_var.EXCHANGES, "width": 200},
            {"code_name": "pairs", "widget": QComboBox, "data_type": str, "values": self.binance_symbols, "width": 150},
            {"code_name": "timeframe", "widget": QComboBox, "data_type": str, "values": r_var.TIME_FRAMES, "width": 150},
            {"code_name": "from_time", "widget": QDateEdit, "data_type": QDate, "width": 150},
            {"code_name": "to_time", "widget": QDateEdit, "data_type": QDate, "width": 150},
        ]
        # Important for where to add pair data in Scroll area
        # self._body_index = 0 is the header area          
        self._body_index = 1
        self._row_tracker = 0
        self._column_tracker = 0
        self.collecting = False
        self.strategizing = False
        
        # Generate parameters based on strategy selection
        self.initialize_strategy.currentTextChanged.connect(self._upload_widgets)
    
    def _add_log(self, message: str):
        """ 
        Send information to logger frame to be displayed
        later
        """
        logger.info(f"{message}")
        self.logs.append({"log": message, "displayed": False})    
     
    def _upload_widgets(self):
        """
        Upload Qtwidgets based no the strategy the user 
        selected. This is a mid point to decide what to 
        upload to the ui.
        """
        selection = self.initialize_strategy.currentText()
        if selection == "":
            self._delete_row()
            self._column_tracker_header = 0
            return
        
        elif selection in r_var.STRATEGIES:  
            self._add_strategy_row()
            
        elif selection == "Collect Data":
            self._add_collect_data_row()
    
    def _delete_row(self):
        """
        Permanently removes the specified rows and widgets from the ui
        """
        if self._row_tracker > 0:
            
            for row in range(self._row_tracker):
                
                if row == 2:
                    for col in range(self.row_four_columns):
                        del_widget = self._headers_frame.itemAtPosition((row+1), col).widget()
                        del_widget.deleteLater()
                        del del_widget
                    # del self.row_four_columns
                    
                elif row == 3:
                    for col in range(self.row_five_columns):
                        del_widget = self._headers_frame.itemAtPosition((row+1), col).widget()
                        del_widget.deleteLater()
                        extra_input_copy = self._extra_input.copy()
                        for elements in extra_input_copy.keys():
                            del self._extra_input[elements]
                    # del self.row_five_columns
                    
                elif row == 4:
                    for col in range(self.row_six_columns):
                        del_widget = self._headers_frame.itemAtPosition((row+1), col).widget()
                        del_widget.deleteLater()
                        del del_widget
                        
                elif row == 5:
                    for col in range(self.row_seven_columns):
                        print(col)
                        print(range(self.row_seven_columns))
                        print(self._headers_frame.itemAtPosition((row+2), col))
                        del_widget = self._headers_frame.itemAtPosition((row+2), col).widget()
                        del_widget.deleteLater()
                        del del_widget
                        
                elif self._column_tracker > 0:
                    for col in range(self._column_tracker_header):
                        del_widget = self._headers_frame.itemAtPosition((row+1), col).widget()
                        del_widget.deleteLater()
                    # Delete items completely from ui   
                    
                    if self.strategizing == True: 
                        for element in self._base_params_strategy:
                            del self.body_widgets[element['code_name']]
                        self.strategizing = False
                        
                    elif self.collecting == True: 
                        for element in self._base_params_data_collect:
                            del self.body_widgets[element['code_name']]
                        self.collecting = False 
                        
            self._row_tracker = 0
            self._column_tracker = 0
        else: 
            return       
    
    def _add_collect_data_row(self):
        """
        Add Data collector to _headers_frame
        """
        
        self._delete_row()
        self._column_tracker_header = 0
        self.collecting = True
        
        # Create a list of QLabels for the number of headers 
        self._headers_labels_data_collect = [QLabel() for _ in range(len(self._headers_data_collect))] 
        
        # Create labels for headers
        for idx, h in enumerate(self._headers_labels_data_collect):
            h.setObjectName(f"label_{self._headers_data_collect[idx]}")
            h.setText(f"{self._headers_data_collect[idx]}")
            h.setMaximumWidth(200)
            self._headers_frame.addWidget(h, 1, idx)
            self._column_tracker_header += 1
            self._column_tracker += 1
            # changing values in "code_name" into dictionary
            # Ex. "strategy_type" = dict() inside body widget
            
            for h in self._base_params_data_collect:
                self.body_widgets[h['code_name']] = dict()
                
        self._row_tracker += 1
        
        # Now add other widgets under the labels
        b_index = self._row_tracker + 1
        
        # Enumerates over dictionaries in base_params list
        for col, base_params in enumerate(self._base_params_data_collect):
            code_name = base_params['code_name']
            
            # Create combo boxes 
            if base_params['widget'] == QComboBox:
                self.body_widgets[code_name][b_index] = QComboBox()
                self.body_widgets[code_name][b_index].addItem("")
                self.body_widgets[code_name][b_index].setItemText(0, "")
                self.body_widgets[code_name][b_index].addItems(base_params['values'])
                self.body_widgets[code_name][b_index].setMaximumWidth(base_params['width'])  
                  
                if base_params['code_name'] == "timeframe":
                    self.body_widgets[code_name][b_index].setCurrentIndex(1) 
                    self.body_widgets[code_name][b_index].setEnabled(False)

            elif base_params['widget'] == QDateEdit:
                self.body_widgets[code_name][b_index] = QDateEdit()
                
                if code_name == "from_time":
                    self.body_widgets[code_name][b_index].setMaximumDateTime(QDateTime.currentDateTime())
                    self.body_widgets[code_name][b_index].setMinimumDateTime(QDateTime(QDate(2008, 1, 1), QTime(0, 0, 0)))
                    self.body_widgets[code_name][b_index].setDate(QDate(2020, 5, 1))
                    
                if code_name == "to_time":
                    self.body_widgets[code_name][b_index].setMaximumDateTime(QDateTime.currentDateTime())
                    self.body_widgets[code_name][b_index].setMinimumDateTime(QDateTime(QDate(2008, 1, 1), QTime(0, 0, 0)))
                    self.body_widgets[code_name][b_index].setDate(QDate(2023, 5, 1))
                    
                self.body_widgets[code_name][b_index].setCalendarPopup(True)
                self.body_widgets[code_name][b_index].setMaximumWidth(base_params['width'])   
                
            else:
                continue
            
            #  add specified widget to its location
            self._headers_frame.addWidget(self.body_widgets[code_name][b_index], b_index, col)
            
        # Create dictionary for additional parameters    
        self._additional_parameters[b_index] = dict()
        self._row_tracker += 1
        # Turns the code names of the strategy types None
        # Ex. "ema_fast" = None
        
        # Have to update to go to next line
        self._body_index += 1
        
        # Add button to collect data
        self.row_four_columns = 0
        self.collect_data_button = QPushButton("Collect Data")
        self.collect_data_button.setObjectName("Blue_button")
        self.collect_data_button.setMaximumWidth(200)
        self.collect_data_button.setMinimumHeight(50)
        self._headers_frame.addWidget(self.collect_data_button, (self._row_tracker + 1), self.row_four_columns)
        self.collect_data_button.clicked.connect(self.collect_all)
 
        self.row_four_columns += 1
        self.stop_collect_data_button = QPushButton("Stop Collecting")
        self.stop_collect_data_button.setObjectName("remove_button_watchlist")
        self.stop_collect_data_button.setMaximumWidth(200)
        self.stop_collect_data_button.setMinimumHeight(50)
        self.stop_collect_data_button.setEnabled(False)
        self._headers_frame.addWidget(self.stop_collect_data_button, (self._row_tracker + 1), self.row_four_columns)
        self.stop_collect_data_button.clicked.connect(self.stop_collect_all)
        
        self.row_four_columns += 1
        self._row_tracker += 1
        
    def collect_all(self):
        """
        It first validates if you input all of the
        necessary parameters into their respective fields.
        Then it collects data and inputs it into an hdf5 file
        """
        
        # Stop user from collecting data with no exchange
        if self.body_widgets['exchange'][2].currentText() == "":
            QMessageBox.warning(self.backtest_widget,
                                "No Exchange Selected",
                                "Please select an exchange to collect data from",
                                QMessageBox.StandardButton.Ok)
            return
        
        client = self._exchanges[self.body_widgets['exchange'][2].currentText()]
        # Stop user from collecting data with no pair
        if self.body_widgets['pairs'][2].currentText() == "":
            QMessageBox.warning(self.backtest_widget,
                                "No Pair Selected",
                                "Please select an pair symbol to collect data from",
                                QMessageBox.StandardButton.Ok)
            return
        
        symbol = self.body_widgets['pairs'][2].currentText().split("_")[0]
        symbol_exchange = self.body_widgets['pairs'][2].currentText().split("_")[1]
        # Stop user from collecting data with a pair not on the same exchange
        if symbol_exchange != self.body_widgets["exchange"][2].currentText():
            QMessageBox.warning(self.backtest_widget,
                                "Wrong Exchange",
                                "The Pair you selected does not belong to the exchange you've chosen",
                                QMessageBox.StandardButton.Ok)
            return
        
        # Stop user from collecting data with invalid to and from dates
        if self.body_widgets["from_time"][2].dateTime().toSecsSinceEpoch() \
        >= self.body_widgets["to_time"][2].dateTime().toSecsSinceEpoch():
            QMessageBox.warning(self.backtest_widget,
                            "Invalid From and To Time",
                            "The From Time cannot be after the To Time\n Please change dates",
                            QMessageBox.StandardButton.Ok)
            return
        
        self.collect_data_button.setEnabled(False)
        self.stop_collect_data_button.setEnabled(True)
        self.initialize_strategy.setEnabled(False)
        self.body_widgets['exchange'][2].setEnabled(False)
        self.body_widgets['pairs'][2].setEnabled(False)
        self.body_widgets["from_time"][2].setEnabled(False)
        self.body_widgets["to_time"][2].setEnabled(False)
        self.stop_collect_thread = False
        
        # Initiate thread for data collection
        self.collect_thread = threading.Thread(target = data_collector.collect_all,
                             args=(self,
                                   client,
                                   self.body_widgets["exchange"][2].currentText(),
                                   symbol,
                                   self.body_widgets["timeframe"][2].currentText(),
                                   self.body_widgets["from_time"][2].dateTime(),
                                   self.body_widgets["to_time"][2].dateTime(),
                                   (lambda: self.stop_collect_thread)))
        self.collect_thread.setName("Data_Collecting_Thread")
        self.collect_thread.start() # Start thread
        
    def stop_collect_all(self):
        """
        Stops collection into an HDF5 database immediately
        """
        
        ret = QMessageBox.warning(self.backtest_widget,
                                  "Stop Data Collector",
                                  """You are about to stop the data collector before it finishes collecting data.
                                  \n Are you sure you want to stop?
                                  \n This could lead to some corrupted data or unfinished data into the HDF5 database""",
                                  QMessageBox.StandardButton.Yes | QMessageBox.StandardButton.Cancel)
        
        if ret == QMessageBox.StandardButton.Yes:
            self.collect_data_button.setEnabled(True)
            self.stop_collect_data_button.setEnabled(False)
            self.initialize_strategy.setEnabled(True)
            self.body_widgets['exchange'][2].setEnabled(True)
            self.body_widgets['pairs'][2].setEnabled(True)
            self.body_widgets["from_time"][2].setEnabled(True)
            self.body_widgets["to_time"][2].setEnabled(True)
            self.stop_collect_thread = True
            
        if ret == QMessageBox.StandardButton.Cancel:
            pass
        
        else:
            pass
                    
    def _add_strategy_row(self):
        """
        Add strategy to _headers_frame
        """
        
        self._delete_row()
        self._column_tracker_header = 0
        self.strategizing = True
        
        # Create a list of QLabels for the number of headers 
        self._headers_labels_strategy = [QLabel() for _ in range(len(self._headers_strategy))]   
        # Create labels for headers
        
        for idx, h in enumerate(self._headers_labels_strategy):
            h.setObjectName(f"label_{self._headers_strategy[idx]}")
            h.setText(f"{self._headers_strategy[idx]}")
            h.setMaximumWidth(150)
            self._headers_frame.addWidget(h, 1, idx)
            self._column_tracker_header += 1
            self._column_tracker += 1
            
            # changing values in "code_name" into dictionary
            # Ex. "strategy_type" = dict() inside body widget
            for h in self._base_params_strategy:
                self.body_widgets[h['code_name']] = dict()
                
        self._row_tracker += 1
        
        # Now add other widgets under the labels
        b_index = self._row_tracker + 1
        
        # Enumerates over dictionaries in base_params list
        for col, base_params in enumerate(self._base_params_strategy):
            
            code_name = base_params['code_name']
            
            # Create combo boxes 
            if base_params['widget'] == QComboBox:
                self.body_widgets[code_name][b_index] = QComboBox()
                self.body_widgets[code_name][b_index].addItem("")
                self.body_widgets[code_name][b_index].setItemText(0, "")
                self.body_widgets[code_name][b_index].addItems(base_params['values'])
                self.body_widgets[code_name][b_index].setMaximumWidth(base_params['width'])   
                   
            # Create combo line edits     
            elif base_params['widget'] == QLineEdit:
                self.body_widgets[code_name][b_index] = QLineEdit()
                # limit wht can be entered into the line edits
                self.body_widgets[code_name][b_index].setMaximumWidth(base_params['width'])   
                 
                if base_params['data_type'] == int:
                    self.body_widgets[code_name][b_index].setValidator(self._valid_integer)
                    
                if base_params['data_type'] == float:
                    self.body_widgets[code_name][b_index].setValidator(self._valid_float)
                    
            elif base_params['widget'] == QDateEdit:
                self.body_widgets[code_name][b_index] = QDateEdit()
                
                if code_name == "from_time":
                    self.body_widgets[code_name][b_index].setMaximumDateTime(QDateTime.currentDateTime())
                    self.body_widgets[code_name][b_index].setMinimumDateTime(QDateTime(QDate(2008, 1, 1), QTime(0, 0, 0)))
                    self.body_widgets[code_name][b_index].setDate(QDate(2020, 5, 1))
                    
                if code_name == "to_time":
                    self.body_widgets[code_name][b_index].setMaximumDateTime(QDateTime.currentDateTime())
                    self.body_widgets[code_name][b_index].setMinimumDateTime(QDateTime(QDate(2008, 1, 1), QTime(0, 0, 0)))
                    self.body_widgets[code_name][b_index].setDate(QDate(2023, 5, 1))
                    
                self.body_widgets[code_name][b_index].setCalendarPopup(True)
                self.body_widgets[code_name][b_index].setMaximumWidth(base_params['width'])   
                
            else:
                continue
            
            # Add specified widget to its location
            self._headers_frame.addWidget(self.body_widgets[code_name][b_index], b_index, col)
            
        # Create dictionary for additional parameters    
        self._additional_parameters[b_index] = dict()
        self._row_tracker += 1
        
        # Turns the code names of the strategy types None
        # Ex. "ema_fast" = None
        for strat, params in r_var.EXTRA_PARAMETERS.items():
            
            for param in params:
                self._additional_parameters[b_index][param['code_name']] = None
                
        # Have to update to go to next line
        self._body_index += 1
        
        # Add button to collect data
        self.row_four_columns = 0
        self.row_five_columns = 0
        
        # Add extra parameters to the Popup Window
        for param in r_var.EXTRA_PARAMETERS[self.initialize_strategy.currentText()]:
            
            # Inside strategy list that was selected
            code_name = param['code_name']
            
            # Create labels for line edits
            extra_param_label = QLabel(param['name']) 
            extra_param_label.setObjectName("Parameter_" + param['name'])
            extra_param_label.setMaximumWidth(150)
            
            # Add label to fourth row
            self._headers_frame.addWidget(extra_param_label, (self._row_tracker + 1), self.row_four_columns)
            self.row_four_columns += 1
            
            # The labels widget to the fifth column
            if param['widget'] == QLineEdit:
                self._extra_input[code_name] = QLineEdit()
                self._extra_input[code_name].setAlignment(Qt.AlignmentFlag.AlignCenter)
                self._extra_input[code_name].setMaximumWidth(150)
                self._headers_frame.addWidget(self._extra_input[code_name], (self._row_tracker + 2), self.row_five_columns)
                self.row_five_columns += 1
                
                # Limit what is entered into these line edits
                if param['data_type'] == int:
                    self._extra_input[code_name].setValidator(self._valid_integer)
                    
                if param['data_type'] == float:
                    self._extra_input[code_name].setValidator(self._valid_float)
                    
                # Makes sure that the parameters stay when you exit the window
                if self._additional_parameters[b_index][code_name] is not None:
                    self._extra_input[code_name].setText(str(self._additional_parameters[b_index][code_name]))
                    
            else:
                ...
                
        self._row_tracker += 2  
        self._body_index += 2
        self.row_six_columns = 0
        
        # Create backtesting button
        self.backtest_data_button = QPushButton("Backtest Data")
        self.backtest_data_button.setObjectName("Blue_button")
        self.backtest_data_button.setMaximumWidth(250)
        self.backtest_data_button.setMinimumHeight(50)
        self._headers_frame.addWidget(self.backtest_data_button, (self._row_tracker + 1), self.row_six_columns)
        self.backtest_data_button.clicked.connect(self.backtest_strategy)
        
        # Create Optimizing button
        self.row_six_columns += 1
        self.optimize_button = QPushButton("Optimize")
        self.optimize_button.setObjectName("Yellow_button")
        self.optimize_button.setMaximumWidth(150)
        self.optimize_button.setMinimumHeight(50)
        self.optimize_button.setEnabled(False)
        self._headers_frame.addWidget(self.optimize_button, (self._row_tracker + 1), self.row_six_columns)
        # self.optimize_button.clicked.connect(self.stop_collect_all)
        ...
        
        self.row_six_columns += 1
        self.chart_button = QPushButton("Chart Data")
        self.chart_button.setObjectName("Add_strategy")
        self.chart_button.setMaximumWidth(150)
        self.chart_button.setMinimumHeight(50)
        self.chart_button.setEnabled(True)
        self._headers_frame.addWidget(self.chart_button, (self._row_tracker + 1), self.row_six_columns)
        self.chart_button.clicked.connect(self.charting_data)
        self.row_six_columns += 1
        
        self.post_strategy_button = QPushButton("Post Strategy")
        self.post_strategy_button.setObjectName("Blue_button")
        self.post_strategy_button.setMaximumWidth(150)
        self.post_strategy_button.setMinimumHeight(50)
        self.post_strategy_button.setEnabled(True)
        self._headers_frame.addWidget(self.post_strategy_button, (self._row_tracker + 1), self.row_six_columns)
        # self.chart_button.clicked.connect(self.stop_collect_all)
        ...
        
        self.row_six_columns += 1
        self._row_tracker += 1

    def backtest_strategy(self):
        """
        It first validates if you input all of the
        necessary parameters into their respective fields.
        Then it collects data and inputs it into an hdf5 file\n
        parameter example:
        [{'Balance_percent': '100',
        'Client': <initiate.connectors.binance_us.BinanceUSClient object at 0x000001A9C25DA730>,
        'Exchange': 'BinanceUS',
        'Extra_Parameters': {'min_volume': <PyQt6.QtWidgets.QLineEdit object at 0x000001A9C1395C10>},
        'From_Time': 1588312800000,
        'Pair': 'BCHUSDT',
        'Stop_Loss': '2',
        'Strategy': 'Breakout',
        'Take_Profit': '1',
        'TimeFrame': '5m',
        'To_Time': 1682920800000}]
        """
        
        validate = self.validate_backtest_input()
        
        if validate == False:
            return
        
        # prepare Parameters 
        symbol = self.body_widgets['pairs'][2].currentText().split("_")[0]
        symbol_exchange = self.body_widgets['pairs'][2].currentText().split("_")[1]
        
        parameters = [{
            "Strategy"         : self.initialize_strategy.currentText(),
            "Pair"             : symbol,
            "Exchange"         : symbol_exchange,
            "Client"           : self._exchanges[symbol_exchange],
            "TimeFrame"        : self.body_widgets['timeframe'][2].currentText(),
            "Balance"          : self.body_widgets['balance'][2].text(),
            "Balance_percent"  : self.body_widgets['balance_percentage'][2].text(),
            "Take_Profit"      : self.body_widgets['take_profit'][2].text(),
            "Stop_Loss"        : self.body_widgets['stop_loss'][2].text(),
            "From_Time"        : (self.body_widgets["from_time"][2].dateTime().toSecsSinceEpoch() * 1000),
            "To_Time"          : (self.body_widgets["to_time"][2].dateTime().toSecsSinceEpoch() * 1000),
            "Extra_Parameters" : self._extra_input
            }] 
        
        for input in parameters[0]["Extra_Parameters"].values():
            if input.text() == "":
                QMessageBox.warning(self.backtest_widget,
                                        f"No Parameter Value",
                                        f"Please enter in a value for the parameters to backtest",
                                        QMessageBox.StandardButton.Ok)
                return
            
        self.backtest_data_button.setEnabled(False)
        self.optimize_button.setEnabled(False)
        self.chart_button.setEnabled(True)
        self.initialize_strategy.setEnabled(False)
        self.body_widgets['pairs'][2].setEnabled(False)
        self.body_widgets['timeframe'][2].setEnabled(False)
        self.body_widgets["balance_percentage"][2].setEnabled(False)
        self.body_widgets["take_profit"][2].setEnabled(False)
        self.body_widgets["stop_loss"][2].setEnabled(False)
        self.stop_backtesting_thread = False
        
        if self._row_tracker == 5:
            # Create PnL label
            self._row_tracker += 1  
            self._body_index += 1
            self.row_seven_columns = 0
            
        # Create PnL label
        try:
            if self.pnl_label:
                try:
                    self.pnl_label.setText("PnL: ")
                    
                except RuntimeError:
                    self.pnl_label = QLabel(f"PnL: ")
                    self.pnl_label.setMaximumWidth(150)
                    self._headers_frame.addWidget(self.pnl_label, (self._row_tracker + 1), self.row_seven_columns)
            self.row_seven_columns += 1
            
        except AttributeError:            
            self.pnl_label = QLabel(f"PnL: ")
            self.pnl_label.setMaximumWidth(150)
            self._headers_frame.addWidget(self.pnl_label, (self._row_tracker + 1), self.row_seven_columns)
            self.row_seven_columns += 1
        
        # Creates Max Drawdown Label
        try:
            if self.max_dd_label:
                try:
                    self.max_dd_label.setText("Max Drawdown: ")
                    
                except RuntimeError:
                    # Create Maxdrawdown label
                    self.max_dd_label = QLabel(f"Max Drawdown: ")
                    self.max_dd_label.setMaximumWidth(150)
                    self._headers_frame.addWidget(self.max_dd_label, (self._row_tracker + 1), self.row_seven_columns)
                    self.row_seven_columns += 1   
                    
        except AttributeError:    
            # Create Maxdrawdown label
            self.max_dd_label = QLabel(f"Max Drawdown: ")
            self.max_dd_label.setMaximumWidth(150)
            self._headers_frame.addWidget(self.max_dd_label, (self._row_tracker + 1), self.row_seven_columns)
            self.row_seven_columns += 1 
        
        # Creates Max Drawdown Results      
        try:
            if self.max_dd_results:
                try:
                    self.max_dd_results.setText(" ")  
                    
                except RuntimeError:
                    # Create Maxdrawdown results
                    self.max_dd_results = QLabel(" ")
                    self.max_dd_results.setMaximumWidth(150)
                    self._headers_frame.addWidget(self.max_dd_results, (self._row_tracker + 1), self.row_seven_columns)
                    self.row_seven_columns += 1  
                                 
        except AttributeError:       
            # Create Maxdrawdown results
            self.max_dd_results = QLabel(" ")
            self.max_dd_results.setMaximumWidth(150)
            self._headers_frame.addWidget(self.max_dd_results, (self._row_tracker + 1), self.row_seven_columns)
            self.row_seven_columns += 1 
                
        # Initiate thread for data collection
        self.collect_thread = threading.Thread(target = self.run_backtester,
                             args=(parameters))
        self.collect_thread.setName("Data_Backtesting_Thread")
        self.collect_thread.start() # Start thread
    
    def run_backtester(self, parameters):
        """
        Thread: Data_Backtesting_Thread
        
        A seperate thread goes to collect fetch data 
        from collected data on h5 file and backtest it
        based on the parameters from user input. 
        
        It generates the pnl and max drawdown and sends data
        to main thread from trade period to generate chart 
        """
        try:
            self.pnl, self.max_drawdown, self.df_results = backtest_helper.run(self, parameters=parameters)
            # this button will need to be controlled so 
            # it's not pushed until backtesting is finished
            self.optimize_button.setEnabled(True)
            self.backtest_data_button.setEnabled(True)
            self.optimize_button.setEnabled(True)
            self.chart_button.setEnabled(True)
            self.initialize_strategy.setEnabled(True)
            self.body_widgets['pairs'][2].setEnabled(True)
            self.body_widgets['timeframe'][2].setEnabled(True)
            self.body_widgets["balance_percentage"][2].setEnabled(True)
            self.body_widgets["take_profit"][2].setEnabled(True)
            self.body_widgets["stop_loss"][2].setEnabled(True)
            
            # Create PnL label
            self.pnl_label.setText(f"PnL: {self.pnl}")
            
            # Create Maxdrawdown label
            self.max_dd_results.setText(f"{self.max_drawdown}")
            
            # Prepare data for chart
            candle_data = self.df_results[["open", "high", "low", "close", "volume"]]
            dataframe_copy = self.df_results.copy()
            for idx, i in enumerate(dataframe_copy.index):
                
                if dataframe_copy.loc[i, "Enter"] == "Enter":
                    dataframe_copy.loc[i, "Enter"] = dataframe_copy.loc[i, "open"]
                    
                if dataframe_copy.loc[i, "Exit"] == "Exit":
                    dataframe_copy.loc[i, "Exit"] = dataframe_copy.loc[i, "close"] 
                       
            enter = dataframe_copy[["Enter"]]
            exit = dataframe_copy[["Exit"]]
            
            self._chart_backtest(data=candle_data, title=parameters['Pair'], enter=enter, exit=exit)
            
        except Exception as e:
            logger.error(e)

        
    def validate_backtest_input(self):
        """
        Makes sure all necessary input is there 
        """
        
        # Stop user from collecting data with no missing input
        for missing_input in ["pairs", 'timeframe', 'balance', 'balance_percentage', 'take_profit', 'stop_loss']:
            
            if self.body_widgets[missing_input][2].__class__ == QComboBox:
                
                if self.body_widgets[missing_input][2].currentText() == "":
                    QMessageBox.warning(self.backtest_widget,
                                        f"No {missing_input.capitalize()} Selected",
                                        f"Please select a {missing_input.capitalize()} to backtest",
                                        QMessageBox.StandardButton.Ok)
                    return False
                
            elif self.body_widgets[missing_input][2].__class__ == QLineEdit:
                
                if self.body_widgets[missing_input][2].text() == "":
                    QMessageBox.warning(self.backtest_widget,
                                        f"No {missing_input.capitalize()} Selected",
                                        f"Please select a {missing_input.capitalize()} to backtest",
                                        QMessageBox.StandardButton.Ok)
                    return False   
                   
        # Stop user from collecting data with percentages above 100%    
        for above_percent in ['balance_percentage', 'take_profit', 'stop_loss']:
             
            if self.body_widgets[above_percent][2].text() != "":
                
                if float(self.body_widgets[above_percent][2].text()) > 100.0:
                    QMessageBox.warning(self.backtest_widget,
                                        f"No {above_percent.capitalize()} above 100%",
                                        f"{above_percent.capitalize()} cannot be above 100%",
                                        QMessageBox.StandardButton.Ok)
                    return False
                
        # Stop user from collecting data with invalid to and from dates
        if self.body_widgets["from_time"][2].dateTime().toSecsSinceEpoch() \
        >= self.body_widgets["to_time"][2].dateTime().toSecsSinceEpoch():
            QMessageBox.warning(self.backtest_widget,
                            "Invalid From and To Time",
                            "The From Time cannot be after the To Time\n Please change dates",
                            QMessageBox.StandardButton.Ok)
            return False
        
        return True
    
    def validate_optimize_input(self):
        """
        Makes sure all necessary input is there 
        """
        
        # Stop user from collecting data with no missing input
        for missing_input in ["pairs", 'timeframe', 'balance', 
                              'balance_percentage', 'take_profit', 'stop_loss', 
                              'population_size', 'generation_size']:
            
            if self.body_widgets[missing_input][2].__class__ == QComboBox:
                
                if self.body_widgets[missing_input][2].currentText() == "":
                    QMessageBox.warning(self.backtest_widget,
                                        f"No {missing_input.capitalize()} Selected",
                                        f"Please select a {missing_input.capitalize()} to backtest",
                                        QMessageBox.StandardButton.Ok)
                    return False
                
            elif self.body_widgets[missing_input][2].__class__ == QLineEdit:
                
                if self.body_widgets[missing_input][2].text() == "":
                    QMessageBox.warning(self.backtest_widget,
                                        f"No {missing_input.capitalize()} Selected",
                                        f"Please select a {missing_input.capitalize()} to backtest",
                                        QMessageBox.StandardButton.Ok)
                    return False   
                   
        # Stop user from collecting data with percentages above 100%    
        for above_percent in ['balance_percentage', 'take_profit', 'stop_loss']:
             
            if self.body_widgets[above_percent][2].text() != "":
                
                if float(self.body_widgets[above_percent][2].text()) > 100.0:
                    QMessageBox.warning(self.backtest_widget,
                                        f"No {above_percent.capitalize()} above 100%",
                                        f"{above_percent.capitalize()} cannot be above 100%",
                                        QMessageBox.StandardButton.Ok)
                    return False
                
        # Stop user from collecting data with invalid to and from dates
        if self.body_widgets["from_time"][2].dateTime().toSecsSinceEpoch() \
        >= self.body_widgets["to_time"][2].dateTime().toSecsSinceEpoch():
            QMessageBox.warning(self.backtest_widget,
                            "Invalid From and To Time",
                            "The From Time cannot be after the To Time\n Please change dates",
                            QMessageBox.StandardButton.Ok)
            return False
        
        return True
    
    def charting_data(self):
        """
        From the "Chart Data" button, data that has been collected
        will be visualized on the matplotlib canvas. This only works
        as long as there is data available for what the user is 
        interested in. If it's not available, the user will need 
        to collect the data using the "Collect Data" button
        """
        validate = self.validate_backtest_input()
        
        if validate == False:
            return
        
        # prepare Parameters 
        symbol = self.body_widgets['pairs'][2].currentText().split("_")[0]
        symbol_exchange = self.body_widgets['pairs'][2].currentText().split("_")[1]
        
        parameters = {
            "Strategy"         : self.initialize_strategy.currentText(),
            "Pair"             : symbol,
            "Exchange"         : symbol_exchange,
            "Client"           : self._exchanges[symbol_exchange],
            "TimeFrame"        : self.body_widgets['timeframe'][2].currentText(),
            "Balance"          : self.body_widgets['balance'][2].text(),
            "Balance_percent"  : self.body_widgets['balance_percentage'][2].text(),
            "Take_Profit"      : self.body_widgets['take_profit'][2].text(),
            "Stop_Loss"        : self.body_widgets['stop_loss'][2].text(),
            "From_Time"        : (self.body_widgets["from_time"][2].dateTime().toSecsSinceEpoch() * 1000),
            "To_Time"          : (self.body_widgets["to_time"][2].dateTime().toSecsSinceEpoch() * 1000),
            "Extra_Parameters" : self._extra_input
            }
        
        h5_db = Hdf5Client(parameters["Exchange"], self)        
        chart_data = h5_db.get_data(symbol=parameters["Pair"], 
                                    from_time=parameters["From_Time"], 
                                    to_time=parameters["To_Time"])
        
        if chart_data is not None:
            # converts the data timeframe into what you want 
            chart_data = r_var.resample_timeframe(data=chart_data, tf=parameters["TimeFrame"])
            
        self._change_chart(chart_data, parameters["Pair"])
        
    def optimizing_parameters(self):
        """
        Backtest the parameters of a strategy iof the user's choosing
        and then this attempts to optimize the parameters for the best
        Pnl and markdown
        """
        ...
        validate = self.validate_optimize_input()
        
        if validate == False:
            return
        
        # prepare Parameters 
        symbol = self.body_widgets['pairs'][2].currentText().split("_")[0]
        symbol_exchange = self.body_widgets['pairs'][2].currentText().split("_")[1]
        
        parameters = [{
            "Strategy"         : self.initialize_strategy.currentText(),
            "Pair"             : symbol,
            "Exchange"         : symbol_exchange,
            "Client"           : self._exchanges[symbol_exchange],
            "TimeFrame"        : self.body_widgets['timeframe'][2].currentText(),
            "Balance"          : self.body_widgets['balance'][2].text(),
            "Balance_percent"  : self.body_widgets['balance_percentage'][2].text(),
            "Take_Profit"      : self.body_widgets['take_profit'][2].text(),
            "Stop_Loss"        : self.body_widgets['stop_loss'][2].text(),
            "From_Time"        : (self.body_widgets["from_time"][2].dateTime().toSecsSinceEpoch() * 1000),
            "To_Time"          : (self.body_widgets["to_time"][2].dateTime().toSecsSinceEpoch() * 1000),
            "Population_Size"  : self.body_widgets['population_size'][2].text(),
            "Generation_Size"  : self.body_widgets['generation_size'][2].text(),
            "Extra_Parameters" : self._extra_input
            }]
        
        for input in parameters[0]["Extra_Parameters"].values():
            
            if input.text() == "":
                QMessageBox.warning(self.backtest_widget,
                                        f"No Parameter Value",
                                        f"Please enter in a value for the parameters to backtest",
                                        QMessageBox.StandardButton.Ok)
                return
        
        # Disable all the buttons to prevent error    
        self.backtest_data_button.setEnabled(False)
        self.optimize_button.setEnabled(False)
        self.chart_button.setEnabled(True)
        self.initialize_strategy.setEnabled(False)
        self.body_widgets['pairs'][2].setEnabled(False)
        self.body_widgets['timeframe'][2].setEnabled(False)
        self.body_widgets["balance_percentage"][2].setEnabled(False)
        self.body_widgets["take_profit"][2].setEnabled(False)
        self.body_widgets["stop_loss"][2].setEnabled(False)
        self.body_widgets["population_size"][2].setEnabled(False)
        self.body_widgets["generation_size"][2].setEnabled(False)
        self.stop_optimizing_thread = False
        
        if self._row_tracker == 5:
            # Create PnL label
            self._row_tracker += 1  
            self._body_index += 1
            self.row_seven_columns = 0
            
        # Create PnL label
        try:
            if self.pnl_label:
                try:
                    self.pnl_label.setText("PnL: ")
                    
                except RuntimeError:
                    self.pnl_label = QLabel(f"PnL: ")
                    self.pnl_label.setMaximumWidth(150)
                    self._headers_frame.addWidget(self.pnl_label, (self._row_tracker + 1), self.row_seven_columns)
                    
            self.row_seven_columns += 1
            
        except AttributeError:            
            self.pnl_label = QLabel(f"PnL: ")
            self.pnl_label.setMaximumWidth(150)
            self._headers_frame.addWidget(self.pnl_label, (self._row_tracker + 1), self.row_seven_columns)
            self.row_seven_columns += 1
        
        try:
            if self.max_dd_label:
                try:
                    self.max_dd_label.setText("Max Drawdown: ")
                    
                except RuntimeError:
                    # Create Maxdrawdown label
                    self.max_dd_label = QLabel(f"Max Drawdown: ")
                    self.max_dd_label.setMaximumWidth(150)
                    self._headers_frame.addWidget(self.max_dd_label, (self._row_tracker + 1), self.row_seven_columns)
                    self.row_seven_columns += 1   
                    
        except AttributeError:    
            # Create Maxdrawdown label
            self.max_dd_label = QLabel(f"Max Drawdown: ")
            self.max_dd_label.setMaximumWidth(150)
            self._headers_frame.addWidget(self.max_dd_label, (self._row_tracker + 1), self.row_seven_columns)
            self.row_seven_columns += 1 
              
        try:
            if self.max_dd_results:
                try:
                    self.max_dd_results.setText(" ")  
                    
                except RuntimeError:
                    # Create Maxdrawdown results
                    self.max_dd_results = QLabel(" ")
                    self.max_dd_results.setMaximumWidth(150)
                    self._headers_frame.addWidget(self.max_dd_results, (self._row_tracker + 1), self.row_seven_columns)
                    self.row_seven_columns += 1  
                                 
        except AttributeError:       
            # Create Maxdrawdown results
            self.max_dd_results = QLabel(" ")
            self.max_dd_results.setMaximumWidth(150)
            self._headers_frame.addWidget(self.max_dd_results, (self._row_tracker + 1), self.row_seven_columns)
            self.row_seven_columns += 1  
               
        # Initiate thread for data collection
        self.optimizer_thread = threading.Thread(target = self.run_backtester,
                             args=(parameters))
        self.optimizer_thread.setName("Data_Optimizer_Thread")
        self.optimizer_thread.start() # Start thread
        
    def run_optimizer(self, parameters):
        """
        Thread: Data_Optimizer_Thread
        
        Seperately runs the optimizer after all of 
        user's input is validated. works on optimzer file
        """
        optimizer_helper.run(self, parameters=parameters)
        
        # this button will need to be controlled so 
        # it's not pushed until backtesting is finished
        self.optimize_button.setEnabled(True)
        self.backtest_data_button.setEnabled(True)
        self.optimize_button.setEnabled(True)
        self.chart_button.setEnabled(True)
        self.initialize_strategy.setEnabled(True)
        self.body_widgets['pairs'][2].setEnabled(True)
        self.body_widgets['timeframe'][2].setEnabled(True)
        self.body_widgets["balance_percentage"][2].setEnabled(True)
        self.body_widgets["take_profit"][2].setEnabled(True)
        self.body_widgets["stop_loss"][2].setEnabled(True)
        self.body_widgets["population_size"][2].setEnabled(True)
        self.body_widgets["generation_size"][2].setEnabled(True)
        
    def _chart_backtest(self, data, title, enter: pd.DataFrame, exit: pd.DataFrame):
        """
        Charts results after backtesting strategy
        """
        self.matplotlib_chart.ax.clear()
        
        mc = mpf.make_marketcolors(up='tab:green',
                                   down='tab:red', 
                                   edge='black', 
                                   wick={'up':'green','down':'red'}, 
                                   inherit=True)
        s  = mpf.make_mpf_style(base_mpf_style='mike', marketcolors=mc)
        
        mpf.plot(data[:],
                 type='candle',
                 ax=self.matplotlib_chart.ax, 
                 style=s, 
                 ylabel='Price', 
                 returnfig=False, 
                 axtitle=title)
        xpoints = np.arange(len(data))
        
        # Chart entry points
        self.matplotlib_chart.ax.plot(xpoints,
                                      enter, 
                                      color='green', 
                                      markersize=10, 
                                      marker='^')
        
        # Chart exit points
        self.matplotlib_chart.ax.plot(xpoints,
                                      exit, 
                                      color='red', 
                                      markersize=10, 
                                      marker='v')
        
        # Plot only 15 x axis ticks at a time
        self.matplotlib_chart.ax.xaxis.set_major_locator(plt.MaxNLocator(15))
        
        # Use all of the canvas that is available
        plt.tight_layout()
        self.matplotlib_chart.draw()
        return
    
    def _change_chart(self, data, title):
        """
        This function is called when the user clicks the 
        "Chart Data" button. After user input is validated and 
        data is collected, data will appear on the matplotlib 
        canvas
        """
        self.matplotlib_chart.ax.clear()
        
        mc = mpf.make_marketcolors(up='tab:green',
                                   down='tab:red', 
                                   edge='black', 
                                   wick={'up':'green','down':'red'}, 
                                   inherit=True)
        s  = mpf.make_mpf_style(base_mpf_style='mike', marketcolors=mc)
        
        mpf.plot(data[:], 
                 volume=True, 
                 type='candle', 
                 ax=self.matplotlib_chart.ax, 
                 style=s, 
                 ylabel='Price', 
                 returnfig=False, 
                 axtitle=title)
        
        # Plot only 15 x axis ticks at a time
        self.matplotlib_chart.ax.xaxis.set_major_locator(plt.MaxNLocator(15))
        
        # Use all of the canvas that is available
        plt.tight_layout()
        self.matplotlib_chart.draw()
        return
            
    def _upload_strategy_parameters(self):
        """
        
        Not in use yet...
        
        """
        return
        
#     # def _load_workspace(self):
#     #     data = self.db.get("strategies")
#     #     for row in data:
#     #         self._add_strategy_row()
            
#     #         b_index = self._body_index - 1
           
#     #         for base_param in self._base_params:
#     #             code_name = base_param['code_name']
                
#     #             if base_param['widget'] == QComboBox and row[code_name] is not None:
#     #                 self.body_widgets[code_name][b_index].setCurrentText(row[code_name])
                    
#     #             elif base_param['widget'] == QLineEdit and row[code_name] is not None:
#     #                 self.body_widgets[code_name][b_index].setText(str(row[code_name]))
                    
#     #         extra_params = json.loads(row['extra_params'])
                    
#     #         for param, value in extra_params.items():
#     #             if value is not None:
#     #                 self._additional_parameters[b_index][param] = value     