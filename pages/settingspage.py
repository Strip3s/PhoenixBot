from theming.styles import globalStyles
from PyQt5 import QtCore, QtGui, QtWidgets
from utils import return_data,write_data,Encryption
import sys,platform,settings

def no_abort(a, b, c):
    sys.__excepthook__(a, b, c)
sys.excepthook = no_abort

class SettingsPage(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(SettingsPage, self).__init__(parent)
        self.header_font = self.create_font("Arial", 18)
        self.small_font = self.create_font("Arial", 13)
        self.setupUi(self)

    def create_font(self, family, pt_size) -> QtGui.QFont:
        font = QtGui.QFont()
        font.setPointSize(pt_size) if platform.system() == "Darwin" else font.setPointSize(pt_size * .75)
        font.setFamily(family)
        font.setWeight(50)
        return font

    def create_header(self, parent, rect, font, text) -> QtWidgets.QLabel:
        header = QtWidgets.QLabel(self.settings_card)
        header.setParent(parent)
        header.setGeometry(rect)
        header.setFont(font)
        header.setStyleSheet("color: rgb(212, 214, 214);border: none;")
        header.setText(text)
        return header

    def create_checkbox(self, rect, text) -> QtWidgets.QCheckBox:
        checkbox = QtWidgets.QCheckBox(self.settings_card)
        checkbox.setGeometry(rect)
        checkbox.setStyleSheet("color: #FFFFFF;border: none;")
        checkbox.setText(text)
        return checkbox

    def create_edit(self, parent, rect, font, placeholder) -> QtWidgets.QLineEdit:
        edit = QtWidgets.QLineEdit(parent)
        edit.setGeometry(rect)
        edit.setStyleSheet("outline: 0;border: 1px solid #5D43FB;border-width: 0 0 2px;color: rgb(234, 239, 239);")
        edit.setFont(font)
        edit.setPlaceholderText(placeholder)
        edit.setAttribute(QtCore.Qt.WA_MacShowFocusRect, 0)
        return edit

    def setupUi(self, settingspage):
        self.settingspage = settingspage
        self.settingspage.setAttribute(QtCore.Qt.WA_StyledBackground, True)
        self.settingspage.setGeometry(QtCore.QRect(60, 0, 1041, 601))
        self.settingspage.setStyleSheet("QComboBox::drop-down {    border: 0px;}QComboBox::down-arrow {    image: url(images/down_icon.png);    width: 14px;    height: 14px;}QComboBox{    padding: 1px 0px 1px 3px;}QLineEdit:focus {   border: none;   outline: none;}")
        self.settings_card = QtWidgets.QWidget(self.settingspage)
        self.settings_card.setGeometry(QtCore.QRect(30, 70, 941, 501))
        self.settings_card.setFont(self.small_font)
        self.settings_card.setStyleSheet("background-color: #232323;border-radius: 20px;border: 1px solid #2e2d2d;")

        self.webhook_edit = self.create_edit(self.settings_card, QtCore.QRect(30, 50, 411, 21), self.small_font,
                                                  "Webhook Link")
        self.webhook_header = self.create_header(self.settings_card, QtCore.QRect(20, 10, 101, 31), self.header_font,
                                                 "Webhook")
        
        self.savesettings_btn = QtWidgets.QPushButton(self.settings_card)
        self.savesettings_btn.setGeometry(QtCore.QRect(190, 450, 86, 32))
        self.savesettings_btn.setFont(self.small_font)
        self.savesettings_btn.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.savesettings_btn.setStyleSheet("color: #FFFFFF;background-color: {};border-radius: 10px;border: 1px solid #2e2d2d;".format(globalStyles["primary"]))
        self.savesettings_btn.setText("Save")
        self.savesettings_btn.clicked.connect(self.save_settings)

        self.browser_checkbox = self.create_checkbox(QtCore.QRect(30, 90, 300, 20), "Browser Opened")
        self.order_checkbox = self.create_checkbox(QtCore.QRect(30, 120, 221, 20), "Order Placed")
        self.paymentfailed_checkbox = self.create_checkbox(QtCore.QRect(30, 150, 121, 20), "Payment Failed")

        self.general_header = self.create_header(self.settings_card, QtCore.QRect(20, 180, 101, 31), self.header_font,
                                                 "General")
        self.onfailed_checkbox = self.create_checkbox(QtCore.QRect(30, 220, 221, 20), "Open browser on payment failed")
        self.buy_one_checkbox = self.create_checkbox(QtCore.QRect(30, 250, 221, 20), "Stop All after success")
        self.dont_buy_checkbox = self.create_checkbox(QtCore.QRect(30, 280, 400, 20),
                                                      "Don't actually buy items. (Used for dev and testing)")
        self.random_delay_start = self.create_edit(self.settings_card, QtCore.QRect(30, 310, 235, 20),
                                                   self.small_font, "Random Start Delay (Default is 10ms)")
        self.random_delay_stop = self.create_edit(self.settings_card, QtCore.QRect(30, 335, 235, 20),
                                                  self.small_font, "Random Stop Delay (Default is 40ms)")
        self.proxies_header = self.create_header(self.settingspage, QtCore.QRect(30, 10, 81, 31),
                                                 self.create_font("Arial", 22), "Settings")
        self.bestbuy_user_edit = self.create_edit(self.settings_card, QtCore.QRect(300, 310, 235, 20),
                                                 self.small_font, "Bestbuy.com Username (Email)")
        self.bestbuy_pass_edit = self.create_edit(self.settings_card, QtCore.QRect(300, 335, 235, 20),
                                                 self.small_font, "Bestbuy.com Password")
        self.target_user_edit = self.create_edit(self.settings_card, QtCore.QRect(30, 365, 235, 20),
                                                 self.small_font, "Target.com Username (Email/Cell #)")
        self.target_pass_edit = self.create_edit(self.settings_card, QtCore.QRect(30, 390, 235, 20),
                                                 self.small_font, "Target.com Password")
        self.gamestop_user_edit = self.create_edit(self.settings_card, QtCore.QRect(300, 365, 235, 20),
                                                 self.small_font, "Gamestop.com Username (Email)")
        self.gamestop_pass_edit = self.create_edit(self.settings_card, QtCore.QRect(300, 390, 235, 20),
                                                 self.small_font, "Gamestop.com Password")
        
        self.set_data()
        QtCore.QMetaObject.connectSlotsByName(settingspage)

    def set_data(self):
        settings = return_data("./data/settings.json")
        self.webhook_edit.setText(settings["webhook"])
        if settings["webhookonbrowser"]:
            self.browser_checkbox.setChecked(True)
        if settings["webhookonorder"]:
            self.order_checkbox.setChecked(True)
        if settings["webhookonfailed"]:
            self.paymentfailed_checkbox.setChecked(True)
        if settings["browseronfailed"]:
            self.onfailed_checkbox.setChecked(True)
        if settings['onlybuyone']:
            self.buy_one_checkbox.setChecked(True)
        if settings['dont_buy']:
            self.dont_buy_checkbox.setChecked(True)
        if settings['random_delay_start']:
            self.random_delay_start.setText(settings["random_delay_start"])
        if settings['random_delay_stop']:
            self.random_delay_stop.setText(settings["random_delay_stop"])

        try:
            self.bestbuy_user_edit.setText(settings["bestbuy_user"])
        except:
            self.bestbuy_user_edit.setText("")

        try:
            self.bestbuy_pass_edit.setText((Encryption().decrypt(settings["bestbuy_pass"].encode("utf-8"))).decode("utf-8"))
        except:
            self.bestbuy_pass_edit.setText("")

        try:
            self.target_user_edit.setText(settings["target_user"])
        except:
            self.target_user_edit.setText("")

        try:
            self.target_pass_edit.setText((Encryption().decrypt(settings["target_pass"].encode("utf-8"))).decode("utf-8"))
        except:
            self.target_pass_edit.setText("")
        
        try:
            self.gamestop_user_edit.setText(settings["gamestop_user"])
        except:
            self.gamestop_user_edit.setText("")

        try:
            self.gamestop_pass_edit.setText((Encryption().decrypt(settings["gamestop_pass"].encode("utf-8"))).decode("utf-8"))
        except:
            self.gamestop_pass_edit.setText("")

        self.update_settings(settings)

    def save_settings(self):
        settings = {"webhook":            self.webhook_edit.text(),
                    "webhookonbrowser":   self.browser_checkbox.isChecked(),
                    "webhookonorder":     self.order_checkbox.isChecked(),
                    "webhookonfailed":    self.paymentfailed_checkbox.isChecked(),
                    "browseronfailed":    self.onfailed_checkbox.isChecked(),
                    "onlybuyone":         self.buy_one_checkbox.isChecked(),
                    "dont_buy":           self.dont_buy_checkbox.isChecked(),
                    "random_delay_start": self.random_delay_start.text(),
                    "random_delay_stop":  self.random_delay_stop.text(),
                    "bestbuy_user": self.bestbuy_user_edit.text(),
                    "bestbuy_pass": Encryption().encrypt(self.bestbuy_pass_edit.text()).decode("utf-8"),
                    "target_user": self.target_user_edit.text(),
                    "target_pass": Encryption().encrypt(self.target_pass_edit.text()).decode("utf-8"),
                    "gamestop_user": self.gamestop_user_edit.text(),
                    "gamestop_pass": Encryption().encrypt(self.gamestop_pass_edit.text()).decode("utf-8")}

        write_data("./data/settings.json",settings)
        self.update_settings(settings)
        QtWidgets.QMessageBox.information(self, "Phoenix Bot", "Saved Settings")

    def update_settings(self, settings_data):
        global webhook, webhook_on_browser, webhook_on_order, webhook_on_failed, browser_on_failed, dont_buy, random_delay_start, random_delay_stop, target_user, target_pass, gamestop_user, gamestop_pass
        settings.webhook, settings.webhook_on_browser, settings.webhook_on_order, settings.webhook_on_failed, settings.browser_on_failed, settings.buy_one, settings.dont_buy = settings_data["webhook"], settings_data["webhookonbrowser"], settings_data["webhookonorder"], settings_data["webhookonfailed"], settings_data["browseronfailed"], settings_data['onlybuyone'], settings_data['dont_buy']

        if settings_data.get("random_delay_start", "") != "":
            settings.random_delay_start = settings_data["random_delay_start"]
        if settings_data.get("random_delay_stop", "") != "":
            settings.random_delay_stop = settings_data["random_delay_stop"]
        if settings_data.get("bestbuy_user", "") != "":
            settings.bestbuy_user = settings_data["bestbuy_user"]
        if settings_data.get("bestbuy_pass", "") != "":
            settings.bestbuy_pass = (Encryption().decrypt(settings_data["bestbuy_pass"].encode("utf-8"))).decode("utf-8")
        if settings_data.get("target_user", "") != "":
            settings.target_user = settings_data["target_user"]
        if settings_data.get("target_pass", "") != "":
            settings.target_pass = (Encryption().decrypt(settings_data["target_pass"].encode("utf-8"))).decode("utf-8")
        if settings_data.get("gamestop_user", "") != "":
            settings.gamestop_user = settings_data["gamestop_user"]
        if settings_data.get("gamestop_pass", "") != "":
            settings.gamestop_pass = (Encryption().decrypt(settings_data["gamestop_pass"].encode("utf-8"))).decode("utf-8")
