##########  Python IMPORTs  ############################################################
from pathlib import Path
import threading 
import time
########################################################################################
##########  Python THIRD PARTY IMPORTs  ################################################
from PyQt6 import QtTest
from PyQt6.QtWidgets import (QMainWindow,
                             QWidget,
                             QMessageBox,
                             QStackedWidget,
                             QPushButton,
                             QLabel,
                             QGraphicsOpacityEffect)
from PyQt6.QtGui import QAction
from PyQt6.QtCore import (QRect,
                          QParallelAnimationGroup, 
                          QSequentialAnimationGroup,
                          QPoint,
                          QEasingCurve, 
                          QPropertyAnimation,)
########################################################################################
##########  Created files IMPORTS  #####################################################
import initiate.root_component.util.root_variables as r_var
from initiate.root_component.util.custom_label import Top_Notification
from initiate.root_component.util.custom_side_menu import Side_Menu
from initiate.root_component.components.logging_component import Logging
from initiate.root_component.components.watchlist_component import Watchlist
from initiate.root_component.components.trades_component import TradesWatch
from initiate.root_component.components.strategy_component import StrategyEditor
from initiate.root_component.components.backtesting_component import BacktestLab
from initiate.connectors.binance_us import BinanceUSClient
import initiate.root_component.util.style.resources # Do not remove. Needed for images
########################################################################################

class Root(QWidget):
    """
    This class is responsible for handling files and directories
    to other components that may not have access to certain
    files directly and controlling the base application\n
    Thread: Main Thread
    """
    def __init__(self, MainWindow: QMainWindow, 
                 logger, 
                 binance_us: BinanceUSClient):
        super().__init__(MainWindow)
        
        # initiate logger in this class
        self.root_h_log = logger
        
        # Prepare MainWindow
        MainWindow.setObjectName("MainWindow")
        MainWindow.resize(1920, 1080)
        MainWindow.setWindowTitle("Trading GUI")
        # Gives Mainwindow dark mode style
        MainWindow.setStyleSheet(Path(r_var.DARK_MODE).read_text())
        # Replace QMainWindow closeEvent with one of our own
        MainWindow.closeEvent = self.closeEvent
        MainWindow.setMaximumSize(1920, 1080)
        
        # Begin the main parent widget of the main window
        # Mainwindow -> central widget
        self.centralwidget = QWidget(MainWindow)
        self.centralwidget.setObjectName(u"centralwidget")
        self.centralwidget.setGeometry(QRect(0, 0, 1920, 1080))
        
        # Menu Bar
        # Mainwindow -> Menu Bar
        self.actionSave_Workspace = QAction(MainWindow)
        self.actionSave_Workspace.setObjectName(u"actionSave_Workspace")
        self.actionSave_Workspace.setText("Save Workspace")
        # Action of "Save Workspace" in menu bar
        self.actionSave_Workspace.triggered.connect(self._save_workspace)
        # Apply menu bar to MainWindow
        self.menu_bar = MainWindow.menuBar()
        self.menu_bar.setGeometry(QRect(0, 0, 1920, 15))
        # On the menu bar there were be a menu called "Workspace"
        workspace_menu = self.menu_bar.addMenu('&Workspace')
        workspace_menu.addAction(self.actionSave_Workspace)
        
        # Set up nofication pop up animation
        # Mainwindow -> central widget -> notification
        self.notification = Top_Notification(r_var.NOTIFICATION_STYLE, 
                                             self.centralwidget)
        self.notification.notify("Welcome!")
        self.notification.raise_()
        
        # Prepare page swap button
        self.side_menu_button = QPushButton(self.centralwidget)
        self.side_menu_button.setObjectName("side_menu_button")
        self.side_menu_button.setGeometry(QRect(10, 40, 50, 50))
        # indicator for side menu button position
        # 0 means off. 1 means active
        self.side_menu_position = 0
        
        # Prepare Pages (i.e. Stack Widgets) for Main Window
        # Mainwindow -> central widget -> StackWidget
        self.stackedWidget = QStackedWidget(self.centralwidget)
        self.stackedWidget.stackUnder(self.notification)
        self.stackedWidget.setObjectName(u"Main_stackedWidget")
        self.stackedWidget.setGeometry(QRect(0, 75, 1895, 856))
        
        # Starting Dashboard
        # Mainwindow -> central widget -> StackWidget -> Main Page
        self.main_page = QWidget()
        self.main_page.setObjectName(u"Main_page")
        self.stackedWidget.addWidget(self.main_page)
        
        # For Strategy Page
        # Mainwindow -> central widget -> StackWidget -> Strategy Page
        self.strategy_page = QWidget()
        self.strategy_page.setObjectName(u"Strategy_page")
        self.stackedWidget.addWidget(self.strategy_page)
        
        # For Backtesting
        # Mainwindow -> central widget -> StackWidget -> Backtesting Page
        self.backtesting_page = QWidget()
        self.backtesting_page.setObjectName(u"Backtesting_page")
        self.stackedWidget.addWidget(self.backtesting_page)
        
        # Make the main page the main page upon initializing
        self.stackedWidget.setCurrentWidget(self.main_page)
        
        # Prepare log for all activity in Main Window
        # Mainwindow -> central widget -> logging_frame
        self.logging_frame = Logging(self.centralwidget)
        
        # Create Side Menu and place in Main Window
        self.side_menu = Side_Menu(self.centralwidget)
        self.side_menu.raise_()
        
        # Create animations for the program
        self.animation_creation()

        # initiate Binance US connection to Main Window
        self.binance_us = binance_us 
        
        # Watchlist: -> Main Page
        self.watchlist = Watchlist(self.main_page,
                                   self.binance_us.pairs, 
                                   self.notification)
        
        # Trades: -> Main Page
        self.trades = TradesWatch(self.main_page, 
                                  self.binance_us.pairs, 
                                  self.notification)
        
        # Strategies: -> Page 2
        self.strategies = StrategyEditor(self.strategy_page,
                                         self.binance_us.pairs,
                                         self.binance_us,
                                         self.notification)
        
        # BackTest, Optimization, Collect Data: -> Page 3
        self.backtest = BacktestLab(self.backtesting_page, 
                                    self.binance_us.pairs,
                                    self.binance_us)
        
        # Upon login
        self.stackedWidget_animation_1()
        
        # Triggers and events
        self.side_menu_button.clicked.connect(self.side_menu_trigger)
        self.side_menu.dashboard_page_button.clicked.connect(self.change_to_main_page)
        self.side_menu.strategy_page_button.clicked.connect(self.change_to_strategy_page)
        self.side_menu.backtesting_button.clicked.connect(self.change_to_backtesting_page)
        
        # Begin thread for updating ui when needed
        t = threading.Thread(target=self._update_ui)
        t.setName("update_ui")
        t.start() 
        
    def closeEvent(self, event):
        """
        Custom close event handler\n
        closes:\n
        Main Application\n
        Binance US websocket
        """
        ret = QMessageBox.question(self, "Confirmation",
                                 "Do you really want to exit the application?",
                                 QMessageBox.StandardButton.Close | QMessageBox.StandardButton.Cancel)
        
        # If user chooses to exit the application
        if ret == QMessageBox.StandardButton.Close:
            self.binance_us.reconnect = False
            self.binance_us.ws.close()
            event.accept()
            self.destroy()
            
        # If user chooses not to close application
        elif ret == QMessageBox.StandardButton.Cancel:
            event.ignore()
            
        # Close event will be ignored if neither are selected
        else:
            event.ignore()

    def _update_ui(self):
        """
        Responsible for for delivering
        new information to the application\n
        Thread: update_ui
        """
        while True:
            try:
                # Logs
                for log in self.binance_us.logs:
                    if not log["displayed"]:
                        self.logging_frame.add_log(log['log'])
                        log["displayed"] = True
                
                # Trades and logs
                for client in [self.binance_us]:
                    try:
                        for b_index, strat in client.strategies.items():
                            for log in strat.logs:
                                if not log['displayed']:
                                    self.logging_frame.add_log(log['log'])
                                    log["displayed"] = True
                                    
                            for trade in strat.trades:
                                if trade.time not in self.trades.body_widgets['symbol']:
                                    self.trades.add_trade(trade)
                                
                                if trade.pair.exchange == 'binance':
                                    precision = trade.pair.price_decimal 
                                else:
                                    precision = 8
                                    
                                pnl_str = "{0:.{prec}f}".format(trade.pnl, prec=precision)
                                self.trades.body_widgets['PnL'][trade.time].setText(pnl_str)
                                self.trades.body_widgets['Status'][trade.time].setText(trade.status.capitalize())    
                
                    except RuntimeError as e:
                        self.logging_frame.add_log("Error while looping through strategies dictionary: %s", e)
                        self.root_h_log.error("Error while looping through strategies dictionary: %s", e)
                        
                for widget_logs in [self.strategies, self.backtest]:
                    try:
                        for log in widget_logs.logs:
                            if not log['displayed']:
                                self.logging_frame.add_log(log['log'])
                                log["displayed"] = True
                    except RuntimeError as e:
                        self.logging_frame.add_log("Error while looping through component logs: %s", e)
                        self.root_h_log.error("Error while looping through component logs: %s", e)
                
                # Watchlist prices
                for key, value in self.watchlist.body_widgets['symbol'].items():
                    symbol = self.watchlist.body_widgets['symbol'][key].text()
                    exchange = self.watchlist.body_widgets['exchange'][key].text()
                    # Method to get Binance US bid/ask prices
                    if exchange == "Binance US": 
                        # Skip data not available
                        if symbol not in self.binance_us.pairs:
                            continue
                        # Get bid and ask price from Binance US Rest API
                        if symbol not in self.binance_us.prices:
                            self.binance_us.get_bid_ask(self.binance_us.pairs[symbol])
                        # give precision of prices from PairData information
                        precision = self.binance_us.pairs[symbol].price_decimal     
                        prices = self.binance_us.prices[symbol]
                    # This will be for when more exchanges are added    
                    else:
                        continue
                    # updates bid information if given
                    if prices['bid'] is not None:
                        price_str = "{0: .{prec}f}".format(prices['bid'], prec=precision)
                        self.watchlist.body_widgets['bid'][key].setText(price_str)
                    # updates ask information if given    
                    if prices['ask'] is not None:
                        price_str = "{0: .{prec}f}".format(prices['bid'], prec=precision)
                        self.watchlist.body_widgets['ask'][key].setText(price_str)
                # Breaks the thread if connection set to False        
                if self.binance_us.reconnect == False:
                    break     
                
            except RuntimeError as e:
                self.logging_frame.add_log(f"Error while looping through watchlist dictionary: {e}")
                self.root_h_log.error("Error while looping through watchlist dictionary: %s", e)
            # Only updates/activates every 1.5 seconds     
            time.sleep(1)
            
    def _save_workspace(self):
        self.notification.notify("Workspace clicked")
        return
    
    def stackedWidget_animation_1(self):
        self.stackedWidget_widget_open_animation.start()
        # self.stackedWidget_widget_open_animation.stop()
        
    def animation_creation(self):
        """"
        initialize so animations are already prepared for 
        interface trigger function\n
        return: void
        """
        # Central widget animation upon login
        self.stackedWidget_show = QPropertyAnimation(self.stackedWidget, b"pos")
        self.stackedWidget_show.setEndValue(QPoint(0, 25))
        self.stackedWidget_show.setEasingCurve(QEasingCurve.Type.OutBack)
        self.stackedWidget_show.setDuration(2500)  # time in ms
        self.stackedWidget_effect = QGraphicsOpacityEffect(self.stackedWidget)
        self.stackedWidget.setGraphicsEffect(self.stackedWidget_effect)
        self.stackedWidget_opacity_animation = QPropertyAnimation(self.stackedWidget_effect, b"opacity")
        self.stackedWidget_opacity_animation.setStartValue(0)
        self.stackedWidget_opacity_animation.setEndValue(1)
        self.stackedWidget_opacity_animation.setEasingCurve(QEasingCurve.Type.OutQuad)
        self.stackedWidget_opacity_animation.setDuration(1000)
        self.stackedWidget_widget_open_animation = QParallelAnimationGroup()
        self.stackedWidget_widget_open_animation.addAnimation(self.stackedWidget_show)
        self.stackedWidget_widget_open_animation.addAnimation(self.stackedWidget_opacity_animation)
        
        # side menu button animation showing menu
        self.sm_button_show = QPropertyAnimation(self.side_menu_button, b"pos")
        self.sm_button_show.setEndValue(QPoint(280, 40))
        self.sm_button_show.setEasingCurve(QEasingCurve.Type.OutQuad)
        self.sm_button_show.setDuration(1000)  # time in ms
        
        # side menu button animation closing menu
        self.sm_button_close = QPropertyAnimation(self.side_menu_button, b"pos")
        self.sm_button_close.setEndValue(QPoint(10, 40))
        self.sm_button_close.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.sm_button_close.setDuration(1200)  # time in ms
        
        # Close side menu animation
        self.close_group_animation = QParallelAnimationGroup()
        self.close_group_animation.addAnimation(self.side_menu.anim_group_disappear)
        self.close_group_animation.addAnimation(self.sm_button_close)
        
        # Open side menu animation
        self.show_group_animation = QParallelAnimationGroup()
        self.show_group_animation.addAnimation(self.side_menu.anim_group_appear)
        self.show_group_animation.addAnimation(self.sm_button_show)
        
    def side_menu_trigger(self):
        if not self.side_menu_position:
            self.show_group_animation.start()
            self.side_menu_position = 1
            return
        
        elif self.side_menu_position:
            self.close_group_animation.start()
            self.side_menu_position = 0
            return
        
        else:
            self.side_menu_position = 0
            return
        
    def change_to_main_page(self):
        self.stackedWidget.setCurrentWidget(self.main_page)
        return
     
    def change_to_strategy_page(self):
        self.stackedWidget.setCurrentWidget(self.strategy_page)
        return        
    
    def change_to_backtesting_page(self):
        self.stackedWidget.setCurrentWidget(self.backtesting_page)
        return      
            