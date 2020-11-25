from PyQt5 import QtCore, QtGui, QtWidgets
from utils import return_data,write_data,get_profile,Encryption
import sys,platform
def no_abort(a, b, c):
    sys.__excepthook__(a, b, c)
sys.excepthook = no_abort

class ProfilesPage(QtWidgets.QWidget):

    def __init__(self,parent=None):
        super(ProfilesPage, self).__init__(parent)
        self.setupUi(self)




    def setupUi(self, profilespage):
        self.profilespage = profilespage
        self.profilespage.setAttribute(QtCore.Qt.WA_StyledBackground, True)
        self.profilespage.setGeometry(QtCore.QRect(60, 0, 1041, 601))
        self.profilespage.setStyleSheet("QComboBox::drop-down {    border: 0px;}QComboBox::down-arrow {    image: url(:/images/down_icon.png);    width: 14px;    height: 14px;}QComboBox{    padding: 1px 0px 1px 3px;}QLineEdit:focus {   border: none;   outline: none;}")
        self.shipping_card = QtWidgets.QWidget(self.profilespage)
        self.shipping_card.setGeometry(QtCore.QRect(30, 70, 313, 501))
        self.shipping_card.setStyleSheet("background-color: #232323;border-radius: 20px;border: 1px solid #2e2d2d;")
        self.shipping_fname_edit = QtWidgets.QLineEdit(self.shipping_card)
        self.shipping_fname_edit.setAttribute(QtCore.Qt.WA_MacShowFocusRect, 0)
        self.shipping_fname_edit.setGeometry(QtCore.QRect(30, 50, 113, 21))
        font = QtGui.QFont()
        font.setPointSize(13) if platform.system() == "Darwin" else font.setPointSize(13*.75)
        font.setFamily("Arial")
        self.shipping_fname_edit.setFont(font)
        self.shipping_fname_edit.setStyleSheet("outline: 0;border: 1px solid #5D43FB;border-width: 0 0 2px;color: rgb(234, 239, 239);")
        self.shipping_fname_edit.setPlaceholderText("First Name")
        self.shipping_header = QtWidgets.QLabel(self.shipping_card)
        self.shipping_header.setGeometry(QtCore.QRect(20, 10, 81, 31))
        font.setPointSize(18) if platform.system() == "Darwin" else font.setPointSize(18*.75)
        font.setBold(False)
        font.setWeight(50)
        self.shipping_header.setFont(font)
        self.shipping_header.setStyleSheet("color: rgb(212, 214, 214);border:  none;")
        self.shipping_header.setText("Shipping")
        self.shipping_lname_edit = QtWidgets.QLineEdit(self.shipping_card)
        self.shipping_lname_edit.setAttribute(QtCore.Qt.WA_MacShowFocusRect, 0)
        self.shipping_lname_edit.setGeometry(QtCore.QRect(170, 50, 113, 21))
        font = QtGui.QFont()
        font.setPointSize(13) if platform.system() == "Darwin" else font.setPointSize(13*.75)
        font.setFamily("Arial")
        self.shipping_lname_edit.setFont(font)
        self.shipping_lname_edit.setStyleSheet("outline: 0;border: 1px solid #5D43FB;border-width: 0 0 2px;color: rgb(234, 239, 239);")
        self.shipping_lname_edit.setPlaceholderText("Last Name")
        self.shipping_email_edit = QtWidgets.QLineEdit(self.shipping_card)
        self.shipping_email_edit.setAttribute(QtCore.Qt.WA_MacShowFocusRect, 0)
        self.shipping_email_edit.setGeometry(QtCore.QRect(30, 100, 253, 21))
        self.shipping_email_edit.setFont(font)
        self.shipping_email_edit.setStyleSheet("outline: 0;border: 1px solid #5D43FB;border-width: 0 0 2px;color: rgb(234, 239, 239);")
        self.shipping_email_edit.setPlaceholderText("Email Address")
        self.shipping_phone_edit = QtWidgets.QLineEdit(self.shipping_card)
        self.shipping_phone_edit.setAttribute(QtCore.Qt.WA_MacShowFocusRect, 0)
        self.shipping_phone_edit.setGeometry(QtCore.QRect(30, 150, 253, 21))
        self.shipping_phone_edit.setFont(font)
        self.shipping_phone_edit.setStyleSheet("outline: 0;border: 1px solid #5D43FB;border-width: 0 0 2px;color: rgb(234, 239, 239);")
        self.shipping_phone_edit.setPlaceholderText("Phone Number")
        self.shipping_address1_edit = QtWidgets.QLineEdit(self.shipping_card)
        self.shipping_address1_edit.setAttribute(QtCore.Qt.WA_MacShowFocusRect, 0)
        self.shipping_address1_edit.setGeometry(QtCore.QRect(30, 200, 151, 21))
        self.shipping_address1_edit.setFont(font)
        self.shipping_address1_edit.setStyleSheet("outline: 0;border: 1px solid #5D43FB;border-width: 0 0 2px;color: rgb(234, 239, 239);")
        self.shipping_address1_edit.setPlaceholderText("Address 1")
        self.shipping_address2_edit = QtWidgets.QLineEdit(self.shipping_card)
        self.shipping_address2_edit.setAttribute(QtCore.Qt.WA_MacShowFocusRect, 0)
        self.shipping_address2_edit.setGeometry(QtCore.QRect(208, 200, 75, 21))
        self.shipping_address2_edit.setFont(font)
        self.shipping_address2_edit.setStyleSheet("outline: 0;border: 1px solid #5D43FB;border-width: 0 0 2px;color: rgb(234, 239, 239);")
        self.shipping_address2_edit.setPlaceholderText("Address 2")
        self.shipping_city_edit = QtWidgets.QLineEdit(self.shipping_card)
        self.shipping_city_edit.setAttribute(QtCore.Qt.WA_MacShowFocusRect, 0)
        self.shipping_city_edit.setGeometry(QtCore.QRect(30, 250, 151, 21))
        self.shipping_city_edit.setFont(font)
        self.shipping_city_edit.setStyleSheet("outline: 0;border: 1px solid #5D43FB;border-width: 0 0 2px;color: rgb(234, 239, 239);")
        self.shipping_city_edit.setPlaceholderText("City")
        self.shipping_zipcode_edit = QtWidgets.QLineEdit(self.shipping_card)
        self.shipping_zipcode_edit.setAttribute(QtCore.Qt.WA_MacShowFocusRect, 0)
        self.shipping_zipcode_edit.setGeometry(QtCore.QRect(208, 250, 75, 21))
        self.shipping_zipcode_edit.setFont(font)
        self.shipping_zipcode_edit.setStyleSheet("outline: 0;border: 1px solid #5D43FB;border-width: 0 0 2px;color: rgb(234, 239, 239);")
        self.shipping_zipcode_edit.setPlaceholderText("Zip Code")
        self.shipping_state_box = QtWidgets.QComboBox(self.shipping_card)
        self.shipping_state_box.setGeometry(QtCore.QRect(30, 300, 253, 26))
        self.shipping_state_box.setFont(font)
        self.shipping_state_box.setStyleSheet("outline: 0;border: 1px solid #5D43FB;border-width: 0 0 2px;color: rgb(234, 239, 239);")
        self.shipping_state_box.addItem("State")
        self.shipping_country_box = QtWidgets.QComboBox(self.shipping_card)
        self.shipping_country_box.setGeometry(QtCore.QRect(30, 360, 253, 26))
        self.shipping_country_box.setFont(font)
        self.shipping_country_box.setStyleSheet("outline: 0;border: 1px solid #5D43FB;border-width: 0 0 2px;color: rgb(234, 239, 239);")
        self.shipping_country_box.addItem("Country")
        self.shipping_country_box.addItem("United States")
        self.shipping_country_box.addItem("Canada")
        self.profiles_header = QtWidgets.QLabel(self.profilespage)
        self.profiles_header.setGeometry(QtCore.QRect(30, 10, 81, 31))
        font.setPointSize(22) if platform.system() == "Darwin" else font.setPointSize(22*.75)
        font.setBold(False)
        font.setWeight(50)
        self.profiles_header.setFont(font)
        self.profiles_header.setStyleSheet("color: rgb(234, 239, 239);")
        self.profiles_header.setText("Profiles")
        self.billing_card = QtWidgets.QWidget(self.profilespage)
        self.billing_card.setGeometry(QtCore.QRect(365, 70, 313, 501))
        self.billing_card.setStyleSheet("background-color: #232323;border-radius: 20px;border: 1px solid #2e2d2d;")
        self.billing_fname_edit = QtWidgets.QLineEdit(self.billing_card)
        self.billing_fname_edit.setAttribute(QtCore.Qt.WA_MacShowFocusRect, 0)
        self.billing_fname_edit.setGeometry(QtCore.QRect(30, 50, 113, 21))
        font = QtGui.QFont()
        font.setPointSize(13) if platform.system() == "Darwin" else font.setPointSize(13*.75)
        font.setFamily("Arial")
        self.billing_fname_edit.setFont(font)
        self.billing_fname_edit.setStyleSheet("outline: 0;border: 1px solid #5D43FB;border-width: 0 0 2px;color: rgb(234, 239, 239);")
        self.billing_fname_edit.setPlaceholderText("First Name")
        self.billing_header = QtWidgets.QLabel(self.billing_card)
        self.billing_header.setGeometry(QtCore.QRect(20, 10, 51, 31))
        font.setPointSize(18) if platform.system() == "Darwin" else font.setPointSize(18*.75)
        font.setBold(False)
        font.setWeight(50)
        self.billing_header.setFont(font)
        self.billing_header.setStyleSheet("color: rgb(212, 214, 214);border:  none;")
        self.billing_header.setText("Billing")
        font = QtGui.QFont()
        font.setPointSize(13) if platform.system() == "Darwin" else font.setPointSize(13*.75)
        font.setFamily("Arial")
        self.billing_lname_edit = QtWidgets.QLineEdit(self.billing_card)
        self.billing_lname_edit.setAttribute(QtCore.Qt.WA_MacShowFocusRect, 0)
        self.billing_lname_edit.setGeometry(QtCore.QRect(170, 50, 113, 21))
        self.billing_lname_edit.setFont(font)
        self.billing_lname_edit.setStyleSheet("outline: 0;border: 1px solid #5D43FB;border-width: 0 0 2px;color: rgb(234, 239, 239);")
        self.billing_lname_edit.setPlaceholderText("Last Name")
        self.billing_email_edit = QtWidgets.QLineEdit(self.billing_card)
        self.billing_email_edit.setAttribute(QtCore.Qt.WA_MacShowFocusRect, 0)
        self.billing_email_edit.setGeometry(QtCore.QRect(30, 100, 253, 21))
        self.billing_email_edit.setFont(font)
        self.billing_email_edit.setStyleSheet("outline: 0;border: 1px solid #5D43FB;border-width: 0 0 2px;color: rgb(234, 239, 239);")
        self.billing_email_edit.setPlaceholderText("Email Address")
        self.billing_phone_edit = QtWidgets.QLineEdit(self.billing_card)
        self.billing_phone_edit.setAttribute(QtCore.Qt.WA_MacShowFocusRect, 0)
        self.billing_phone_edit.setGeometry(QtCore.QRect(30, 150, 253, 21))
        self.billing_phone_edit.setFont(font)
        self.billing_phone_edit.setStyleSheet("outline: 0;border: 1px solid #5D43FB;border-width: 0 0 2px;color: rgb(234, 239, 239);")
        self.billing_phone_edit.setPlaceholderText("Phone Number")
        self.billing_address1_edit = QtWidgets.QLineEdit(self.billing_card)
        self.billing_address1_edit.setAttribute(QtCore.Qt.WA_MacShowFocusRect, 0)
        self.billing_address1_edit.setGeometry(QtCore.QRect(30, 200, 151, 21))
        self.billing_address1_edit.setFont(font)
        self.billing_address1_edit.setStyleSheet("outline: 0;border: 1px solid #5D43FB;border-width: 0 0 2px;color: rgb(234, 239, 239);")
        self.billing_address1_edit.setPlaceholderText("Address 1")
        self.billing_address2_edit = QtWidgets.QLineEdit(self.billing_card)
        self.billing_address2_edit.setAttribute(QtCore.Qt.WA_MacShowFocusRect, 0)
        self.billing_address2_edit.setGeometry(QtCore.QRect(208, 200, 75, 21))
        self.billing_address2_edit.setFont(font)
        self.billing_address2_edit.setStyleSheet("outline: 0;border: 1px solid #5D43FB;border-width: 0 0 2px;color: rgb(234, 239, 239);")
        self.billing_address2_edit.setPlaceholderText("Address 2")
        self.billing_city_edit = QtWidgets.QLineEdit(self.billing_card)
        self.billing_city_edit.setAttribute(QtCore.Qt.WA_MacShowFocusRect, 0)
        self.billing_city_edit.setGeometry(QtCore.QRect(30, 250, 151, 21))
        self.billing_city_edit.setFont(font)
        self.billing_city_edit.setStyleSheet("outline: 0;border: 1px solid #5D43FB;border-width: 0 0 2px;color: rgb(234, 239, 239);")
        self.billing_city_edit.setPlaceholderText("City")
        self.billing_zipcode_edit = QtWidgets.QLineEdit(self.billing_card)
        self.billing_zipcode_edit.setAttribute(QtCore.Qt.WA_MacShowFocusRect, 0)
        self.billing_zipcode_edit.setGeometry(QtCore.QRect(208, 250, 75, 21))
        self.billing_zipcode_edit.setFont(font)
        self.billing_zipcode_edit.setStyleSheet("outline: 0;border: 1px solid #5D43FB;border-width: 0 0 2px;color: rgb(234, 239, 239);")
        self.billing_zipcode_edit.setPlaceholderText("Zip Code")
        self.billing_state_box = QtWidgets.QComboBox(self.billing_card)
        self.billing_state_box.setGeometry(QtCore.QRect(30, 300, 253, 26))
        self.billing_state_box.setFont(font)
        self.billing_state_box.setStyleSheet("outline: 0;border: 1px solid #5D43FB;border-width: 0 0 2px;color: rgb(234, 239, 239);")
        self.billing_state_box.addItem("State")
        self.billing_country_box = QtWidgets.QComboBox(self.billing_card)
        self.billing_country_box.setGeometry(QtCore.QRect(30, 360, 253, 26))
        self.billing_country_box.setFont(font)
        self.billing_country_box.setStyleSheet("outline: 0;border: 1px solid #5D43FB;border-width: 0 0 2px;color: rgb(234, 239, 239);")
        self.billing_country_box.addItem("Country")
        self.billing_country_box.addItem("United States")
        self.billing_country_box.addItem("Canada")
        self.same_shipping_checkbox = QtWidgets.QCheckBox(self.billing_card)
        self.same_shipping_checkbox.setGeometry(QtCore.QRect(160, 16, 131, 20))
        self.same_shipping_checkbox.setFont(font)
        self.same_shipping_checkbox.setStyleSheet("border:none;color: rgb(234, 239, 239);")
        self.same_shipping_checkbox.setText("Same as shipping")
        self.same_shipping_checkbox.stateChanged.connect(self.same_shipping_checkbox_clicked)
        self.tasks_card_3 = QtWidgets.QWidget(self.profilespage)
        self.tasks_card_3.setGeometry(QtCore.QRect(700, 70, 313, 501))
        self.tasks_card_3.setStyleSheet("background-color: #232323;border-radius: 20px;border: 1px solid #2e2d2d;")
        self.payment_header = QtWidgets.QLabel(self.tasks_card_3)
        self.payment_header.setGeometry(QtCore.QRect(20, 10, 81, 31))
        font.setPointSize(18) if platform.system() == "Darwin" else font.setPointSize(18*.75)
        font.setBold(False)
        font.setWeight(50)
        self.payment_header.setFont(font)
        self.payment_header.setStyleSheet("color: rgb(212, 214, 214);border:  none;")
        self.payment_header.setText("Payment")
        self.cardnumber_edit = QtWidgets.QLineEdit(self.tasks_card_3)
        self.cardnumber_edit.setAttribute(QtCore.Qt.WA_MacShowFocusRect, 0)
        self.cardnumber_edit.setGeometry(QtCore.QRect(30, 100, 151, 21))
        font = QtGui.QFont()
        font.setFamily("Arial")
        self.cardnumber_edit.setFont(font)
        self.cardnumber_edit.setStyleSheet("outline: 0;border: 1px solid #5D43FB;border-width: 0 0 2px;color: rgb(234, 239, 239);")
        self.cardnumber_edit.setPlaceholderText("Card Number")
        self.cardcvv_edit = QtWidgets.QLineEdit(self.tasks_card_3)
        self.cardcvv_edit.setAttribute(QtCore.Qt.WA_MacShowFocusRect, 0)
        self.cardcvv_edit.setGeometry(QtCore.QRect(208, 100, 75, 21))
        self.cardcvv_edit.setFont(font)
        self.cardcvv_edit.setStyleSheet("outline: 0;border: 1px solid #5D43FB;border-width: 0 0 2px;color: rgb(234, 239, 239);")
        self.cardcvv_edit.setPlaceholderText("CVV")
        self.save_btn = QtWidgets.QPushButton(self.tasks_card_3)
        self.save_btn.setGeometry(QtCore.QRect(70, 300, 86, 32))
        self.save_btn.setFont(font)
        self.save_btn.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.save_btn.setStyleSheet("color: #FFFFFF;background-color: #5D43FB;border-radius: 10px;border: 1px solid #2e2d2d;")
        self.save_btn.setText("Save")  
        self.save_btn.clicked.connect(self.save_profile)      
        self.cardtype_box = QtWidgets.QComboBox(self.tasks_card_3)
        self.cardtype_box.setGeometry(QtCore.QRect(30, 50, 253, 26))
        self.cardtype_box.setFont(font)
        self.cardtype_box.setStyleSheet("outline: 0;border: 1px solid #5D43FB;border-width: 0 0 2px;color: rgb(234, 239, 239);")
        self.cardtype_box.addItem("Card Type")
        self.cardmonth_box = QtWidgets.QComboBox(self.tasks_card_3)
        self.cardmonth_box.setGeometry(QtCore.QRect(30, 150, 113, 26))
        self.cardmonth_box.setFont(font)
        self.cardmonth_box.setStyleSheet("outline: 0;border: 1px solid #5D43FB;border-width: 0 0 2px;color: rgb(234, 239, 239);")
        self.cardmonth_box.addItem("Month")
        self.cardyear_box = QtWidgets.QComboBox(self.tasks_card_3)
        self.cardyear_box.setGeometry(QtCore.QRect(170, 150, 113, 26))
        self.cardyear_box.setFont(font)
        self.cardyear_box.setStyleSheet("outline: 0;border: 1px solid #5D43FB;border-width: 0 0 2px;color: rgb(234, 239, 239);")
        self.cardyear_box.addItem("Year")
        self.profile_header = QtWidgets.QLabel(self.tasks_card_3)
        self.profile_header.setGeometry(QtCore.QRect(20, 220, 81, 31))
        font.setPointSize(18) if platform.system() == "Darwin" else font.setPointSize(18*.75)
        font.setBold(False)
        font.setWeight(50)
        self.profile_header.setFont(font)
        self.profile_header.setStyleSheet("color: rgb(212, 214, 214);border:  none;")
        self.profile_header.setText("Profile")
        self.profilename_edit = QtWidgets.QLineEdit(self.tasks_card_3)
        self.profilename_edit.setAttribute(QtCore.Qt.WA_MacShowFocusRect, 0)
        self.profilename_edit.setGeometry(QtCore.QRect(30, 260, 253, 21))
        font = QtGui.QFont()
        font.setPointSize(13) if platform.system() == "Darwin" else font.setPointSize(13*.75)
        font.setFamily("Arial")
        self.profilename_edit.setFont(font)
        self.profilename_edit.setStyleSheet("outline: 0;border: 1px solid #5D43FB;border-width: 0 0 2px;color: rgb(234, 239, 239);")
        self.profilename_edit.setPlaceholderText("Profile Name")
        self.loadprofile_box = QtWidgets.QComboBox(self.tasks_card_3)
        self.loadprofile_box.setGeometry(QtCore.QRect(30, 350, 253, 26))
        self.loadprofile_box.setFont(font)
        self.loadprofile_box.setStyleSheet("outline: 0;border: 1px solid #5D43FB;border-width: 0 0 2px;color: rgb(234, 239, 239);")
        self.loadprofile_box.addItem("Load Profile")
        self.loadprofile_box.currentTextChanged.connect(self.load_profile)
        self.delete_btn = QtWidgets.QPushButton(self.tasks_card_3)
        self.delete_btn.setGeometry(QtCore.QRect(167, 300, 86, 32))
        self.delete_btn.setFont(font)
        self.delete_btn.setCursor(QtGui.QCursor(QtCore.Qt.PointingHandCursor))
        self.delete_btn.setStyleSheet("color: #FFFFFF;background-color: #5D43FB;border-radius: 10px;border: 1px solid #2e2d2d;")
        self.delete_btn.setText("Delete")
        self.delete_btn.clicked.connect(self.delete_profile)
        self.set_data()
        QtCore.QMetaObject.connectSlotsByName(profilespage)

    def updateShippingStateBox(self, newValue):
         self.shipping_state_box.clear()
         if newValue == "United States":
             for state in ["AL", "AK", "AS", "AZ", "AR", "CA", "CO", "CT", "DE", "DC", "FM", "FL", "GA", "GU", "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MH", "MD", "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ", "NM", "NY", "NC", "ND", "MP", "OH", "OK", "OR", "PW", "PA", "PR", "RI", "SC", "SD", "TN", "TX", "UT", "VT", "VI", "VA", "WA", "WV", "WI", "WY"]:
                 self.shipping_state_box.addItem(state)
         elif newValue == "Canada":
             for state in ["AB", "BC",  "MB", "NB", "NL", "NS", "NT", "NU",  "ON", "PE", "QC", "SK", "YT"]:
                 self.shipping_state_box.addItem(state)

    def updateBillingStateBox(self, newValue):
         self.billing_state_box.clear()
         if newValue == "United States":
             for state in ["AL", "AK", "AS", "AZ", "AR", "CA", "CO", "CT", "DE", "DC", "FM", "FL", "GA", "GU", "HI", "ID", "IL", "IN", "IA", "KS", "KY", "LA", "ME", "MH", "MD", "MA", "MI", "MN", "MS", "MO", "MT", "NE", "NV", "NH", "NJ", "NM", "NY", "NC", "ND", "MP", "OH", "OK", "OR", "PW", "PA", "PR", "RI", "SC", "SD", "TN", "TX", "UT", "VT", "VI", "VA", "WA", "WV", "WI", "WY"]:
                 self.billing_state_box.addItem(state)
         elif newValue == "Canada":
             for state in ["AB", "BC",  "MB", "NB", "NL", "NS", "NT", "NU",  "ON", "PE", "QC", "SK", "YT"]:
                 self.billing_state_box.addItem(state)
    
    def set_data(self):
        self.shipping_state_box.clear()
        self.billing_state_box.clear()
        self.shipping_country_box.currentTextChanged.connect(self.updateShippingStateBox)
        self.billing_country_box.currentTextChanged.connect(self.updateBillingStateBox)
        for month in range(1,13):
            self.cardmonth_box.addItem(str(month)) if month>9 else self.cardmonth_box.addItem("0"+str(month))
        for year in range(2020,2031):
            self.cardyear_box.addItem(str(year))
        for card_type in ["Visa", "Mastercard", "American Express", "Discover"]:
            self.cardtype_box.addItem(card_type)
        profiles = return_data("./data/profiles.json")
        for profile in profiles:
            profile_name = profile["profile_name"]
            self.loadprofile_box.addItem(profile_name)
            self.parent().parent().createdialog.profile_box.addItem(profile_name)
    
    def same_shipping_checkbox_clicked(self):
        if self.same_shipping_checkbox.isChecked():
            self.billing_country_box.setCurrentIndex(self.billing_country_box.findText(self.shipping_country_box.currentText()))
            self.billing_fname_edit.setText(self.shipping_fname_edit.text())
            self.billing_lname_edit.setText(self.shipping_lname_edit.text())
            self.billing_email_edit.setText(self.shipping_email_edit.text())
            self.billing_phone_edit.setText(self.shipping_phone_edit.text())
            self.billing_address1_edit.setText(self.shipping_address1_edit.text())
            self.billing_address2_edit.setText(self.shipping_address2_edit.text())
            self.billing_city_edit.setText(self.shipping_city_edit.text())
            self.billing_zipcode_edit.setText(self.shipping_zipcode_edit.text())
            self.billing_state_box.setCurrentIndex(self.billing_state_box.findText(self.shipping_state_box.currentText()))
   
    def load_profile(self):
        profile_name = self.loadprofile_box.currentText()
        p = get_profile(profile_name)
        if p is not None:
            self.profilename_edit.setText(p["profile_name"])
            self.shipping_fname_edit.setText(p["shipping_fname"])
            self.shipping_lname_edit.setText(p["shipping_lname"])
            self.shipping_email_edit.setText(p["shipping_email"])
            self.shipping_phone_edit.setText(p["shipping_phone"])
            self.shipping_address1_edit.setText(p["shipping_a1"])
            self.shipping_address2_edit.setText(p["shipping_a2"])
            self.shipping_city_edit.setText(p["shipping_city"])
            self.shipping_zipcode_edit.setText(p["shipping_zipcode"])
            self.shipping_state_box.setCurrentIndex(self.shipping_state_box.findText(p["shipping_state"]))
            self.shipping_country_box.setCurrentIndex(self.shipping_country_box.findText(p["shipping_country"]))
            self.billing_fname_edit.setText(p["billing_fname"])
            self.billing_lname_edit.setText(p["billing_lname"])
            self.billing_email_edit.setText(p["billing_email"])
            self.billing_phone_edit.setText(p["billing_phone"])
            self.billing_address1_edit.setText(p["billing_a1"])
            self.billing_address2_edit.setText(p["billing_a2"])
            self.billing_city_edit.setText(p["billing_city"])
            self.billing_zipcode_edit.setText(p["billing_zipcode"])
            self.billing_state_box.setCurrentIndex(self.billing_state_box.findText(p["billing_state"]))
            self.billing_country_box.setCurrentIndex(self.billing_country_box.findText(p["billing_country"]))
            self.cardnumber_edit.setText(p["card_number"])
            self.cardmonth_box.setCurrentIndex(self.cardmonth_box.findText(p["card_month"]))
            self.cardyear_box.setCurrentIndex(self.cardyear_box.findText(p["card_year"]))
            self.cardtype_box.setCurrentIndex(self.cardtype_box.findText(p["card_type"]))
            self.cardcvv_edit.setText(p["card_cvv"])
        return
    def save_profile(self):
        profile_name = self.profilename_edit.text()
        profile_data={
            "profile_name":profile_name,
            "shipping_fname": self.shipping_fname_edit.text(),
            "shipping_lname": self.shipping_lname_edit.text(),
            "shipping_email": self.shipping_email_edit.text(),
            "shipping_phone": self.shipping_phone_edit.text(),
            "shipping_a1": self.shipping_address1_edit.text(),
            "shipping_a2": self.shipping_address2_edit.text(),
            "shipping_city": self.shipping_city_edit.text(),
            "shipping_zipcode": self.shipping_zipcode_edit.text(),
            "shipping_state": self.shipping_state_box.currentText(),
            "shipping_country": self.shipping_country_box.currentText(),
            "billing_fname": self.billing_fname_edit.text(),
            "billing_lname": self.billing_lname_edit.text(),
            "billing_email": self.billing_email_edit.text(),
            "billing_phone": self.billing_phone_edit.text(),
            "billing_a1": self.billing_address1_edit.text(),
            "billing_a2": self.billing_address2_edit.text(),
            "billing_city": self.billing_city_edit.text(),
            "billing_zipcode": self.billing_zipcode_edit.text(),
            "billing_state": self.billing_state_box.currentText(),
            "billing_country": self.billing_country_box.currentText(),
            "card_number": (Encryption().encrypt(self.cardnumber_edit.text())).decode("utf-8"),
            "card_month": self.cardmonth_box.currentText(),
            "card_year": self.cardyear_box.currentText(),
            "card_type": self.cardtype_box.currentText(),
            "card_cvv": self.cardcvv_edit.text()
        }      
        profiles = return_data("./data/profiles.json")
        for p in profiles:
            if p["profile_name"] == profile_name:
                profiles.remove(p)
                break
        profiles.append(profile_data)
        write_data("./data/profiles.json",profiles)
        if self.loadprofile_box.findText(profile_name) == -1:
            self.loadprofile_box.addItem(profile_name)
            self.parent().parent().createdialog.profile_box.addItem(profile_name)
        QtWidgets.QMessageBox.information(self, "Phoenix Bot", "Saved Profile")
    
    def delete_profile(self):
        profile_name = self.profilename_edit.text()
        profiles = return_data("./data/profiles.json")
        for profile in profiles:
            if profile["profile_name"] == profile_name:
                profiles.remove(profile)
                break
        write_data("./data/profiles.json",profiles)
        self.loadprofile_box.removeItem(self.loadprofile_box.findText(profile_name))
        self.parent().parent().createdialog.profile_box.removeItem(self.parent().parent().createdialog.profile_box.findText(profile_name))

        self.loadprofile_box.setCurrentIndex(0)
        self.profilename_edit.setText("")
        self.profilename_edit.setText("")
        self.shipping_fname_edit.setText("")
        self.shipping_lname_edit.setText("")
        self.shipping_email_edit.setText("")
        self.shipping_phone_edit.setText("")
        self.shipping_address1_edit.setText("")
        self.shipping_address2_edit.setText("")
        self.shipping_city_edit.setText("")
        self.shipping_zipcode_edit.setText("")
        self.shipping_state_box.setCurrentIndex(0)
        self.shipping_country_box.setCurrentIndex(0)
        self.billing_fname_edit.setText("")
        self.billing_lname_edit.setText("")
        self.billing_email_edit.setText("")
        self.billing_phone_edit.setText("")
        self.billing_address1_edit.setText("")
        self.billing_address2_edit.setText("")
        self.billing_city_edit.setText("")
        self.billing_zipcode_edit.setText("")
        self.billing_state_box.setCurrentIndex(0)
        self.billing_country_box.setCurrentIndex(0)
        self.cardnumber_edit.setText("")
        self.cardmonth_box.setCurrentIndex(0)
        self.cardyear_box.setCurrentIndex(0)
        self.cardtype_box.setCurrentIndex(0)
        self.cardcvv_edit.setText("")
        QtWidgets.QMessageBox.information(self, "Phoenix Bot", "Deleted Profile")
