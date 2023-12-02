##########  Python IMPORTs  ############################################################
from PyQt6.QtCore import (Qt, 
                          QPoint, 
                          QRect,
                          QEasingCurve, 
                          QPropertyAnimation, 
                          QParallelAnimationGroup, 
                          QSequentialAnimationGroup)
from PyQt6.QtWidgets import (QLabel, 
                             QWidget,
                             QGraphicsOpacityEffect,
                             QPushButton)
from pathlib import Path
########################################################################################

class Side_Menu(QWidget):
    """
    This is the custom Side menu that will appear
    when triggered. It will contain all of the buttons
    needed to change pages on the stack widget
    """
    def __init__(self,
                 parent=None
                 ):
        super().__init__(parent)
        self.setObjectName(u"side_menu_w")
        self.setGeometry(QRect(-300, 50, 300, 1030))
        self.setMaximumWidth(300)
        self.widget = QWidget(self)
        self.widget.setObjectName(u"side_menu")
        self.widget.setGeometry(QRect(0, 0, 290, 730))
        self.widget.setMaximumWidth(290)
        self.effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.effect)
        
        # Appearing animation movement
        self.show_animation = QPropertyAnimation(self, b"pos")
        self.show_animation.setEndValue(QPoint(-30, 50))
        self.show_animation.setEasingCurve(QEasingCurve.Type.OutQuad)
        self.show_animation.setDuration(1000)  # time in ms
        
        # Appearing animation opacity
        self.show_opacity_animation = QPropertyAnimation(self.effect, b"opacity")
        self.show_opacity_animation.setStartValue(0)
        self.show_opacity_animation.setEndValue(1)
        self.show_opacity_animation.setEasingCurve(QEasingCurve.Type.OutQuad)
        self.show_opacity_animation.setDuration(1000)
        
        # Grouping appearing animation together to occur simultaneously
        self.anim_group_appear = QParallelAnimationGroup()
        self.anim_group_appear.addAnimation(self.show_animation)
        self.anim_group_appear.addAnimation(self.show_opacity_animation)
        
        # Disappering animation movement
        self.disappear_animation = QPropertyAnimation(self, b"pos")
        self.disappear_animation.setEndValue(QPoint(-300, 50))
        self.disappear_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.disappear_animation.setDuration(1200)  # time in ms
        
        # Disappering animation opacity
        self.disappear_opacity_animation = QPropertyAnimation(self.effect, b"opacity")
        self.disappear_opacity_animation.setStartValue(1)
        self.disappear_opacity_animation.setEndValue(0)
        self.disappear_opacity_animation.setEasingCurve(QEasingCurve.Type.OutCubic)
        self.disappear_opacity_animation.setDuration(1200)
        
        # Grouping disappearing animation together to occur simultaneously
        self.anim_group_disappear = QParallelAnimationGroup()
        self.anim_group_disappear.addAnimation(self.disappear_animation)
        self.anim_group_disappear.addAnimation(self.disappear_opacity_animation)
        
        # Make Label for title
        self.title = QLabel("Menu", self.widget)
        self.title.setObjectName("side_menu_title")
        self.title.setGeometry(QRect(70, 20, 200, 100))
        self.title.setAlignment(Qt.AlignmentFlag.AlignCenter)
        
        # button for Dashboard Page
        self.dashboard_page_button = QPushButton("Dashboard", self.widget)
        self.dashboard_page_button.setObjectName("Dashboard_button")
        self.dashboard_page_button.setGeometry(QRect(70, 120, 200, 50))
        
        # button for Strategy Page
        self.strategy_page_button = QPushButton("Strategies", self.widget)
        self.strategy_page_button.setObjectName("Strategies_button")
        self.strategy_page_button.setGeometry(QRect(70, 220, 200, 50))
        
        # button for Backtesting Page
        self.backtesting_button = QPushButton("Backtesting Lab", self.widget)
        self.backtesting_button.setObjectName("Backtesting_button")
        self.backtesting_button.setGeometry(QRect(70, 320, 200, 50))
        
    def appear(self):
        self.anim_group_appear.start()
        
    def disappear(self):
        self.anim_group_disappear.start()