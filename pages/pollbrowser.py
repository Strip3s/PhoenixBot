from theming.styles import globalStyles
from pages.createdialog import CreateDialog
from PyQt5 import QtCore, QtGui, QtWidgets
import sys,platform



class PollBrowserDialog(QtWidgets.QDialog):
    def __init__(self, parent=None):
        super(PollBrowserDialog, self).__init__(parent)
        self.acceptListeners = []
        self.setupUi(self)
        self.show()
        


    def setupUi(self, PbdObj):
        self.PollBrowserDialog = PbdObj
        PbdObj.setFixedSize(380, 200)
        PbdObj.setWindowTitle("Confirm Captcha")

        self.background = QtWidgets.QWidget(PbdObj)
        self.background.setGeometry(QtCore.QRect(0,0,380, 200))


        self.background.setStyleSheet("* {background-color: {}} QPushButton { background-color: %s;color: #FFFFFF;}" % (globalStyles["primary"]) .format(globalStyles["backgroundDark"]))
        font = QtGui.QFont()
        font.setPointSize(16) if platform.system() == "Darwin" else font.setPointSize(16 * .75)
        font.setFamily("Arial")

        self.label = QtWidgets.QLabel(self.background)
        self.label.setGeometry(QtCore.QRect(10, 50, 370, 40))
        self.label.setText("Solve any Captchas in the New Browser Window\nClick Below When Finished")
        self.label.setStyleSheet("color: rgb(234, 239, 239); text-align: center; qproperty-alignment: 'AlignCenter'")
        self.label.setFont(font)

        self.confirmButton = QtWidgets.QPushButton(self.background)
        self.confirmButton.setGeometry(QtCore.QRect(150, 150, 100, 25))
        self.confirmButton.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.confirmButton.setFont(font)
        self.confirmButton.setStyleSheet("color: rgb(234, 239, 239); background-color: {}".format(globalStyles["primary"]))
        self.confirmButton.setText("All Done.")
        

        self.confirmButton.clicked.connect(self.accept)


        QtCore.QMetaObject.connectSlotsByName(PbdObj)
