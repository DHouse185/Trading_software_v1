##########  Python IMPORTs  ############################################################
import typing
from pathlib import Path
########################################################################################

##########  Python THIRD PARTY IMPORTs  ################################################
from PyQt6.QtWidgets import (QVBoxLayout,
                            QScrollArea,
                            QWidget,
                            QGridLayout,
                            QLabel,
                            QLineEdit,
                            QCompleter,
                            QPushButton)
from PyQt6.QtCore import Qt, QRect
########################################################################################

##########  Created files IMPORTS  #####################################################
from initiate.connectors.models import *
########################################################################################

#from database import Workspace

class Watchlist:
    """
    This is essentially a widget that will control everything
    That occurs within the Watchlist
    """
    def __init__(self, page, binance_pairs, notification): #: typing.Dict[str, PairData]):
        super().__init__()
        
        # self.db = Workspace()
        
        self.binance_symbols = list(binance_pairs.keys())
        self.notification = notification
        self.main_page = page
        
        # Create a widget that will contain all things related
        # to the Watchlist
        # Mainwindow -> central widget -> StackWidget -> Main Page
        # -> watchlist_widget
        self.watchlist_widget = QWidget(self.main_page)
        self.watchlist_widget.setObjectName(u"watchlist_widget")
        self.watchlist_widget.setGeometry(QRect(30, 130, 607, 706))
        
        # Command Frame will be the main layout of watchlist widget
        # Mainwindow -> central widget -> StackWidget -> Main Page
        # -> watchlist_widget -> _commands_frame
        self._commands_frame = QVBoxLayout(self.watchlist_widget) 
        self._commands_frame.setObjectName("Watchlist_Commands_frame")
        self._commands_frame.setSpacing(6)
        
        # This will be were all symbol ask and bid prices for a 
        # symbol will occur
        # Mainwindow -> central widget -> StackWidget -> Main Page
        # -> watchlist_widget -> _commands_frame -> watchlist_scrollArea
        # -> scrollAreaWidgetContents
        self.watchlist_scrollArea = QScrollArea()
        self.watchlist_scrollArea.setObjectName("Watchlist_scrollArea")
        self.watchlist_scrollArea.setWidgetResizable(True)
        self.watchlist_scrollArea.setMaximumSize(587, 620)
        self.scrollAreaWidgetContents = QWidget()
        self.scrollAreaWidgetContents.setObjectName("watchlist_scrollAreaWidgetContents")
        
        # Creating a grid layout for headers, columns, and rows
        # Mainwindow -> central widget -> StackWidget -> Main Page
        # -> watchlist_widget -> _commands_frame -> watchlist_scrollArea
        # -> scrollAreaWidgetContents -> _headers_frame
        self._headers_frame = QGridLayout(self.scrollAreaWidgetContents)
        self._headers_frame.setObjectName("Watchlist_Headers_frame")
        self._headers_frame.setSpacing(0)
        self._headers_frame.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        # Label with Bianace US exchange name 
        self._binance_label = QLabel()
        self._binance_label.setObjectName("binance_label_symbol")
        self._binance_label.setText("Binance US")
        self._binance_label.setMaximumWidth(200)
        self._binance_label.setMaximumHeight(50)
        self._binance_label.setIndent(0)
        self._binance_label.setAlignment(Qt.AlignmentFlag.AlignTop)
        self._binance_label.setAlignment(Qt.AlignmentFlag.AlignHCenter)
        
        # LineEdit for Bianace US exchange 
        self._binance_entry = QLineEdit()
        self._binance_entry.setObjectName("lineEdit_binance_entry")
        self._binance_entry.setPlaceholderText("BTCUSDT")
        self._binance_entry.setMaximumWidth(200)
        self._binance_entry.setAlignment(Qt.AlignmentFlag.AlignTop)
        
        # Applies an autocompleter when typing a pair in the LineEdit
        _binance_entry_autocompleter = QCompleter(self.binance_symbols)
        _binance_entry_autocompleter.popup().setStyleSheet("""background-color: #4d4d4d;
                                                           border: 2px solid #4d4d4d;
                                                           color: #ffffff;
                                                           padding: 5px;""")
        self._binance_entry.setCompleter(_binance_entry_autocompleter)
        
        # Enter button trigger to add symbol to watchlist
        self._binance_entry.returnPressed.connect(self._add_binance_symbol)
        
        # Applying widgets to _command frame. Order is important
        self._commands_frame.addWidget(self._binance_label)
        self._commands_frame.addWidget(self._binance_entry)
        self._commands_frame.addWidget(self.watchlist_scrollArea)
        
        # Creating headers for scrollAreaWidgetContents
        self._headers = ["symbol", "exchange", "bid", "ask", "remove"]
        
        # Create a list of QLabels for the number of headers 
        self._headers_labels = [QLabel() for _ in range(len(self._headers))]
        
        # Initiate body widget dictionary
        self.body_widgets = dict()
        
        # enumerate over QLabel list
        for idx, h in enumerate(self._headers_labels):
            
            # Give each header QLabel a setObjectName. Good for stylesheet
            h.setObjectName(f"label_{self._headers[idx]}")
            
            if self._headers[idx] == 'remove':
                h.setText("") # remove Qlabel isn't need initially
                
            else:
                h.setText(f"{self._headers[idx]}") # initiate headers text
                h.setMinimumWidth(200)
                
            self._headers_frame.addWidget(h, 0, idx) # remember, headers are in scroll area
            
        # Fill initiated dictionary with header dictionary     
        for h in self._headers:
            
            self.body_widgets[h] = dict()
            
            if h in ['bid', 'ask']:
                self.body_widgets[h + "_var"] = dict()
                
        # Important for where to add pair data in Scroll area
        # self._body_index = 0 is the header area    
        self._body_index = 1
        
        # saved_symbols = self.db.get("watchlist")
        # for s in saved_symbols:
        #     self._add_symbol(s['symbol'], s['exchange'])
        
        # Now we add the scrollAreaWidgetContents to watchlist_scrollArea
        self.watchlist_scrollArea.setWidget(self.scrollAreaWidgetContents)
        
        # Push widgets up in watchlist_widget
        self._commands_frame.setAlignment(Qt.AlignmentFlag.AlignTop)
              
    def _remove_symbol(self, b_index: int):
        """Remove pair data from watchlist"""
        
        for h in range(len(self._headers)):
            del_widget = self._headers_frame.itemAtPosition(b_index, h).widget()
            del_widget.deleteLater()
            
        for h in self._headers:
            del self.body_widgets[h][b_index]
    
    def _add_binance_symbol(self):
        """Add pair data to watchlist"""
        
        symbol = self._binance_entry.text()
        
        # Only add symbol if it exist on exchange
        if symbol in self.binance_symbols:
            self._add_symbol(symbol, "Binance US")
            self._binance_entry.setText("")
            self._binance_entry.setPlaceholderText("")
            self.notification.notify(f"{symbol} has been added to watchlist")
        
    def _add_symbol(self, symbol:str, exchange:str):
        
        b_index = self._body_index
        
        # Symbol data from self.prices on exchange
        # handeled by websocket
        self.body_widgets['symbol'][b_index] = QLabel()
        self.body_widgets['symbol'][b_index].setText(symbol)
        self._headers_frame.addWidget(self.body_widgets['symbol'][b_index], b_index, 0)
        
        # Exchange
        self.body_widgets['exchange'][b_index] = QLabel()
        self.body_widgets['exchange'][b_index].setText(exchange)
        self._headers_frame.addWidget(self.body_widgets['exchange'][b_index], b_index, 1)
        
        # Bid data -> refer to self.prices on exchange connection file
        self.body_widgets['bid_var'][b_index] = QLabel()
        self.body_widgets['bid_var'][b_index].setText("")
        self.body_widgets['bid'][b_index] = QLabel()
        self.body_widgets['bid'][b_index].setText(self.body_widgets['bid_var'][b_index].text())
        self._headers_frame.addWidget(self.body_widgets['bid'][b_index], b_index, 2)
        
        # Ask data -> refer to self.prices on exchange connection file
        self.body_widgets['ask_var'][b_index] = QLabel()
        self.body_widgets['ask_var'][b_index].setText("")
        self.body_widgets['ask'][b_index] = QLabel()
        self.body_widgets['ask'][b_index].setText(self.body_widgets['ask_var'][b_index].text())
        self._headers_frame.addWidget(self.body_widgets['ask'][b_index], b_index, 3)
        
        # Created PushButton widget for removing symbol
        self.body_widgets['remove'][b_index] = QPushButton()
        self.body_widgets['remove'][b_index].setText("X")
        self.body_widgets['remove'][b_index].setObjectName("remove_button_watchlist")
        self._headers_frame.addWidget(self.body_widgets['remove'][b_index], b_index, 4)
        self.body_widgets['remove'][b_index].clicked.connect(lambda: self._remove_symbol(b_index=b_index))
        
        self._body_index += 1