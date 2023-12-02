##########  Python IMPORTs  ############################################################
from PyQt6.QtCore import (Qt, 
                          QPoint, 
                          QRect,
                          QEasingCurve, 
                          QPropertyAnimation, 
                          QParallelAnimationGroup, 
                          QSequentialAnimationGroup)
from PyQt6.QtWidgets import QLabel, QGraphicsOpacityEffect
from pathlib import Path
########################################################################################

class Top_Notification(QLabel):
    """
    This is a custom QLabel with notification-like
    animation. Whenever their is a notification, this
    label will appear from the top and them disappear
    back to the top
    """
    def __init__(self,
                 style, 
                 parent=None
                 ):
        super().__init__(parent)
        self.style = style
        self.setStyleSheet(Path(self.style).read_text())
        self.setObjectName("notification_label")
        self.setText("")
        self.setGeometry(QRect(635, -100, 650, 500))
        self.setMaximumWidth(650)
        self.setMaximumHeight(50)
        self.setAlignment(Qt.AlignmentFlag.AlignCenter)
        self.setIndent(30)
        self.effect = QGraphicsOpacityEffect(self)
        self.setGraphicsEffect(self.effect)
        
        self.position_animation_1 = QPropertyAnimation(self, b"pos")
        self.position_animation_1.setEndValue(QPoint(635, 45))
        self.position_animation_1.setEasingCurve(QEasingCurve.Type.OutQuad)
        self.position_animation_1.setDuration(1500)  # time in ms
        
        self.position_animation_2 = QPropertyAnimation(self, b"pos")
        self.position_animation_2.setEndValue(QPoint(635, 45))
        self.position_animation_2.setEasingCurve(QEasingCurve.Type.Linear)
        self.position_animation_2.setDuration(5000)  # time in ms
        
        self.position_animation_3 = QPropertyAnimation(self, b"pos")
        self.position_animation_3.setEndValue(QPoint(635, -100))
        self.position_animation_3.setEasingCurve(QEasingCurve.Type.OutInQuart)
        self.position_animation_3.setDuration(1500)  # time in ms
        
        self.opacity_animation_1 = QPropertyAnimation(self.effect, b"opacity")
        self.opacity_animation_1.setStartValue(0)
        self.opacity_animation_1.setEndValue(1)
        self.opacity_animation_1.setEasingCurve(QEasingCurve.Type.InQuad)
        self.opacity_animation_1.setDuration(1200)
        
        self.opacity_animation_2 = QPropertyAnimation(self.effect, b"opacity")
        self.opacity_animation_2.setStartValue(1)
        self.opacity_animation_2.setEndValue(0)
        self.opacity_animation_2.setEasingCurve(QEasingCurve.Type.InQuad)
        self.opacity_animation_2.setDuration(1400)
        
        self.anim_group_appear = QParallelAnimationGroup()
        self.anim_group_appear.addAnimation(self.position_animation_1)
        self.anim_group_appear.addAnimation(self.opacity_animation_1)
        
        self.anim_group_disappear = QParallelAnimationGroup()
        self.anim_group_disappear.addAnimation(self.position_animation_3)
        self.anim_group_disappear.addAnimation(self.opacity_animation_2)
        
        self.notification_animation = QSequentialAnimationGroup()
        self.notification_animation.addAnimation(self.anim_group_appear)
        self.notification_animation.addAnimation(self.position_animation_2)
        self.notification_animation.addAnimation(self.anim_group_disappear)
        
    def notify(self, text: str):
        """
        Text sent to this function will be displayed with the animation
        """
        self.setText(text)
        self.notification_animation.start()