##########  Python IMPORTs  ############################################################
from PyQt6.QtWidgets import QTextEdit
from PyQt6.QtGui import QTextCursor
from PyQt6.QtCore import QSize, Qt, QRect
from datetime import datetime
########################################################################################

class Logging(QTextEdit):
    def __init__(self, parent=None):
        super().__init__(parent)
        self.setObjectName("TextEdit_display_info")
        self.setHtml("<!DOCTYPE HTML PUBLIC \"-//W3C//DTD HTML 4.0//EN\" \"http://www.w3.org/TR/REC-html40/strict.dtd\">\n"
                                 "<html><head><meta name=\"qrichtext\" content=\"1\" /><meta charset=\"utf-8\" /><style type=\"text/css\">\n"
                                 "p, li { white-space: pre-wrap; }\n"
                                 "</style></head><body style=\" font-family:\'Times New Roman\'; font-size:12pt; font-weight:400; font-style:normal;\">\n"
                                 "<p style=\"-qt-paragraph-type:empty; margin-top:0px; margin-bottom:0px; margin-left:0px; margin-right:0px; -qt-block-indent:0; text-indent:0px; font-family:\'Arial\'; font-size:14pt;\"><br /></p></body></html>")
        self.setPlaceholderText("Log Display...")
        self.setReadOnly(True)
        self.setGeometry(QRect(100, 869, 1720, 204))
        self.setMaximumSize(QSize(1720, 204))
        self.setMinimumWidth(500)
        
    def add_log(self, message: str):
        try:
            time = datetime.utcnow().strftime("%a %H:%M:%S ::")
            self.insertPlainText(time + message + "\n")
            self.setTextCursor(QTextCursor(self.document()))
        except Exception as e:
            print(e)
    def add_log_with_red_color(self, message:str, color):
        cursor = self.textCursor()
        # Get current format
        format_original = cursor.charFormat()
        format_temp = cursor.charFormat()
        # modify temporary one
        format_temp.setForeground(Qt.GlobalColor.red)
        cursor.setCharFormat(format_temp)
        # Apply text
        self.add_log(message)
        # Apply original again 
        cursor.setCharFormat(format_original)
        