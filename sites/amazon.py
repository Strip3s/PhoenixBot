import json
import secrets
import time
import os
import math
import re
from datetime import datetime
from price_parser import parse_price

from amazoncaptcha import AmazonCaptcha
from chromedriver_py import binary_path  # this will get you the path variable
from furl import furl
from selenium import webdriver
from selenium.common.exceptions import (
    NoSuchElementException,
    SessionNotCreatedException,
    TimeoutException,
)
from selenium.webdriver.common.keys import Keys
from selenium.webdriver.support.ui import WebDriverWait

from utils import selenium_utils
from utils.json_utils import InvalidAutoBuyConfigException
from utils import create_msg
from utils.selenium_utils import options, enable_headless, wait_for_element

# https://github.com/Hari-Nagarajan/nvidia-bot/blob/master/stores/amazon.py

AMAZON_URLS = {
    "BASE_URL": "https://{domain}/",
    "CART_URL": "https://{domain}/gp/aws/cart/add.html",
    "OFFER_URL": "https://{domain}/gp/offer-listing/",
}
CHECKOUT_URL = "https://{domain}/gp/cart/desktop/go-to-checkout.html/ref=ox_sc_proceed?partialCheckoutCart=1&isToBeGiftWrappedBefore=0&proceedToRetailCheckout=Proceed+to+checkout&proceedToCheckout=1&cartInitiateId={cart_id}"

AUTOBUY_CONFIG_PATH = "amazon_config.json"

SIGN_IN_TEXT = [
    "Hello, Sign in",
    "Sign in",
    "Hola, Identifícate",
    "Bonjour, Identifiez-vous",
    "Ciao, Accedi",
    "Hallo, Anmelden",
    "Hallo, Inloggen",
]
SIGN_IN_TITLES = [
    "Amazon Sign In",
    "Amazon Sign-In",
    "Amazon Anmelden",
    "Iniciar sesión en Amazon",
    "Connexion Amazon",
    "Amazon Accedi",
    "Inloggen bij Amazon",
]
CAPTCHA_PAGE_TITLES = ["Robot Check"]
HOME_PAGE_TITLES = [
    "Amazon.com: Online Shopping for Electronics, Apparel, Computers, Books, DVDs & more",
    "AmazonSmile: You shop. Amazon gives.",
    "Amazon.ca: Low Prices – Fast Shipping – Millions of Items",
    "Amazon.co.uk: Low Prices in Electronics, Books, Sports Equipment & more",
    "Amazon.de: Low Prices in Electronics, Books, Sports Equipment & more",
    "Amazon.de: Günstige Preise für Elektronik & Foto, Filme, Musik, Bücher, Games, Spielzeug & mehr",
    "Amazon.es: compra online de electrónica, libros, deporte, hogar, moda y mucho más.",
    "Amazon.de: Günstige Preise für Elektronik & Foto, Filme, Musik, Bücher, Games, Spielzeug & mehr",
    "Amazon.fr : livres, DVD, jeux vidéo, musique, high-tech, informatique, jouets, vêtements, chaussures, sport, bricolage, maison, beauté, puériculture, épicerie et plus encore !",
    "Amazon.it: elettronica, libri, musica, fashion, videogiochi, DVD e tanto altro",
    "Amazon.nl: Groot aanbod, kleine prijzen in o.a. Elektronica, boeken, sport en meer",
]
SHOPING_CART_TITLES = [
    "Amazon.com Shopping Cart",
    "Amazon.ca Shopping Cart",
    "Amazon.co.uk Shopping Basket",
    "Amazon.de Basket",
    "Amazon.de Einkaufswagen",
    "Cesta de compra Amazon.es",
    "Amazon.fr Panier",
    "Carrello Amazon.it",
    "AmazonSmile Shopping Cart",
    "Amazon.nl-winkelwagen",
]
CHECKOUT_TITLES = [
    "Amazon.com Checkout",
    "Amazon.co.uk Checkout",
    "Place Your Order - Amazon.ca Checkout",
    "Place Your Order - Amazon.co.uk Checkout",
    "Amazon.de Checkout",
    "Place Your Order - Amazon.de Checkout",
    "Amazon.de - Bezahlvorgang",
    "Bestellung aufgeben - Amazon.de-Bezahlvorgang",
    "Place Your Order - Amazon.com Checkout",
    "Place Your Order - Amazon.com",
    "Tramitar pedido en Amazon.es",
    "Processus de paiement Amazon.com",
    "Confirmar pedido - Compra Amazon.es",
    "Passez votre commande - Processus de paiement Amazon.fr",
    "Ordina - Cassa Amazon.it",
    "AmazonSmile Checkout",
    "Plaats je bestelling - Amazon.nl-kassa",
]
ORDER_COMPLETE_TITLES = [
    "Amazon.com Thanks You",
    "Amazon.ca Thanks You",
    "AmazonSmile Thanks You",
    "Thank you",
    "Amazon.fr Merci",
    "Merci",
    "Amazon.es te da las gracias",
    "Amazon.fr vous remercie.",
    "Grazie da Amazon.it",
    "Hartelijk dank",
]
ADD_TO_CART_TITLES = [
    "Amazon.com: Please Confirm Your Action",
    "Amazon.de: Bitte bestätigen Sie Ihre Aktion",
    "Amazon.de: Please Confirm Your Action",
    "Amazon.es: confirma tu acción",
    "Amazon.com : Veuillez confirmer votre action",  # Careful, required non-breaking space after .com (&nbsp)
    "Amazon.it: confermare l'operazione",
    "AmazonSmile: Please Confirm Your Action",
    "",  # Amazon.nl has en empty title, sigh.
]
DOGGO_TITLES = ["Sorry! Something went wrong!"]
SHIPPING_ONLY_IF = "FREE Shipping on orders over"


class Amazon:
    def __init__(
        self,
        notification_handler,
        headless=False,
        checkshipping=False,
        detailed=False,
        used=False,
    ):
        self.notification_handler = notification_handler
        self.asin_list = []
        self.reserve = []
        self.checkshipping = checkshipping
        self.detailed = detailed
        self.used = used
        if os.path.exists(AUTOBUY_CONFIG_PATH):
            with open(AUTOBUY_CONFIG_PATH) as json_file:
                try:
                    config = json.load(json_file)
                    self.username = config["username"]
                    self.password = config["password"]
                    self.asin_groups = int(config["asin_groups"])
                    self.amazon_website = config.get(
                        "amazon_website", "smile.amazon.com"
                    )
                    for x in range(self.asin_groups):
                        self.asin_list.append(config[f"asin_list_{x + 1}"])
                        self.reserve.append(float(config[f"reserve_{x + 1}"]))
                    # assert isinstance(self.asin_list, list)
                except Exception:
                    self.status_signal.emit(create_msg(
                        "amazon_config.json file not formatted properly: https://github.com/Hari-Nagarajan/nvidia-bot/wiki/Usage#json-configuration",
                        "error")
                    )
                    exit(0)
        else:
            self.status_signal.emit(create_msg(
                "No config file found, see here on how to fix this: https://github.com/Hari-Nagarajan/nvidia-bot/wiki/Usage#json-configuration",
                "error")
            )
            exit(0)

        if headless:
            enable_headless()

        # profile_amz = ".profile-amz"
        # # keep profile bloat in check
        # if os.path.isdir(profile_amz):
        #     os.remove(profile_amz)
        options.add_argument(f"user-data-dir=.profile-amz")
        try:
            self.driver = webdriver.Chrome(executable_path=binary_path, options=options)
            self.wait = WebDriverWait(self.driver, 10)
        except Exception as e:
            self.status_signal.emit(create_msg(f"{e}","error"))
            exit(1)

        for key in AMAZON_URLS.keys():
            AMAZON_URLS[key] = AMAZON_URLS[key].format(domain=self.amazon_website)
        self.driver.get(AMAZON_URLS["BASE_URL"])
        self.status_signal.emit(create_msg("Waiting for home page.", "normal"))
        self.check_if_captcha(self.wait_for_pages, HOME_PAGE_TITLES)
        if self.is_logged_in():
            self.status_signal.emit(create_msg("Already logged in", "normal"))
        else:
            self.status_signal.emit(create_msg("Lets log in.", "normal"))

            is_smile = "smile" in AMAZON_URLS["BASE_URL"]
            xpath = (
                '//*[@id="ge-hello"]/div/span/a'
                if is_smile
                else '//*[@id="nav-link-accountList"]/div/span'
            )
            selenium_utils.button_click_using_xpath(self.driver, xpath)
            self.status_signal.emit(create_msg("Wait for Sign In page", "normal"))
            self.check_if_captcha(self.wait_for_pages, SIGN_IN_TITLES)
            self.login()
            self.status_signal.emit(create_msg("Waiting 15 seconds.", "normal"))
            time.sleep(
                15
            )  # We can remove this once I get more info on the phone verification page.

    def is_logged_in(self):
        try:
            text = self.driver.find_element_by_id("nav-link-accountList").text
            return not any(sign_in in text for sign_in in SIGN_IN_TEXT)
        except Exception:
            return False

    def login(self):

        try:
            self.status_signal.emit(create_msg("Email", "normal"))
            self.driver.find_element_by_xpath('//*[@id="ap_email"]').send_keys(
                self.username + Keys.RETURN
            )
        except:
            self.status_signal.emit(create_msg("Email not needed.", "normal"))
            pass

        if self.driver.find_elements_by_xpath('//*[@id="auth-error-message-box"]'):
            self.status_signal.emit(create_msg("Login failed, check your username in amazon_config.json", "error"))
            time.sleep(240)
            exit(1)

        self.status_signal.emit(create_msg("Remember me checkbox", "normal"))
        selenium_utils.button_click_using_xpath(self.driver, '//*[@name="rememberMe"]')

        self.status_signal.emit(create_msg("Password", "normal"))
        self.driver.find_element_by_xpath('//*[@id="ap_password"]').send_keys(
            self.password + Keys.RETURN
        )

        self.status_signal.emit(create_msg(f"Logged in as {self.username}", "normal"))

    def run_item(self, delay=3, test=False):
        self.save_screenshot("start-up")
        self.status_signal.emit(create_msg("Checking stock for items.", "normal"))
        checkout_success = False
        while not checkout_success:
            pop_list = []
            for i in range(len(self.asin_list)):
                for asin in self.asin_list[i]:
                    checkout_success = self.check_stock(asin, self.reserve[i])
                    if checkout_success:
                        self.status_signal.emit(create_msg(f"attempting to buy {asin}", "normal"))
                        if self.checkout(test=test):
                            self.status_signal.emit(create_msg(f"bought {asin}", "normal"))
                            pop_list.append(asin)
                            break
                        else:
                            self.status_signal.emit(create_msg(f"checkout for {asin} failed", "normal"))
                            checkout_success = False
                    time.sleep(delay)
            if pop_list:
                for asin in pop_list:
                    for i in range(len(self.asin_list)):
                        if asin in self.asin_list[i]:
                            self.asin_list.pop(i)
                            self.reserve.pop(i)
                            break
            if self.asin_list:  # keep bot going if additional ASINs left
                checkout_success = False

    def check_stock(self, asin, reserve):
        if self.checkshipping:
            if self.used:
                f = furl(AMAZON_URLS["OFFER_URL"] + asin)
            else:
                f = furl(AMAZON_URLS["OFFER_URL"] + asin + "/ref=olp_f_new&f_new=true")
        else:
            if self.used:
                f = furl(AMAZON_URLS["OFFER_URL"] + asin + "/f_freeShipping=on")
            else:
                f = furl(
                    AMAZON_URLS["OFFER_URL"]
                    + asin
                    + "/ref=olp_f_new&f_new=true&f_freeShipping=on"
                )
        try:
            self.driver.get(f.url)
            elements = self.driver.find_elements_by_xpath(
                '//*[@name="submit.addToCart"]'
            )
            prices = self.driver.find_elements_by_xpath(
                '//*[@class="a-size-large a-color-price olpOfferPrice a-text-bold"]'
            )
            shipping = self.driver.find_elements_by_xpath(
                '//*[@class="a-color-secondary"]'
            )
        except Exception as e:
            self.status_signal.emit(create_msg(f"{e}", "error"))
            return False

        for i in range(len(elements)):
            price = parse_price(prices[i].text)
            if SHIPPING_ONLY_IF in shipping[i].text:
                ship_price = parse_price("0")
            else:
                ship_price = parse_price(shipping[i].text)
            ship_float = ship_price.amount
            price_float = price.amount
            if price_float is None:
                return False
            if ship_float is None or not self.checkshipping:
                ship_float = 0

            if (ship_float + price_float) <= reserve or math.isclose(
                (price_float + ship_float), reserve, abs_tol=0.01
            ):
                self.status_signal.emit(create_msg("Item in stock and under reserve!", "normal"))
                elements[i].click()
                self.status_signal.emit(create_msg("clicking add to cart", "normal"))
                return True
        return False

    def save_screenshot(self, page):
        file_name = get_timestamp_filename("screenshot-" + page, ".png")

        if self.driver.save_screenshot(file_name):
            try:
                self.notification_handler.send_notification(page, file_name)
            except TimeoutException:
                self.status_signal.emit(create_msg("Timed out taking screenshot, trying to continue anyway", "normal"))
                pass
            except Exception as e:
                self.status_signal.emit(create_msg(f"Trying to recover from error: {e}", "error"))
                pass
        else:
            self.status_signal.emit(create_msg("Error taking screenshot due to File I/O error", "error"))

    def save_page_source(self, page):
        """Saves DOM at the current state when called.  This includes state changes from DOM manipulation via JS"""
        file_name = get_timestamp_filename(page + "_source", "html")

        page_source = self.driver.page_source
        with open(file_name, "w", encoding="utf-8") as f:
            f.write(page_source)

    def get_captcha_help(self):
        if not self.on_captcha_page():
            self.status_signal.emit(create_msg("Not on captcha page.", "normal"))
            return
        try:
            self.status_signal.emit(create_msg("Stuck on a captcha... Lets try to solve it.", "normal"))
            captcha = AmazonCaptcha.fromdriver(self.driver)
            solution = captcha.solve()
            self.status_signal.emit(create_msg(f"The solution is: {solution}", "normal"))
            if solution == "Not solved":
                self.status_signal.emit(create_msg(f"Failed to solve {captcha.image_link}, lets reload and get a new captcha.", "normal"))
                self.driver.refresh()
                time.sleep(5)
                self.get_captcha_help()
            else:
                self.save_screenshot("captcha")
                self.driver.find_element_by_xpath(
                    '//*[@id="captchacharacters"]'
                ).send_keys(solution + Keys.RETURN)
        except Exception as e:
            self.status_signal.emit(create_msg(f"{e}", "normal"))
            self.status_signal.emit(create_msg("Error trying to solve captcha. Refresh and retry.", "normal"))
            self.driver.refresh()
            time.sleep(5)

    def on_captcha_page(self):
        try:
            if self.driver.title in CAPTCHA_PAGE_TITLES:
                return True
            if self.driver.find_element_by_xpath(
                '//form[@action="/errors/validateCaptcha"]'
            ):
                return True
        except Exception:
            pass
        return False

    def check_if_captcha(self, func, args):
        try:
            func(args)
        except Exception as e:
            self.status_signal.emit(create_msg(f"{str(e)}", "normal"))
            if self.on_captcha_page():
                self.get_captcha_help()
                func(args, t=300)
            else:
                self.status_signal.emit(create_msg(f"{self.driver.title}", "normal"))
                self.status_signal.emit(create_msg(
                    f"An error happened, please submit a bug report including a screenshot of the page the selenium "
                    f"browser is on. There may be a file saved at: amazon-{func.__name__}.png",
                    "error")
                )
                self.save_screenshot("title-fail")
                time.sleep(60)
                # self.driver.close()
                self.status_signal.emit(create_msg(f"{e}", "normal"))
                pass

    def wait_for_pages(self, page_titles, t=30):
        try:
            selenium_utils.wait_for_any_title(self.driver, page_titles, t)
        except Exception as e:
            self.status_signal.emit(create_msg(f"wait_for_pages exception: {e}", "normal"))
            pass

    def wait_for_pyo_page(self):
        self.check_if_captcha(self.wait_for_pages, CHECKOUT_TITLES + SIGN_IN_TITLES)

        if self.driver.title in SIGN_IN_TITLES:
            self.status_signal.emit(create_msg("Need to sign in again", "normal"))
            self.login()

    def finalize_order_button(self, test, retry=0):
        returnVal = False
        button_xpaths = [
            '//*[@id="orderSummaryPrimaryActionBtn"]',
            '//*[@id="bottomSubmitOrderButtonId"]/span/input',
            '//*[@id="placeYourOrder"]/span/input',
            '//*[@id="submitOrderButtonId"]/span/input',
            '//input[@name="placeYourOrder1"]',
            '//*[@id="hlb-ptc-btn-native"]',
            '//*[@id="sc-buy-box-ptc-button"]/span/input',
        ]
        button = None
        for button_xpath in button_xpaths:
            try:
                if (
                    self.driver.find_element_by_xpath(button_xpath).is_displayed()
                    and self.driver.find_element_by_xpath(button_xpath).is_enabled()
                ):
                    button = self.driver.find_element_by_xpath(button_xpath)
            except NoSuchElementException:
                self.status_signal.emit(create_msg(f"{button_xpath}, lets try a different one.", "normal"))
        if button:
            self.status_signal.emit(create_msg(f"Clicking Button: {button.text}", "normal"))
            if not test:
                button.click()
            return True
        else:
            if retry < 3:
                # log.info("Couldn't find button. Lets retry in a sec.")
                time.sleep(2)
                returnVal = self.finalize_order_button(test, retry + 1)
            else:
                self.status_signal.emit(create_msg("Couldn't find button after 3 retries. Open a GH issue for this.", "normal"))
                self.save_page_source("finalize-order-button-fail")
                self.save_screenshot("finalize-order-button-fail")
        return returnVal

    def wait_for_order_completed(self, test):
        if not test:
            try:
                self.check_if_captcha(self.wait_for_pages, ORDER_COMPLETE_TITLES)
            except:
                self.status_signal.emit(create_msg("error during order completion", "error"))
                self.save_screenshot("order-failed")
                return False
        else:
            self.status_signal.emit(create_msg("This is a test, so we don't need to wait for the order completed page.", "normal"))
        return True

    def checkout(self, test):
        self.status_signal.emit(create_msg("Waiting for Cart Page", "normal"))
        self.notification_handler.send_notification("Attempting to checkout")
        self.check_if_captcha(self.wait_for_pages, SHOPING_CART_TITLES)
        if self.detailed:
            self.save_screenshot("waiting-for-cart")

        try:  # This is fast.
            self.status_signal.emit(create_msg("Quick redirect to checkout page", "normal"))
            cart_initiate_id = self.driver.find_element_by_name("cartInitiateId")
            cart_initiate_id = cart_initiate_id.get_attribute("value")
            self.driver.get(
                CHECKOUT_URL.format(
                    domain=self.amazon_website, cart_id=cart_initiate_id
                )
            )
        except:
            self.status_signal.emit(create_msg("clicking checkout.", "normal"))
            try:
                self.driver.find_element_by_xpath(
                    '//*[@id="hlb-ptc-btn-native"]'
                ).click()
            except:
                self.save_screenshot("start-checkout-fail")
                self.status_signal.emit(create_msg("Failed to checkout. Returning to stock check.", "normal"))
                return False

        self.status_signal.emit(create_msg("Waiting for Place Your Order Page", "normal"))
        self.wait_for_pyo_page()

        self.status_signal.emit(create_msg("Attempting to Finish checkout", "normal"))
        if self.detailed:
            self.save_screenshot("finish-checkout")

        if not self.finalize_order_button(test):
            self.status_signal.emit(create_msg("Failed to click finalize the order", "normal"))
            if self.detailed:
                self.save_screenshot("finalize-fail")
            return False

        self.status_signal.emit(create_msg("Waiting for Order completed page.", "normal"))
        if not self.wait_for_order_completed(test):
            self.status_signal.emit(create_msg("order not completed, going back to stock check", "normal"))
            return False

        self.status_signal.emit(create_msg("Order Placed.", "normal"))
        self.save_screenshot("order-placed")
        return True


def get_timestamp_filename(name, extension):
    """Utility method to create a filename with a timestamp appended to the root and before
    the provided file extension"""
    now = datetime.now()
    date = now.strftime("%m-%d-%Y_%H_%M_%S")
    if extension.startswith("."):
        return name + "_" + date + extension
    else:
        return name + "_" + date + "." + extension