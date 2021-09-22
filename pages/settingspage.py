import platform
import settings
import sys

from PyQt5 import QtCore, QtGui, QtWidgets

from theming.styles import globalStyles
from utils import return_data, send_text, write_data, Encryption, data_exists, BirdLogger, validate_data, create_twilio_client


def no_abort(a, b, c):
    sys.__excepthook__(a, b, c)


sys.excepthook = no_abort
logger = BirdLogger()


class SettingsPage(QtWidgets.QWidget):
    def __init__(self, parent=None):
        super(SettingsPage, self).__init__(parent)
        self.header_font = self.create_font("Arial", 18)
        self.small_font = self.create_font("Arial", 13)
        self.setup_ui(self)

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

    def get_folder(self):
        self.geckodriver_path = QtWidgets.QFileDialog.getExistingDirectory(self, 'Select Folder')
    
    def send_test_text(self):
        send_text("This is a test text from your PhoenixBot.")

    def setup_ui(self, settingspage):
        self.settingspage = settingspage
        self.geckodriver_path = ''
        self.settingspage.setAttribute(QtCore.Qt.WA_StyledBackground, True)
        self.settingspage.setGeometry(QtCore.QRect(60, 0, 1041, 601))
        self.settingspage.setStyleSheet(
            "QComboBox::drop-down {    border: 0px;}QComboBox::down-arrow {    image: url(images/down_icon.png);    width: 14px;    height: 14px;}QComboBox{    padding: 1px 0px 1px 3px;}QLineEdit:focus {   border: none;   outline: none;}")
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
        self.savesettings_btn.setStyleSheet(
            "color: #FFFFFF;background-color: {};border-radius: 10px;border: 1px solid #2e2d2d;".format(
                globalStyles["primary"]))
        self.savesettings_btn.setText("Save")
        self.savesettings_btn.clicked.connect(self.save_settings)

        self.geckodriver = QtWidgets.QPushButton(self.settings_card)
        # self.getfolder_btn.setGeometry(QtCore.QRect(QtCore.QPoint(250,100), QtCore.QSize(10, 5)))
        self.geckodriver.setGeometry(QtCore.QRect(300, 450, 150, 32))
        self.geckodriver.setFont(self.small_font)
        self.geckodriver.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.geckodriver.setStyleSheet("color: #FFFFFF;background-color: {};border-radius: 10px;border: 1px solid #2e2d2d;".format(globalStyles["primary"]))
        self.geckodriver.setText("GeckoDriver Location")
        self.geckodriver.clicked.connect(self.get_folder)

        

        self.browser_checkbox = self.create_checkbox(QtCore.QRect(30, 90, 300, 20), "Browser Opened")
        self.order_checkbox = self.create_checkbox(QtCore.QRect(30, 120, 221, 20), "Order Placed")
        self.paymentfailed_checkbox = self.create_checkbox(QtCore.QRect(30, 150, 121, 20), "Payment Failed")

        self.general_header = self.create_header(self.settings_card, QtCore.QRect(20, 180, 101, 31), self.header_font,
                                                 "General")
                                                 
        self.headless_checkbox = self.create_checkbox(QtCore.QRect(30, 220, 221, 20), "Run Headless (hidden browser windows)")
        self.onfailed_checkbox = self.create_checkbox(QtCore.QRect(30, 240, 221, 20), "Open browser on payment failed")
        self.bb_ac_beta_checkbox = self.create_checkbox(QtCore.QRect(30, 260, 221, 20), "Enable Best Buy Auto Checkout (BETA)")
        self.buy_one_checkbox = self.create_checkbox(QtCore.QRect(30, 280, 221, 20), "Stop All after success")
        self.dont_buy_checkbox = self.create_checkbox(QtCore.QRect(30, 300, 400, 20),
                                                      "Don't actually buy items. (Used for dev and testing)")
        self.random_delay_start = self.create_edit(self.settings_card, QtCore.QRect(30, 330, 235, 20),
                                                   self.small_font, "Random Start Delay (Default is 10ms)")
        self.random_delay_stop = self.create_edit(self.settings_card, QtCore.QRect(30, 360, 235, 20),
                                                  self.small_font, "Random Stop Delay (Default is 40ms)")
        self.proxies_header = self.create_header(self.settingspage, QtCore.QRect(30, 10, 81, 31),
                                                 self.create_font("Arial", 22), "Settings")
        self.bestbuy_user_edit = self.create_edit(self.settings_card, QtCore.QRect(300, 330, 235, 20),
                                                  self.small_font, "Bestbuy.com Username (Email)")
        self.bestbuy_pass_edit = self.create_edit(self.settings_card, QtCore.QRect(300, 360, 235, 20),
                                                  self.small_font, "Bestbuy.com Password")
        self.target_user_edit = self.create_edit(self.settings_card, QtCore.QRect(30, 390, 235, 20),
                                                 self.small_font, "Target.com Username (Email/Cell #)")
        self.target_pass_edit = self.create_edit(self.settings_card, QtCore.QRect(30, 415, 235, 20),
                                                 self.small_font, "Target.com Password")
        self.gamestop_user_edit = self.create_edit(self.settings_card, QtCore.QRect(300, 390, 235, 20),
                                                   self.small_font, "Gamestop.com Username (Email)")
        self.gamestop_pass_edit = self.create_edit(self.settings_card, QtCore.QRect(300, 415, 235, 20),
                                                   self.small_font, "Gamestop.com Password")  

        # Twilio stuff
        self.twilio_auth_token_edit = self.create_edit(self.settings_card, QtCore.QRect(600, 50, 235, 20),
                                                   self.small_font, "Twilio Auth Token")
        self.twilio_sid_edit = self.create_edit(self.settings_card, QtCore.QRect(600, 75, 235, 20),
                                                   self.small_font, "Twilio SID")
        self.toNumber_edit = self.create_edit(self.settings_card, QtCore.QRect(600, 100, 235, 20),
                                                   self.small_font, "To Number")
        self.fromNumber_edit = self.create_edit(self.settings_card, QtCore.QRect(600, 125, 235, 20),
                                                   self.small_font, "From Number")
        self.text_on_error_checkbox = self.create_checkbox(QtCore.QRect(600, 150, 400, 20), "Send Text on Error")
        self.text_on_success_checkbox = self.create_checkbox(QtCore.QRect(600, 175, 400, 20), "Send Text on Success")
        self.text_on_stock_checkbox = self.create_checkbox(QtCore.QRect(600, 200, 400, 20), "Send Text on Stock Alert")

        # Audio stuff
        self.audio_on_error_checkbox = self.create_checkbox(QtCore.QRect(600, 225, 400, 20), "Audio Alert on Error")
        self.audio_on_success_checkbox = self.create_checkbox(QtCore.QRect(600, 250, 400, 20), "Audio Alert on Success")
        self.audio_on_stock_checkbox = self.create_checkbox(QtCore.QRect(600, 275, 400, 20), "Audio Alert on Stock")

        self.testtext_btn = QtWidgets.QPushButton(self.settings_card)
        self.testtext_btn.setGeometry(QtCore.QRect(600, 325, 86, 32))
        self.testtext_btn.setFont(self.small_font)
        self.testtext_btn.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.testtext_btn.setStyleSheet(
            "color: #FFFFFF;background-color: {};border-radius: 10px;border: 1px solid #2e2d2d;".format(
                globalStyles["primary"]))
        self.testtext_btn.setText("Send Test Text")
        self.testtext_btn.clicked.connect(self.send_test_text)

        self.set_data()
        QtCore.QMetaObject.connectSlotsByName(settingspage)

    def set_data(self):

        settings_default = return_data("./data/settings_default.json")
        if data_exists("./data/settings.json"):
            settings = return_data("./data/settings.json")
        else:
            logger.alt("Set-Settings-Data", "No existing settings found to be parsed, creating new from default.")
            write_data("./data/settings.json", settings_default)
            settings = return_data("./data/settings.json")

        settings = validate_data(settings, settings_default)
        # add missing settings to user specific setting file just to be sure
        write_data("./data/settings.json", settings)

        self.webhook_edit.setText(settings["webhook"])
        if settings["webhookonbrowser"]:
            self.browser_checkbox.setChecked(True)
        if settings["webhookonorder"]:
            self.order_checkbox.setChecked(True)
        if settings["webhookonfailed"]:
            self.paymentfailed_checkbox.setChecked(True)
        if settings["browseronfailed"]:
            self.onfailed_checkbox.setChecked(True)
        if settings["runheadless"]:
            self.headless_checkbox.setChecked(True)
        if settings["bb_ac_beta"]:
            self.bb_ac_beta_checkbox.setChecked(True)
        if settings['onlybuyone']:
            self.buy_one_checkbox.setChecked(True)
        if settings['dont_buy']:
            self.dont_buy_checkbox.setChecked(True)
        if settings['random_delay_start']:
            self.random_delay_start.setText(settings["random_delay_start"])
        if settings['random_delay_stop']:
            self.random_delay_stop.setText(settings["random_delay_stop"])

        self.geckodriver_path = settings["geckodriver"]

        # try:
        #     self.geckodriver.setText(settings["geckodriver"])
        # except:
        #     self.geckodriver.setText("")

        try:
            self.bestbuy_user_edit.setText(settings["bestbuy_user"])
        except:
            self.bestbuy_user_edit.setText("")

        try:
            self.bestbuy_pass_edit.setText(
                (Encryption().decrypt(settings["bestbuy_pass"].encode("utf-8"))).decode("utf-8"))
        except:
            self.bestbuy_pass_edit.setText("")

        try:
            self.target_user_edit.setText(settings["target_user"])
        except:
            self.target_user_edit.setText("")

        try:
            self.target_pass_edit.setText(
                (Encryption().decrypt(settings["target_pass"].encode("utf-8"))).decode("utf-8"))
        except:
            self.target_pass_edit.setText("")

        try:
            self.gamestop_user_edit.setText(settings["gamestop_user"])
        except:
            self.gamestop_user_edit.setText("")

        try:
            self.gamestop_pass_edit.setText(
                (Encryption().decrypt(settings["gamestop_pass"].encode("utf-8"))).decode("utf-8"))
        except:
            self.gamestop_pass_edit.setText("")

        # Twilio Settings
        try:
            self.twilio_auth_token_edit.setText(
                (Encryption().decrypt(settings["twilio_auth_token"].encode("utf-8"))).decode("utf-8"))
        except:
            self.twilio_auth_token_edit.setText("")
        
        try:
            self.twilio_sid_edit.setText(
                (Encryption().decrypt(settings["twilio_sid"].encode("utf-8"))).decode("utf-8"))
        except:
            self.twilio_sid_edit.setText("")

        try:
            self.toNumber_edit.setText(
                (Encryption().decrypt(settings["toNumber"].encode("utf-8"))).decode("utf-8"))
        except:
            self.toNumber_edit.setText("")
            
        try:
            self.fromNumber_edit.setText(
                (Encryption().decrypt(settings["fromNumber"].encode("utf-8"))).decode("utf-8"))
        except:
            self.fromNumber_edit.setText("")

        if settings['text_on_error']:
            self.text_on_error_checkbox.setChecked(settings["text_on_error"])
            
        if settings['text_on_success']:
            self.text_on_success_checkbox.setChecked(settings["text_on_success"])

        if settings['text_on_stock']:
            self.text_on_stock_checkbox.setChecked(settings["text_on_stock"])

        # Audio Settings
        if settings['audio_on_error']:
            self.audio_on_error_checkbox.setChecked(settings["audio_on_error"])
        if settings['audio_on_success']:
            self.audio_on_success_checkbox.setChecked(settings["audio_on_success"])
        if settings['audio_on_stock']:
            self.audio_on_stock_checkbox.setChecked(settings["audio_on_stock"])

        self.update_settings(settings)

    def save_settings(self):
        print(f"Saving path: {self.geckodriver_path}")
        settings = {"webhook":            self.webhook_edit.text(),
                    "webhookonbrowser":   self.browser_checkbox.isChecked(),
                    "webhookonorder":     self.order_checkbox.isChecked(),
                    "webhookonfailed":    self.paymentfailed_checkbox.isChecked(),
                    "browseronfailed":    self.onfailed_checkbox.isChecked(),
                    "runheadless":        self.headless_checkbox.isChecked(),
                    "bb_ac_beta":         self.bb_ac_beta_checkbox.isChecked(),
                    "onlybuyone":         self.buy_one_checkbox.isChecked(),
                    "dont_buy":           self.dont_buy_checkbox.isChecked(),
                    "random_delay_start": self.random_delay_start.text(),
                    "random_delay_stop": self.random_delay_stop.text(),
                    "bestbuy_user": self.bestbuy_user_edit.text(),
                    "bestbuy_pass": Encryption().encrypt(self.bestbuy_pass_edit.text()).decode("utf-8"),
                    "target_user": self.target_user_edit.text(),
                    "target_pass": Encryption().encrypt(self.target_pass_edit.text()).decode("utf-8"),
                    "gamestop_user": self.gamestop_user_edit.text(),
                    "gamestop_pass": Encryption().encrypt(self.gamestop_pass_edit.text()).decode("utf-8"),
                    "geckodriver" : self.geckodriver_path,
                    "twilio_auth_token" : Encryption().encrypt(self.twilio_auth_token_edit.text()).decode('utf-8'),
                    "twilio_sid" : Encryption().encrypt(self.twilio_sid_edit.text()).decode('utf-8'),
                    "toNumber" : Encryption().encrypt(self.toNumber_edit.text()).decode('utf-8'),
                    "fromNumber" : Encryption().encrypt(self.fromNumber_edit.text()).decode('utf-8'),
                    "text_on_error":self.text_on_error_checkbox.isChecked(),
                    "text_on_success":self.text_on_success_checkbox.isChecked(),
                    "text_on_stock":self.text_on_stock_checkbox.isChecked(),
                    "audio_on_error":self.audio_on_error_checkbox.isChecked(),
                    "audio_on_success":self.audio_on_success_checkbox.isChecked(),
                    "audio_on_stock":self.audio_on_stock_checkbox.isChecked()
                    }

        write_data("./data/settings.json", settings)
        self.update_settings(settings)
        QtWidgets.QMessageBox.information(self, "Phoenix Bot", "Saved Settings")

    def update_settings(self, settings_data):
        global \
            webhook, \
            webhook_on_browser, \
            webhook_on_order, \
            webhook_on_failed, \
            browser_on_failed, \
            run_headless, \
            bb_ac_beta, \
            buy_one, \
            dont_buy, \
            random_delay_start, \
            random_delay_stop, \
            target_user, \
            target_pass, \
            gamestop_user, \
            gamestop_pass, \
            geckodriver, \
            twilio_auth_token, \
            twilio_sid, \
            toNumber, \
            fromNumber, \
            text_on_error, \
            text_on_success, \
            text_on_stock, \
            audio_on_error, \
            audio_on_success, \
            audio_on_stock

        settings.webhook = settings_data["webhook"]
        settings.webhook_on_browser = settings_data["webhookonbrowser"]
        settings.webhook_on_order = settings_data["webhookonorder"]
        settings.webhook_on_failed = settings_data["webhookonfailed"]
        settings.browser_on_failed = settings_data["browseronfailed"]
        settings.run_headless = settings_data["runheadless"]
        settings.bb_ac_beta = settings_data["bb_ac_beta"]
        settings.buy_one = settings_data["onlybuyone"]
        settings.dont_buy = settings_data["dont_buy"]
        settings.text_on_error = settings_data["text_on_error"]
        settings.text_on_success = settings_data["text_on_success"]
        settings.text_on_stock = settings_data["text_on_stock"]
        settings.audio_on_error = settings_data["audio_on_error"]
        settings.audio_on_success = settings_data["audio_on_success"]
        settings.audio_on_stock = settings_data["audio_on_stock"]

        if settings_data.get("random_delay_start", "") != "":
            settings.random_delay_start = settings_data["random_delay_start"]
        if settings_data.get("random_delay_stop", "") != "":
            settings.random_delay_stop = settings_data["random_delay_stop"]
        if settings_data.get("bestbuy_user", "") != "":
            settings.bestbuy_user = settings_data["bestbuy_user"]
        if settings_data.get("bestbuy_pass", "") != "":
            settings.bestbuy_pass = (Encryption().decrypt(settings_data["bestbuy_pass"].encode("utf-8"))).decode(
                "utf-8")
        if settings_data.get("target_user", "") != "":
            settings.target_user = settings_data["target_user"]
        if settings_data.get("target_pass", "") != "":
            settings.target_pass = (Encryption().decrypt(settings_data["target_pass"].encode("utf-8"))).decode("utf-8")
        if settings_data.get("gamestop_user", "") != "":
            settings.gamestop_user = settings_data["gamestop_user"]
        if settings_data.get("gamestop_pass", "") != "":
            settings.gamestop_pass = (Encryption().decrypt(settings_data["gamestop_pass"].encode("utf-8"))).decode(
                "utf-8")
        if settings_data.get("geckodriver","") != "":
            settings.geckodriver_path = settings_data["geckodriver"]

        # Twilio
        if settings_data.get("twilio_auth_token","") != "":
            settings.twilio_auth_token = (Encryption().decrypt(settings_data["twilio_auth_token"].encode("utf-8"))).decode("utf-8")
        
        if settings_data.get("twilio_sid","") != "":
            settings.twilio_sid = (Encryption().decrypt(settings_data["twilio_sid"].encode("utf-8"))).decode("utf-8")
            
        if settings_data.get("toNumber","") != "":
            settings.toNumber = (Encryption().decrypt(settings_data["toNumber"].encode("utf-8"))).decode("utf-8")

        if settings_data.get("fromNumber","") != "":
            settings.fromNumber = (Encryption().decrypt(settings_data["fromNumber"].encode("utf-8"))).decode("utf-8")
        
        settings.twclient = create_twilio_client()