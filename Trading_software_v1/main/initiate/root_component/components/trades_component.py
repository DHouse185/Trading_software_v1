##########  Python IMPORTs  ############################################################
import datetime
########################################################################################
##########  Python THIRD PARTY IMPORTs  ################################################
from PyQt6.QtWidgets import (QWidget,
                            QGridLayout,
                            QLabel, 
                            QScrollArea)
from PyQt6.QtCore import Qt, QRect
########################################################################################
##########  Created files IMPORTS  #####################################################
from initiate.connectors.models import *
########################################################################################

class TradesWatch:
    """"
    This is essentially a widget that will control everything
    That occurs within the Trades Watch area. You can find all
    your active trades here
    """
    def __init__(self, main_page, binance_pairs, notification): #: typing.Dict[str, PairData]):
        super().__init__()
        self.binance_symbols = list(binance_pairs.keys())
        self.main_page = main_page
        self.notification = notification
        
        # Create a widget that will contain all things related
        # to the Trades Watch area
        # Mainwindow -> central widget -> StackWidget -> Main Page
        # -> Trades_widget
        self.trades_widget = QWidget(self.main_page)
        self.trades_widget.setObjectName(u"trades_widget")
        self.trades_widget.setGeometry(QRect(657, 130, 607, 706))
        
        # Mainwindow -> central widget -> StackWidget -> Main Page
        # -> watchlist_widget -> trades_scrollArea
        self.trades_scrollArea = QScrollArea(self.trades_widget)
        self.trades_scrollArea.setObjectName("Trades_scrollArea")
        self.trades_scrollArea.setWidgetResizable(True)
        self.trades_scrollArea.setMaximumSize(587, 686)
        self.trades_scrollArea.setGeometry(QRect(10, 10, 587, 686))
        
        # _Headers Frame will be the main layout of trades widget
        # Mainwindow -> central widget -> StackWidget -> Main Page
        # -> watchlist_widget -> trades_scrollArea 
        # -> scrollAreaWidgetContents
        self.scrollAreaWidgetContents = QWidget()
        self.scrollAreaWidgetContents.setObjectName("trades_scrollAreaWidgetContents")
        
        # Creating a grid layout for headers, columns, and rows
        # Mainwindow -> central widget -> StackWidget -> Main Page
        # -> watchlist_widget -> trades_scrollArea -> scrollAreaWidgetContents 
        # -> _headers_frame
        self._headers_frame = QGridLayout(self.scrollAreaWidgetContents)
        self._headers_frame.setObjectName("Trades_Headers_frame")
        self._headers_frame.setSpacing(10)
        
        # Creating headers for scrollAreaWidgetContents
        self._headers = ["Time", "Symbol", "Exchange", "Strategy", "Side", "Quantity", "Status", "PnL"]
        
        # Create a list of QLabels for the number of headers 
        self._headers_labels = [QLabel() for _ in range(len(self._headers))]
        
        # Initiate body widget dictionary
        self.body_widgets = dict()
        
        # enumerate over QLabel list
        for idx, h in enumerate(self._headers_labels):
            # Give each header QLabel a setObjectName. Good for stylesheet
            h.setObjectName(f"label_{self._headers[idx]}")
            h.setText(f"{self._headers[idx]}")
            h.setMinimumWidth(100)
            h.setIndent(25)
            # Adding to specific location
            self._headers_frame.addWidget(h, 0, idx) # remember, headers are in scroll area
            
        # Fill initiated dictionary with header dictionary      
        for h in self._headers:
            
            self.body_widgets[h] = dict()
            
            if h in ['Status', 'PnL']:
                self.body_widgets[h + "_var"] = dict()
                
        # Important for where to add pair data in Scroll area
        # self._body_index = 0 is the header area        
        self._body_index = 1
        
        # Now we add the scrollAreaWidgetContents to trades_scrollArea
        self.trades_scrollArea.setWidget(self.scrollAreaWidgetContents)
        
        # Push widgets up in watchlist_widget
        self._headers_frame.setAlignment(Qt.AlignmentFlag.AlignTop)
        
    def add_trade(self, trade: Trade):
        """
        Responsible for adding currently active trades on the 
        Trades Watch area
        """
        
        b_index = self._body_index
        t_index = trade.time
        dt_str = datetime.datetime.fromtimestamp(trade.time / 1000).strftime("%b %d %H:%M")
        
        # Time
        self.body_widgets['Time'][t_index] = QLabel()
        self.body_widgets['Time'][t_index].setText(dt_str)
        self._headers_frame.addWidget(self.body_widgets['Time'][t_index], b_index, 0)
        
        # Symbol
        self.body_widgets['Symbol'][t_index] = QLabel()
        self.body_widgets['Symbol'][t_index].setText(str(trade.pair.symbol))
        self._headers_frame.addWidget(self.body_widgets['Symbol'][t_index], b_index, 1)
        
        # Exchange
        self.body_widgets['Exchange'][t_index] = QLabel()
        self.body_widgets['Exchange'][t_index].setText(str(trade.pair.exchange.capitalize()))
        self._headers_frame.addWidget(self.body_widgets['Exchange'][t_index], b_index, 2)
        
        # Strategy
        self.body_widgets['Strategy'][t_index] = QLabel()
        self.body_widgets['Strategy'][t_index].setText(str(trade.strategy))
        self._headers_frame.addWidget(self.body_widgets['Strategy'][t_index], b_index, 3)
        
        # Side
        self.body_widgets['Side'][t_index] = QLabel()
        self.body_widgets['Side'][t_index].setText(str(trade.side.capitalize()))
        self._headers_frame.addWidget(self.body_widgets['Side'][t_index], b_index, 4)
        
        # Quantity
        self.body_widgets['Quantity'][t_index] = QLabel()
        self.body_widgets['Quantity'][t_index].setText(str(trade.quantity))
        self._headers_frame.addWidget(self.body_widgets['Quantity'][t_index], b_index, 5)
        
        # Status
        self.body_widgets['Status_var'][t_index] = QLabel()
        self.body_widgets['Status_var'][t_index].setText("")
        self.body_widgets['Status'][t_index] = QLabel()
        self.body_widgets['Status'][t_index].setText(self.body_widgets['Status_var'][t_index].text())
        self._headers_frame.addWidget(self.body_widgets['Status'][t_index], b_index, 6)
        
        # PnL
        self.body_widgets['PnL_var'][t_index] = QLabel()
        self.body_widgets['PnL_var'][t_index].setText("")
        self.body_widgets['PnL'][t_index] = QLabel()
        self.body_widgets['PnL'][t_index].setText(self.body_widgets['PnL_var'][t_index].text())
        self._headers_frame.addWidget(self.body_widgets['PnL'][t_index], b_index, 7)
        
        # Update to next line
        self._body_index += 1